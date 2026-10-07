# Hylo IR syntax

`hylo-ir.tmLanguage.json` is a TextMate grammar for Hylo IR as the compiler prints it
(`hc --emit raw-ir` and `--emit ir`). It works with anything that reads TextMate grammars, such as
[Shiki](https://shiki.style), which hylo-lang.org and the playground use, and VS Code. Its language
id is `hylo-ir`.

It lives here, next to the printer, so that the two change together. `test.mjs` highlights the IR
expected by the compiler's own tests (`Tests/CompilerTests/**/*-ir.expected`) and fails if any
word is left without a scope, so a construct the printer learns shows up here first:

```sh
cd Tools/syntax && npm install && npm test
node test.mjs more.ir   # also check other IR
```

The scopes are the conventional TextMate ones, so any theme colours it:

| what | scope |
|---|---|
| `fun`, `global` | `keyword.other.*` |
| instructions (`access`, `store`, ...) | `keyword.other.instruction` |
| terminators (`br`, `condbr`, `return`, ...) | `keyword.control.terminator` |
| conventions and capabilities (`let`, `inout`, `sink`, `set`) | `storage.modifier.convention` |
| `%pN`, `%rN`, `%bN` | `variable.parameter`, `variable.other.register`, `entity.name.label.block` |
| function names, synthesized names (`$implementation[...]`) | `entity.name.function`, `support.function.synthesized` |
| builtins (`icmp_sgt_i32`) | `support.function.builtin` |
| machine types (`i32`, `ptr`, `float64`), other types | `storage.type.machine`, `entity.name.type` |
| `#preferred`, `#witness`, `#!poison` | `constant.language.*` |
