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
  const lib = new Map([...sysroot].map(([n, b]) => [n, new File(b, { readonly: true })]));
  const scratch = new PreopenDirectory("/tmp", new Map());
  const wasi = new WASI(
    ["hylo-wasm"],
    [],
    [
      new OpenFile(new File([])),
      ConsoleStdout.lineBuffered(record),
      ConsoleStdout.lineBuffered(record),
      new PreopenDirectory("/sysroot", new Map([["lib", new Directory(lib)]])),
      scratch,
    ],
    { debug: false },
  );
  // The `onFrontEnd` of the request being compiled, and what it threw. What it throws is rethrown
  // once compiling is done: thrown from the import, it would unwind through the compiler, leaving
  // it in an unknown state.
  let onFrontEnd: CompileOptions["onFrontEnd"];
  const thrown: unknown[] = [];
  const instance = await WebAssembly.instantiate(compiler, {
    wasi_snapshot_preview1: wasi.wasiImport,
    hylo_host: {
      front_end_done(p: number, n: number): void {
        try {
          onFrontEnd?.(JSON.parse(readString(p, n)));
        } catch (e) {
          thrown.push(e);
        }
      },
    },
  });
  wasi.initialize(instance as Parameters<WASI["initialize"]>[0]);
  const m = instance.exports as unknown as Exports;

  /** Returns the `n` bytes of UTF-8 at `p` in the compiler's memory. */
  const readString = (p: number, n: number): string =>
    new TextDecoder().decode(new Uint8Array(m.memory.buffer, p, n));

  // Why the instance can no longer be used, once it cannot.
  let unusable: string | null = null;

  /** Calls the export `f` with `value` as JSON, and returns its JSON answer. */
  const call = (f: (request: number, size: number) => number, value: unknown): unknown => {
    if (unusable !== null) throw new Error(`the compiler cannot be used anymore: ${unusable}`);
    const request = new TextEncoder().encode(JSON.stringify(value));
    const p = m.hylo_alloc(request.length);
    new Uint8Array(m.memory.buffer).set(request, p);
    let answer: number;
    try {
      answer = f(p, request.length);
    } catch (e) {
      // A trap leaves the instance's state wherever it was, so nothing more is asked of it.
      unusable = e instanceof Error ? e.message : String(e);
      throw e;
    }
    m.hylo_free(p);
    try {
      // Read afresh: the call may have grown the memory, detaching any earlier view of it.
      const length = new DataView(m.memory.buffer).getUint32(answer, true);
      return JSON.parse(readString(answer + 4, length));
    } finally {
      m.hylo_free(answer);
    }
  };

  const started = performance.now();
  const init = call(m.hylo_init, { standardLibrary, sysroot: "/sysroot", scratch: "/tmp" }) as {
    ok?: true;
    error?: string;
  };
  if (init.ok !== true) throw new Error(init.error ?? "the standard library did not load");
  const standardLibraryMilliseconds = performance.now() - started;

  return {
    standardLibraryMilliseconds,
    log,
    get usable() {
      return unusable === null;
    },
    compile(request, options = {}) {
      onFrontEnd = options.onFrontEnd;
      thrown.length = 0;
      let r: Omit<CompileResponse, "executable"> & { executable?: string };
      try {
        r = call(m.hylo_compile, { emit: ["executable"], ...request }) as typeof r;
      } finally {
        onFrontEnd = undefined;
      }
      scratch.dir.contents.clear();
      if (r.compilerUnusable) unusable = r.error ?? "the compiler reported it cannot run again";
      if (thrown.length > 0) throw thrown[0];
      const { executable, ...rest } = r;
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
      new ConsoleStdout((b) => stdout.push(b.slice())),
      new ConsoleStdout((b) => stderr.push(b.slice())),
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
  } catch (e) {
    // Engines report a stack overflow in WebAssembly as a `RangeError` rather than a trap.
    if (e instanceof WebAssembly.RuntimeError || e instanceof RangeError) {
      return { exitCode: null, trap: e.message, stdout: text(stdout), stderr: text(stderr) };
    }
    throw e;
  }
}

/** The number of lines of the compiler's output that `log` keeps. */
const maximumLogLength = 1000;

/** Returns the bytes encoded in `s`, in base64. */
function fromBase64(s: string): Uint8Array {
  const binary = atob(s);
  const b = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; ++i) b[i] = binary.charCodeAt(i);
  return b;
}

/** Returns `chunks`, end to end. */
function concatenate(chunks: Uint8Array[]): Uint8Array {
  const r = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
  let i = 0;
  for (const c of chunks) {
    r.set(c, i);
    i += c.length;
  }
  return r;
}
