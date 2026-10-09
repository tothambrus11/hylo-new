# Shared settings for building the Hylo compiler for WebAssembly. Sourced by every script in this
# directory; any value can be overridden from the environment.

# The Swift toolchain and its Swift SDK for WebAssembly. The URL and checksum are published at
# https://www.swift.org/install/linux/.
: "${SWIFT_VERSION:=6.3.2}"
: "${SWIFT_SDK:=swift-${SWIFT_VERSION}-RELEASE_wasm}"
: "${SWIFT_SDK_URL:=https://download.swift.org/swift-${SWIFT_VERSION}-release/wasm-sdk/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE_wasm.artifactbundle.tar.gz}"
: "${SWIFT_SDK_CHECKSUM:=a61f0584c93283589f8b2f42db05c1f9a182b506c2957271402992655591dd7c}"
: "${WASI_TRIPLE:=wasm32-unknown-wasip1}"

# The LLVM the compiler links, built to run in WebAssembly by hylo-lang/llvm-build (see its
# docs/wasm.md) and published as a release asset. The version must match the major version
# Swifty-LLVM requires, and should match what `.github/workflows/build-and-test.yml` uses natively.
# The package is compiled against the Swift SDK's libc++, so it is specific to `SWIFT_VERSION`.
: "${LLVM_VERSION:=23.1.0}"
: "${LLVM_BUILD_RELEASE:=llvm-23.1.0-1}"
: "${LLVM_WASM_PACKAGE:=llvm-${LLVM_VERSION}-wasm32-unknown-wasip1-swift${SWIFT_VERSION}-MinSizeRel}"
: "${LLVM_WASM_URL:=https://github.com/hylo-lang/llvm-build/releases/download/${LLVM_BUILD_RELEASE}/${LLVM_WASM_PACKAGE}.tar.zst}"
# The SHA-256 of that archive, which `fetch-llvm.sh` checks.
: "${LLVM_WASM_CHECKSUM:=b4e015b6bed6f8fbdfd27260c50a1ec0898a8a38129c246b76368dd71993a1fc}"

# binaryen, whose `wasm-opt` shrinks the release build of the compiler. Optional locally.
: "${BINARYEN_VERSION:=version_132}"
: "${BINARYEN_URL:=https://github.com/WebAssembly/binaryen/releases/download/${BINARYEN_VERSION}/binaryen-${BINARYEN_VERSION}-x86_64-linux.tar.gz}"
: "${BINARYEN_CHECKSUM:=195ddc94f9bc89f45abdabb0b9eea86023d727ba90eac8b35b80f2544fc30572}"

# Downloads live here, outside the repository.
: "${HYLO_WASM_CACHE:=${XDG_CACHE_HOME:-$HOME/.cache}/hylo-wasm}"
# The unpacked LLVM package: headers, static libraries, the libc++ overlay and `pkgconfig/llvm.pc`.
: "${LLVM_WASM_PREFIX:=$HYLO_WASM_CACHE/$LLVM_WASM_PACKAGE}"

# Locates the Swift toolchain and the Swift SDK for WebAssembly, setting `SWIFT_BIN`,
# `WASI_SYSROOT` and `WASI_RESOURCE_DIR`.
locate_swift_toolchain() {
  local swift
  swift="$(command -v swift)" || { echo "swift is not in PATH" >&2; return 1; }
  SWIFT_BIN="$(dirname "$(readlink -f "$swift")")"
  local configuration
  configuration="$(swift sdk configure --show-configuration "$SWIFT_SDK" "$WASI_TRIPLE")" || {
    echo "the Swift SDK '$SWIFT_SDK' is not installed; run: swift sdk install $SWIFT_SDK_URL" >&2
    return 1
  }
  WASI_SYSROOT="$(sed -n 's/^sdkRootPath: //p' <<<"$configuration")"
  # The SDK's static resource directory is a complete clang resource directory, including the
  # compiler-rt builtins for wasm32 that the toolchain's own clang does not carry.
  WASI_RESOURCE_DIR="$(sed -n 's/^swiftStaticResourcesPath: //p' <<<"$configuration")/clang"
}
