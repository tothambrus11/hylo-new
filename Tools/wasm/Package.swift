// swift-tools-version:6.3
import PackageDescription

// The Hylo compiler as a WebAssembly module, for running in a browser.
//
// This is a separate package so that the compiler's own package, and every CI job building it,
// is unaffected by the WebAssembly build and its prerequisites. It is meant to be built with the
// Swift SDK for WebAssembly, against an LLVM cross-compiled for `wasm32-unknown-wasip1` by
// `build-llvm.sh`; see `README.md`.

/// The installation of LLVM for wasm32 that `build-llvm.sh` produces.
///
/// Swifty-LLVM finds the same installation through the `llvm.pc` file it contains, which must be
/// in `PKG_CONFIG_PATH`; this package additionally needs lld's headers from it.
let llvmPrefix = Context.environment["LLVM_WASM_PREFIX"] ?? "/LLVM_WASM_PREFIX-is-not-set"

let package = Package(
  name: "hylo-wasm",
  platforms: [
    .macOS(.v26)
  ],
  products: [
    .executable(name: "hylo-wasm", targets: ["hylo-wasm"])
  ],
  dependencies: [
    .package(name: "hylo-new", path: "../.."),
    .package(path: "../../Swifty-LLVM"),
  ],
  targets: [
    // What compiling a program is, independently of how a request arrives.
    .target(
      name: "HyloWasmSession",
      dependencies: [
        .target(name: "WasmLinker"),
        .product(name: "HyloFrontEnd", package: "hylo-new"),
        .product(name: "HyloBackEnd", package: "hylo-new"),
        .product(name: "SwiftyLLVM", package: "Swifty-LLVM"),
      ]),

    // lld's WebAssembly port, called in-process.
    .target(
      name: "WasmLinker",
      cxxSettings: [
        .unsafeFlags([
          "-I", "\(llvmPrefix)/include",
          // Configures libc++ the way LLVM was compiled; see `build-llvm.sh`.
          "-I", "\(llvmPrefix)/libcxx-threads",
          "-fno-exceptions", "-fno-rtti",
        ])
      ]),

    // The browser transport: functions exported from a WebAssembly reactor.
    .executableTarget(
      name: "hylo-wasm",
      dependencies: [
        .target(name: "HyloWasmSession"),
        // Not used by the reactor, which is handed the standard library's sources by its host,
        // but depending on it is what puts the sources, including the generated ones, in the
        // build directory, where `build-compiler.sh` collects them.
        .product(name: "HyloStandardLibrary", package: "hylo-new"),
      ],
      linkerSettings: [
        .unsafeFlags([
          "-Xclang-linker", "-mexec-model=reactor",
          // LLVM reaches mmap in code the compiler never runs; wasi-libc emulates it.
          "-Xlinker", "-lwasi-emulated-mman",
          // Compiling takes more stack than the default 64 KiB. (`--stack-first`, which would make
          // an overflow trap instead of corrupting data, conflicts with the `--global-base` that
          // the Swift driver passes.)
          "-Xlinker", "-z", "-Xlinker", "stack-size=8388608",
        ])
      ]),
  ],
  cxxLanguageStandard: .cxx20)
