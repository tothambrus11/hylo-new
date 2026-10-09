// swift-tools-version:6.3
import PackageDescription

#if os(Windows)
  let onWindows = true
#else
  let onWindows = false
#endif

/// Settings common to all Swift targets.
let commonSwiftSettings: [SwiftSetting] = [
  .unsafeFlags(["-warnings-as-errors"])
]

let package = Package(
  name: "Hylo",
  platforms: [
    .macOS(.v26)
  ],
  products: [
    .executable(name: "hc", targets: ["hc"]),
    .executable(name: "hylo-demangle", targets: ["hylo-demangle"]),
    .library(name: "HyloStandardLibrary", targets: ["StandardLibrary"]),
    .library(name: "HyloFrontEnd", targets: ["FrontEnd"]),
  ],
  dependencies: [
    .package(
      url: "https://github.com/attaswift/BigInt.git",
      from: "6.0.1"),
    .package(
      url: "https://github.com/kyouko-taiga/Archivist.git",
      from: "1.0.0"),
    .package(
      url: "https://github.com/apple/swift-algorithms.git",
      from: "1.2.0"),
    .package(
      url: "https://github.com/apple/swift-argument-parser.git",
      from: "1.1.4"),
    .package(
      url: "https://github.com/apple/swift-collections.git",
      from: "1.1.0"),
    .package(path: "./Swifty-LLVM"),
    .package(
      url: "https://github.com/swiftlang/swift-subprocess.git",
      from: "1.0.0"),
  ],
  targets: [
    .executableTarget(
      name: "hc",
      dependencies: [
        .target(name: "Driver"),
        .target(name: "FrontEnd"),
        .target(name: "HostUtilities"),
        .target(name: "Utilities"),
        .product(name: "ArgumentParser", package: "swift-argument-parser"),
        .product(name: "SwiftyLLVM", package: "Swifty-LLVM"),
      ],
      swiftSettings: commonSwiftSettings),

    .executableTarget(
      name: "hc-tests",
      dependencies: [
        .product(name: "ArgumentParser", package: "swift-argument-parser")
      ],
      swiftSettings: commonSwiftSettings),

    .executableTarget(
      name: "hylo-demangle",
      dependencies: [
        .target(name: "FrontEnd"),
        .product(name: "ArgumentParser", package: "swift-argument-parser"),
      ],
      swiftSettings: commonSwiftSettings),

    .executableTarget(
      name: "frontend-smoke-test",
      dependencies: [
        .target(name: "FrontEnd"),
        .target(name: "StandardLibrary"),
      ],
      swiftSettings: commonSwiftSettings),

    .executableTarget(
      name: "hc-generate-stdlib",
      dependencies: [
        .product(name: "ArgumentParser", package: "swift-argument-parser"),
        .target(name: "HostUtilities"),
        .target(name: "Utilities"),
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "Driver",
      dependencies: [
        .target(name: "BackEnd"),
        .target(name: "FrontEnd"),
        .target(name: "HostUtilities"),
        .target(name: "StandardLibrary"),
        .target(name: "Utilities"),
        .product(name: "Archivist", package: "archivist"),
        .product(name: "Subprocess", package: "swift-subprocess"),
        .product(name: "SwiftyLLVM", package: "Swifty-LLVM"),
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "BackEnd",
      dependencies: [
        .target(name: "FrontEnd"),
        .target(name: "Utilities"),
        .product(name: "SwiftyLLVM", package: "Swifty-LLVM"),
      ],
      swiftSettings: commonSwiftSettings,
    ),

    .target(
      name: "FrontEnd",
      dependencies: [
        .target(name: "Utilities"),
        .target(name: "StableCollections"),
        .product(name: "Archivist", package: "archivist"),
        .product(name: "Algorithms", package: "swift-algorithms"),
        .product(name: "Collections", package: "swift-collections"),
        .product(name: "BigInt", package: "BigInt"),
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "StableCollections",
      dependencies: [
        .target(name: "Utilities")
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "StandardLibrary",
      path: "StandardLibrary",
      resources: [.copy("Sources")],
      swiftSettings: commonSwiftSettings,
      plugins: ["GenerateStandardLibraryPlugin"]),

    .target(
      name: "Utilities",
      dependencies: [
        .product(name: "Algorithms", package: "swift-algorithms"),
        .product(name: "Collections", package: "swift-collections"),
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "HostUtilities",
      dependencies: [
        .product(name: "Subprocess", package: "swift-subprocess")
      ],
      swiftSettings: commonSwiftSettings),

    .target(
      name: "Interpreter",
      dependencies: [
        "FrontEnd",
        .product(name: "Collections", package: "swift-collections"),
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "CompilerTests",
      dependencies: [
        .target(name: "Driver"),
        .target(name: "FrontEnd"),
        .target(name: "HostUtilities"),
        .target(name: "StandardLibrary"),
        .target(name: "Utilities"),
        .product(name: "Subprocess", package: "swift-subprocess"),
      ],
      exclude: ["negative", "positive", "README.md"],
      swiftSettings: commonSwiftSettings,
      plugins: ["CompilerTestsPlugin"]),

    .testTarget(
      name: "CommandLineTests",
      dependencies: [
        .target(name: "hc"),
        .target(name: "FrontEnd"),
        .target(name: "HostUtilities"),
        .target(name: "Utilities"),
        .product(name: "ArgumentParser", package: "swift-argument-parser"),
        .product(name: "Subprocess", package: "swift-subprocess"),
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "FrontEndTests",
      dependencies: [
        .target(name: "FrontEnd"),
        .target(name: "StandardLibrary"),
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "BackEndTests",
      dependencies: [
        .target(name: "BackEnd"),
        .product(name: "BigInt", package: "BigInt"),
        .target(name: "Driver"),
        .target(name: "HostUtilities"),
        .target(name: "Utilities"),
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "RuntimeTests",
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "StableCollectionsTests",
      dependencies: [
        .target(name: "StableCollections")
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "UtilitiesTests",
      dependencies: [
        .target(name: "HostUtilities"),
        .target(name: "Utilities"),
        .product(name: "Subprocess", package: "swift-subprocess"),
      ],
      swiftSettings: commonSwiftSettings),

    .testTarget(
      name: "InterpreterTests",
      dependencies: [
        "Interpreter", "FrontEnd", "Driver"
      ],
      resources: [
        .copy("InterpreterTestPrograms")
      ],
      swiftSettings: commonSwiftSettings),

    .plugin(
      name: "CompilerTestsPlugin",
      capability: .buildTool(),
      dependencies: [
        .target(name: "hc-tests"),
      ],
      packageAccess: true),

    .plugin(
      name: "GenerateStandardLibraryPlugin",
      capability: .buildTool(),
      dependencies: [
        .target(name: "hc-generate-stdlib"),
      ]),
  ])

// The compiler built for WebAssembly, to run in a browser, which the website's playground runs.
// Its targets exist only when the manifest is evaluated with `LLVM_WASM_PREFIX` naming an LLVM
// built to run in WebAssembly, which `Sources/WASM/scripts/build-compiler.sh` sets: they compile
// against that LLVM, so no other build could build them. See `Sources/WASM/README.md`.
if let llvm = Context.environment["LLVM_WASM_PREFIX"] {
  package.products.append(.executable(name: "hylo-wasm", targets: ["hylo-wasm"]))
  package.targets += [
    // The browser transport: functions exported from a WebAssembly reactor.
    .executableTarget(
      name: "hylo-wasm",
      dependencies: [
        .target(name: "HyloWASMSession")
      ],
      path: "Sources/WASM/hylo-wasm",
      swiftSettings: commonSwiftSettings,
      linkerSettings: [
        .unsafeFlags([
          "-Xclang-linker", "-mexec-model=reactor",
          // `build-compiler.sh` runs wasm-opt on the module; clang would otherwise run it too,
          // whenever it is on `PATH`, which takes minutes and gains nothing.
          "-Xclang-linker", "--no-wasm-opt",
          // LLVM reaches mmap in code the compiler never runs; wasi-libc emulates it.
          "-Xlinker", "-lwasi-emulated-mman",
          // Compiling takes more stack than the default 64 KiB. (`--stack-first`, which would make
          // an overflow trap instead of corrupting data, conflicts with the `--global-base` that
          // the Swift driver passes.)
          "-Xlinker", "-z", "-Xlinker", "stack-size=8388608",
        ])
      ]),

    // What compiling a program is, independently of how a request arrives.
    .target(
      name: "HyloWASMSession",
      dependencies: [
        .target(name: "BackEnd"),
        .target(name: "FrontEnd"),
        .target(name: "WASMLinker"),
        .product(name: "SwiftyLLVM", package: "Swifty-LLVM"),
      ],
      path: "Sources/WASM/HyloWASMSession",
      swiftSettings: commonSwiftSettings),

    // lld's WebAssembly port, called in-process. Swifty-LLVM finds LLVM through the `llvm.pc` in
    // `LLVM_WASM_PREFIX`; this needs lld's headers from it too.
    .target(
      name: "WASMLinker",
      path: "Sources/WASM/WASMLinker",
      cxxSettings: [
        .unsafeFlags([
          "-I", "\(llvm)/include",
          // Configures libc++ the way LLVM was compiled; see llvm-build's docs/wasm.md.
          "-I", "\(llvm)/libcxx-threads",
          "-std=c++20", "-fno-exceptions", "-fno-rtti",
        ])
      ]),
  ]
}
