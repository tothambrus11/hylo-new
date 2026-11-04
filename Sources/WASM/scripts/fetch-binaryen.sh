#!/usr/bin/env bash
# Downloads binaryen, whose `wasm-opt` `build-compiler.sh` runs on release builds, and unpacks it
# into $BINARYEN_PREFIX. This checks it against the checksum pinned in `config.sh`, and does nothing
# if the same release is already unpacked. The release is binaryen's build for x86_64 Linux.
#
#   fetch-binaryen.sh
#
# Requires: curl, tar, sha256sum.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/config.sh"

stamp="$BINARYEN_PREFIX/.checksum"
if [[ -f "$stamp" && "$(cat "$stamp")" == "$BINARYEN_CHECKSUM" ]]; then
  echo "binaryen $BINARYEN_VERSION is already in $BINARYEN_PREFIX"
  exit 0
fi

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch:?}"' EXIT
download_verified "$BINARYEN_URL" "$BINARYEN_CHECKSUM" "$scratch/binaryen.tar.gz"

# The archive holds one directory named after the release.
tar -xzf "$scratch/binaryen.tar.gz" -C "$scratch"
rm -rf "${BINARYEN_PREFIX:?}"
mkdir -p "$(dirname "$BINARYEN_PREFIX")"
mv "$scratch/binaryen-$BINARYEN_VERSION" "$BINARYEN_PREFIX"
echo "$BINARYEN_CHECKSUM" > "$stamp"
echo "Unpacked binaryen $BINARYEN_VERSION into $BINARYEN_PREFIX"
