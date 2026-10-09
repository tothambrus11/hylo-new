import BackEnd
import FoundationEssentials
import FrontEnd
import SwiftyLLVM
import WASILibc
import WASMLinker

/// A Hylo compiler whose standard library has been compiled once, compiling programs written
/// against it to WebAssembly.
///
/// Compiling the standard library dominates the cost of a session and happens when it is created.
/// Each request is then compiled in a copy of the resulting program, which is discarded afterwards
/// so that a long-lived session does not retain every request it has served.
public struct CompilerSession: Sendable {

  /// The program containing the standard library, compiled to refined IR.
  private let baseline: Program

  /// Where the files linked into executables are, in the WASI file system.
  private let sysroot: String

  /// A directory where intermediate files can be written, in the WASI file system.
  private let scratch: String

  /// The issues found in the standard library.
  public let diagnostics: [DiagnosticDescription]

  /// Creates an instance compiling the standard library given by `sources`, linking executables
  /// with the files at `sysroot` and writing intermediate files into `scratch`.
  public init(standardLibrary sources: [SourceFile], sysroot: String, scratch: String) async {
    var p = Program()
    let m = p.demandModule(FrontEnd.Module.standardLibraryName)
    for f in sources {
      _ = p[m].addSource(f)
    }
    await Self.compileToRefinedIR(m, in: &p)

    self.diagnostics = p[m].diagnostics.flatMap(DiagnosticDescription.all(of:))
    self.baseline = p
    self.sysroot = sysroot
    self.scratch = scratch
  }

  /// Creates an instance compiling the standard library given by `sources`, keyed by file name.
  public init(
    standardLibrary sources: [String: String], sysroot: String, scratch: String
  ) async {
    // Sorted, so that the identities given to declarations do not depend on the order in which
    // the host happened to serialize the sources.
    await self.init(
      standardLibrary: sources.keys.sorted().map { (n) in
        SourceFile(name: .virtual(virtualURL(n)), contents: sources[n]!)
      },
      sysroot: sysroot, scratch: scratch)
  }

  /// Applies the compilation phases up to refined IR to `m`, stopping after the first phase that
  /// reports an error.
  private static func compileToRefinedIR(_ m: FrontEnd.Module.ID, in p: inout Program) async {
    await p.assignScopes(m)
    if p[m].containsError { return }
    p.assignTypes(m, loggingInferenceWhere: nil)
    if p[m].containsError { return }
    p.lower(m)
    if p[m].containsError { return }
    p.applyTransformationPasses(m)
  }

  /// Returns the result of compiling `request`.
  public func compile(_ request: CompileRequest) async -> CompileResponse {
    var r = CompileResponse()
    let start = ContinuousClock.now
    await compile(request, into: &r)
    let elapsed = start.duration(to: .now)
    r.milliseconds = Self.milliseconds(elapsed)
    return r
  }

  /// Compiles `request`, writing the results into `r`.
  private func compile(_ request: CompileRequest, into r: inout CompileResponse) async {
    let usesStandardLibrary = request.standardLibrary ?? true
    var p = usesStandardLibrary ? baseline : Program()
    let m = p.demandModule(.init("Main"))
    if usesStandardLibrary { p[m].addDependency(FrontEnd.Module.standardLibraryName) }
    let main = SourceFile(name: .virtual(virtualURL("main.hylo")), contents: request.source)
    _ = p[m].addSource(main)

    // The front end, up to the phase the request asks for.
    defer { r.diagnostics = p[m].diagnostics.flatMap(DiagnosticDescription.all(of:)) }
    if p[m].containsError || !request.runs(.scoping) { return }
    await p.assignScopes(m)
    if p[m].containsError || !request.runs(.typing) { return }
    p.assignTypes(m, loggingInferenceWhere: nil)
    if p[m].containsError || !request.runs(.lowering) { return }
    p.lower(m)
    if p[m].containsError { return }
    if request.wants(.rawIR) { r.artifacts["raw-ir"] = p.show(p[m].ir) }
    p.applyTransformationPasses(m)
    if p[m].containsError { return }
    if request.wants(.ir) { r.artifacts["ir"] = p.show(p[m].ir) }
    guard request.wants(.llvm) || request.wants(.assembly) || request.wants(.executable) else {
      return
    }

    // The back end.
    do {
      let target = try TargetSpecification(target: Target(triple))
      let machine = TargetMachine(target: target, optimization: request.optimizationLevel)
      var llvm = try p.compileToLLVM(m, target: machine)
      // The back end reports some errors as diagnostics of the program.
      if p[m].containsError { return }
      try llvm.verify()
      llvm.runDefaultModulePasses(optimization: request.optimizationLevel)

      if request.wants(.llvm) { r.artifacts["llvm"] = llvm.llCode() }
      if request.wants(.assembly) {
        r.artifacts["assembly"] = try llvm.compile(.assembly).utf8Decoded ?? ""
      }
      if request.wants(.executable) {
        let object = try llvm.compile(.objectFile)
        r.executable = try link(object)
      }
    } catch let e as LinkError {
      r.error = "\(e)"
      r.compilerUnusable = !e.canRunAgain
    } catch let e {
      r.error = "\(e)"
    }
  }

