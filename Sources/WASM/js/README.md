# @hylo-lang/hylo-wasm

Compile and run [Hylo](https://hylo-lang.org) programs in a browser or in Node, with the Hylo
compiler compiled to WebAssembly.

The package holds the compiler, about 15 MB, and the JavaScript that loads it, drives it, and runs
the WebAssembly executables it produces in an in-memory WASI environment. Importing the package
costs nothing: the compiler is only downloaded, or read from disk in Node, when `load` is called.

```ts
import { load } from "@hylo-lang/hylo-wasm";

const hylo = await load(); // fetches, or in Node reads, the compiler this package ships
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

## Serving the compiler

The compiler's files sit next to the loader in `dist/`, and the loader refers to each with
`new URL("./<file>", import.meta.url)`. Bundlers recognize that pattern: Vite, webpack, Rollup
with its URL plugin, and esbuild-based tools copy the files into their output, with hashes in their
names so they can be cached as immutable, and rewrite the URLs. Nothing is fetched until `load` is
called, and nothing about the compiler ends up in the JavaScript a page loads first.

Two things are worth doing for a page:

- **Serve `.wasm` as `application/wasm`**, as most servers do, so that the compiler compiles as it
  downloads; otherwise it is compiled once downloaded. Compressing it on the wire, as most servers
  and CDNs do, makes it 14 MB rather than 38.
- **With Vite's dev server**, exclude the package from dependency optimization, which would move
  the loader away from the files:

  ```ts
  export default defineConfig({ optimizeDeps: { exclude: ["@hylo-lang/hylo-wasm"] } });
  ```

In a PWA, leave the compiler out of the precache, which the service worker would download on
install, and cache it at runtime instead, the first time a page loads it; with Workbox:

```ts
{ urlPattern: /\.(wasm|o|a)$|stdlib.*\.json$/, handler: "CacheFirst" }
```

In Node, the `node` export condition selects a loader that reads the files from disk.

## Entry points

| | |
|---|---|
| `@hylo-lang/hylo-wasm` | `load` the compiler, or `instantiate` one from its parts; `run` an executable. |
| `@hylo-lang/hylo-wasm/worker` | A Web Worker hosting the compiler, so that a page's main thread never waits on it; with Vite, `import HyloWorker from "@hylo-lang/hylo-wasm/worker?worker"`. |
| `@hylo-lang/hylo-wasm/protocol` | The types of requests, answers, and worker messages. |


## Developing

This package lives in hylo-new's `Sources/WASM/js`, next to the compiler it drives, and is tested
with it; see `Sources/WASM/README.md`.

| | |
|---|---|
| `src/` | What is published. |
| `tests/` | Tests of the compiler through this package, against what `build-compiler.sh` produced (`npm test`). |
| `scripts/` | What the build uses to collect the standard library's sources, and what CI uses to check this package as its users get it (`smoke-test-package.ts`). |

`npm run build` copies the compiler from `.build/wasm/compiler` (or `$HYLO_WASM_DIST`) into
`dist/`, so build the compiler first.
