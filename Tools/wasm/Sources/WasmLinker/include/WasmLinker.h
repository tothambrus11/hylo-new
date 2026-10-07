#ifndef HYLO_WASM_LINKER_H
#define HYLO_WASM_LINKER_H

#ifdef __cplusplus
extern "C" {
#endif

/// Runs lld's WebAssembly port in-process with the `argc` command-line arguments in `argv`, the
/// first of which names the program, and returns its exit status.
///
/// Sets `*diagnostics` to what the linker reported, as a null-terminated string that the caller
/// must release with `free`.
int hylo_wasm_link(int argc, const char *const *argv, char **diagnostics);

#ifdef __cplusplus
}
#endif

#endif
