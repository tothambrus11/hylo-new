# @hylo-lang/hylo-wasm

Compile and run [Hylo](https://hylo-lang.org) programs in a browser or in Node, with the Hylo
compiler compiled to WebAssembly.

The package holds the compiler, about 15 MB, and the JavaScript that loads it, drives it, and runs
the WebAssembly executables it produces in an in-memory WASI environment. Importing the package
costs nothing: the compiler is only downloaded, or read from disk in Node, when `load` is called.

```ts
import { load } from "@hylo-lang/hylo-wasm";

const hylo = await load(); // the compiler shipped next to this module
const r = hylo.compile({
  source: "public fun main() -> Int32 { 42 }",
  emit: ["executable", "ir", "llvm", "assembly"], // any subset
});
r.diagnostics; // [] or errors, with sites and rendered text
r.artifacts.llvm; // LLVM IR, as text
const { exitCode, stdout, trap } = await hylo.run(r.executable!);
```

Loading compiles the standard library, which takes a few seconds; every `compile` after that takes
a fraction of a second.

## Where the compiler comes from

The compiler is a release: `manifest.json` and the files it names, in `dist/` next to the loader.
`load()` finds it there through the loader's own URL, which works when the package is served as it
is: from a CDN that serves npm packages, such as `https://cdn.jsdelivr.net/npm/@hylo-lang/hylo-wasm@<version>/dist/index.js`,
from a page's server, or from `node_modules` in Node.

A bundler moves the loader into its own output, away from those files, so a bundled page either
serves them itself (copying `node_modules/@hylo-lang/hylo-wasm/dist/` except the `.js` files) or
names where they are:

```ts
const hylo = await load({ baseUrl: "https://cdn.jsdelivr.net/npm/@hylo-lang/hylo-wasm@<version>/dist/" });
```

Every file but `manifest.json` has a hash of its contents in its name, so it can be cached as
immutable. The same files are published with every Hylo release as
`hylo-<tag>-wasm32-wasip1.tar.zst`, with the loaders bundled next to them.

## Entry points

| | |
|---|---|
| `@hylo-lang/hylo-wasm` | `load` the compiler (the package's, or a release at another URL), or `instantiate` one from its files; `run` an executable. |
| `@hylo-lang/hylo-wasm/worker` | A Web Worker hosting the compiler, so that a page's main thread never waits on it. It loads the compiler next to it, or the release its URL's `compiler` parameter names. |
| `@hylo-lang/hylo-wasm/protocol` | The types of requests, answers, worker messages, and a release's `manifest.json`. |

## Developing

This package lives in hylo-new's `Sources/WASM/js`, next to the compiler it drives, and is tested
with it; see `Sources/WASM/README.md`.

| | |
|---|---|
| `src/` | What is published. |
| `tests/` | Tests of the compiler through this package, against a build of it (`npm test`), and of a packaged release in Chromium (`npm run test:browser`). |
| `scripts/` | What CI uses to package a compiler release and check one, to put a release's compiler into this package (`include-compiler.ts`, after `npm run build`), and to check this package as its users get it (`smoke-test-package.ts`). |
