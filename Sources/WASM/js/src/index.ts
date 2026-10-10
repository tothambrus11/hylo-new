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
import { allFiles, sysrootFiles } from "./files.ts";
import { totalSize } from "./sizes.ts";

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

/**
 * Downloads the compiler and compiles it, ready to `instantiate` as often as needed.
 *
 * Reports progress to `onProgress` as the files arrive, against the sizes the package records, or
 * against a total of 0 if it records none. Rejects if a file cannot be fetched or the compiler
 * does not compile.
 */
export async function loadParts({ onProgress }: LoadOptions = {}): Promise<CompilerParts> {
  const responses = await Promise.all(
    allFiles.map(async (url) => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`could not fetch ${url} (${r.status})`);
      return r;
    }),
  );
  if (onProgress) countProgress(responses, onProgress);

  const [compiler, standardLibrary, ...sysroot] = responses;
  const sysrootNames = [...sysrootFiles.keys()];
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
 * Reports to `onProgress` the bytes of `responses`, the responses for `allFiles`, as they arrive,
 * reading copies of their bodies, so that the responses themselves stay as fetched.
 *
 * The responses are not wrapped, so that `compileStreaming` is given the one fetched, which an
 * engine may cache the compiled module with.
 */
function countProgress(
  responses: readonly Response[],
  onProgress: NonNullable<LoadOptions["onProgress"]>,
): void {
  const total = totalSize() ?? 0;
  let loaded = 0;
  for (const r of responses) {
    const reader = r.clone().body!.getReader();
    const read = (): Promise<void> =>
      reader.read().then(({ done, value }) => {
        if (done) return;
        loaded += value.length;
        onProgress({ loaded, total });
        return read();
      });
    // A body that fails to arrive fails `loadParts` through the response itself.
    read().catch(() => {});
  }
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
