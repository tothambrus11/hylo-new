// Reads what `build-compiler.sh` produced, for the scripts checking it in Node.

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

/**
 * Returns the parts `instantiate` (from `index.mjs`) takes, read from `dist`, the output
 * directory of `build-compiler.sh`.
 *
 * @param {string} dist
 */
export async function readDist(dist) {
  const lib = path.join(dist, "sysroot", "lib");
  return {
    compiler: await WebAssembly.compile(readFileSync(path.join(dist, "hylo-wasm.wasm"))),
    standardLibrary: JSON.parse(readFileSync(path.join(dist, "stdlib.json"), "utf8")),
    sysroot: new Map(readdirSync(lib).map((n) => [n, readFileSync(path.join(lib, n))])),
  };
}
