import Archivist
import Foundation
import FrontEnd
import LLVMEmitter
import StandardLibrary
import SwiftyLLVM
import Utilities
typealias Host = Utilities.Host

public typealias LLVMModule = SwiftyLLVM.Module

/// A FrontEnd module.
public typealias Module = FrontEnd.Module // Shadowing the name ambiguity

/// A helper to drive the compilation of Hylo source files.
public struct Driver {

  /// The path containing cached module data.
  public let moduleCachePath: URL?

  /// The target specification (triple + CPU + features).
  public var target: TargetSpecification

  /// The optimization level for code generation.
  public var optimization: OptimizationLevel

  /// The relocation model for code generation.
  public var relocation: RelocationModel

  /// The code model for code generation.
  public var codeModel: CodeModel

  /// The list of directories in which to search for libraries to link.
  public var librarySearchPaths: [URL]

  /// The names of the libraries to link.
  public var libraries: [String]

  /// `true` iff the standard library and its shim should be excluded from compilation and linking.
  public var noStandardLibrary: Bool = false

  /// The program being compiled by the driver.
  public var program: Program

  /// The corresponding LLVM module for each Hylo module.
  ///
  /// It's set after LLVM lowering.
  private var llvmModules: [Module.ID: LLVMModuleBox] = [:]

  /// Creates an instance with the given properties.
  public init(
    moduleCachePath: URL? = nil, targetSpecification: TargetSpecification,
    optimization: OptimizationLevel = .none,
    relocation: RelocationModel = .default,
    codeModel: CodeModel = .default,
    librarySearchPaths: [URL] = [], libraries: [String] = [],
  ) {
    self.moduleCachePath = moduleCachePath
    self.target = targetSpecification
    self.optimization = optimization
    self.relocation = relocation
    self.codeModel = codeModel
    self.librarySearchPaths = librarySearchPaths
    self.libraries = libraries
    self.program = .init()
  }

  /// `true` iff the driver should read/write modules from/to the cache.
  public var cachingIsEnabled: Bool {
    moduleCachePath != nil
  }

  /// Parses the source files in `inputs` and adds them to `module`.
  @discardableResult
  public mutating func parse(
    _ sources: [SourceFile], into module: Module.ID
  ) async -> (elapsed: Duration, containsError: Bool) {
    let clock = ContinuousClock()
    let elapsed = clock.measure {
      modify(&program[module]) { (m) in
        for s in sources { m.addSource(s) }
      }
    }
    return (elapsed, program[module].containsError)
  }

  /// Assigns the trees in `module` to their scopes.
  @discardableResult
  public mutating func assignScopes(
    of module: Module.ID
  ) async -> (elapsed: Duration, containsError: Bool) {
    let clock = ContinuousClock()
    let elapsed = await clock.measure {
      await program.assignScopes(module)
    }
    return (elapsed, program[module].containsError)
  }

  /// Assigns the trees in `module` to their types.
  @discardableResult
  public mutating func assignTypes(
    of module: Module.ID,
    loggingInferenceWhere isLoggingEnabled: ((AnySyntaxIdentity, Program) -> Bool)? = nil
  ) async -> (elapsed: Duration, containsError: Bool) {
    let clock = ContinuousClock()
    let elapsed = clock.measure {
      program.assignTypes(module, loggingInferenceWhere: isLoggingEnabled)
    }
    return (elapsed, program[module].containsError)
  }

  /// Lowers the contents of `module` to IR.
  @discardableResult
  public mutating func lower(
    _ module: Module.ID
  ) async -> (elapsed: Duration, containsError: Bool) {
    let clock = ContinuousClock()
    let elapsed = clock.measure {
      program.lower(module)
    }
    return (elapsed, program[module].containsError)
  }

  /// Applies mandatory transformation passes on the IR of `module`.
  @discardableResult
  public mutating func applyTransformationPasses(
    _ module: Module.ID
  ) async -> (elapsed: Duration, containsError: Bool) {
    let elapsed = ContinuousClock().measure {
      program.applyTransformationPasses(module)
    }
    return (elapsed, program[module].containsError)
  }

