// Loads the Hylo compiler compiled to WebAssembly, compiles programs with it, and runs them.
//
// Works in browsers and in Node alike: the compiler and the programs it produces see a WASI file
// system that lives in memory, provided by @bjorn3/browser_wasi_shim. Nothing here touches the
// host's file system or network except through the `fetch` that `load` is given.
//
//   import { load } from "hylo-wasm";
//   const hylo = await load({ baseUrl: "https://…/releases/download/v0.1.0/" });
//   const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }" });
//   const { exitCode } = await hylo.run(r.executable);

import {
  WASI,
  File,
  Directory,
  PreopenDirectory,
  OpenFile,
  ConsoleStdout,
} from "@bjorn3/browser_wasi_shim";

/**
 * Loads the compiler described by the `manifest.json` at `baseUrl` and compiles its standard
 * library, which is what makes this slow and every later `compile` fast.
 *
 * @param {object} options
 * @param {string | URL} options.baseUrl Where `manifest.json` and the files it names are.
 * @param {typeof fetch} [options.fetch] How to fetch them.
 * @param {(event: { loaded: number, total: number }) => void} [options.onProgress]
 */
export async function load({ baseUrl, fetch: get = globalThis.fetch, onProgress } = {}) {
  const base = new URL(baseUrl, globalThis.location?.href);
  const manifest = await (await get(new URL("manifest.json", base))).json();

  const total = Object.values(manifest.files).reduce((a, f) => a + f.bytes, 0);
  let loaded = 0;
  const bytes = async (key) => {
    const response = await get(new URL(manifest.files[key].path, base));
    if (!response.ok) throw new Error(`could not fetch ${manifest.files[key].path}`);
    const b = new Uint8Array(await response.arrayBuffer());
    loaded += b.length;
    onProgress?.({ loaded, total });
    return b;
  };

  const [compiler, stdlib, ...sysroot] = await Promise.all([
    bytes("compiler").then((b) => WebAssembly.compile(b)),
    bytes("standardLibrary").then((b) => JSON.parse(new TextDecoder().decode(b))),
    ...manifest.sysroot.map((key) => bytes(key).then((b) => [manifest.files[key].name, b])),
  ]);
  return instantiate({ compiler, standardLibrary: stdlib, sysroot: new Map(sysroot) });
}

/**
 * Instantiates `compiler`, a compiled `hylo-wasm` reactor, and compiles `standardLibrary` with it.
 *
 * This is `load` without the fetching, for hosts that have the files at hand.
 *
 * @param {object} parts
 * @param {WebAssembly.Module} parts.compiler
 * @param {Record<string, string>} parts.standardLibrary The library's sources by file name.
 * @param {Map<string, Uint8Array>} parts.sysroot The files linked into executables, by name.
 */
export async function instantiate({ compiler, standardLibrary, sysroot }) {
  const log = [];
  const lib = new Map([...sysroot].map(([n, b]) => [n, new File(b, { readonly: true })]));
  const scratch = new PreopenDirectory("/tmp", new Map());
  const wasi = new WASI(
    ["hylo-wasm"],
    [],
    [
      new OpenFile(new File([])),
      ConsoleStdout.lineBuffered((l) => log.push(l)),
      ConsoleStdout.lineBuffered((l) => log.push(l)),
      new PreopenDirectory("/sysroot", new Map([["lib", new Directory(lib)]])),
      scratch,
    ],
    { debug: false },
  );
  const instance = await WebAssembly.instantiate(compiler, {
    wasi_snapshot_preview1: wasi.wasiImport,
  });
  wasi.initialize(instance);
  const m = instance.exports;

  /** Calls the export `f` with `value` as JSON, and returns its JSON answer. */
  const call = (f, value) => {
    const request = new TextEncoder().encode(JSON.stringify(value));
    const p = m.hylo_alloc(request.length);
    new Uint8Array(m.memory.buffer).set(request, p);
    let answer;
    try {
      answer = f(p, request.length);
    } finally {
      m.hylo_free(p);
    }
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
  const init = call(m.hylo_init, { standardLibrary, sysroot: "/sysroot", scratch: "/tmp" });
  if (init.ok !== true) throw new Error(init.error ?? "the standard library did not load");
  const standardLibraryMilliseconds = performance.now() - started;

  return {
    /** How long compiling the standard library took. */
    standardLibraryMilliseconds,

    /** What the compiler wrote to its standard streams; normally nothing. */
    log,

    /**
     * Compiles a program.
     *
     * @param {{ source: string, emit?: string[], optimization?: number }} request
     *   `emit` lists any of "raw-ir", "ir", "llvm", "assembly" and "executable" (the default).
     */
    compile(request) {
      const r = call(m.hylo_compile, { emit: ["executable"], ...request });
      scratch.dir.contents.clear();
      if (typeof r.executable === "string") r.executable = fromBase64(r.executable);
      return r;
    },

    run,
  };
}

/**
 * Runs `executable`, a WASI command, and returns its exit code and what it wrote.
 *
 * A trap is reported as `trap` rather than thrown, because a program that traps is a program that
 * ran, as far as a REPL is concerned.
 *
 * @param {Uint8Array} executable
 * @param {{ args?: string[], stdin?: Uint8Array }} [options]
 */
export async function run(executable, { args = [], stdin = new Uint8Array() } = {}) {
  const stdout = [];
  const stderr = [];
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
  const instance = await WebAssembly.instantiate(await WebAssembly.compile(executable), {
    wasi_snapshot_preview1: wasi.wasiImport,
  });
  const text = (chunks) => new TextDecoder().decode(concatenate(chunks));
  try {
    const exitCode = wasi.start(instance);
    return { exitCode, stdout: text(stdout), stderr: text(stderr) };
  } catch (e) {
    if (e instanceof WebAssembly.RuntimeError) {
      return { exitCode: null, trap: e.message, stdout: text(stdout), stderr: text(stderr) };
    }
    throw e;
  }
}

/** Returns the bytes encoded in `s`. */
function fromBase64(s) {
  const binary = atob(s);
  const b = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; ++i) b[i] = binary.charCodeAt(i);
  return b;
}

/** Returns `chunks`, end to end. */
function concatenate(chunks) {
  const r = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
  let i = 0;
  for (const c of chunks) {
    r.set(c, i);
    i += c.length;
  }
  return r;
}
