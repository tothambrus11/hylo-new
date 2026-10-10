#!/usr/bin/env bash
# Downloads the LLVM that the compiler links when it is itself compiled to WebAssembly, and unpacks
# it into $LLVM_WASM_PREFIX. The package is built by hylo-lang/llvm-build; this checks it against
# the checksum pinned in `config.sh`, and does nothing if the same package is already unpacked.
#
#   fetch-llvm.sh
#
# Requires: curl, tar with zstd support, sha256sum.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/config.sh"

stamp="$LLVM_WASM_PREFIX/.checksum"
if [[ -f "$stamp" && "$(cat "$stamp")" == "$LLVM_WASM_CHECKSUM" ]]; then
  echo "$LLVM_WASM_PACKAGE is already in $LLVM_WASM_PREFIX"
  exit 0
fi

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch:?}"' EXIT
download_verified "$LLVM_WASM_URL" "$LLVM_WASM_CHECKSUM" "$scratch/llvm.tar.zst"

# The archive holds one directory named after the package.
tar --zstd -xf "$scratch/llvm.tar.zst" -C "$scratch"
[[ -f "$scratch/$LLVM_WASM_PACKAGE/pkgconfig/llvm.pc" ]] || {
  echo "the archive has no $LLVM_WASM_PACKAGE/pkgconfig/llvm.pc" >&2
  exit 1
}
rm -rf "${LLVM_WASM_PREFIX:?}"
mkdir -p "$(dirname "$LLVM_WASM_PREFIX")"
mv "$scratch/$LLVM_WASM_PACKAGE" "$LLVM_WASM_PREFIX"
echo "$LLVM_WASM_CHECKSUM" > "$stamp"
echo "Unpacked $LLVM_WASM_PACKAGE into $LLVM_WASM_PREFIX"
