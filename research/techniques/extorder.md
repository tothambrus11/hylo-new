# `extorder`: order-independent member lookup through extensions

**Status:** semantic fix, part of the final configuration. It replaces `cyclecut`, which is unsound.

## How it works

Member lookup of `n` in `q` visits the visible extensions.

1. An extension that declares no member named `n` contributes no candidate. It is skipped *without* evaluating its applicability, so evaluating its extendee is never triggered by an unrelated lookup.
2. An extension `e` that declares `n` and whose extendee is being computed (it is on the stack) cannot be evaluated. The lookup skips it, as the baseline does, and **records** `(q, scope, n)` for `e`.
3. When `e`'s extendee has been computed and memoized, each recorded lookup is checked. The check asks whether `e` *may* apply to `q`:
   - the extendee's head, with its parameters opened, unifies with `q`'s head;
   - the coercions this unification needs are not ruled out by `canDeriveCoercions`.

   If `e` may apply, the lookup depended on itself, and "circular extension: the extendee of this extension depends on a lookup of 'n', which this extension may affect" is reported at `e`.

## Why it is sound

- The verdict depends only on memoized extendees, so it does not depend on the order in which declarations are checked.
- If `e` cannot apply to `q`, then skipping `e` was exact, and the lookup's result is the one any order computes.
- If it may apply, the program has no reading independent of evaluation order, and rejecting it is the only order-independent answer.
- Review2 found two problems in the first version, which reported eagerly. Both are fixed by the deferred check:
  - It rejected valid programs whose lookup was in a type the extension can never extend: `x01`, `x03`, `x06`, `x09`, `x10b`, `r1_*`, `r2_where_assoc`, `al2`, `v4_noC`. All are accepted now.
  - The genuinely circular programs are still rejected: `pc1_selfapply_nouse`, `amb3`, `r2_bare`, `ge2`.
- The corpus oracle is identical.

## What it speeds up

It is a semantic fix, not a speed-up. Skipping extensions that do not declare `n` avoids applicability checks; that work is also what `memberskip` saves.

## Costs

- One `mayMatch` test per recorded lookup, which is rare: it needs a lookup inside an extendee computation.
- One string-keyed table lookup per extension per member lookup.
