// Checks that a built compiler compiles programs, reports diagnostics, and produces executables
// that run, through the same in-memory WASI file system a browser uses.
//
//   node smoke.mjs <dist>
//
// where <dist> is what `build-compiler.sh` produced.

import assert from "node:assert/strict";
import { readDist } from "./dist.mjs";
import { instantiate } from "./index.mjs";

const dist = process.argv[2];
if (dist === undefined) {
  console.error("usage: node smoke.mjs <dist>");
  process.exit(2);
}

const hylo = await instantiate(await readDist(dist));
console.log(`standard library compiled in ${hylo.standardLibraryMilliseconds.toFixed(0)} ms`);

let failures = 0;
async function check(name, body) {
  try {
    await body();
    console.log(`ok    ${name}`);
  } catch (e) {
    failures += 1;
    console.log(`FAIL  ${name}\n${e.stack ?? e}`);
  }
}

await check("compiles and runs a program returning its exit status", async () => {
  const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }" });
  assert.equal(r.error, undefined, r.error);
  assert.deepEqual(r.diagnostics, []);
  assert.ok(r.executable instanceof Uint8Array && r.executable.length > 0);
  console.log(`      compiled in ${r.milliseconds.toFixed(0)} ms, ${r.executable.length} bytes`);
  const x = await hylo.run(r.executable);
  assert.equal(x.exitCode, 42);
});

await check("uses the standard library", async () => {
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
  assert.equal(r.error, undefined, r.error);
  assert.deepEqual(r.diagnostics, []);
  assert.equal((await hylo.run(r.executable)).exitCode, 7);
});

await check("emits every intermediate representation", async () => {
  const r = hylo.compile({
    source: "public fun main() -> Int32 { 1 }",
    emit: ["raw-ir", "ir", "llvm", "assembly"],
  });
  assert.equal(r.error, undefined, r.error);
  for (const k of ["raw-ir", "ir", "llvm", "assembly"]) {
    assert.ok((r.artifacts[k] ?? "").length > 0, `no ${k}`);
  }
  assert.match(r.artifacts.llvm, /define .*@main/);
  assert.equal(r.executable, undefined);
});

await check("optimizes", async () => {
  const r = hylo.compile({ source: "public fun main() -> Int32 { 3 }", emit: ["llvm"], optimization: 2 });
  assert.equal(r.error, undefined, r.error);
  assert.match(r.artifacts.llvm, /ret i32 3/);
});

await check("reports diagnostics and carries on", async () => {
  const r = hylo.compile({ source: "public fun main() -> Int32 { undefined_name }" });
  assert.equal(r.executable, undefined);
  assert.ok(r.diagnostics.length > 0);
  assert.equal(r.diagnostics[0].level, "error");
  assert.equal(r.diagnostics[0].site.line, 1);
  const again = hylo.compile({ source: "public fun main() -> Int32 { 0 }" });
  assert.equal((await hylo.run(again.executable)).exitCode, 0);
});

await check("reports a trap as such", async () => {
  const r = hylo.compile({ source: "public fun main() { Builtin.trap() }" });
  assert.equal(r.error, undefined, r.error);
  assert.deepEqual(r.diagnostics, []);
  const x = await hylo.run(r.executable);
  assert.equal(x.exitCode, null);
  assert.ok(x.trap);
});

await check("reports running out of stack as a trap", async () => {
  const r = hylo.compile({
    source: `
      fun deeper() -> Int32 { deeper() + (1 as Int32) }
      public fun main() -> Int32 { deeper() }
    `,
  });
  assert.equal(r.error, undefined, r.error);
  assert.deepEqual(r.diagnostics.filter((d) => d.level === "error"), []);
  const x = await hylo.run(r.executable);
  assert.equal(x.exitCode, null);
  assert.ok(x.trap);
  assert.ok(hylo.usable);
});

if (hylo.log.length > 0) console.log(`compiler output:\n${hylo.log.join("\n")}`);
process.exit(failures === 0 ? 0 : 1);
