// What the tests share: where the compiler they test is, and the compiler itself.

import path from "node:path";
import { fileURLToPath } from "node:url";
import { readDist } from "../scripts/dist.ts";
import { type Compiler, instantiate } from "../src/index.ts";

/** The root of the hylo-new repository. */
export const repository = fileURLToPath(new URL("../../../../", import.meta.url));

/**
 * What `build-compiler.sh` produced: `HYLO_WASM_DIST`, or where the script puts it by default.
 */
const dist = process.env.HYLO_WASM_DIST ?? path.join(repository, ".build/wasm/dist");

let shared: Promise<Compiler> | undefined;

/** Returns the compiler in `dist`, instantiated once for every test in a file. */
export function compiler(): Promise<Compiler> {
  shared ??= readDist(dist).then(instantiate);
  return shared;
}
