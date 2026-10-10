/**
 * The compiler's files, which the package ships next to this module.
 *
 * Each is named by a literal `new URL(..., import.meta.url)`, the form bundlers recognize: they copy
 * the file into their output and rewrite the URL, and without a bundler it resolves as is.
 *
 * @module
 */

/** The compiler, a WASI reactor. */
export const compilerFile = new URL("./hylo-wasm.wasm", import.meta.url);

/** The standard library's sources, as a JSON object keyed by file name. */
export const standardLibraryFile = new URL("./stdlib.json", import.meta.url);

/** The files linked into every executable, by the names the linker knows them by. */
export const sysrootFiles: ReadonlyMap<string, URL> = new Map([
  ["crt1-command.o", new URL("./crt1-command.o", import.meta.url)],
  ["entry.o", new URL("./entry.o", import.meta.url)],
  ["libc.a", new URL("./libc.a", import.meta.url)],
  ["libclang_rt.builtins-wasm32.a", new URL("./libclang_rt.builtins-wasm32.a", import.meta.url)],
  ["shims.o", new URL("./shims.o", import.meta.url)],
]);

/**
 * Every file, in the order the loaders fetch them: the compiler, the standard library, and the
 * files of `sysrootFiles` in its order. `tsdown.config.ts` records their sizes in this order.
 */
export const allFiles: readonly URL[] = [
  compilerFile,
  standardLibraryFile,
  ...sysrootFiles.values(),
];