  /// Generates backend code for `module`.
  public mutating func lowerToLLVM(_ module: Module.ID) throws ->
    (elapsed: Duration, containsError: Bool) {
    precondition(llvmModules[module] == nil, "LLVM code is already generated for module \(moduleName(module))")

    let elapsed = try ContinuousClock().measure {
      var m = try program.compileToLLVM(
        module,
        target: TargetMachine(target: target, optimization: optimization, relocation: relocation, codeModel: codeModel))

      #if DEBUG
        try m.verify()
      #endif

      m.runDefaultModulePasses()

      #if DEBUG
        try m.verify()
      #endif

      llvmModules[module] = LLVMModuleBox(consume m)
    }
    return (elapsed, program[module].containsError)
  }

  /// Generates executable from `module`, linking the standard library unless `isFreestanding` is true.
  ///
  /// - Requires: `lowerToLLVM(_:)` has been called for `module`.
  /// - Throws when the parent folder of `output` doesn't exist.
  public mutating func generateExecutable(
    for module: Module.ID,
    writingTo output: URL
  ) throws -> (elapsed: Duration, containsError: Bool) {
    let elapsed = try ContinuousClock().measure {
      let modulesToLink = [module]
      if !noStandardLibrary {
        // todo enable this after we can lower the standard library
        // modulesToLink.append(program.modules[.standardLibrary]!.identity)
      }

      try FileManager.default.withUniqueTemporaryDirectory{ objectDirectory in
        let objects = try writeObjectFiles(for: modulesToLink, into: objectDirectory)
        try linkExecutable(from: objects, writingTo: output)
      }
    }
    return (elapsed, program[module].containsError)
  }

  /// Returns the LLVM IR generated for `module`, or `nil` if backend code has not been generated.
  public func llvmIR(of module: Module.ID) -> String? {
    llvmModules[module]?.module.llCode()
  }

  /// Returns the assembly generated for `module`.
  ///
  /// - Requires: `lowerToLLVM(_:)` has been called for `module`.
  public mutating func assembly(of module: Module.ID) throws -> String {
    let buffer = try llvmModules[module]!.module.compile(.assembly)
    return Self.decode(buffer)
  }

  /// Writes object files for `modules` into `directory` and returns their paths.
  ///
  /// - Requires: `lowerToLLVM(_:)` has been called for each module in `modules`.
  @discardableResult
  public mutating func writeObjectFiles(
    for modules: [Module.ID], into directory: URL
  ) throws -> [URL] {
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    let objectFiles = try modules.map { (module) in
      let object = directory.appendingPathComponent(moduleName(module) + ".o", isDirectory: false)
      try llvmModules[module]!.module.write(.objectFile, to: object.path)
      return object
    }
    return objectFiles
  }

  /// Loads `module`, whose sources are in `root`, into `program`.
  ///
  /// If `moduleCachePath` is set, the module is loaded from cache if an archive is found and its
  /// fingerprint matches the fingerprint of the source files in `root`. Otherwise, the module is
  /// compiled from sources and an archive is stored at `moduleCachePath`. If `moduleCachePath` is
  /// not set, the module is unconditionally compiled from sources and no archive is stored.
  public mutating func load(
    _ module: Module.Name, withSourcesAt root: URL
  ) async throws {
    // Compute a fingerprint of all source files.
    var sources: [SourceFile] = []
    try SourceFile.forEach(in: root) { (s) in
      sources.append(s)
    }

    // Attempt to load the module from disk.
    do {
      if cachingIsEnabled, let data = archive(of: module) {
        let h = SourceFile.fingerprint(contentsOf: sources)
        var a = ReadableArchive(data)
        let (_, fingerprint) = try Module.header(&a)
        if h == fingerprint {
          a = ReadableArchive(data)
          try program.load(module: module, from: &a)
          return
        }
      }
    } catch ArchiveError.invalidInput {
      let m = """
        Failed to parse module archive of '\(module)' at '\(moduleCachePath, default: "nil")'.

        Maybe the archive is compiled using a different version of the compiler. Try erasing the module cache.
        """
      fatalError(m)
    }

    // Compile the module from sources.
    let m = program.demandModule(module)

    await parse(sources, into: m)
    try throwIfContainsError(m)

    await assignScopes(of: m)
    try throwIfContainsError(m)

    await assignTypes(of: m)
    try throwIfContainsError(m)

    if cachingIsEnabled {
      let a = try program.archive(module: m)
      let f = moduleCachePath!.appending(component: module + ".hylomodule")
      try a.write(into: f)
    }
  }

