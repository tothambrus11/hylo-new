# Constant-factor speed-ups (`typevec`, `reifymemo`, `unify`, `symindex`)

**Kind:** speed-ups; results are unchanged.

These four techniques do not change the algorithm; they remove overhead.

## Contiguous type storage (`typevec`)

**How.** Every type lives in a hash-consed set, and reading a type by its identifier is the most frequent operation of the checker. The set's implementation is generic code that the compiler cannot specialize, so profiles showed 12–37% of the time in its subscript. Types are now also appended to a plain array, and reads go through that array. Insertion still goes through the set, so hash-consing is unchanged.

**Correct because:** types are never removed, and each new type is appended at the next position. Element `i` of the array is therefore the same type as element `i` of the set.

**Effect:** 1.1–1.4× on every program, −20% on the standard library.

**Cost:** 8 bytes per type, and one copy of the array after the constraint solver forks.

## Substitute shared terms once (`reifymemo`)

**How.** Substituting the solved unification variables into a type walks it recursively. Solutions often share structure: `?a1 := P<?a2, ?a2>`, `?a2 := P<?a3, ?a3>`, … Walked as a tree, this is exponential. Each call now remembers the result for every subterm.

**Correct because:** within one call, the substitution is fixed, so the result depends only on the subterm.

**Effect:** 2.3 s → 2.3 ms on such a program, and 8.8 s → 3.7 ms with two more levels of sharing.

**Cost:** one dictionary per call.

## Tag-first unification (`unify`)

**How.** Unification used to match the pair of types against about 20 pattern cases, building a tuple of existential values and trying casts. It now compares the two kinds of type first, returns early on a mismatch, and casts each side once.

**Correct because:** the set of kinds of type is closed, so a cast succeeds exactly when the kinds are equal, and the same per-kind code runs.

**Effect:** about 1.1×.

**Cost:** none.

## One-pass symbol table (`symindex`)

**How.** The compiler finds about 24 standard-library types it needs by name (`Bool`, `Int`, `Movable`, …). It now does so in one scan of the standard library instead of one scan per type.

**Correct because:** the predicate and the order are the same, so each lookup finds the same declarations.

**Effect:** −12% on standard-library typing, on every compilation.

**Cost:** one small table during start-up.
