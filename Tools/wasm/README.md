# The Hylo compiler on WebAssembly

The whole compiler, built as one WebAssembly module that runs in a browser: the front end,
the lowering to LLVM IR, LLVM's WebAssembly back end, and lld's WebAssembly linker. It turns a
Hylo program into a WebAssembly executable, which the page then runs. That is the basis for an
online REPL.

```js
import { load } from "./index.mjs"; // from a release

const hylo = await load({ baseUrl: "./" });       // ~2.5 s: compiles the standard library
const r = hylo.compile({
  source: "public fun main() -> Int32 { 42 }",
  emit: ["executable", "ir", "llvm", "assembly"], // any subset
});
r.diagnostics;                                    // [] or errors, with sites and rendered text
r.artifacts.llvm;                                 // LLVM IR, as text
const { exitCode, stdout, trap } = await hylo.run(r.executable);
```

## What it costs

Measured on a release build (`-Osize`, then `wasm-opt -Os`), in Node 22 and headless Chromium:

| | |
|---|---:|
| compiler module | 69 MB (27.5 MB gzipped) |
| everything else (standard library sources, C runtime) | 0.5 MB gzipped |
| compiling the standard library, once at load | ~2.5 s |
| compiling **and linking** a small program | 150–320 ms |
| the resulting executable | ~10 KB |

Every one of the compiler's 183 single-file test cases (`Tests/CompilerTests`) passes through it:
positive cases compile, link and run with the exit status or trap they expect, and negative cases
report the same diagnostics as the native compiler, site for site.

## How it is put together

```
 page ──JSON──▶ hylo-wasm.wasm (a WASI reactor)
                 ├─ FrontEnd       parse, scope, type, lower to Hylo IR
                 ├─ BackEnd        Hylo IR → LLVM IR       ┐
                 ├─ Swifty-LLVM    LLVM's C API + shims    ├ LLVM 23, built for wasm32-wasip1
                 └─ WasmLinker     lld::wasm, in-process   ┘
                       │ reads /sysroot/lib/{crt1-command.o, entry.o, libc.a, shims.o, builtins}
                       ▼ writes /tmp/main.wasm
 page ◀──bytes── a WASI command, run with an in-memory WASI shim
```

- **`Sources/hylo-wasm`** is the reactor. The host instantiates it once, hands over the
  standard library's sources through `hylo_init`, and calls `hylo_compile` as often as it likes.
  Strings cross as length-prefixed UTF-8 in linear memory; the protocol is the one
  [hylo-abi-wasm](https://github.com/tothambrus11/hylo-abi-wasm) uses.
- **`Sources/HyloWasmSession`** is what compiling means, independently of the transport:
  each request is compiled in a copy of a program whose standard library is already lowered.
- **`Sources/WasmLinker`** calls `lld::lldMain` with the WebAssembly driver. The files it reads
  and writes live in a WASI file system that the host keeps in memory
  ([`@bjorn3/browser_wasi_shim`](https://github.com/bjorn3/browser_wasi_shim)), the same in a
  browser and in Node.
- **`js/index.mjs`** loads a release, drives the reactor, and runs what it produces. A release
  ships it bundled with its one dependency, so a page can import it directly.

This is a package of its own so that the compiler's package, and every CI job building it, is
unaffected.

## The decisions that are not obvious

**LLVM is compiled by the Swift toolchain's own clang, against the Swift SDK's sysroot.** The
compiler is one binary, so LLVM's C++ and the Swift runtime must agree on the C++ standard library.
The Swift SDK for WebAssembly ships wasi-libc and libc++ (ABI version 2); building LLVM with the
toolchain's clang against exactly those (`wasi-toolchain.cmake`) rules out a mismatch, and needs
no wasi-sdk.

**LLVM needs a patch to build for a WASI host** (`patches/llvm-wasi-host.patch`). It is
[YoWASP](https://github.com/YoWASP/llvm-project)'s, written for LLVM 22, ported to 23.1.0 (four
hunks moved, and LLVM 23 added a `posix_madvise` call and a parameter to `AddSignalHandler`
that the original does not know about). It stubs out signals, process spawning, file locking and
the like, none of which the compiler reaches.

**The Swift SDK's libc++ is built without threads, and LLVM does not compile without them.** LLVM
uses `std::mutex`, `std::shared_future` and the like even when configured with
`LLVM_ENABLE_THREADS=OFF`. wasi-libc does provide single-threaded pthread stubs, so `build-llvm.sh`
compiles LLVM against a `__config_site` that enables threads over pthreads, and builds the parts of
libc++ this configuration needs out of line (`mutex.cpp`, `future.cpp`, ...; 121 symbols, none
defined by the SDK's libc++) from the same libc++ release into `libc++threads.a`. No type the SDK
defines changes layout.

**A Hylo `main` needs a forwarder on WASI** (`entry.c`). wasi-libc's `_start` calls
`__main_argc_argv`, the name clang gives a C `main(argc, argv)`. LLVM IR from any other front end
defines plain `main`, so without the forwarder `_start` calls an undefined weak symbol and traps.

**The compiler now runs on a 32-bit host**, which no other configuration exercises. That found two
bugs in `BackEnd`, fixed here: a 64-bit integer literal that does not fit in `Int`, and integer
constants built from `BigInt.words`, whose words are host-sized, so that `-1 as Int64` became
`4294967295`.

## Building

Requires Swift 6.3.2 with its Swift SDK for WebAssembly, CMake, Ninja, Node, and optionally
binaryen's `wasm-opt`. Everything heavy goes in `~/.cache/hylo-wasm` (`$HYLO_WASM_CACHE`).

```sh
swift sdk install <URL and checksum in config.sh>
Tools/wasm/build-llvm.sh            # once: ~35 min on 4 cores, ~3 GB of disk
Tools/wasm/build-compiler.sh        # ~5 min in release, ~2 min in debug
(cd Tools/wasm/js && npm install)
node Tools/wasm/js/smoke.mjs Tools/wasm/.build/dist
node Tools/wasm/js/conformance.mjs Tools/wasm/.build/dist Tests/CompilerTests
```

`build-llvm.sh` runs in stamped steps (`source`, `native`, `libcxx-threads`, `wasm`, `install`),
so running it again only redoes what changed, and a failed run resumes.

## CI and releases

`.github/workflows/wasm-compiler.yml` builds LLVM when its inputs change (otherwise it is restored
from the cache, and a cold build that runs out of time is banked and resumed by the next run),
builds the compiler, runs the smoke test, the compiler's test cases and a browser check, and
uploads the release as an artifact. A `wasm-v*` tag publishes it as a GitHub release.

A release is content-addressed: every file but `manifest.json` has a hash of its contents in its
name and can be served as immutable. `index.mjs` reads the manifest to find the others.

## What is next

- **Run it in a Web Worker.** Loading blocks for as long as the standard library takes to compile.
- **Put the LLVM build in `hylo-lang/llvm-build`**, which already builds LLVM for the native CI,
  as one more target. This workflow could then download it like the others do.
- **Shrink the module.** Nothing has been done yet: candidates are dropping the LLVM passes that
  `-O0` never runs, LTO, and stripping the names section.
- **Printing.** Programs can only report an exit status so far, because the standard library has no
  output yet. `run` already captures standard output for when it does.
- **Upstream the WASI patch** to LLVM, so that this stops depending on a ported fork.
