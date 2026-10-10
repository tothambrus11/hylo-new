/**
 * The compiler, independently of how its files are obtained: instantiating it, and running the
 * executables it produces. `index.ts` (browsers) and `node.ts` (Node) obtain the files.
 *
 * @module
 */

import {
  ConsoleStdout,
  Directory,
  File,
  OpenFile,
  PreopenDirectory,
  WASI,
} from "@bjorn3/browser_wasi_shim";
import type { CompileRequest, CompileResponse, Execution } from "./protocol.ts";

/** The compiler, ready to compile programs. */
export interface Compiler {
  /** How long compiling the standard library took, in milliseconds. */
  readonly standardLibraryMilliseconds: number;

  /** The last lines the compiler wrote to its standard streams; normally none. */
  readonly log: readonly string[];

  /**
   * `false` iff the compiler trapped or reported that it cannot serve further requests, in which
   * case it must be instantiated again.
   */
  readonly usable: boolean;

  /**
   * Compiles `request`.
   *
   * Throws if the compiler traps, which is a bug in the compiler; it is then no longer `usable`.
   * Throws what `options.onFrontEnd` throws, once compiling is done.
   */
  compile(request: CompileRequest, options?: CompileOptions): CompileResponse;

  /** Runs `executable`; the same as the module's `run`. */
  run(executable: Uint8Array, options?: RunOptions): Promise<Execution>;
}

/** How `Compiler.compile` reports on its progress. */
export interface CompileOptions {
  /**
   * Called during compilation, once the front end is done and before the back end runs, with
   * what the front end produced: the diagnostics, the Hylo IR requested (`raw-ir`, `ir`), and how
   * long compiling has taken so far. Not called if the back end does not run: if the request
   * asks for nothing it produces, sets `stopAfter`, or the program has errors.
   *
   * The back end takes most of the time, so this lets a host show the front end's results sooner.
   * It must not call the compiler.
   */
  onFrontEnd?: (frontEnd: Omit<CompileResponse, "executable">) => void;
}

/** The parts of the compiler that `instantiate` needs. */
export interface CompilerParts {
  /** The compiler, compiled. */
  compiler: WebAssembly.Module;
  /** The standard library's sources, by file name. */
  standardLibrary: Record<string, string>;
  /** The files linked into every executable, by name. */
  sysroot: Map<string, Uint8Array>;
}

/** How `run` runs a program. */
export interface RunOptions {
  /** The program's arguments, after its name. */
  args?: string[];
  /** What the program reads from its standard input. */
  stdin?: Uint8Array;
}

/** The exports of the compiler, a WASI reactor. */
interface Exports {
  memory: WebAssembly.Memory;
  hylo_alloc(size: number): number;
  hylo_free(pointer: number): void;
  hylo_init(request: number, size: number): number;
  hylo_compile(request: number, size: number): number;
}

/**
 * Instantiates the compiler in `parts` and compiles its standard library.
 *
 * This is `load` without the fetching, for hosts that have the files at hand.
 */
