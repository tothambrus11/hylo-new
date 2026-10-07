// Checks the grammars of what the compiler prints. The Hylo IR grammar is checked against the IR
// the compiler's own test cases expect, plus any files named on the command line; both grammars
// are checked line by line for the scopes that are easy to get subtly wrong.
//
//   node test.mjs [file.ir ...]
//
// Every word must be given a scope of its own, so that a construct the printer learns and the
// grammar does not shows up here rather than as uncoloured text on a web page. A few lines are
// also checked token by token, for the scopes that are easy to get subtly wrong.

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { createHighlighter } from "shiki";

const here = path.dirname(new URL(import.meta.url).pathname);
const grammar = (name) => JSON.parse(readFileSync(path.join(here, `${name}.tmLanguage.json`), "utf8"));
const highlighter = await createHighlighter({
  themes: ["github-dark"],
  langs: [grammar("hylo-ir"), grammar("wasm-asm")],
});

/** Returns each token of `text`, highlighted as `lang`, with the innermost scope it was given. */
function tokens(text, lang = "hylo-ir") {
  return highlighter
    .codeToTokens(text, { lang, theme: "github-dark", includeExplanation: true })
    .tokens.flatMap((line, i) =>
      line.flatMap((t) =>
        t.explanation.map((e) => ({ line: i + 1, text: e.content, scope: e.scopes.at(-1).scopeName })),
      ),
    );
}

const tests = path.join(here, "../../Tests/CompilerTests");
const corpus = ["positive", "negative"]
  .flatMap((d) => readdirSync(path.join(tests, d)).map((f) => path.join(tests, d, f)))
  .filter((f) => f.endsWith("-ir.expected"))
  .concat(process.argv.slice(2));
assert.ok(corpus.length > 0, "no IR to check the grammar against");

let failures = 0;
for (const file of corpus) {
  for (const t of tokens(readFileSync(file, "utf8"))) {
    if (/[A-Za-z0-9]/.test(t.text) && t.scope === "source.hylo-ir") {
      failures += 1;
      console.log(`${path.relative(process.cwd(), file)}:${t.line}: unscoped ${JSON.stringify(t.text)}`);
    }
  }
}

/** Asserts that `text` scopes each of `expected`'s words as given, in order. */
function check(text, expected, lang = "hylo-ir") {
  const got = tokens(text, lang)
    .filter((t) => t.text.trim() !== "")
    .map((t) => [t.text.trim(), t.scope.replace(/\.(hylo-ir|wasm-asm)$/, "")]);
  for (const [word, scope] of expected) {
    const i = got.findIndex(([w]) => w === word);
    assert.ok(i >= 0, `${JSON.stringify(word)} not found in ${JSON.stringify(text)}`);
    assert.equal(got[i][1], scope, `scope of ${JSON.stringify(word)} in ${JSON.stringify(text)}`);
    got.splice(0, i + 1);
  }
}

check("fun factorial(_:)(sink %p0: Int32, set %p1: Int32) {", [
  ["fun", "keyword.other.fun"],
  ["factorial", "entity.name.function"],
  ["(_:)", "entity.name.function.labels"],
  ["sink", "storage.modifier.convention"],
  ["%p0", "variable.parameter"],
  ["Int32", "entity.name.type"],
]);
check("fun id(_:)(inout %p0: Int32) inout <: Int32 {", [
  ["inout", "storage.modifier.convention"],
  ["inout", "storage.modifier.convention"],
  ["<:", "keyword.operator"],
  ["Int32", "entity.name.type"],
]);
check("fun $implementation[P.f for Self: T].existentialized(let %p0: Type) {", [
  ["$implementation", "support.function.synthesized"],
  ["for", "keyword.other"],
  ["existentialized", "support.function.derived"],
]);
check("fun Triple.$<ConformanceDeclaration at main:4.18>() let <: Deinitializable<Triple> {", [
  ["Triple", "entity.name.type"],
  ["ConformanceDeclaration", "support.class"],
  ["main:4.18", "constant.other.source-site"],
  ["<:", "keyword.operator"],
]);
check("  %r6 = apply make.existentialized(%r14) => %r17", [
  ["make", "entity.name.function"],
  ["existentialized", "support.function.derived"],
]);
check('  %r3 = property "two" of %r2 as [Void](let P<Self>, self: let Self) let -> Int32', [
  ["self", "variable.parameter.label"],
  ["->", "keyword.operator"],
]);
check("%b2:", [["%b2", "entity.name.label.block"]]);
check("  %r20 = condbr %r18, %b3, %b2", [
  ["%r20", "variable.other.register.definition"],
  ["condbr", "keyword.control.terminator"],
  ["%r18", "variable.other.register"],
  ["%b3", "entity.name.label.block"],
]);
check("  %r2 = access [let, inout] %r1", [
  ["access", "keyword.other.instruction"],
  ["let", "storage.modifier.convention"],
  ["inout", "storage.modifier.convention"],
]);
check("  %r82 = apply_builtin icmp_sgt_i32(%r79, %r81)", [
  ["apply_builtin", "keyword.other.instruction"],
  ["icmp_sgt_i32", "support.function.builtin"],
]);
check('  %r78 = property "value" of %r12 as i32', [
  ['"value"', "string.quoted.double"],
  ["of", "keyword.other"],
  ["i32", "storage.type.machine"],
]);
check("  %r0 = alloca Int32, #preferred", [["#preferred", "constant.language.alignment"]]);

check("\t.functype\tmain (i32, i32) -> (i32)", [
  [".functype", "keyword.control.directive"],
  ["main", "variable.other.symbol"],
  ["i32", "storage.type"],
  ["->", "keyword.operator"],
], "wasm-asm");
check("main:", [["main", "entity.name.function"]], "wasm-asm");
check(".LBB0_2:", [[".LBB0_2", "entity.name.label"]], "wasm-asm");
check("\ti32.const\t24", [["i32.const", "keyword.other.instruction"], ["24", "constant.numeric"]], "wasm-asm");
check("\tbr_if   \t0  # 0: down to label1", [
  ["br_if", "keyword.other.instruction"],
  ["# 0: down to label1", "comment.line.number-sign"],
], "wasm-asm");
check('\t.section\t.text.main,"",@', [[".section", "keyword.control.directive"], ['""', "string.quoted.double"]], "wasm-asm");

if (failures > 0) {
  console.log(`${failures} unscoped word(s)`);
  process.exit(1);
}
console.log(`ok: ${corpus.length} file(s) of IR, and the spot checks`);
