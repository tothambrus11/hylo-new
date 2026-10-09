/**
 * Loads the Hylo compiler compiled to WebAssembly, compiles programs with it, and runs them, in
 * Node. (Browsers get `index.ts` instead, through the package's export conditions.)
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

import { readFile } from "node:fs/promises";
import { type Compiler, type CompilerParts, instantiate } from "./core.ts";
import { compilerFile, standardLibraryFile, sysrootFiles } from "./files.ts";

export * from "./core.ts";
export type * from "./protocol.ts";

/** Reads the compiler and compiles its standard library, which takes a few seconds. */
export async function load(): Promise<Compiler> {
  return instantiate(await loadParts());
}

/** Reads the compiler and compiles it, ready to `instantiate` as often as needed. */
export async function loadParts(): Promise<CompilerParts> {
  const [compiler, standardLibrary, sysroot] = await Promise.all([
    readFile(compilerFile).then((b) => WebAssembly.compile(new Uint8Array(b))),
    readFile(standardLibraryFile, "utf8").then((t) => JSON.parse(t) as Record<string, string>),
    Promise.all(
      [...sysrootFiles].map(
        async ([name, url]) => [name, new Uint8Array(await readFile(url))] as const,
      ),
    ),
  ]);
  return { compiler, standardLibrary, sysroot: new Map(sysroot) };
}
