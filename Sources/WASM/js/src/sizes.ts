/**
 * The total size of the compiler's files, which `loadParts` reports its progress against.
 *
 * `npm run build` records the files' sizes in the bundle as it copies the files next to it (see
 * `tsdown.config.ts`), since a response cannot say them: a server that compresses a file sends the
 * compressed size, if any, while the body is read decompressed, and a file a bundler inlined as a
 * `data:` URL has no size at all. They are recorded by position in `allFiles`, since a bundler
 * renames the files it copies.
 *
 * @module
 */

/** The size in bytes of each file of `allFiles`; set by `tsdown.config.ts`, absent from sources. */
declare const __HYLO_WASM_FILE_SIZES__: readonly number[] | undefined;

/**
 * Returns the total size in bytes of `allFiles`, or `undefined` if it is not recorded, as when
 * the sources are used rather than the built package.
 */
export function totalSize(): number | undefined {
  if (typeof __HYLO_WASM_FILE_SIZES__ === "undefined") return undefined;
  return __HYLO_WASM_FILE_SIZES__.reduce((a, n) => a + n, 0);
}
