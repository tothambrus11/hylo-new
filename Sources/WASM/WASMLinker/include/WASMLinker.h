#ifndef HYLO_WASM_LINKER_H
#define HYLO_WASM_LINKER_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/// Runs lld's WebAssembly port in-process with the `argc` command-line arguments in `argv`, the
/// first of which names the program, and returns its exit status.
///
/// Sets `*diagnostics` to what the linker reported, as a null-terminated string that the caller
/// must release with `free`, and `*canRunAgain` to `false` iff the linker failed in a way that
/// may have left the process in a state where it cannot run again.
int hylo_wasm_link(int argc, const char *const *argv, char **diagnostics, bool *canRunAgain);

#ifdef __cplusplus
}
#endif

#endif
