/**
 * What a host and the compiler say to each other.
 *
 * The requests and answers mirror `Sources/WASM/HyloWASMSession/Messages.swift`, which the
 * reactor encodes and decodes as JSON.
 *
 * @module
 */

/** A textual artifact the compiler can produce. */
export type Artifact = "raw-ir" | "ir" | "llvm" | "assembly";

/** A phase of compilation after which a request can stop. */
export type Phase = "parsing" | "scoping" | "typing" | "lowering";

/** A request to compile a program. */
export interface CompileRequest {
  /** The program's source, as a single file. */
  source: string;
  /** The artifacts to produce: by default, only an executable. */
  emit?: (Artifact | "executable")[];
  /** LLVM's optimization level, from 0 (the default) to 3. */
  optimization?: number;
  /** `false` iff the program is compiled without the standard library; `true` by default. */
  standardLibrary?: boolean;
  /** The phase after which compilation stops, rather than once `emit` is satisfied. */
  stopAfter?: Phase;
}

/** An issue found in a program, at 1-based lines and 1-based UTF-16 columns. */
export interface Diagnostic {
  level: "error" | "warning" | "note";
  message: string;
  /** The file containing the issue. */
  file: string;
  site: { line: number; column: number; endLine: number; endColumn: number };
  /** The diagnostic as the command-line compiler renders it, without styling. */
  rendered: string;
}

/** The result of a `CompileRequest`. */
export interface CompileResponse {
  /** The issues found in the program. */
  diagnostics: Diagnostic[];
  /** The textual artifacts requested. */
  artifacts: Partial<Record<Artifact, string>>;
  /** The executable, a WASI command, if one was requested and the program compiled. */
  executable?: Uint8Array;
  /** A failure that is not a diagnostic of the program, such as an internal error. */
  error?: string;
  /**
   * `true` iff the failure reported in `error` left the compiler unable to serve further
   * requests.
   */
  compilerUnusable?: boolean;
  /** How long compilation took, in milliseconds. */
  milliseconds: number;
}

/** What running an executable did. */
export interface Execution {
  /** The program's exit status, or `null` if it trapped. */
  exitCode: number | null;
  /** Set iff the program trapped or ran out of stack, to why. */
  trap?: string;
  /** What the program wrote to its standard output, decoded as UTF-8. */
  stdout: string;
  /** What the program wrote to its standard error, decoded as UTF-8. */
  stderr: string;
}

/** A message to the compiler's worker (`compiler-worker.ts`). */
export interface CompilerWorkerRequest {
  /** An identifier the answer carries. */
  id: number;
  request: CompileRequest;
  /**
   * Whether the worker runs the executable, if one is produced; `true` by default. If `false`, the
   * worker answers with the executable instead, for the page to run elsewhere, such as in a
   * program worker (`program-worker.ts`), which it can terminate without losing the compiler.
   */
  run?: boolean;
}

/** A message from the compiler's worker (`compiler-worker.ts`). */
export type CompilerWorkerMessage =
  | { type: "progress"; loaded: number; total: number }
  | { type: "ready"; standardLibraryMilliseconds: number }
  | { type: "failed"; error: string }
  | CompilerWorkerStage
  | CompilerWorkerResult;

/**
 * A stage of compiling:
 * - `"front-end"`: parsing, typing and lowering to Hylo IR;
 * - `"back-end"`: generating LLVM IR, WebAssembly and the executable.
 */
export type CompilationStage = "front-end" | "back-end";

/**
 * What a stage of serving a request produced, sent as soon as the stage is done, before the
 * `CompilerWorkerResult` that answers the request.
 *
 * `"front-end"` is sent iff the back end runs next (see `CompileOptions.onFrontEnd`), with the
 * front end's diagnostics and the Hylo IR requested. `"back-end"` is sent iff the worker is about
 * to run the executable, with everything compiling produced, as the `CompilerWorkerResult` will
 * have it. A request whose program never returns thus still gets what compiling it produced.
 */
export interface CompilerWorkerStage {
  type: "stage";
  /** The `id` of the request. */
  id: number;
  /** The stage done. */
  stage: CompilationStage;
  /** What compiling produced so far. */
  compilation: Compilation;
}

/** The compiler's worker's answer to a `CompilerWorkerRequest`. */
export interface CompilerWorkerResult {
  type: "result";
  /** The `id` of the request. */
  id: number;
  /** What compiling produced. */
  compilation: Compilation;
  /** What running the executable did, if the worker ran it. */
  execution: Execution | null;
  /** The executable, if the request produced one and asked not to `run` it. */
  executable?: Uint8Array;
}

/** A message to a program worker (`program-worker.ts`): run `executable`. */
export interface ProgramWorkerRequest {
  /** An identifier the answer carries. */
  id: number;
  /** A WASI command, as `CompileResponse.executable`. */
  executable: Uint8Array;
  /** The program's arguments, after its name. */
  args?: string[];
  /** What the program reads from its standard input. */
  stdin?: Uint8Array;
}

/** A program worker's answer to a `ProgramWorkerRequest`. */
export type ProgramWorkerResult =
  /** The program ran: it returned, exited, or trapped. */
  | { type: "ran"; id: number; execution: Execution }
  /** The program could not be run, for the reason `error` gives, such as an invalid module. */
  | { type: "failed"; id: number; error: string };

/**
 * A `CompileResponse` as the compiler's worker sends it: with the executable's size in bytes
 * rather than the executable, which goes in `CompilerWorkerResult.executable` if anywhere. A
 * request that could not be served at all is answered with an `error`, no diagnostics and no
 * artifacts.
 */
export type Compilation = Omit<CompileResponse, "executable"> & { executableByteCount?: number };
