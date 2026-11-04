import { defineConfig } from "vitest/config";

// Against what `build-compiler.sh` produced; see `tests/support.ts`.
export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    hookTimeout: 120_000,
  },
});
