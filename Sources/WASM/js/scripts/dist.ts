// What the scripts and the tests share about the compiler's build output and releases.

import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import type { CompilerParts } from "../src/index.ts";

/** Where `build-compiler.sh` puts the parts of the compiler, relative to its output directory. */
export const distLayout = {
  /** The compiler, a WASI reactor. */
  compiler: "hylo-wasm.wasm",
  /** The standard library's sources, as a JSON object keyed by file name. */
  standardLibrary: "stdlib.json",
  /** The files linked into every executable. */
  sysroot: "sysroot/lib",
};

/** Returns the parts `instantiate` takes, read from `dist`, an output of `build-compiler.sh`. */
export async function readDist(dist: string): Promise<CompilerParts> {
  const lib = path.join(dist, distLayout.sysroot);
  const read = (name: string): Buffer => readFileSync(path.join(dist, name));
  return {
    compiler: await WebAssembly.compile(new Uint8Array(read(distLayout.compiler))),
    standardLibrary: JSON.parse(read(distLayout.standardLibrary).toString("utf8")),
    sysroot: new Map(readdirSync(lib).map((n) => [n, readFileSync(path.join(lib, n))])),
  };
}

/** Returns what a release's manifest records about a file holding `bytes`. */
export function fingerprint(bytes: Uint8Array): { sha256: string; bytes: number } {
  return { sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length };
}
