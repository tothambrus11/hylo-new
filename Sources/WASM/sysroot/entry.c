// The entry point of a Hylo program on WASI.
//
// wasi-libc's `_start` calls `__main_argc_argv`, the name clang gives a C `main` taking `argc` and
// `argv`. Other front ends define `main` itself, which the WebAssembly back end gives the type of
// `int main(int, char **)` by wrapping a `main` declared as taking no argument. Without this
// forwarding, `_start` would call an undefined weak symbol and trap.

/// The `main` that the Hylo compiler defines, as the WebAssembly back end rewrites it.
int hylo_main(int argc, char **argv) __asm__("main");

int __main_argc_argv(int argc, char **argv) {
  return hylo_main(argc, argv);
}
