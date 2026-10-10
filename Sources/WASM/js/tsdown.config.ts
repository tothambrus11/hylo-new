import { statSync } from "node:fs";
import path from "node:path";
import { defineConfig } from "tsdown";
import { fileURLToPath } from "node:url";
import { allFiles } from "./src/files.ts";

/** Where `build-compiler.sh` put the compiler's files, which `npm run build` copies into `dist/`. */
const compiler = path.resolve(
  import.meta.dirname,
  process.env.HYLO_WASM_DIST ?? "../../../.build/wasm/compiler",
);

/** The size of each of the compiler's files, in the order of `allFiles`, which `src/sizes.ts` reads. */
const sizes = allFiles.map(
  (url) => statSync(path.join(compiler, path.basename(fileURLToPath(url)))).size,
);

// ES modules and their declarations in `dist/`, with the WASI shim left a dependency. The
// compiler's files are copied next to them by `npm run build`, where `src/files.ts` finds them.
export default defineConfig({
  entry: ["src/index.ts", "src/node.ts", "src/worker.ts", "src/protocol.ts"],
  format: "esm",
  platform: "neutral",
  deps: { neverBundle: [/^node:/] }, // for `src/node.ts`
  define: { __HYLO_WASM_FILE_SIZES__: JSON.stringify(sizes) },
  outDir: "dist",
  dts: true,
  clean: true,
});
