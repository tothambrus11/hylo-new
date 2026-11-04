// What the tests share: the compiler they test, which they read from where `build-compiler.sh`
// put it, by the names the package ships its files under.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { type Compiler, instantiate } from "../src/core.ts";
import { compilerFile, standardLibraryFile, sysrootFiles } from "../src/files.ts";

/** The root of the hylo-new repository. */
export const repository = fileURLToPath(new URL("../../../../", import.meta.url));

/** What `build-compiler.sh` produced: `HYLO_WASM_DIST`, or where the script puts it by default. */
const dist = process.env.HYLO_WASM_DIST ?? path.join(repository, ".build/wasm/compiler");

/** Returns the contents of the file of the package at `url`, from `dist`. */
const read = (url: URL): Buffer => readFileSync(path.join(dist, path.basename(url.pathname)));

let shared: Promise<Compiler> | undefined;

/** Returns the compiler in `dist`, instantiated once for every test in a file. */
export function compiler(): Promise<Compiler> {
  shared ??= (async () =>
    instantiate({
      compiler: await WebAssembly.compile(new Uint8Array(read(compilerFile))),
      standardLibrary: JSON.parse(read(standardLibraryFile).toString("utf8")),
      sysroot: new Map([...sysrootFiles].map(([name, url]) => [name, new Uint8Array(read(url))])),
    }))();
  return shared;
}