  /// Loads the standard library with `load(_:withSourcesAt:)`.
  /// 
  /// Use the `USE_BUNDLED_STANDARD_LIBRARY` compiler flag to control whether the 
  /// bundled or local standard library is used. Defaults to local.
  public mutating func loadStandardLibrary() async throws {
    let sourceRoot: URL
    #if USE_BUNDLED_STANDARD_LIBRARY // Set compiler flag in distributable builds.
    sourceRoot = bundledStandardLibrarySources
    #else
    sourceRoot = localStandardLibrarySources
    #endif
    try await load(Module.standardLibraryName, withSourcesAt: sourceRoot)
  }

  /// Searches for an archive of `module` in `librarySearchPaths`, returning it if found.
  public func archive(of module: Module.Name) -> Data? {
    if let prefix = moduleCachePath {
      let path = prefix.appending(path: module + ".hylomodule")
      return try? Data(contentsOf: path)
    } else {
      return nil
    }
  }

  /// Throws the diagnostics of `m` if those contain an error.
  private func throwIfContainsError(_ m: Module.ID) throws {
    if program[m].containsError {
      throw CompilationError(diagnostics: .init(program[m].diagnostics))
    }
  }

  /// Links the provided object files into an executable at `output`, using lld.
  ///
  /// - Throws when the parent folder of `output` doesn't exist.
  private func linkExecutable(from objectFiles: [URL], writingTo output: URL) throws {
    var arguments = ["-fuse-ld=lld", "-o", output.path]
    arguments += librarySearchPaths.map({ "-L\($0.path)" })
    arguments += libraries.map({ "-l\($0)" })
    arguments += objectFiles.map(\.path)

    #if os(macOS)
    let sdk = try runCommand(
      try findExecutable("xcrun"),
      arguments: ["--sdk", "macosx", "--show-sdk-path"]).standardOutput
      .trimmingCharacters(in: .whitespacesAndNewlines)
    arguments += ["-isysroot", sdk, "-lSystem"]
    #endif

    _ = try Process.executionOutput(try Host.findNativeExecutable(invokedAs: "clang"), arguments: arguments)
  }

  /// Executes the given `executable` with `arguments, capturing stdout, stderr and exit code.
  private func runCommand(_ executable: URL, arguments: [String]) throws -> ExecutionResult {
    let process = Process()
    let standardOutput = Pipe()
    let standardError = Pipe()
    process.executableURL = executable
    process.arguments = arguments
    process.standardOutput = standardOutput
    process.standardError = standardError
    try process.run()
    process.waitUntilExit()

    let output = String(
      decoding: standardOutput.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)
    let error = String(
      decoding: standardError.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)

    guard process.terminationStatus == 0 else {
      throw DriverFailure.commandFailed(
        executable.path, arguments, process.terminationStatus, error.isEmpty ? output : error)
    }

    return .init(standardOutput: output, standardError: error, terminationStatus: process.terminationStatus)
  }

  private func moduleName(_ module: Module.ID) -> String {
    program.modules.elements[module].key
  }

  private static func decode(_ buffer: borrowing SwiftyLLVM.MemoryBuffer) -> String {
    buffer.withUnsafeBytes({ (bytes) in
      String(decoding: bytes.map(UInt8.init(bitPattern:)), as: UTF8.self)
    })
  }

  private final class LLVMModuleBox {

    var module: LLVMModule

    init(_ module: consuming LLVMModule) {
      self.module = module
    }

  }

  private struct ExecutionResult {
    let standardOutput: String
    let standardError: String
    let terminationStatus: Int32
  }

  private enum DriverFailure: LocalizedError, CustomStringConvertible {

    case commandFailed(String, [String], Int32, String)
    case missingBackendArtifact(String)

    var errorDescription: String {
      switch self {
      case .commandFailed(let executable, let arguments, let status, let output):
        let command = ([executable] + arguments).joined(separator: " ")
        if output.isEmpty {
          return "command failed with exit code \(status): \(command)"
        } else {
          return "command failed with exit code \(status): \n $ \(command)\n\(output)"
        }
      case .missingBackendArtifact(let module):
        return "missing backend artifact for module '\(module)'"
      }
    }

    var description: String { "\n\(errorDescription)" }

  }

}
