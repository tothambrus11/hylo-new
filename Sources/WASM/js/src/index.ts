/**
 * Loads the Hylo compiler compiled to WebAssembly, compiles programs with it, and runs them.
 *
 * Works in browsers and in Node alike: the compiler and the programs it produces see a WASI file
 * system that lives in memory, provided by `@bjorn3/browser_wasi_shim`. Nothing here touches the
 * host's file system or network except through the `fetch` that `load` is given.
 *
 * ```ts
 * import { load } from "@hylo-lang/hylo-wasm";
 *
 * const hylo = await load({ baseUrl: "https://example.com/hylo-compiler/" });
 * const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }" });
 * const { exitCode } = await hylo.run(r.executable!);
 * ```
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
import type { CompileRequest, CompileResponse, Execution, Manifest } from "./protocol.ts";

export type * from "./protocol.ts";

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
   */
  compile(request: CompileRequest): CompileResponse;

  /** Runs `executable`; the same as the module's `run`. */
  run(executable: Uint8Array, options?: RunOptions): Promise<Execution>;
}

/** What `load` needs. */
export interface LoadOptions {
  /** Where the release's `manifest.json` and the files it names are. */
  baseUrl: string | URL;
  /** How to fetch them; `globalThis.fetch` by default. */
  fetch?: typeof globalThis.fetch;
  /** Called as the release downloads. */
  onProgress?: (event: { loaded: number; total: number }) => void;
}

/** The parts of a release that `instantiate` needs. */
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

/**
 * Loads the compiler release at `baseUrl` and compiles its standard library, which is what makes
 * this slow and every later `compile` fast.
 */
export async function load({
  baseUrl,
  fetch: get = globalThis.fetch,
  onProgress,
}: LoadOptions): Promise<Compiler> {
  const base = new URL(baseUrl, globalThis.location?.href);
  const response = await get(new URL("manifest.json", base));
  if (!response.ok) throw new Error(`could not fetch manifest.json (${response.status})`);
  const manifest = (await response.json()) as Manifest;
  if (manifest.schemaVersion !== 2) {
    throw new Error(`unsupported compiler release (manifest schema ${manifest.schemaVersion})`);
  }

  const total = Object.values(manifest.files).reduce((a, f) => a + f.bytes, 0);
  let loaded = 0;
  const bytes = async (key: string): Promise<Uint8Array<ArrayBuffer>> => {
    const file = manifest.files[key];
    const response = await get(new URL(file.path, base));
    if (!response.ok) throw new Error(`could not fetch ${file.path} (${response.status})`);
    const b = new Uint8Array(await response.arrayBuffer());
    loaded += b.length;
    onProgress?.({ loaded, total });
    return file.encoding === "gzip" ? gunzip(b) : b;
  };

  const [compiler, standardLibrary, sysroot] = await Promise.all([
    bytes("compiler").then((b) => WebAssembly.compile(b)),
    bytes("standardLibrary").then(
      (b) => JSON.parse(new TextDecoder().decode(b)) as Record<string, string>,
    ),
    Promise.all(
      manifest.sysroot.map(async (key) => [manifest.files[key].name!, await bytes(key)] as const),
    ),
  ]);
  return instantiate({ compiler, standardLibrary, sysroot: new Map(sysroot) });
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
  const instance = await WebAssembly.instantiate(compiler, {
    wasi_snapshot_preview1: wasi.wasiImport,
  });
  wasi.initialize(instance as Parameters<WASI["initialize"]>[0]);
  const m = instance.exports as unknown as Exports;

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
      const text = new TextDecoder().decode(new Uint8Array(m.memory.buffer, answer + 4, length));
      return JSON.parse(text);
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
    compile(request) {
      const r = call(m.hylo_compile, { emit: ["executable"], ...request }) as Omit<
        CompileResponse,
        "executable"
      > & { executable?: string };
      scratch.dir.contents.clear();
      if (r.compilerUnusable) unusable = r.error ?? "the compiler reported it cannot run again";
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

/**
 * Returns `b`, a file stored compressed with gzip, decompressed.
 *
 * A server may already have decompressed it, if it serves `.gz` files with a `Content-Encoding`,
 * so `b` is returned as is unless it starts with gzip's magic number.
 */
async function gunzip(b: Uint8Array<ArrayBuffer>): Promise<Uint8Array<ArrayBuffer>> {
  if (b[0] !== 0x1f || b[1] !== 0x8b) return b;
  const decompressed = new Blob([b]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(decompressed).arrayBuffer());
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
