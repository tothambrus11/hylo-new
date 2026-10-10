// The compiler compiles programs, reports diagnostics, and produces executables that run, through
// the same in-memory WASI file system a browser uses.

import { beforeAll, expect, test } from "vitest";
import type { Compiler } from "../src/index.ts";
import { compiler } from "./support.ts";

let hylo: Compiler;
beforeAll(async () => {
  hylo = await compiler();
});

test("compiles and runs a program returning its exit status", async () => {
  const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }" });
  expect(r.error).toBeUndefined();
  expect(r.diagnostics).toEqual([]);
  expect(r.executable?.length).toBeGreaterThan(0);
  expect((await hylo.run(r.executable!)).exitCode).toBe(42);
});

test("uses the standard library", async () => {
  const r = hylo.compile({
    source: `
      fun use<T>(x: T) {}

      public fun main() -> Int32 {
        var x = 40
        &x = x + 2
        use(x == 42)
        return 7
      }
    `,
  });
  expect(r.error).toBeUndefined();
  expect(r.diagnostics).toEqual([]);
  expect((await hylo.run(r.executable!)).exitCode).toBe(7);
});

test("emits every intermediate representation", () => {
  const r = hylo.compile({
    source: "public fun main() -> Int32 { 1 }",
    emit: ["raw-ir", "ir", "llvm", "assembly"],
  });
  expect(r.error).toBeUndefined();
  for (const k of ["raw-ir", "ir", "llvm", "assembly"] as const) {
    expect(r.artifacts[k], k).not.toHaveLength(0);
  }
  expect(r.artifacts.llvm).toMatch(/define .*@main/);
  expect(r.executable).toBeUndefined();
});

test("stops after the phase `stopAfter` names", () => {
  const r = hylo.compile({
    source: "public fun main() -> Int32 { 1 }",
    emit: ["ir", "llvm", "executable"],
    stopAfter: "lowering",
  });
  expect(r.error).toBeUndefined();
  expect(Object.keys(r.artifacts)).toEqual(["ir"]);
  expect(r.executable).toBeUndefined();
});

test("reports what the front end produced before the back end runs", () => {
  const reports: unknown[] = [];
  const r = hylo.compile(
    { source: "public fun main() -> Int32 { 1 }", emit: ["raw-ir", "ir", "llvm"] },
    { onFrontEnd: (f) => reports.push(f) },
  );
  expect(r.error).toBeUndefined();
  expect(reports).toEqual([
    {
      diagnostics: [],
      artifacts: { "raw-ir": r.artifacts["raw-ir"], ir: r.artifacts.ir },
      compilerUnusable: false,
      milliseconds: expect.any(Number),
    },
  ]);
});

test("reports nothing early when the back end does not run", () => {
  let reports = 0;
  const onFrontEnd = () => ++reports;
  hylo.compile({ source: "public fun main() -> Int32 { 1 }", emit: ["ir"] }, { onFrontEnd });
  hylo.compile(
    { source: "public fun main() -> Int32 { x }", emit: ["ir", "llvm"] },
    { onFrontEnd },
  );
  hylo.compile(
    { source: "public fun main() -> Int32 { 1 }", emit: ["ir", "llvm"], stopAfter: "lowering" },
    { onFrontEnd },
  );
  expect(reports).toBe(0);
});

test("throws what the front end's report threw, once compiling is done", () => {
  const thrown = new Error("from the host");
  expect(() =>
    hylo.compile(
      { source: "public fun main() -> Int32 { 1 }", emit: ["ir", "llvm"] },
      {
        onFrontEnd: () => {
          throw thrown;
        },
      },
    ),
  ).toThrow(thrown);
  expect(hylo.usable).toBe(true);
  expect(hylo.compile({ source: "public fun main() -> Int32 { 1 }" }).error).toBeUndefined();
});

test("optimizes", () => {
  const r = hylo.compile({
    source: "public fun main() -> Int32 { 3 }",
    emit: ["llvm"],
    optimization: 2,
  });
  expect(r.error).toBeUndefined();
  expect(r.artifacts.llvm).toMatch(/ret i32 3/);
});

test("reports diagnostics and carries on", async () => {
  const r = hylo.compile({ source: "public fun main() -> Int32 { undefined_name }" });
  expect(r.executable).toBeUndefined();
  expect(r.diagnostics[0]).toMatchObject({ level: "error", site: { line: 1 } });
  const again = hylo.compile({ source: "public fun main() -> Int32 { 0 }" });
  expect((await hylo.run(again.executable!)).exitCode).toBe(0);
});

test("reports a trap as such", async () => {
  const r = hylo.compile({ source: "public fun main() { Builtin.trap() }" });
  expect(r.error).toBeUndefined();
  expect(r.diagnostics).toEqual([]);
  const x = await hylo.run(r.executable!);
  expect(x.exitCode).toBeNull();
  expect(x.trap).toBeDefined();
});

test("reports running out of stack as a trap", async () => {
  const r = hylo.compile({
    source: `
      fun deeper() -> Int32 { deeper() + (1 as Int32) }
      public fun main() -> Int32 { deeper() }
    `,
  });
  expect(r.error).toBeUndefined();
  expect(r.diagnostics.filter((d) => d.level === "error")).toEqual([]);
  const x = await hylo.run(r.executable!);
  expect(x.exitCode).toBeNull();
  expect(x.trap).toBeDefined();
  expect(hylo.usable).toBe(true);
});
