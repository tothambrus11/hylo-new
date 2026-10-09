// A packaged release works in a browser the way its consumers use it: a page imports the release's
// `index.mjs`, loads the compiler through `manifest.json`, compiles a program and runs it.
//
// Runs in Chromium, with the release the `release` value names (see `vitest.config.ts`).

import { expect, inject, test } from "vitest";
import type { load as Load } from "../src/index.ts";

test("loads the release, compiles a program and runs it", async () => {
  const base = `/@fs${inject("release")}/`;
  const { load }: { load: typeof Load } = await import(/* @vite-ignore */ `${base}index.mjs`);
  const hylo = await load({ baseUrl: base });
  const source = `
    public fun main() -> Int32 {
      var x = 40
      &x = x + 2
      return if x == 42 { 42 } else { 1 }
    }
  `;
  const r = hylo.compile({ source, emit: ["executable", "llvm"] });
  expect(r.diagnostics).toEqual([]);
  expect(r.artifacts.llvm).toMatch(/define .*@main/);
  expect((await hylo.run(r.executable!)).exitCode).toBe(42);
});

test("loads the compiler next to the loader by default", async () => {
  const { load }: { load: typeof Load } = await import(
    /* @vite-ignore */ `/@fs${inject("release")}/index.mjs`
  );
  const hylo = await load();
  const r = hylo.compile({ source: "public fun main() -> Int32 { 7 }" });
  expect((await hylo.run(r.executable!)).exitCode).toBe(7);
});
