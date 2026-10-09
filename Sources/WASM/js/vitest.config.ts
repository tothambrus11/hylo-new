import path from "node:path";
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

/** The packaged release the browser test loads; see `scripts/package-release.ts`. */
const release = path.resolve(
  process.env.HYLO_WASM_RELEASE ?? path.join(import.meta.dirname, "../../../.build/wasm/release"),
);

export default defineConfig({
  test: {
    projects: [
      {
        // Against what `build-compiler.sh` produced; see `tests/support.ts`.
        test: {
          name: "node",
          environment: "node",
          include: ["tests/**/*.test.ts"],
          exclude: ["tests/**/*.browser.test.ts"],
          hookTimeout: 120_000,
        },
      },
      {
        server: { fs: { allow: [import.meta.dirname, release] } },
        test: {
          name: "browser",
          include: ["tests/**/*.browser.test.ts"],
          provide: { release },
          testTimeout: 120_000,
          browser: {
            enabled: true,
            headless: true,
            provider: playwright({
              // A Chromium of one's own, instead of the one Playwright installs.
              launchOptions: { executablePath: process.env.CHROMIUM || undefined },
            }),
            instances: [{ browser: "chromium" }],
          },
        },
      },
    ],
  },
});

declare module "vitest" {
  export interface ProvidedContext {
    release: string;
  }
}
