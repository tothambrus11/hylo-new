#!/usr/bin/env bash
# Builds the Hylo compiler for WebAssembly against the LLVM that `fetch-llvm.sh` unpacked, and
# assembles everything a host needs to run it in `$OUT` (default: `.build/wasm/dist`):
#
#   hylo-wasm.wasm      the compiler, as a WASI reactor
#   stdlib.json         the standard library's sources, keyed by file name
#   sysroot/lib/*       the files linked into every executable
#
#   build-compiler.sh [debug|release]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WASM="$(dirname "$HERE")"
REPOSITORY="$(cd "$WASM/../.." && pwd)"
source "$HERE/config.sh"
CONFIGURATION="${1:-release}"
OUT="${OUT:-$REPOSITORY/.build/wasm/dist}"

[[ -f "$LLVM_WASM_PREFIX/pkgconfig/llvm.pc" ]] || {
  echo "no wasm LLVM in $LLVM_WASM_PREFIX; run fetch-llvm.sh first" >&2
  exit 1
}
locate_swift_toolchain
export LLVM_WASM_PREFIX
export PKG_CONFIG_PATH="$LLVM_WASM_PREFIX/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"

# The SDK's libc++abi has no exception support, and LLVM is built without exceptions.
# `LLVM_WASM_PREFIX` is also what adds the targets to the package; see `Package.swift`.
#
# The toolset links `FoundationEssentials` rather than Foundation, and why is in
# `Sources/WASM/README.md`.
flags=(-c "$CONFIGURATION" --swift-sdk "$SWIFT_SDK" --package-path "$REPOSITORY" -Xcxx -fno-exceptions
  --toolset "$REPOSITORY/foundation-essentials.toolset.json")
if [[ "$CONFIGURATION" == release ]]; then
  flags+=(-Xswiftc -Osize -Xswiftc -gnone)
fi
swift build "${flags[@]}" --product hylo-wasm
# The reactor is handed the standard library's sources by its host, so it does not link the target
# holding them, whose resource accessor needs Foundation. Building that target puts the sources,
# including the generated ones, in the build directory, where they are collected below.
swift build "${flags[@]}" --target StandardLibrary
BIN="$(swift build "${flags[@]}" --show-bin-path)"

rm -rf "$OUT"
mkdir -p "$OUT/sysroot/lib"

# `wasm-opt` is optional: it roughly halves the time to compile the standard library and shrinks
# the module by more than half, mostly by dropping the names section, but the module works without
# it. `-Oz` takes no longer than `-Os` and makes a 2% smaller module, which runs as fast.
PATH="$BINARYEN_PREFIX/bin:$PATH" # where `fetch-binaryen.sh` puts it, if it did
if [[ "$CONFIGURATION" == release ]] && command -v wasm-opt >/dev/null; then
  wasm-opt -Oz --strip-debug --strip-dwarf --enable-bulk-memory --enable-sign-ext \
    --enable-mutable-globals --enable-nontrapping-float-to-int \
    -o "$OUT/hylo-wasm.wasm" "$BIN/hylo-wasm.wasm"
else
  cp "$BIN/hylo-wasm.wasm" "$OUT/hylo-wasm.wasm"
fi

# The standard library, keyed by path relative to its resource bundle.
bundle="$(find "$BIN" -maxdepth 1 -name '*_StandardLibrary.resources' | head -1)"
[[ -d "$bundle" ]] || { echo "no standard library bundle in $BIN" >&2; exit 1; }
node "$WASM/js/scripts/collect-stdlib.ts" "$bundle" > "$OUT/stdlib.json"

# What every executable links: the C runtime's entry point and the shim calling a Hylo `main`
# from it, the C library, compiler-rt's builtins, and the standard library's C shim.
cp "$WASI_SYSROOT/lib/wasm32-wasip1/crt1-command.o" "$WASI_SYSROOT/lib/wasm32-wasip1/libc.a" \
  "$OUT/sysroot/lib/"
cp "$WASI_RESOURCE_DIR/lib/wasip1/libclang_rt.builtins-wasm32.a" "$OUT/sysroot/lib/"
"$SWIFT_BIN/clang" --target="$WASI_TRIPLE" --sysroot="$WASI_SYSROOT" \
  -resource-dir="$WASI_RESOURCE_DIR" -Os -c "$bundle/Sources/shims.c" -o "$OUT/sysroot/lib/shims.o"
"$SWIFT_BIN/clang" --target="$WASI_TRIPLE" --sysroot="$WASI_SYSROOT" \
  -resource-dir="$WASI_RESOURCE_DIR" -Os -c "$WASM/sysroot/entry.c" -o "$OUT/sysroot/lib/entry.o"

ls -l "$OUT" "$OUT/sysroot/lib"
