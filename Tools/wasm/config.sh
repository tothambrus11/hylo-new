# Shared settings for building the Hylo compiler for WebAssembly. Sourced by every script in this
# directory; any value can be overridden from the environment.

# The LLVM release the compiler is built against. Must match the major version Swifty-LLVM
# requires, and should match what `.github/workflows/build-and-test.yml` uses natively.
: "${LLVM_TAG:=llvmorg-23.1.0}"

# The Swift toolchain and its Swift SDK for WebAssembly. LLVM is compiled with this toolchain's
# own clang against this SDK's sysroot, so that the C++ standard library LLVM is built against is
# the one the Swift SDK links. The URL and checksum are published at
# https://www.swift.org/install/linux/.
: "${SWIFT_VERSION:=6.3.2}"
: "${SWIFT_SDK:=swift-${SWIFT_VERSION}-RELEASE_wasm}"
: "${SWIFT_SDK_URL:=https://download.swift.org/swift-${SWIFT_VERSION}-release/wasm-sdk/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE_wasm.artifactbundle.tar.gz}"
: "${SWIFT_SDK_CHECKSUM:=a61f0584c93283589f8b2f42db05c1f9a182b506c2957271402992655591dd7c}"
: "${WASI_TRIPLE:=wasm32-unknown-wasip1}"

# binaryen, whose `wasm-opt` shrinks the release build of the compiler. Optional locally.
: "${BINARYEN_VERSION:=version_132}"
: "${BINARYEN_URL:=https://github.com/WebAssembly/binaryen/releases/download/${BINARYEN_VERSION}/binaryen-${BINARYEN_VERSION}-x86_64-linux.tar.gz}"
: "${BINARYEN_CHECKSUM:=195ddc94f9bc89f45abdabb0b9eea86023d727ba90eac8b35b80f2544fc30572}"

# Everything heavy lives here, outside the repository, so that `git clean -xfd` never throws away
# an LLVM build.
: "${HYLO_WASM_CACHE:=${XDG_CACHE_HOME:-$HOME/.cache}/hylo-wasm}"
: "${LLVM_SRC:=$HYLO_WASM_CACHE/llvm-project}"
: "${LLVM_NATIVE_BUILD:=$HYLO_WASM_CACHE/build-native}"
: "${LLVM_WASM_BUILD:=$HYLO_WASM_CACHE/build-wasm}"
# The installed wasm LLVM: headers, static libraries and a `llvm.pc` for Swifty-LLVM.
: "${LLVM_WASM_PREFIX:=$HYLO_WASM_CACHE/llvm-wasm}"

# The configuration of the wasm LLVM. Changing it invalidates the cached build.
#
# Only the WebAssembly back end is built: the compiler running in the browser emits code for the
# browser. lld is built for its WebAssembly port, which links in-process.
#
# Threads are off because the Swift SDK's wasi-libc and libc++ are single-threaded. Assertions are
# off because they cost size and time and the native CI already runs LLVM with them.
: "${LLVM_WASM_CMAKE_OPTIONS:=
  -DCMAKE_BUILD_TYPE=MinSizeRel
  -DLLVM_TARGETS_TO_BUILD=WebAssembly
  -DLLVM_ENABLE_PROJECTS=lld
  -DLLVM_ENABLE_ASSERTIONS=OFF
  -DLLVM_ENABLE_THREADS=OFF
  -DLLVM_ENABLE_PIC=OFF
  -DLLVM_BUILD_STATIC=ON
  -DLLVM_ENABLE_UNWIND_TABLES=OFF
  -DLLVM_ENABLE_ZLIB=OFF
  -DLLVM_ENABLE_ZSTD=OFF
  -DLLVM_ENABLE_LIBXML2=OFF
  -DLLVM_ENABLE_LIBEDIT=OFF
  -DLLVM_ENABLE_LIBPFM=OFF
  -DLLVM_ENABLE_TERMINFO=OFF
  -DLLVM_ENABLE_PLUGINS=OFF
  -DLLVM_ENABLE_BINDINGS=OFF
  -DLLVM_ENABLE_CRASH_OVERRIDES=OFF
  -DLLVM_INCLUDE_TESTS=OFF
  -DLLVM_INCLUDE_EXAMPLES=OFF
  -DLLVM_INCLUDE_BENCHMARKS=OFF
  -DLLVM_INCLUDE_UTILS=OFF
  -DLLVM_INCLUDE_DOCS=OFF
  -DLLVM_BUILD_TOOLS=OFF
  -DLLVM_BUILD_UTILS=OFF
  -DLLD_BUILD_TOOLS=OFF
}"

# The libraries the compiler links: what Swifty-LLVM's C API surface and shims reach, plus lld's
# WebAssembly port. Building these targets rather than `all` keeps tools out of the build.
: "${LLVM_WASM_TARGETS:=
  LLVMCore LLVMSupport LLVMAnalysis LLVMBitWriter LLVMPasses LLVMTarget LLVMTargetParser
  LLVMWebAssemblyCodeGen LLVMWebAssemblyAsmParser LLVMWebAssemblyDisassembler
  LLVMWebAssemblyDesc LLVMWebAssemblyInfo LLVMWebAssemblyUtils
  lldWasm lldCommon
}"

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