export async function instantiate({
  compiler,
  standardLibrary,
  sysroot,
}: CompilerParts): Promise<Compiler> {
  // What the compiler writes is kept for diagnosing it, up to a bound, since a long-lived page may
  // compile many programs.
  const log: string[] = [];
  const record = (line: string): void => {
    log.push(line);
    if (log.length > maximumLogLength) log.splice(0, log.length - maximumLogLength);
  };
  const libraries = new Map(
    [...sysroot].map(([name, contents]) => [name, new File(contents, { readonly: true })]),
  );
  const scratch = new PreopenDirectory("/tmp", new Map());
  const wasi = new WASI(
    ["hylo-wasm"],
    [],
    [
      new OpenFile(new File([])),
      ConsoleStdout.lineBuffered(record),
      ConsoleStdout.lineBuffered(record),
      new PreopenDirectory("/sysroot", new Map([["lib", new Directory(libraries)]])),
      scratch,
    ],
    { debug: false },
  );
  // The `onFrontEnd` of the request being compiled, and what it threw. What it throws is rethrown
  // once compiling is done: thrown from the import, it would unwind through the compiler, leaving
  // it in an unknown state.
  let onFrontEnd: CompileOptions["onFrontEnd"];
  const thrownByOnFrontEnd: unknown[] = [];
  const instance = await WebAssembly.instantiate(compiler, {
    wasi_snapshot_preview1: wasi.wasiImport,
    hylo_host: {
      front_end_done(address: number, length: number): void {
        try {
          onFrontEnd?.(JSON.parse(readString(address, length)));
        } catch (thrown) {
          thrownByOnFrontEnd.push(thrown);
        }
      },
    },
  });
  wasi.initialize(instance as Parameters<WASI["initialize"]>[0]);
  const exports = instance.exports as unknown as Exports;

  /** Returns the `length` bytes of UTF-8 at `address` in the compiler's memory. */
  const readString = (address: number, length: number): string =>
    new TextDecoder().decode(new Uint8Array(exports.memory.buffer, address, length));

  // Why the instance can no longer be used, once it cannot.
  let unusable: string | null = null;

  /** Calls `exported`, an export of the compiler, with `argument` as JSON, and returns its JSON answer. */
  const callExport = (
    exported: (address: number, length: number) => number,
    argument: unknown,
  ): unknown => {
    if (unusable !== null) throw new Error(`the compiler cannot be used anymore: ${unusable}`);
    const request = new TextEncoder().encode(JSON.stringify(argument));
    const requestAddress = exports.hylo_alloc(request.length);
    new Uint8Array(exports.memory.buffer).set(request, requestAddress);
    let answerAddress: number;
    try {
      answerAddress = exported(requestAddress, request.length);
    } catch (thrown) {
      // A trap leaves the instance's state wherever it was, so nothing more is asked of it.
      unusable = thrown instanceof Error ? thrown.message : String(thrown);
      throw thrown;
    }
    exports.hylo_free(requestAddress);
    try {
      // Read afresh: the call may have grown the memory, detaching any earlier view of it.
      const length = new DataView(exports.memory.buffer).getUint32(answerAddress, true);
      return JSON.parse(readString(answerAddress + 4, length));
    } finally {
      exports.hylo_free(answerAddress);
    }
  };

  const started = performance.now();
  const initialization = callExport(exports.hylo_init, {
    standardLibrary,
    sysroot: "/sysroot",
    scratch: "/tmp",
  }) as { ok?: true; error?: string };
  if (initialization.ok !== true) {
    throw new Error(initialization.error ?? "the standard library did not load");
  }
  const standardLibraryMilliseconds = performance.now() - started;

  return {
    standardLibraryMilliseconds,
    log,
    get usable() {
      return unusable === null;
    },
    compile(request, options = {}) {
      onFrontEnd = options.onFrontEnd;
      thrownByOnFrontEnd.length = 0;
      let response: Omit<CompileResponse, "executable"> & { executable?: string };
      try {
        response = callExport(exports.hylo_compile, {
          emit: ["executable"],
          ...request,
        }) as typeof response;
      } finally {
        onFrontEnd = undefined;
      }
      scratch.dir.contents.clear();
      if (response.compilerUnusable) {
        unusable = response.error ?? "the compiler reported it cannot run again";
      }
      if (thrownByOnFrontEnd.length > 0) throw thrownByOnFrontEnd[0];
      const { executable, ...rest } = response;
      return executable === undefined ? rest : { ...rest, executable: fromBase64(executable) };
    },
    run,
  };
}

/**
 * Runs `executable`, a WASI command, and returns its exit code and what it wrote.
 *
 * A trap, or running out of stack, is reported as `trap` rather than thrown, because a program
 * that traps is a program that ran, as far as a playground is concerned.
 */
export async function run(
  executable: Uint8Array,
  { args = [], stdin = new Uint8Array() }: RunOptions = {},
): Promise<Execution> {
  const stdout: Uint8Array[] = [];
  const stderr: Uint8Array[] = [];
  const wasi = new WASI(
    ["main", ...args],
    [],
    [
      new OpenFile(new File(stdin)),
      new ConsoleStdout((chunk) => stdout.push(chunk.slice())),
      new ConsoleStdout((chunk) => stderr.push(chunk.slice())),
    ],
    { debug: false },
  );
  const module = await WebAssembly.compile(executable as Uint8Array<ArrayBuffer>);
  const instance = await WebAssembly.instantiate(module, {
    wasi_snapshot_preview1: wasi.wasiImport,
  });
  const text = (chunks: Uint8Array[]): string => new TextDecoder().decode(concatenate(chunks));
  try {
    const exitCode = wasi.start(instance as Parameters<WASI["start"]>[0]);
    return { exitCode, stdout: text(stdout), stderr: text(stderr) };
  } catch (thrown) {
    // Engines report a stack overflow in WebAssembly as a `RangeError` rather than a trap.
    if (thrown instanceof WebAssembly.RuntimeError || thrown instanceof RangeError) {
      return { exitCode: null, trap: thrown.message, stdout: text(stdout), stderr: text(stderr) };
    }
    throw thrown;
  }
}

/** The number of lines of the compiler's output that `log` keeps. */
const maximumLogLength = 1000;

/** Returns the bytes `base64` encodes. */
function fromBase64(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; ++i) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/** Returns `chunks`, end to end. */
function concatenate(chunks: Uint8Array[]): Uint8Array {
  const whole = new Uint8Array(chunks.reduce((length, chunk) => length + chunk.length, 0));
  let offset = 0;
  for (const chunk of chunks) {
    whole.set(chunk, offset);
    offset += chunk.length;
  }
  return whole;
}
