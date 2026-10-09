import { defineConfig } from "tsdown";

// The npm package: ES modules and their declarations in `dist/`, with the WASI shim left a
// dependency. (JSR publishes `src/` as it is; see `jsr.json`. A compiler release bundles the
// loaders with their dependency instead; see `scripts/package-release.ts`.)
export default defineConfig({
  entry: ["src/index.ts", "src/worker.ts", "src/protocol.ts"],
  format: "esm",
  platform: "neutral",
  outDir: "dist",
  dts: true,
  clean: true,
});
