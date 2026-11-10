# `givencheck`: givens skipped while their type is computed are checked afterwards

**Status:** semantic fix, part of the final configuration. It fixes a baseline unsoundness found by review2.

## How it works

`givens(visibleFrom:)` silently drops every given whose declaration is on the stack. That is right while the given's own type is being computed, because it cannot be used yet. But the results computed meanwhile are memoized: alias types, extendees, the given's own type. Nothing re-checks the skipped given afterwards. Review2 found three consequences:
- **`gz1.hylo`**: `given Z.O is P` where `type Z = T.Y` needs `P<T>`. It is accepted with no consistent reading, while its reordering `gz3` is rejected.
- **`ge1.hylo`**: the same through an extension's extendee. It is accepted, while `ge2` is rejected.
- **`gx1.hylo`**: the same through an extension-applicability check.

With `givencheck`:
1. While declarations are on the stack, `summon` records the user givens it skips because their type is being computed, with the queried type and the scope.
2. Two kinds of declaration are deliberately hidden, and their skips are not recorded:
   - where-clause usings being introduced by `initializeContext` (scoping rule);
   - a conformance resolving its own refined requirements (`anonymousImplementation`).
3. Each record keeps the environment of the skipped resolution, with its assumed givens.
4. Once a recorded given's type is known (checked at the next `summon`, and at the end of the module), it is tested with `mayMatch`, in the recorded environment: unification of the heads up to coercions that `canDeriveCoercions` allows. An empty environment could miss a coercion that the skipped resolution's assumptions allow, and with it a circularity. If it may match the query it was skipped for, "circular given: the type of this given depends on an implicit resolution of 'Q' that it may satisfy" is reported.

## Why it is sound

- The verdict uses only final memoized types, so it is order-independent.
- If the given cannot match the query, skipping it was exact: `gvalid.hylo` is still accepted.
- If it may match, the resolution's result depends on the given's type, which depends on that result. No order reads the program consistently, and it is rejected in every order: `gz1`, `gx1` and `gx1_swap` now report the cycle.
- The corpus oracle is identical. The stdlib's `given Void is Copyable` showed that the conformance self-hiding must not be recorded.

## What it speeds up

Nothing; it is a semantic fix.

## Costs

While a declared type is being computed, every `summon` scans the givens of the lexical scopes and of the other files of the module. That happens only during declared-type computations, and it is not measurable on the corpus.
