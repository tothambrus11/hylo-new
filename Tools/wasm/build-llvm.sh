#!/usr/bin/env bash
# Builds the LLVM libraries the Hylo compiler links when it is itself compiled to WebAssembly.
#
#   1. source          LLVM at $LLVM_TAG, patched to build for a WASI host
#   2. native          llvm-tblgen for the build machine, which the cross build runs
#   3. libcxx-threads  the parts of libc++ the Swift SDK leaves out (see below)
#   4. wasm            LLVM and lld's WebAssembly port, cross-compiled to wasm32-wasip1
#   5. install         headers, static libraries and `llvm.pc` in $LLVM_WASM_PREFIX
#
# Every step is stamped with a hash of its inputs and skipped when they have not changed, so
# running this again is cheap and a failed run resumes. CI caches the steps separately and runs
# them one at a time:
#
#   build-llvm.sh source|native|libcxx-threads|wasm|install
#
# With no argument, all steps run. `--stamp-only` marks the steps whose outputs are present as
# current, which is what a CI job does after restoring them from its cache.
#
# Requires: swift (with the SDK named by $SWIFT_SDK installed), cmake, ninja, git, a host C++
# compiler.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/config.sh"

JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN)}"
ONLY="${1:-all}"
want() { [[ "$ONLY" == all || "$ONLY" == "$1" ]]; }
step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

mkdir -p "$HYLO_WASM_CACHE"

# A step is current when the hash of its inputs is what its stamp records.
hash() { printf '%s' "$1" | sha256sum | cut -d' ' -f1; }
stamp() { hash "$1" > "$HYLO_WASM_CACHE/.stamp-$2"; }
current() {
  [[ -f "$HYLO_WASM_CACHE/.stamp-$2" ]] && [[ "$(cat "$HYLO_WASM_CACHE/.stamp-$2")" == "$(hash "$1")" ]]
}

locate_swift_toolchain
export SWIFT_BIN WASI_SYSROOT WASI_RESOURCE_DIR

# The version of the libc++ the Swift SDK ships, whose missing parts step 3 builds.
LIBCXX_VERSION="$(sed -n 's/^#  *define _LIBCPP_VERSION \([0-9]*\)$/\1/p' "$WASI_SYSROOT/include/c++/v1/__config")"
LIBCXX_TAG="llvmorg-$((LIBCXX_VERSION / 10000)).$((LIBCXX_VERSION / 100 % 100)).$((LIBCXX_VERSION % 100))"
LIBCXX_SRC="$HYLO_WASM_CACHE/libcxx-$LIBCXX_TAG"
LIBCXX_THREADS="$HYLO_WASM_CACHE/libcxx-threads"
export LIBCXX_THREADS_INCLUDE="$LIBCXX_THREADS/include"

# What each step's output depends on.
PATCH_HASH="$(sha256sum "$HERE/patches/llvm-wasi-host.patch" | cut -d' ' -f1)"
SOURCE_INPUTS="$LLVM_TAG $PATCH_HASH"
NATIVE_INPUTS="$SOURCE_INPUTS"
THREADS_INPUTS="$SWIFT_SDK $LIBCXX_TAG"
TOOLCHAIN_HASH="$(sha256sum "$HERE/wasi-toolchain.cmake" | cut -d' ' -f1)"
WASM_INPUTS="$SOURCE_INPUTS $THREADS_INPUTS $TOOLCHAIN_HASH $LLVM_WASM_CMAKE_OPTIONS $LLVM_WASM_TARGETS"
INSTALL_INPUTS="$WASM_INPUTS"

if [[ "$ONLY" == --stamp-only ]]; then
  [[ -d "$LLVM_SRC/llvm" ]] && stamp "$SOURCE_INPUTS" source
  [[ -x "$LLVM_NATIVE_BUILD/bin/llvm-tblgen" ]] && stamp "$NATIVE_INPUTS" native
  [[ -f "$LIBCXX_THREADS/libc++threads.a" ]] && stamp "$THREADS_INPUTS" libcxx-threads
  [[ -f "$LLVM_WASM_BUILD/lib/libLLVMCore.a" ]] && stamp "$WASM_INPUTS" wasm
  [[ -f "$LLVM_WASM_PREFIX/lib/pkgconfig/llvm.pc" ]] && stamp "$INSTALL_INPUTS" install
  step "Stamped the steps whose outputs are present"
  exit 0
