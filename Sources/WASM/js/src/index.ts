/**
 * Loads the Hylo compiler compiled to WebAssembly, compiles programs with it, and runs them, in a
 * browser. (Node gets `node.ts` instead, through the package's export conditions.)
 *
 * The compiler and the programs it produces see a WASI file system that lives in memory, provided
 * by `@bjorn3/browser_wasi_shim`. Nothing is downloaded until `load` is called.
 *
 * ```ts
 * import { load } from "@hylo-lang/hylo-wasm";
 *
 * const hylo = await load();
 * const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }" });
 * const { exitCode } = await hylo.run(r.executable!);
 * ```
 *
 * @module
 */

import { type Compiler, type CompilerParts, instantiate } from "./core.ts";
import { compilerFile, standardLibraryFile, sysrootFiles } from "./files.ts";

export * from "./core.ts";
export type * from "./protocol.ts";

/** How `load` reports on its progress. */
export interface LoadOptions {
  /**
   * Called as the compiler downloads, with the bytes received so far and the total, which is 0
   * when the server does not say.
   */
  onProgress?: (event: { loaded: number; total: number }) => void;
}

/**
 * Downloads the compiler and compiles its standard library, which is what makes this slow and
 * every later `compile` fast.
 */
export async function load(options: LoadOptions = {}): Promise<Compiler> {
  return instantiate(await loadParts(options));
}

/** Downloads the compiler and compiles it, ready to `instantiate` as often as needed. */
export async function loadParts({ onProgress }: LoadOptions = {}): Promise<CompilerParts> {
  const sysrootNames = [...sysrootFiles.keys()];
  const responses = await Promise.all(
    [compilerFile, standardLibraryFile, ...sysrootFiles.values()].map(async (url) => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`could not fetch ${url} (${r.status})`);
      return r;
    }),
  );

  // Progress is counted as the bodies arrive.
  const sizes = responses.map((r) => Number(r.headers.get("content-length")));
  const total = sizes.every((n) => n > 0) ? sizes.reduce((a, n) => a + n, 0) : 0;
  let loaded = 0;
  const [compiler, standardLibrary, ...sysroot] = responses.map(
    (r) =>
      new Response(
        r.body!.pipeThrough(
          new TransformStream<Uint8Array, Uint8Array>({
            transform(chunk, controller) {
              loaded += chunk.length;
              onProgress?.({ loaded, total });
              controller.enqueue(chunk);
            },
          }),
        ),
        { headers: r.headers },
      ),
  );

  return {
    compiler: await compile(compiler),
    standardLibrary: (await standardLibrary.json()) as Record<string, string>,
    sysroot: new Map(
      await Promise.all(
        sysroot.map(
          async (r, i) => [sysrootNames[i], new Uint8Array(await r.arrayBuffer())] as const,
        ),
      ),
    ),
  };
}

/**
 * Returns the module in `response`, compiled as it downloads if the server serves it as
 * `application/wasm`, which streaming compilation requires, or once downloaded otherwise.
 */
async function compile(response: Response): Promise<WebAssembly.Module> {
  if (response.headers.get("content-type")?.startsWith("application/wasm")) {
    return WebAssembly.compileStreaming(response);
  }
  return WebAssembly.compile(await response.arrayBuffer());
}
