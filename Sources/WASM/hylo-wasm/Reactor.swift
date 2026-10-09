import FoundationEssentials
import HyloWASMSession

// A WebAssembly reactor compiling Hylo programs to WebAssembly.
//
// A browser has no file system to read the standard library from and no way to keep a command's
// standard input open across turns of its event loop, so the compiler is built as a reactor: the
// host instantiates it once, hands over the standard library's sources through `hylo_init`, and
// then calls `hylo_compile` as often as it likes. Compiling the standard library happens in
// `hylo_init` and is not repeated.
//
// Strings cross the boundary as UTF-8 in linear memory. A buffer the host must read back is
// prefixed with its length as a little-endian `UInt32`, so one pointer is enough to return one;
// the host frees it with `hylo_free`.
//
// Linking happens in-process, through the WASI file system: the host must preopen the directory
// named `sysroot` in the request to `hylo_init`, holding the files `CompilerSession` links into
// every executable in its `lib` subdirectory, and a writable directory named `scratch`.

/// The session serving `hylo_compile`, or `nil` until `hylo_init` has succeeded and after a
/// request has left the compiler unusable.
nonisolated(unsafe) private var session: CompilerSession? = nil

/// Returns a buffer of `n` bytes for the host to write a request into.
@_expose(wasm, "hylo_alloc")
@_cdecl("hylo_alloc")
public func hylo_alloc(_ n: Int32) -> UnsafeMutableRawPointer {
  .allocate(byteCount: Int(n), alignment: 1)
}

/// Deallocates a buffer returned by `hylo_alloc`, `hylo_init` or `hylo_compile`.
@_expose(wasm, "hylo_free")
@_cdecl("hylo_free")
public func hylo_free(_ p: UnsafeMutableRawPointer) {
  p.deallocate()
}

/// Compiles the standard library described by the JSON `InitRequest` in `p`, returning a JSON
/// object with `ok: true` if it compiled and an `error` otherwise.
///
/// Calling this again replaces the session serving later requests if, and only if, the new
/// standard library compiles.
@_expose(wasm, "hylo_init")
@_cdecl("hylo_init")
public func hylo_init(_ p: UnsafeRawPointer, _ n: Int32) -> UnsafeMutableRawPointer {
  answer {
    let r = try JSONDecoder().decode(InitRequest.self, from: read(p, n))
    let s = runToCompletion {
      await CompilerSession(
        standardLibrary: r.standardLibrary, sysroot: r.sysroot, scratch: r.scratch)
    }
    // A standard library that does not compile would make every request fail in confusing ways,
    // so the session is only installed once it is known to be sound.
    if s.diagnostics.contains(where: { $0.level == "error" }) {
      let text = s.diagnostics.map(\.rendered).joined()
      return try encode(Failure(error: "the standard library does not compile:\n\(text)"))
    }
    session = s
    return try encode(Success())
  }
}

/// Compiles the program described by the JSON `CompileRequest` in `p`, returning a JSON
/// `CompileResponse`.
@_expose(wasm, "hylo_compile")
@_cdecl("hylo_compile")
public func hylo_compile(_ p: UnsafeRawPointer, _ n: Int32) -> UnsafeMutableRawPointer {
  answer {
    guard let s = session else {
      return try encode(Failure(error: "the standard library has not been loaded"))
    }
    let request = try JSONDecoder().decode(CompileRequest.self, from: read(p, n))
    let r = runToCompletion { await s.compile(request) }
    if r.compilerUnusable { session = nil }
    return try encode(r)
  }
}

/// The argument of `hylo_init`.
private struct InitRequest: Decodable, Sendable {

  /// The standard library's sources, keyed by file name.
  let standardLibrary: [String: String]

  /// The directory containing the files linked into executables.
  let sysroot: String

  /// A writable directory for intermediate files.
  let scratch: String

}

/// The answer to a `hylo_init` that succeeded.
private struct Success: Encodable {

  /// Always `true`; the field exists so that a host can tell the two answers apart.
  let ok = true

}

/// The answer to a request that could not be served.
private struct Failure: Encodable {

  /// What went wrong.
  let error: String

}

/// Returns the `n` bytes at `p`.
private func read(_ p: UnsafeRawPointer, _ n: Int32) -> Data {
  .init(bytes: p, count: Int(n))
}

/// Returns `x` as JSON.
private func encode<T: Encodable>(_ x: T) throws -> Data {
  let e = JSONEncoder()
  e.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
  e.dataEncodingStrategy = .base64
  return try e.encode(x)
}

/// Returns the result of `body` in a length-prefixed buffer, reporting a thrown error as a JSON
/// object with an `error` field.
///
/// Nothing may escape into the host as a Swift error: a reactor that traps takes its instance,
/// and with it the compiled standard library, down with it.
private func answer(_ body: () throws -> Data) -> UnsafeMutableRawPointer {
  let payload: Data
  do {
    payload = try body()
  } catch {
    payload = (try? encode(Failure(error: "\(error)")))
      ?? Data(#"{"error":"the failure could not be reported"}"#.utf8)
  }

  let result = UnsafeMutableRawPointer.allocate(byteCount: 4 + payload.count, alignment: 4)
  result.storeBytes(of: UInt32(payload.count).littleEndian, as: UInt32.self)
  payload.withUnsafeBytes { (b) in
    result.advanced(by: 4).copyMemory(from: b.baseAddress!, byteCount: b.count)
  }
  return result
}
