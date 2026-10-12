// The compiler's own test cases (Tests/CompilerTests), run through the WebAssembly build, which
// must agree with what they expect of the native compiler.
//
// A positive case must compile without errors to the stage it names and, if it runs, exit with the
// status it expects or trap if it expects to. A negative case must report exactly the diagnostics in
// its `.diagnostics.expected` files, compared by site, level and message. Package cases
// (directories) are compiled as requests of several files; those with files other than Hylo
// sources, such as C sources or inputs, are left out, as the WebAssembly build has nowhere to put
// them. The attributes and expectations are those the native harness reads; see
// `Tests/CompilerTests/Manifest.swift` and `CompilerTests.swift`, which this follows.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import type {
  CompileRequest,
  CompileResponse,
  Compiler,
  Diagnostic,
  Phase,
  SourceFile,
} from "../src/index.ts";
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
  const first = source.split("\n", 1)[0];
  return options(first.startsWith("//!") ? first.slice(3).trim().split(/\s+/) : []);
}

/** Returns the attributes `words` give, such as `["stage:typing", "no-std"]`. */
function options(words: string[]): Attributes {
  const a = {
    stage: "execution",
    exitStatus: 0,
    trap: false,
    standardLibrary: true,
    optimizations: false,
  };
  for (const word of words) {
    const [key, value] = word.split(":");
    if (key === "stage") a.stage = value;
    else if (key === "exit-status") a.exitStatus = Number(value);
    else if (key === "trap") a.trap = true;
    else if (key === "no-std") a.standardLibrary = false;
    else if (key === "optimizations") a.optimizations = true;
  }
  return a;
}

/** Returns the request compiling `files` as far as a case with attributes `a` goes. */
function request(files: SourceFile[], a: Attributes, optimization = 0): CompileRequest {
  const stopAfter = ["parsing", "typing", "lowering"].includes(a.stage)
    ? (a.stage as Phase)
    : undefined;
  // Some errors are only found by the back end, which runs when a case would be executed.
  const emit: CompileRequest["emit"] =
    a.stage === "execution" ? ["executable"] : a.stage === "llvm" ? ["llvm"] : [];
  return { files, optimization, standardLibrary: a.standardLibrary, stopAfter, emit };
}

/** Returns `ds` and their notes, and their notes' notes, flattened. */
const flatten = (ds: Diagnostic[]): Diagnostic[] => ds.flatMap((d) => [d, ...flatten(d.notes)]);

/** Returns the first line of each diagnostic of `r`, notes included, without the file name, sorted. */
const sites = (r: CompileResponse, levels = ["error", "warning", "note"]): string[] =>
  flatten(r.diagnostics)
    .filter((d) => levels.includes(d.level))
    .map((d) => withoutFile(d.rendered.split("\n", 1)[0]))
    .sort();

/** Returns `line`, a rendered diagnostic, without the file name, which differs by construction. */
const withoutFile = (line: string): string =>
  line.replace(/^.*?(?=\d+\.\d+(-\S+)?: (error|warning|note): )/, "");

/** A test case: its Hylo sources, its attributes, and the diagnostics it expects, if it says. */
interface Case {
  files: SourceFile[];
  attributes: Attributes;
  /** The lines of its `.diagnostics.expected` files, or `null` if it has none. */
  expected: string[] | null;
}

/** Returns the lines of the `.diagnostics.expected` file next to `hylo`, if there is one. */
const expectedNextTo = (hylo: string): string[] | null => {
  const f = hylo.replace(/\.hylo$/, ".diagnostics.expected");
  return existsSync(f) ? readFileSync(f, "utf8").split("\n") : null;
};

/** Returns the files under `dir`, recursively, relative to it with `/` as separator, sorted. */
const filesUnder = (dir: string): string[] =>
  readdirSync(dir, { recursive: true, withFileTypes: true })
    .filter((e) => e.isFile())
    .map((e) => path.relative(dir, path.join(e.parentPath, e.name)).split(path.sep).join("/"))
    .sort();

/** Returns the package case at `root`, or `null` if it has files other than Hylo sources. */
function packageCase(root: string): Case | null {
  const sources = filesUnder(root).filter(
    (f) => f !== "package.json" && !f.endsWith(".diagnostics.expected"),
  );
  if (!sources.every((f) => f.endsWith(".hylo"))) return null;
  const manifest = JSON.parse(readFileSync(path.join(root, "package.json"), "utf8"));
  const expected = sources.map((f) => expectedNextTo(path.join(root, f)));
  return {
    files: sources.map((f) => ({ name: f, contents: readFileSync(path.join(root, f), "utf8") })),
    attributes: options(manifest.options ?? []),
    expected: expected.every((e) => e === null) ? null : expected.flatMap((e) => e ?? []),
  };
}

/**
 * Returns the cases in `kind`, `positive` or `negative`, as `[name, case]`: single files, and
 * packages whose files are all Hylo sources, besides their manifest and expected diagnostics.
 */
const testCases = (kind: string): [string, Case][] =>
  readdirSync(path.join(cases, kind))
    .sort()
    .flatMap((name): [string, Case][] => {
      const root = path.join(cases, kind, name);
      if (name.endsWith(".package")) {
        const c = packageCase(root);
        return c === null ? [] : [[name, c]];
      }
      if (!name.endsWith(".hylo")) return [];
      const contents = readFileSync(root, "utf8");
      const c = { files: [{ name, contents }], attributes: attributes(contents) };
      return [[name, { ...c, expected: expectedNextTo(root) }]];
    });

describe("positive", () => {
  test.each(testCases("positive"))("%s", async (_, c) => {
    const a = c.attributes;
    for (const optimization of a.optimizations ? [0, 3] : [0]) {
      const r = hylo.compile(request(c.files, a, optimization));
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
  test.each(testCases("negative"))("%s", (_, c) => {
    const r = hylo.compile(request(c.files, c.attributes));
    expect(r.error).toBeUndefined();
    if (c.expected === null) {
      expect(sites(r, ["error"])).not.toEqual([]);
      return;
    }
    const expected = c.expected
      .filter((l) => /^\S+:\d+\.\d+(-\S+)?: (error|warning|note): /.test(l))
      .map(withoutFile)
      .sort();
    expect(sites(r)).toEqual(expected);
  });
});

test("runs package cases, positive and negative", () => {
  for (const kind of ["positive", "negative"]) {
    expect(
      testCases(kind).some(([name]) => name.endsWith(".package")),
      kind,
    ).toBe(true);
  }
});
