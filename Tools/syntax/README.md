# Syntax of what the compiler prints

TextMate grammars for the compiler's textual outputs, for anything that reads them, such as
[Shiki](https://shiki.style) (which hylo-lang.org and the playground use) and VS Code:

| grammar | language id | for |
|---|---|---|
| `hylo-ir.tmLanguage.json` | `hylo-ir` | Hylo IR, as `hc --emit raw-ir` and `--emit ir` print it |
| `wasm-asm.tmLanguage.json` | `wasm-asm` | WebAssembly as LLVM prints it for wasm32 targets (`hc --emit asm`): GNU-style directives and labels, not the WAT text format |

LLVM IR needs no grammar here: Shiki and most editors have one.

They live here, next to the printers, so that the two change together. `test.mjs` highlights the
IR expected by the compiler's own tests (`Tests/CompilerTests/**/*-ir.expected`) and fails if any
word is left without a scope, so a construct the printer learns shows up here first; it also
checks both grammars line by line:

```sh
cd Tools/syntax && npm install && npm test
node test.mjs more.ir   # also check other IR
```

The scopes are the conventional TextMate ones, so any theme colours them. For Hylo IR:

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
