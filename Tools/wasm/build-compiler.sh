#!/usr/bin/env bash
# Builds the Hylo compiler for WebAssembly against the LLVM that `fetch-llvm.sh` unpacked, and
# assembles everything a host needs to run it in `$OUT` (default: `Tools/wasm/.build/dist`):
#
#   hylo-wasm.wasm      the compiler, as a WASI reactor
#   stdlib.json         the standard library's sources, keyed by file name
#   sysroot/lib/*       the files linked into every executable
#
#   build-compiler.sh [debug|release]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/config.sh"
CONFIGURATION="${1:-release}"
OUT="${OUT:-$HERE/.build/dist}"

[[ -f "$LLVM_WASM_PREFIX/pkgconfig/llvm.pc" ]] || {
  echo "no wasm LLVM in $LLVM_WASM_PREFIX; run fetch-llvm.sh first" >&2
  exit 1
}
locate_swift_toolchain
export LLVM_WASM_PREFIX
export PKG_CONFIG_PATH="$LLVM_WASM_PREFIX/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"

# The SDK's libc++abi has no exception support, and LLVM is built without exceptions.
flags=(-c "$CONFIGURATION" --swift-sdk "$SWIFT_SDK" --package-path "$HERE" -Xcxx -fno-exceptions)
if [[ "$CONFIGURATION" == release ]]; then
  flags+=(-Xswiftc -Osize -Xswiftc -gnone)
fi
swift build "${flags[@]}" --product hylo-wasm
BIN="$(swift build "${flags[@]}" --show-bin-path)"

rm -rf "$OUT"
mkdir -p "$OUT/sysroot/lib"

# `wasm-opt` is optional: it roughly halves the time to compile the standard library and shrinks
# the module by a quarter, but the module works without it.
if [[ "$CONFIGURATION" == release ]] && command -v wasm-opt >/dev/null; then
  wasm-opt -Os --strip-debug --strip-dwarf --enable-bulk-memory --enable-sign-ext \
    --enable-mutable-globals --enable-nontrapping-float-to-int \
    -o "$OUT/hylo-wasm.wasm" "$BIN/hylo-wasm.wasm"
else
  cp "$BIN/hylo-wasm.wasm" "$OUT/hylo-wasm.wasm"
fi

# The standard library, keyed by path relative to its resource bundle.
bundle="$(find "$BIN" -maxdepth 1 -name '*_StandardLibrary.resources' | head -1)"
[[ -d "$bundle" ]] || { echo "no standard library bundle in $BIN" >&2; exit 1; }
node "$HERE/js/collect-stdlib.mjs" "$bundle" > "$OUT/stdlib.json"

# What every executable links: the C runtime's entry point and the shim calling a Hylo `main`
# from it, the C library, compiler-rt's builtins, and the standard library's C shim.
cp "$WASI_SYSROOT/lib/wasm32-wasip1/crt1-command.o" "$WASI_SYSROOT/lib/wasm32-wasip1/libc.a" \
  "$OUT/sysroot/lib/"
cp "$WASI_RESOURCE_DIR/lib/wasip1/libclang_rt.builtins-wasm32.a" "$OUT/sysroot/lib/"
"$SWIFT_BIN/clang" --target="$WASI_TRIPLE" --sysroot="$WASI_SYSROOT" \
  -resource-dir="$WASI_RESOURCE_DIR" -Os -c "$bundle/Sources/shims.c" -o "$OUT/sysroot/lib/shims.o"
"$SWIFT_BIN/clang" --target="$WASI_TRIPLE" --sysroot="$WASI_SYSROOT" \
  -resource-dir="$WASI_RESOURCE_DIR" -Os -c "$HERE/entry.c" -o "$OUT/sysroot/lib/entry.o"

ls -l "$OUT" "$OUT/sysroot/lib"
