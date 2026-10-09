# @hylo-lang/hylo-wasm

Compile and run [Hylo](https://hylo-lang.org) programs in a browser or in Node, with the Hylo
compiler compiled to WebAssembly.

This package is the JavaScript side: it loads a compiler release, drives the compiler, and runs
the WebAssembly executables it produces in an in-memory WASI environment. The compiler itself is
not in the package, since it is tens of megabytes: it is a release, a directory of files that a
web server serves as is, published with every Hylo release.

```ts
import { load } from "@hylo-lang/hylo-wasm";

const hylo = await load({ baseUrl: "https://example.com/hylo/" }); // where a release is served
const r = hylo.compile({
  source: "public fun main() -> Int32 { 42 }",
  emit: ["executable", "ir", "llvm", "assembly"], // any subset
});
r.diagnostics; // [] or errors, with sites and rendered text
r.artifacts.llvm; // LLVM IR, as text
const { exitCode, stdout, trap } = await hylo.run(r.executable!);
```

Loading downloads about 15 MB and compiles the standard library, which takes a few seconds; every
`compile` after that takes a fraction of a second.

## Entry points

| | |
|---|---|
| `@hylo-lang/hylo-wasm` | `load` a release by URL, or `instantiate` one from its files; `run` an executable. |
| `@hylo-lang/hylo-wasm/worker` | A Web Worker hosting the compiler, so that a page's main thread never waits on it. It loads the release its URL's `compiler` parameter names. |
| `@hylo-lang/hylo-wasm/protocol` | The types of requests, answers, worker messages, and a release's `manifest.json`. |

## Developing

This package lives in hylo-new's `Sources/WASM/js`, next to the compiler it drives, and is tested
with it; see `Sources/WASM/README.md`.

| | |
|---|---|
| `src/` | What is published. |
| `tests/` | Tests of the compiler through this package, against a build of it (`npm test`), and of a packaged release in Chromium (`npm run test:browser`). |
| `scripts/` | What CI uses to package a compiler release and check one, and to check this package as its users get it (`smoke-test-package.ts`). |
