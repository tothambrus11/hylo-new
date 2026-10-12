/** Returns a description of `thrown`, a thrown value: its stack, if it is an error with one. */
export function describeThrown(thrown: unknown): string {
  return thrown instanceof Error ? (thrown.stack ?? thrown.message) : String(thrown);
}