fi

# ------------------------------------------------------------------------------------ source --
if ! want source; then :
elif current "$SOURCE_INPUTS" source; then step "LLVM source ($LLVM_TAG) — current"
else
  step "Fetching LLVM source ($LLVM_TAG)"
  rm -rf "$LLVM_SRC"
  # Sparse and blobless: only the projects that are built are checked out. `libc` provides
  # headers that LLVM's build requires since version 22.
  git clone --depth 1 --branch "$LLVM_TAG" --filter=blob:none --sparse \
    https://github.com/llvm/llvm-project.git "$LLVM_SRC"
  git -C "$LLVM_SRC" sparse-checkout set llvm lld cmake third-party libunwind libc
  # LLVM does not support WASI as a host upstream. The patch is YoWASP's
  # (https://github.com/YoWASP/llvm-project), ported to this release.
  git -C "$LLVM_SRC" apply "$HERE/patches/llvm-wasi-host.patch"
  stamp "$SOURCE_INPUTS" source
fi

# ------------------------------------------------------------------------------------ native --
if ! want native; then :
elif current "$NATIVE_INPUTS" native; then step "Native tablegen — current"
else
  step "Building native tablegen"
  cmake -G Ninja -S "$LLVM_SRC/llvm" -B "$LLVM_NATIVE_BUILD" \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_TARGETS_TO_BUILD=WebAssembly \
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF \
    -DLLVM_INCLUDE_UTILS=OFF -DLLVM_BUILD_TOOLS=OFF \
    -DLLVM_ENABLE_ZSTD=OFF -DLLVM_ENABLE_ZLIB=OFF -DLLVM_ENABLE_LIBXML2=OFF
  ninja -C "$LLVM_NATIVE_BUILD" -j "$JOBS" llvm-tblgen llvm-min-tblgen
  stamp "$NATIVE_INPUTS" native
fi

