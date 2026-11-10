# Index givens by their head (`index`)

**Kind:** speed-up; results are unchanged.

## Problem

To prove a goal such as `P<A>`, implicit resolution tries every given visible from the current scope: conformance declarations, where-clause requirements and the built-in equality rules. In a scope with many conformances, almost all of these attempts fail at once, but each still costs a unification, at every step of the search.

## How it works

For each scope, the visible givens are grouped by the outermost type constructor of what they prove:
- `A is P`, that is `P<A>`, goes in bucket `P`;
- `S<T>` goes in bucket `S`;
- givens whose conclusion has no fixed head (for example `<T> T`) go in a separate "wildcard" list.

A goal headed by `P` tries only bucket `P` and the wildcards. They are merged back into their original order, and each entry keeps the penalty of its original group, so the search sees the same candidates in the same order, minus the ones that cannot match.

## Why it is correct

A given whose conclusion has a different head constructor fails at its first match:
- if the roots differ, unification reports the root pair as a mismatch, and the match rejects it;
- if a nested part differs, the match could only succeed by assuming an equality, and that needs an equality given that can produce it.

A failed thread has no result and no children, so removing it changes neither the result, nor its penalty, nor the search layer in which it is found.

The index is not used where a coercion could make two different heads match:
- when an equality given, or a given that can prove anything, is visible;
- when an equality is assumed in the current proof;
- while the declaration being typed is itself hidden from lookups.

## What it speeds up

Resolution with many unrelated givens in scope, which is the common case.

| Program | Without | With `index` alone |
|---|---:|---:|
| standard library | 1.0 s | 0.45 s (2.2×) |
| 40 unrelated conformances in scope | 7.4 s | 91 ms (81×) |
| 20 looping goals | 191 ms | 18 ms (10.5×) |

It does not help in generic code with equality requirements, which disable it, nor with equality reasoning; `eqsolve` and `absquotient` cover those.

## Cost

One table per scope, built in time linear in the number of visible givens the first time that scope resolves something.