  /// Returns the executable resulting from linking `object` with the standard library's runtime
  /// support and the C library.
  private func link(_ object: borrowing MemoryBuffer) throws -> Data {
    let input = "\(scratch)/main.o"
    let output = "\(scratch)/main.wasm"
    try object.withUnsafeBytes { (b) in
      try Data(buffer: b).write(to: URL(fileURLWithPath: input))
    }

    let arguments = [
      "wasm-ld",
      "-o", output,
      "\(sysroot)/lib/crt1-command.o",
      "\(sysroot)/lib/entry.o",
      input,
      "\(sysroot)/lib/shims.o",
      "-L\(sysroot)/lib",
      "-lc",
      "\(sysroot)/lib/libclang_rt.builtins-wasm32.a",
    ]
    var diagnostics: UnsafeMutablePointer<CChar>? = nil
    var canRunAgain = true
    let status = withCStrings(arguments) { (argv) in
      hylo_wasm_link(Int32(arguments.count), argv, &diagnostics, &canRunAgain)
    }
    defer { free(diagnostics) }

    if status != 0 {
      throw LinkError(
        message: diagnostics.map({ String(cString: $0) }) ?? "", canRunAgain: canRunAgain)
    }
    return try Data(contentsOf: URL(fileURLWithPath: output))
  }

  /// The triple of the code this session generates.
  public let triple = "wasm32-unknown-wasip1"

  /// Returns `d` in milliseconds.
  private static func milliseconds(_ d: Duration) -> Double {
    let (s, a) = d.components
    return Double(s) * 1e3 + Double(a) / 1e15
  }

}

/// A failure to link an executable.
public struct LinkError: Error, CustomStringConvertible {

  /// What the linker reported.
  public let message: String

  /// `false` iff the failure may have left the linker unable to run again in this process.
  public let canRunAgain: Bool

  /// A textual representation of `self`.
  public var description: String { "link failed: \(message)" }

}

/// Calls `body` with `strings` as an array of null-terminated C strings.
///
/// The pointers and the characters they point to share one allocation: the table of pointers
/// first, since it has the stricter alignment, then each string's UTF-8 and its terminator.
private func withCStrings<T>(
  _ strings: [String], _ body: (UnsafePointer<UnsafePointer<CChar>?>) -> T
) -> T {
  typealias Element = UnsafePointer<CChar>?
  let tableSize = MemoryLayout<Element>.stride * strings.count
  let characterCount = strings.reduce(0, { $0 + $1.utf8.count + 1 })
  let buffer = UnsafeMutableRawPointer.allocate(
    byteCount: tableSize + characterCount, alignment: MemoryLayout<Element>.alignment)
  defer { buffer.deallocate() }

  let table = buffer.bindMemory(to: Element.self, capacity: strings.count)
  var next = buffer + tableSize
  for (i, s) in strings.enumerated() {
    let n = s.utf8.count
    UnsafeMutableRawBufferPointer(start: next, count: n).copyBytes(from: s.utf8)
    next.storeBytes(of: 0, toByteOffset: n, as: UInt8.self)
    table[i] = UnsafePointer(next.bindMemory(to: CChar.self, capacity: n + 1))
    next += n + 1
  }
  return body(table)
}

/// Returns a URL naming a virtual source file called `name`.
private func virtualURL(_ name: String) -> URL {
  let escaped = name.unicodeScalars.map({ (u) in isURLSafe(u) ? String(u) : "_" }).joined()
  return URL(string: "hylo:///\(escaped)")!
}

/// Returns `true` iff a virtual file name may contain `u` verbatim.
///
/// That is a letter, a mark or a number, which is what Foundation's `CharacterSet.alphanumerics`
/// contains, or one of `-._~/`. `CharacterSet` itself is not in `FoundationEssentials`.
private func isURLSafe(_ u: Unicode.Scalar) -> Bool {
  switch u.properties.generalCategory {
  case .uppercaseLetter, .lowercaseLetter, .titlecaseLetter, .modifierLetter, .otherLetter,
    .nonspacingMark, .spacingMark, .enclosingMark, .decimalNumber, .letterNumber, .otherNumber:
    return true
  default:
    return "-._~/".unicodeScalars.contains(u)
  }
}
