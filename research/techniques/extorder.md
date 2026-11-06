# `extorder`: order-independent member lookup through extensions

**Status:** semantic fix, part of the final configuration. It replaces `cyclecut`, which is unsound.

## How it works

Member lookup of `n` in `q` visits the visible extensions.

1. An extension that declares no member named `n` contributes no candidate. It is skipped *without* evaluating its applicability, so evaluating its extendee is never triggered by an unrelated lookup.
2. Extendee computations are tracked as a stack of *frames*. Each frame records the member lookups `(q, scope, n)` made while it is innermost.
3. A lookup can reach an extension `e` that declares `n` while `e`'s extendee is being computed (`e` is on the stack). That closes a cycle of extendee computations. `e` is skipped, as the baseline does, and `e` and every frame entered after it join one *cycle group*; overlapping groups are merged.
4. When the last frame of a group leaves the stack, every member's extendee is known. The group is then checked: for every lookup `(q, n)` recorded by any member, and every member `m` that declares `n`, it asks whether `m` *may* apply to `q`:
   - the extendee's head, with its parameters opened, unifies with `q`'s head;
   - the coercions this unification needs are not ruled out by `canDeriveCoercions`.

   If `m` may apply, the extendees in the group depend on a lookup that a member affects, and "circular extension: the extendee of this extension depends on a lookup of 'n', which this extension may affect" is reported at `m`.

## Why it is sound and order-independent

- **Exact skips are kept.** If no member of a group may apply to a type its members looked up, then every skip in the group was exact, and the lookups' results are those of any evaluation order. This is the case for a single extension looking up a name in its own parameter or in an unrelated type, which review2 showed the first, eager version rejected: `x01`, `x03`, `x06`, `x09`, `x10b`, `r1_*`, `r2_where_assoc`, `al2`. All are accepted now.
- **The verdict does not depend on order.** It depends on the set of members of the group, on all the lookups they make, and on the final extendees. Whichever member is entered first, the same dependency cycle is traversed, so the same lookups are recorded.
  - An intermediate version (eq6) checked only the lookup that hit the cycle. It accepted or rejected `final/n04-order-{a,b}.hylo` depending on where an unrelated function was declared.
  - With groups, `n04-order-a`, `n04-order-b`, `v4_noC`, `v4-swapped` and `v4-use-first` are rejected in every order.
- **Circular programs are rejected**: `pc1_selfapply_nouse`, `amb3`, `r2_bare`, `ge2`.
- **Oracle.** The corpus oracle is identical (`../round3/soundness/oracle-final-config.txt`).

## Limitation

A mutual cycle can have a unique consistent reading that the rule still rejects. In `v4_noC.hylo`:
- `extension A.Inner.Foo` needs `Foo` in `A.Inner`, which `extension A.Inner` provides;
- the second extension's extendee needs `Inner` in `A`, which the first one would provide if it extended `A`.

The baseline accepts it. Accepting it in every order would need a fixpoint with rollback and recomputation of the memoized results, which is what made `cyclecut` unsound and expensive. Rejecting is the conservative order-independent answer.

## What it speeds up

It is a semantic fix, not a speed-up. Skipping extensions that do not declare `n` avoids applicability checks; that work is also what `memberskip` saves.

## Costs

- One recorded lookup per member lookup made inside an extendee computation.
- One `mayMatch` test per (lookup, declaring member) pair of a cycle group. Groups are rare and small.
