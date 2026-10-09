// The compiler's own single-file test cases (Tests/CompilerTests), run through the WebAssembly
// build, which must agree with what they expect of the native compiler.
//
// A positive case must compile without errors to the stage it names and, if it runs, exit with the
// status it expects or trap if it expects to. A negative case must report exactly the diagnostics in
// its `.diagnostics.expected` file, compared by site, level and message. Package cases
// (directories) are left out: they exercise the driver's handling of files, which the WebAssembly
// build does not have.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import type { CompileRequest, CompileResponse, Compiler, Phase } from "../src/index.ts";
import { compiler, repository } from "./support.ts";

const cases = path.join(repository, "Tests/CompilerTests");

let hylo: Compiler;
beforeAll(async () => {
  hylo = await compiler();
});

/** The attributes of a test case, from the first line of its source. */
interface Attributes {
  stage: string;
  exitStatus: number;
  trap: boolean;
  standardLibrary: boolean;
  optimizations: boolean;
}

/** Returns the attributes on the first line of `source`. */
function attributes(source: string): Attributes {
  const a = {
    stage: "execution",
    exitStatus: 0,
    trap: false,
    standardLibrary: true,
    optimizations: false,
  };
  const first = source.split("\n", 1)[0];
  if (!first.startsWith("//!")) return a;
  for (const word of first.slice(3).trim().split(/\s+/)) {
    const [key, value] = word.split(":");
    if (key === "stage") a.stage = value;
    else if (key === "exit-status") a.exitStatus = Number(value);
    else if (key === "trap") a.trap = true;
    else if (key === "no-std") a.standardLibrary = false;
    else if (key === "optimizations") a.optimizations = true;
  }
  return a;
}

/** Returns the request compiling `source` as far as a case with attributes `a` goes. */
function request(source: string, a: Attributes, optimization = 0): CompileRequest {
  const stopAfter = ["parsing", "typing", "lowering"].includes(a.stage)
    ? (a.stage as Phase)
    : undefined;
  // Some errors are only found by the back end, which runs when a case would be executed.
  const emit: CompileRequest["emit"] =
    a.stage === "execution" ? ["executable"] : a.stage === "llvm" ? ["llvm"] : [];
  return { source, optimization, standardLibrary: a.standardLibrary, stopAfter, emit };
}

/** Returns the first line of each diagnostic of `r`, without the file name, sorted. */
const sites = (r: CompileResponse, levels = ["error", "warning", "note"]): string[] =>
  r.diagnostics
    .filter((d) => levels.includes(d.level))
    .map((d) => withoutFile(d.rendered.split("\n", 1)[0]))
    .sort();

/** Returns `line`, a rendered diagnostic, without the file name, which differs by construction. */
const withoutFile = (line: string): string =>
  line.replace(/^.*?(?=\d+\.\d+(-\S+)?: (error|warning|note): )/, "");

/** Returns the single-file cases in `kind`, `positive` or `negative`, as `[name, source]`. */
const files = (kind: string): [string, string][] =>
  readdirSync(path.join(cases, kind))
    .filter((f) => f.endsWith(".hylo"))
    .sort()
    .map((f) => [f, readFileSync(path.join(cases, kind, f), "utf8")]);

describe("positive", () => {
  test.each(files("positive"))("%s", async (_, source) => {
    const a = attributes(source);
    for (const optimization of a.optimizations ? [0, 3] : [0]) {
      const r = hylo.compile(request(source, a, optimization));
      expect(r.error).toBeUndefined();
      expect(sites(r, ["error"])).toEqual([]);
      if (a.stage !== "execution") continue;
      const x = await hylo.run(r.executable!);
      if (a.trap) expect(x.trap, "expected a trap").toBeDefined();
      else expect(x).toMatchObject({ exitCode: a.exitStatus });
    }
  });
});

describe("negative", () => {
  test.each(files("negative"))("%s", (name, source) => {
    const r = hylo.compile(request(source, attributes(source)));
    expect(r.error).toBeUndefined();
    const expectedFile = path.join(
      cases,
      "negative",
      name.replace(/\.hylo$/, ".diagnostics.expected"),
    );
    if (!existsSync(expectedFile)) {
      expect(sites(r, ["error"])).not.toEqual([]);
      return;
    }
    const expected = readFileSync(expectedFile, "utf8")
      .split("\n")
      .filter((l) => /^\S+:\d+\.\d+(-\S+)?: (error|warning|note): /.test(l))
      .map(withoutFile)
      .sort();
    expect(sites(r)).toEqual(expected);
  });
});
