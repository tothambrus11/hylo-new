import { defineConfig } from "tsdown";

// ES modules and their declarations in `dist/`, with the WASI shim left a dependency. The
// compiler's files are copied next to them by `npm run build`, where `src/files.ts` finds them.
export default defineConfig({
  entry: ["src/index.ts", "src/node.ts", "src/worker.ts", "src/protocol.ts"],
  format: "esm",
  platform: "neutral",
  deps: { neverBundle: [/^node:/] }, // for `src/node.ts`
  outDir: "dist",
  dts: true,
  clean: true,
});
