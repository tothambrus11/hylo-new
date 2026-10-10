# The Hylo compiler on WebAssembly

The whole compiler, built as one WebAssembly module that runs in a browser or in Node: the front end,
the lowering to LLVM IR, LLVM's WebAssembly back end, and lld's WebAssembly linker. It turns a
Hylo program into a WebAssembly executable, which the page then runs. It is what the playground
and the runnable snippets on [hylo-lang.org](https://hylo-lang.org) run.

```ts
import { load } from "@hylo-lang/hylo-wasm"; // the package in js/

const hylo = await load();                        // ~2.5 s: compiles the standard library
const r = hylo.compile({
  source: "public fun main() -> Int32 { 42 }",
  emit: ["executable", "ir", "llvm", "assembly"], // any subset
});
r.diagnostics;                                    // [] or errors, with sites and rendered text
r.artifacts.llvm;                                 // LLVM IR, as text
const { exitCode, stdout, trap } = await hylo.run(r.executable!);
```

## What it costs

Measured on a release build (`-Osize`, then `wasm-opt -Oz`), in Node 22 and headless Chromium:

| | |
|---|---:|
| compiler module | 38.6 MB (14.4 MB gzipped) |
| everything else (standard library sources, C runtime) | 0.5 MB gzipped |
| compiling the standard library, once at load | ~2.5 s |
| compiling **and linking** a small program | 150–320 ms |
| the resulting executable | ~10 KB |

Every one of the compiler's single-file test cases (`Tests/CompilerTests`) passes through it:
positive cases compile, link and run with the exit status or trap they expect, and negative cases
report the same diagnostics as the native compiler, site for site. CI holds it to that.

## How it is put together

```
 page ──JSON──▶ hylo-wasm.wasm (a WASI reactor)
                 ├─ FrontEnd       parse, scope, type, lower to Hylo IR
                 ├─ BackEnd        Hylo IR → LLVM IR       ┐
                 ├─ Swifty-LLVM    LLVM's C API + shims    ├ LLVM 23, built for wasm32-wasip1
                 └─ WASMLinker     lld::wasm, in-process   ┘
                       │ reads /sysroot/lib/{crt1-command.o, entry.o, libc.a, shims.o, builtins}
                       ▼ writes /tmp/main.wasm
 page ◀──bytes── a WASI command, run with an in-memory WASI shim
```

Everything is in this directory:

| | |
|---|---|
| `hylo-wasm/` | The reactor. The host instantiates it once, hands over the standard library's sources through `hylo_init`, and calls `hylo_compile` as often as it likes. Requests and answers are JSON, as length-prefixed UTF-8 in linear memory. While compiling, it hands the host what the front end produced through the function `hylo_host.front_end_done`, which the host provides. |
| `HyloWASMSession/` | What compiling means, independently of the transport: each request is compiled in a copy of a program whose standard library is already lowered. |
| `WASMLinker/` | Calls `lld::lldMain` with the WebAssembly driver. The files it reads and writes live in a WASI file system that the host keeps in memory, the same in a browser and in Node. |
| `sysroot/entry.c` | A file linked into every executable; see below. |
| `scripts/` | The build: `config.sh` pins every input, `fetch-llvm.sh` and `fetch-binaryen.sh` download LLVM and binaryen, `build-compiler.sh` builds the module and the files it needs into `.build/wasm/compiler`. |
| `js/` | The npm package `@hylo-lang/hylo-wasm`, which ships the compiler, loads it, drives the reactor, and runs what it produces, in a browser or in Node; see its `README.md`. Its `tests/` test the compiler through it. |

The three Swift targets are targets of the compiler's package, but only when its manifest is
evaluated with `LLVM_WASM_PREFIX` set, as `build-compiler.sh` does: they compile against an LLVM
built for WebAssembly, so every other build of the package, and every CI job building it, leaves
them out.

## The decisions that are not obvious

**LLVM comes from [hylo-lang/llvm-build](https://github.com/hylo-lang/llvm-build)**, which builds
it to run in WebAssembly and publishes it with its native packages (see its `docs/wasm.md`).
`fetch-llvm.sh` downloads the release pinned in `config.sh` and checks it against the pinned
checksum. It is compiled by the Swift toolchain's own clang against the Swift SDK's sysroot,
because the compiler is one binary, so LLVM's C++ and the Swift runtime must agree on the C++
standard library. That makes the package specific to the Swift version, which its name records.
Two things in it are particular to the Swift SDK: the SDK's libc++ is built without threads, which
LLVM does not compile without, so the package carries a `libcxx-threads/__config_site` turning
them back on and a `libc++threads.a` with the parts of libc++ that need; and every C++ file
including LLVM's headers must see that `__config_site`, which `llvm.pc` and `Package.swift` put on
the include path.

**The reactor runs Swift's executor itself.** Its exports are called by the host and must return
synchronously, and a reactor has no `async` entry point whose return would run pending tasks, so
the front end's `async` phases would never finish. `runToCompletion` (in `hylo-wasm/`)
starts the work in a task and runs `MainActor.executor` until it is done. On WASI that executor is
a cooperative run loop that also runs the tasks of the default executor, so the compiler runs its
`async` code unchanged, `Task.detached` included. The `runUntil` it relies on is still behind
`@_spi(ExperimentalCustomExecutors)` in Swift 6.3, which is why it is confined to the reactor.

**Only `FoundationEssentials` is linked, not Foundation.** Foundation brings ICU, whose data alone
is 34 MB, and it gets linked as soon as anything imports Foundation, as some of the compiler's
dependencies do: importing it autolinks it ahead of `FoundationEssentials`, so the symbols the two
share resolve to Foundation's copies, which need the rest of it. `build-compiler.sh` therefore
builds with the repository's `foundation-essentials.toolset.json`, as the native releases do on
Linux and Windows, which stops imports from autolinking Foundation, ICU and CoreFoundation, so that
using anything outside `FoundationEssentials` is a link error. The few such uses are replaced by
what `FoundationEssentials` or the standard library offer, and the reactor does not link the
`StandardLibrary` target, whose resource accessor needs `Bundle`; the script builds that target
separately for its sources.

**A Hylo `main` needs a forwarder on WASI** (`sysroot/entry.c`). wasi-libc's `_start` calls
`__main_argc_argv`, the name clang gives a C `main(argc, argv)`. LLVM IR from any other front end
defines plain `main`, so without the forwarder `_start` calls an undefined weak symbol and traps.

**The compiler now runs on a 32-bit host**, which no other configuration exercises. That found two
bugs in `BackEnd`, fixed here: a 64-bit integer literal that does not fit in `Int`, and integer
constants built from `BigInt.words`, whose words are host-sized, so that `-1 as Int64` became
`4294967295`.

## Building

Requires Swift 6.3.2 with its Swift SDK for WebAssembly, Node, curl, and optionally binaryen's
`wasm-opt`. Downloads go in `~/.cache/hylo-wasm` (`$HYLO_WASM_CACHE`).

```sh
swift sdk install <URL and checksum in scripts/config.sh>
Sources/WASM/scripts/fetch-llvm.sh       # once per LLVM release: ~150 MB unpacked
Sources/WASM/scripts/fetch-binaryen.sh   # optional: wasm-opt, for release builds
Sources/WASM/scripts/build-compiler.sh   # ~5 min in release, ~2 min in debug
cd Sources/WASM/js
npm ci
npm test                                 # the smoke test and Tests/CompilerTests, in Node
npm run build && npm pack                # the package, with the compiler
node scripts/smoke-test-package.ts hylo-lang-hylo-wasm-0.0.0.tgz  # in Node, and bundled, in Chromium
```

To try an LLVM package built locally with llvm-build's `ci/build-llvm-wasi.ts`, point
`LLVM_WASM_PREFIX` at its install directory and skip `fetch-llvm.sh`.

## Releases

The compiler is published as part of the npm package `@hylo-lang/hylo-wasm`, whose `README.md`
says how pages and Node programs load it. Its files keep fixed names, and the loader refers to each
with `new URL("./<file>", import.meta.url)`, which bundlers recognize: they copy the files into
their output, with hashes in their names, and rewrite the URLs. The compiler is shipped
uncompressed, so that it compiles as it downloads (`WebAssembly.compileStreaming`) and servers and
CDNs compress it on the wire as they do any other file.

`.github/actions/wasm-compiler` downloads LLVM, builds the compiler, runs the smoke test and the
compiler's test cases, packs the package and checks it in Node and in a page bundled with Vite, in
Chromium. The "Compiler on WebAssembly" job of `build-and-test.yml` runs it on every change and
uploads the packed package. `release.yml` runs it for every `v*` tag, at the tag's version, and
publishes the package it checked with the rest of the release, once every part of it is verified.

## What is next

- **Shrink the module further.** Most of what is left is LLVM's code. The optimization pipelines
  cannot be dropped by building only the `-O0` one, since lld's LTO, which the compiler never
  uses, reaches all of them; that would take an lld built without LTO, or LTO of LLVM itself.
- **Printing.** Programs can only report an exit status so far, because the standard library has no
  output yet. `run` already captures standard output for when it does.
- **Upstream the WASI host patch** that llvm-build carries, so that LLVM builds for WASI as is.
