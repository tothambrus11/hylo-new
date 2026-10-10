import FoundationEssentials
import FrontEnd
import SwiftyLLVM

/// A request to compile a program.
public struct CompileRequest: Decodable, Sendable {

  /// An artifact a request can ask for.
  public enum Artifact: String, Codable, Sendable {

    /// Hylo IR before mandatory transformations.
    case rawIR = "raw-ir"

    /// Hylo IR.
    case ir

    /// LLVM IR.
    case llvm

    /// WebAssembly in textual form.
    case assembly

    /// A WebAssembly executable using WASI preview 1.
    case executable

  }

  /// A phase of compilation after which a request can stop.
  public enum Phase: String, Codable, Sendable, Comparable, CaseIterable {

    /// The phases, in the order they run.
    case parsing, scoping, typing, lowering

    /// Returns `true` iff `l` happens before `r`.
    public static func < (l: Self, r: Self) -> Bool {
      allCases.firstIndex(of: l)! < allCases.firstIndex(of: r)!
    }

  }

  /// The program's source, as a single file depending on the standard library.
  public let source: String

  /// The artifacts to produce; only diagnostics are produced if empty.
  public let emit: [Artifact]

  /// The optimization level: `0` (the default), `1`, `2` or `3`.
  public let optimization: Int?

  /// `false` iff the program is compiled without the standard library; `true` by default.
  public let standardLibrary: Bool?

  /// The phase after which compilation stops, or `nil` to compile everything `emit` requires.
  public let stopAfter: Phase?

  /// Returns `true` iff `self` asks for phase `p` to run.
  internal func runs(_ p: Phase) -> Bool {
    stopAfter.map({ p <= $0 }) ?? true
  }

  /// Returns `true` iff `self` asks for `a`.
  internal func wants(_ a: Artifact) -> Bool {
    emit.contains(a)
  }

  /// The LLVM optimization level corresponding to `optimization`.
  internal var optimizationLevel: SwiftyLLVM.OptimizationLevel {
    switch optimization ?? 0 {
    case ...0: .none
    case 1: .less
    case 2: .default
    default: .aggressive
    }
  }

}

/// The result of a `CompileRequest`.
public struct CompileResponse: Encodable {

  /// The issues found in the program.
  public var diagnostics: [DiagnosticDescription] = []

  /// The textual artifacts requested, keyed by `CompileRequest.Artifact` raw value.
  public var artifacts: [String: String] = [:]

  /// The executable, if one was requested and the program compiled.
  public var executable: Data? = nil

  /// A failure that is not a diagnostic of the program, such as an internal error.
  public var error: String? = nil

  /// `true` iff the failure reported in `error` left the compiler unable to serve further
  /// requests, which the host must then serve with a new instance.
  public var compilerUnusable: Bool = false

  /// How long compilation took, in milliseconds.
  public var milliseconds: Double = 0

}

/// An issue found in a program, with the notes saying more about it.
public struct DiagnosticDescription: Encodable, Sendable {

  /// A region of a source file, as 1-based lines and 1-based UTF-16 columns.
  public struct Region: Encodable, Sendable {

    public let line: Int
    public let column: Int
    public let endLine: Int
    public let endColumn: Int

    /// Creates an instance describing `s`.
    init(_ s: SourceSpan) {
      let a = s.start.lineAndUTF16Offset
      let b = s.end.lineAndUTF16Offset
      self.line = a.line + 1
      self.column = a.offset + 1
      self.endLine = b.line + 1
      self.endColumn = b.offset + 1
    }

  }

  /// How serious the issue is: `error`, `warning` or `note`.
  public let level: String

  /// What is wrong.
  public let message: String

  /// The file containing the issue.
  public let file: String

  /// Where the issue is.
  public let site: Region

  /// The diagnostic as the command-line compiler renders it, without styling or a final newline,
  /// its notes included.
  public let rendered: String

  /// The notes attached to the diagnostic, which may be in other files, such as the standard
  /// library's declarations of candidates that did not match.
  public let notes: [DiagnosticDescription]

  /// Creates a description of `d` and its notes.
  init(_ d: Diagnostic) {
    var text = ""
    d.render(into: &text, showingPaths: .absolute, style: .unstyled)
    self.level = "\(d.level)"
    self.message = d.message
    self.file = d.site.source.name.url.path
    self.site = .init(d.site)
    self.rendered = text.hasSuffix("\n") ? String(text.dropLast()) : text
    self.notes = d.notes.map(Self.init)
  }

}
