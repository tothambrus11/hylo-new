/**
 * What a host and the compiler say to each other, and what a compiler release holds.
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

/**
 * The `manifest.json` of a compiler release, naming its files.
 *
 * Every file but the manifest and the loaders has a hash of its contents in its name, so it can be
 * served as immutable.
 */
export interface Manifest {
  /** The version of this format; 1. */
  schemaVersion: 1;
  /** The version of the compiler. */
  version: string;
  /** When the release was built, as an ISO 8601 date. */
  built: string;
  /** What the release was built from, where known. */
  inputs: Record<string, string | null>;
  /**
   * The release's files by role: `compiler` (the reactor), `standardLibrary` (its sources, as a
   * JSON object keyed by file name), and those named in `sysroot`.
   */
  files: Record<string, ManifestFile>;
  /** The keys of `files` linked into every executable, installed under `/sysroot/lib`. */
  sysroot: string[];
  /** The bundled loaders, `index.mjs` and `worker.mjs`, which keep their names. */
  loaders?: Record<string, { sha256: string; bytes: number }>;
}

/** A file of a compiler release. */
export interface ManifestFile {
  /** The file's name in the release. */
  path: string;
  /** The SHA-256 of its contents, in hexadecimal. */
  sha256: string;
  /** Its size. */
  bytes: number;
  /** Its size once compressed with gzip, which is roughly what it costs to download. */
  gzip: number;
  /**
   * `"gzip"` if the file is stored compressed with gzip, which a loader undoes; the other fields
   * describe the file as stored.
   */
  encoding?: "gzip";
  /** For a file in `sysroot`, the name it has there. */
  name?: string;
}

/** A message to the worker (`worker.ts`). */
export interface WorkerRequest {
  /** An identifier the answer carries. */
  id: number;
  request: CompileRequest;
  /** Whether to run the executable, if one is produced; `true` by default. */
  run?: boolean;
}

/** A message from the worker (`worker.ts`). */
export type WorkerMessage =
  | { type: "progress"; loaded: number; total: number }
  | { type: "ready"; standardLibraryMilliseconds: number }
  | { type: "failed"; error: string }
  | { type: "result"; id: number; compile: WorkerCompilation; run: Execution | null };

/**
 * A `CompileResponse` as the worker sends it: with the executable's size rather than the
 * executable, which it runs itself, or only an `error` when the request could not be served.
 */
export type WorkerCompilation =
  | (Omit<CompileResponse, "executable"> & { executableBytes?: number })
  | { error: string };
