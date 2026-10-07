#!/usr/bin/env bash
# Builds the Hylo Playground, a static site running the compiler in the browser, around a
# packaged release of the compiler (what `js/package-release.mjs` produces).
#
#   build-site.sh <release> <out>
#
# Serve <out> over HTTP; browsers refuse module workers from file:// URLs.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE="$(cd "${1:?usage: build-site.sh <release> <out>}" && pwd)"
OUT="${2:?usage: build-site.sh <release> <out>}"

cd "$HERE/repl"
npm install --no-audit --no-fund
rm -rf public/compiler
mkdir -p public/compiler
cp "$RELEASE"/* public/compiler/
npx vite build --outDir "$OUT" --emptyOutDir