# ---------------------------------------------------------------------------- libcxx-threads --
# LLVM uses `std::mutex`, `std::shared_future` and their kin even when it is configured without
# threads, but the Swift SDK's libc++ is built with `_LIBCPP_HAS_THREADS 0`, which removes them.
# wasi-libc provides single-threaded pthread stubs, so they can be put back: LLVM is compiled
# against the SDK's headers with a `__config_site` enabling threads over pthreads, and the parts
# of libc++ that configuration needs out of line are compiled from the same libc++ release into
# `libc++threads.a`. None of its symbols is defined by the SDK's libc++, and none of the SDK's
# types changes layout.
if ! want libcxx-threads; then :
elif current "$THREADS_INPUTS" libcxx-threads; then step "libc++ thread support — current"
else
  step "Building libc++ thread support ($LIBCXX_TAG)"
  if [[ ! -d "$LIBCXX_SRC/libcxx" ]]; then
    git clone --depth 1 --branch "$LIBCXX_TAG" --filter=blob:none --sparse \
      https://github.com/llvm/llvm-project.git "$LIBCXX_SRC"
    git -C "$LIBCXX_SRC" sparse-checkout set libcxx
  fi
  rm -rf "$LIBCXX_THREADS"
  mkdir -p "$LIBCXX_THREADS/include" "$LIBCXX_THREADS/obj"
  sed -e 's/#define _LIBCPP_HAS_THREADS 0/#define _LIBCPP_HAS_THREADS 1/' \
      -e 's/#define _LIBCPP_HAS_THREAD_API_PTHREAD 0/#define _LIBCPP_HAS_THREAD_API_PTHREAD 1/' \
      "$WASI_SYSROOT/include/c++/v1/__config_site" > "$LIBCXX_THREADS_INCLUDE/__config_site"
  grep -q '#define _LIBCPP_HAS_THREADS 1' "$LIBCXX_THREADS_INCLUDE/__config_site"
  for f in mutex mutex_destructor condition_variable condition_variable_destructor future \
           shared_mutex thread atomic barrier; do
    "$SWIFT_BIN/clang++" --target="$WASI_TRIPLE" --sysroot="$WASI_SYSROOT" \
      -resource-dir="$WASI_RESOURCE_DIR" -isystem "$LIBCXX_THREADS_INCLUDE" \
      -std=c++23 -Os -fno-exceptions -DNDEBUG -D_LIBCPP_BUILDING_LIBRARY \
      -I"$LIBCXX_SRC/libcxx/src" \
      -c "$LIBCXX_SRC/libcxx/src/$f.cpp" -o "$LIBCXX_THREADS/obj/$f.o"
  done
  "$SWIFT_BIN/llvm-ar" rcs "$LIBCXX_THREADS/libc++threads.a" "$LIBCXX_THREADS"/obj/*.o
  stamp "$THREADS_INPUTS" libcxx-threads
fi

# -------------------------------------------------------------------------------------- wasm --
if ! want wasm; then :
elif current "$WASM_INPUTS" wasm; then step "wasm LLVM — current"
else
  step "Cross-building LLVM for $WASI_TRIPLE"
  # shellcheck disable=SC2086 # The options are a list of words.
  cmake -G Ninja -S "$LLVM_SRC/llvm" -B "$LLVM_WASM_BUILD" \
    -DCMAKE_TOOLCHAIN_FILE="$HERE/wasi-toolchain.cmake" \
    -DLLVM_NATIVE_TOOL_DIR="$LLVM_NATIVE_BUILD/bin" \
    -DLLVM_HOST_TRIPLE="$WASI_TRIPLE" \
    -DLLVM_DEFAULT_TARGET_TRIPLE="$WASI_TRIPLE" \
    $LLVM_WASM_CMAKE_OPTIONS
  # shellcheck disable=SC2086
  ninja -C "$LLVM_WASM_BUILD" -j "$JOBS" $LLVM_WASM_TARGETS
  stamp "$WASM_INPUTS" wasm
fi

# ----------------------------------------------------------------------------------- install --
if ! want install; then :
elif current "$INSTALL_INPUTS" install; then step "Installed wasm LLVM — current"
else
  step "Installing wasm LLVM into $LLVM_WASM_PREFIX"
  rm -rf "$LLVM_WASM_PREFIX"
  mkdir -p "$LLVM_WASM_PREFIX/include" "$LLVM_WASM_PREFIX/lib/pkgconfig"
  cp -R "$LLVM_SRC/llvm/include/llvm" "$LLVM_SRC/llvm/include/llvm-c" "$LLVM_WASM_PREFIX/include/"
  # Generated headers (configuration, intrinsics, ...) overlay the source tree's.
  cp -R "$LLVM_WASM_BUILD/include/llvm" "$LLVM_WASM_PREFIX/include/"
  cp -R "$LLVM_SRC/lld/include/lld" "$LLVM_WASM_PREFIX/include/"
  find "$LLVM_WASM_PREFIX/include" \( -name '*.td' -o -name 'CMakeLists.txt' -o -name '*.in' \) -delete
  cp "$LLVM_WASM_BUILD"/lib/*.a "$LIBCXX_THREADS/libc++threads.a" "$LLVM_WASM_PREFIX/lib/"
  # The libraries are listed in no particular order, which wasm-ld does not need. Every one that
  # was built is listed; those nothing references contribute nothing to the binary.
  libs="$(cd "$LLVM_WASM_PREFIX/lib" && ls lib*.a | sed -e 's/^lib/-l/' -e 's/\.a$//' | tr '\n' ' ')"
  version="${LLVM_TAG#llvmorg-}"
  cat > "$LLVM_WASM_PREFIX/lib/pkgconfig/llvm.pc" <<EOF
prefix=$LLVM_WASM_PREFIX
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: LLVM
Description: LLVM $version and lld for $WASI_TRIPLE
Version: $version
Cflags: -I\${includedir} -I\${prefix}/libcxx-threads
Libs: -L\${libdir} $libs
EOF
  # Every C++ file including LLVM's headers must see libc++ configured the way LLVM was compiled.
  # SwiftPM accepts nothing but `-I` from pkg-config, which serves: `-I` directories are searched
  # before the SDK's own libc++ directory, for `<...>` includes too.
  mkdir -p "$LLVM_WASM_PREFIX/libcxx-threads"
  cp "$LIBCXX_THREADS_INCLUDE/__config_site" "$LLVM_WASM_PREFIX/libcxx-threads/"
  stamp "$INSTALL_INPUTS" install
fi

step "Done ($ONLY)"
