// Runs the compiler's own single-file test cases (Tests/CompilerTests) through the WebAssembly
// build, and checks it agrees with what they expect of the native one.
//
//   node conformance.mjs <dist> <Tests/CompilerTests>
//
// A positive case must compile without errors to the stage it names and, if it runs, exit with
// the status it expects or trap if it expects to. A negative case must report exactly the
// diagnostics in its `.diagnostics.expected` file, compared by site, level and message.
// Package cases (directories) are skipped: they exercise the driver's handling of files, which
// the WebAssembly build does not have.

import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { instantiate } from "./index.mjs";

const [dist, tests] = process.argv.slice(2);
if (tests === undefined) {
  console.error("usage: node conformance.mjs <dist> <Tests/CompilerTests>");
  process.exit(2);
}

const lib = path.join(dist, "sysroot", "lib");
const hylo = await instantiate({
  compiler: await WebAssembly.compile(readFileSync(path.join(dist, "hylo-wasm.wasm"))),
  standardLibrary: JSON.parse(readFileSync(path.join(dist, "stdlib.json"), "utf8")),
  sysroot: new Map(readdirSync(lib).map((n) => [n, readFileSync(path.join(lib, n))])),
});

/** Returns the test attributes on the first line of `source`. */
function attributes(source) {
  const first = source.split("\n", 1)[0];
  const a = { stage: "execution", exitStatus: 0, trap: false, std: true, optimizations: false };
  if (!first.startsWith("//!")) return a;
  for (const w of first.slice(3).trim().split(/\s+/)) {
    const [k, v] = w.split(":");
    if (k === "stage") a.stage = v;
    else if (k === "exit-status") a.exitStatus = Number(v);
    else if (k === "trap") a.trap = true;
    else if (k === "no-std") a.std = false;
    else if (k === "optimizations") a.optimizations = true;
  }
  return a;
}

/** The phase after which a case at `stage` stops, as the compiler names it. */
const stopAfter = { parsing: "parsing", typing: "typing", lowering: "lowering" };

/** Returns the error diagnostics of `r`, rendered as `line.column-range: level: message`. */
const errors = (r) =>
  r.diagnostics.filter((d) => d.level === "error").map((d) => d.rendered.split("\n", 1)[0]);

const results = { pass: 0, fail: 0, skip: 0 };
const failures = [];

async function positive(name, source) {
  const a = attributes(source);
  const levels = a.optimizations ? [0, 3] : [0];
  for (const optimization of levels) {
    const r = hylo.compile({
      source,
      optimization,
      standardLibrary: a.std,
      stopAfter: stopAfter[a.stage],
      emit: a.stage === "execution" ? ["executable"] : a.stage === "llvm" ? ["llvm"] : [],
    });
    if (r.error) return `internal error: ${r.error}`;
    if (errors(r).length > 0) return `unexpected errors:\n${errors(r).join("\n")}`;
    if (a.stage !== "execution") continue;
    const x = await hylo.run(r.executable);
    if (a.trap && x.trap === undefined) return `expected a trap, exited with ${x.exitCode}`;
    if (!a.trap && x.exitCode !== a.exitStatus) {
      return `expected exit status ${a.exitStatus}, got ${x.trap ? `a trap (${x.trap})` : x.exitCode}`;
    }
  }
  return null;
}

async function negative(name, source, expectedFile) {
  const a = attributes(source);
  // Some errors are only found by the back end, which runs when a case would be executed.
  const emit = a.stage === "execution" ? ["executable"] : a.stage === "llvm" ? ["llvm"] : [];
  const r = hylo.compile({ source, standardLibrary: a.std, stopAfter: stopAfter[a.stage], emit });
  if (r.error) return `internal error: ${r.error}`;
  // Sites are compared without file names, which differ by construction.
  const strip = (l) => l.replace(/^.*?(?=\d+\.\d+(-\S+)?: (error|warning|note): )/, "");
  const got = r.diagnostics.map((d) => strip(d.rendered.split("\n", 1)[0])).sort();
  if (!existsSync(expectedFile)) {
    return got.some((l) => / error: /.test(l)) ? null : "expected at least one error";
  }
  const expected = readFileSync(expectedFile, "utf8")
    .split("\n")
    .filter((l) => /^\S+:\d+\.\d+(-\S+)?: (error|warning|note): /.test(l))
    .map(strip)
    .sort();
  const g = got.join("\n");
  const e = expected.join("\n");
  return g === e ? null : `diagnostics differ\n--- expected\n${e}\n--- got\n${g}`;
}

for (const kind of ["positive", "negative"]) {
  const dir = path.join(tests, kind);
  for (const f of readdirSync(dir).sort()) {
    const name = `${kind}/${f}`;
    if (!f.endsWith(".hylo")) {
      if (f.endsWith(".package")) results.skip += 1;
      continue;
    }
    const source = readFileSync(path.join(dir, f), "utf8");
    let failure;
    try {
      failure =
        kind === "positive"
          ? await positive(name, source)
          : await negative(name, source, path.join(dir, f.replace(/\.hylo$/, ".diagnostics.expected")));
    } catch (e) {
      failure = `threw: ${e.stack ?? e}`;
    }
    if (failure === null) {
      results.pass += 1;
    } else {
      results.fail += 1;
      failures.push(`FAIL ${name}: ${failure}`);
    }
  }
}

for (const f of failures) console.log(f + "\n");
console.log(`${results.pass} passed, ${results.fail} failed, ${results.skip} packages skipped`);
process.exit(results.fail === 0 ? 0 : 1);
