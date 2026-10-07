# A CMake toolchain file cross-compiling to wasm32-wasip1 with the Swift toolchain's clang, against
# the sysroot of the Swift SDK for WebAssembly.
#
# Expects `SWIFT_BIN`, `WASI_SYSROOT` and `WASI_RESOURCE_DIR` in the environment; see
# `locate_swift_toolchain` in `config.sh`.

set(CMAKE_SYSTEM_NAME WASI)
set(CMAKE_SYSTEM_VERSION 1)
set(CMAKE_SYSTEM_PROCESSOR wasm32)

set(triple wasm32-unknown-wasip1)
set(CMAKE_C_COMPILER "$ENV{SWIFT_BIN}/clang")
set(CMAKE_CXX_COMPILER "$ENV{SWIFT_BIN}/clang++")
set(CMAKE_C_COMPILER_TARGET ${triple})
set(CMAKE_CXX_COMPILER_TARGET ${triple})
set(CMAKE_AR "$ENV{SWIFT_BIN}/llvm-ar")
set(CMAKE_RANLIB "$ENV{SWIFT_BIN}/llvm-ranlib")
set(CMAKE_SYSROOT "$ENV{WASI_SYSROOT}")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# LLVM reaches mmap in code that the compiler never runs; wasi-libc emulates it behind a macro.
set(flags "-resource-dir=$ENV{WASI_RESOURCE_DIR} -D_WASI_EMULATED_MMAN -fno-exceptions")
set(CMAKE_C_FLAGS_INIT "${flags}")
# LLVM uses `std::mutex` and friends even when built without threads, but the Swift SDK's libc++
# is configured without them. `LIBCXX_THREADS_INCLUDE` holds a `__config_site` enabling them over
# wasi-libc's single-threaded pthread stubs; see `build-llvm.sh`.
set(CMAKE_CXX_FLAGS_INIT "${flags} -isystem $ENV{LIBCXX_THREADS_INCLUDE}")
set(CMAKE_EXE_LINKER_FLAGS_INIT "-resource-dir=$ENV{WASI_RESOURCE_DIR} -lwasi-emulated-mman")
