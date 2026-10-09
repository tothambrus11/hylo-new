// What the tests share: where the compiler they test is, and the compiler itself.

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { type Compiler, type CompilerParts, instantiate } from "../src/index.ts";

/** The root of the hylo-new repository. */
export const repository = fileURLToPath(new URL("../../../../", import.meta.url));

/**
 * What `build-compiler.sh` produced: `HYLO_WASM_DIST`, or where the script puts it by default.
 */
export const dist = process.env.HYLO_WASM_DIST ?? path.join(repository, ".build/wasm/dist");

/** Returns the parts `instantiate` takes, read from `directory`, an output of `build-compiler.sh`. */
export async function readDist(directory: string): Promise<CompilerParts> {
  const lib = path.join(directory, "sysroot", "lib");
  return {
    compiler: await WebAssembly.compile(readFileSync(path.join(directory, "hylo-wasm.wasm"))),
    standardLibrary: JSON.parse(readFileSync(path.join(directory, "stdlib.json"), "utf8")),
    sysroot: new Map(readdirSync(lib).map((n) => [n, readFileSync(path.join(lib, n))])),
  };
}

let shared: Promise<Compiler> | undefined;

/** Returns the compiler in `dist`, instantiated once for every test in a file. */
export function compiler(): Promise<Compiler> {
  shared ??= readDist(dist).then(instantiate);
  return shared;
}
