# 5. Results depend on declaration order

**Status:** fixed by `sigrounds`. On 129 programs constructed for this problem, type-checked in 2,876 orders, no program has two verdicts (existing implementation: 52 programs; the earlier fix by after-the-fact checks: 7).

## Symptom

The problem is not limited to circular programs. This one has no cycle, and the existing implementation accepts it in 6 of the 24 orders of its last four declarations:

```hylo
trait P { type E }
struct A {}
struct Box<T> {}
given A is P { type E = Int }
type X = A.E                       // needs `A is P`
given Box<X> is P { type E = A }   // needs `X`
fun k(x: X) {}
```

In the other 18 orders it reports "definition of 'X' refers to itself". A chain of two such steps (`sigrounds/tests/06b-chain-through-alias.hylo`) is rejected in every order.

Programs that do have a cycle are accepted or rejected depending on where evaluation enters the cycle:

```hylo
trait P { type Y }
trait Q { type O }
struct T {}
struct U {}
given T is P { type Y = U }
given U is Q { type O = T }
given Z.O is P { type Y = Int }   // accepted in 6 of 24 orders
type Z = T.Y
fun k(z: Z) {}
```

This program has no consistent reading: if `Z.O` is `T`, then `T` has two conformances to `P`, so `T.Y`, and hence `Z`, is ambiguous; otherwise `Z = T.Y = U` and `Z.O = U.O = T`, a contradiction.

## Cause

Three properties of the existing implementation act together.

1. A name lookup or an implicit resolution computes the type of every candidate it meets, nested inside the computation that asked. Looking up `A.E` computes the types of all conformances in scope, including that of `given Box<X> is P`, which needs `X`, which is the alias being defined.
2. A declaration whose type is being computed is hidden from lookups and resolutions, to avoid infinite recursion. Their answers are computed without it.
3. Everything computed meanwhile is kept, including types computed from an answer that a hidden declaration would have changed, and including errors.

Which declaration is hidden when it matters depends on which is computed first, that is, on the order of declarations.

## Fix

Extensions, conformances and given bindings are the declarations that lookups and resolutions select *by their type*: the extended type, or the type of the given. Call that type the *signature* of the declaration. `sigrounds` computes all signatures of a module before anything else, in rounds:

- A round computes the signature of every such declaration, starting from the untouched typing state.
- During a round, a lookup or resolution never computes a signature. It reads the signatures from the table that the previous round produced; a declaration without an entry (not computed yet, or erroneous) is ignored. In the first round the table is empty.
- Rounds repeat until two consecutive tables are equal. The state of the last round is kept, and the module is then checked as before, with every signature known.
- If a table repeats an earlier one without being stable, or after `n + 2` rounds for `n` declarations, the declarations whose signatures differ are reported: "the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found".

If no lookup or resolution of the first round ignored a declaration, the first round is final and nothing is recomputed. That is the case for the standard library (72 signatures, one round) and for every program of the compiler's test suite.

For the first example above, round 1 computes `A is P` and fails on `Box<X> is P` (the lookup of `A.E` ignores every conformance); round 2 finds `A is P` in the table, so `X = Int` and `Box<Int> is P`; round 3 computes the same table and stops.

Two kinds of hiding are deliberate scoping rules and are unchanged: a where-clause requirement is invisible while the requirements written before it are typed, and a conformance cannot use itself to satisfy the traits it refines.

## Why the result does not depend on the order

The table after round *k* is a function of the program and of the table after round *k − 1*: a round starts from the same state whatever the order, reads other signatures only from the previous table, and computes each signature from its own expression. By induction no table depends on the order of declarations, and neither does the stopping test, the set of reported declarations, or the state handed to the rest of the checker. The argument needs no approximation of which declaration "could have matched", which is where the earlier fix failed.

After the last round nothing is hidden for a wrong reason: every signature is memoized, so the remaining checks never compute one inside a lookup.

The argument relies on properties of the implementation that are checked in self-checking mode: restoring the state between rounds restores everything a round wrote; the last round computes the same table and the same diagnostics when the declarations are visited in reverse order; and no signature is computed for the first time after the rounds.

## What changes

| Programs of `test-programs/declaration-order` | Existing | Earlier fix (`extorder`, `givencheck`) | `sigrounds` |
|---|---:|---:|---:|
| Verdict depends on the order | 52 | 7 | 0 |
| Accepted in every order | 39 | 42 | 66 |
| Rejected in every order | 38 | 80 | 63 |

`sigrounds` accepts more than the earlier fix: the 7 programs that were still order-dependent, and 17 that the earlier fix rejected in every order as "circular" although a stable table exists. No program accepted in every order before is rejected. Programs without a consistent reading, such as the second example, are rejected in every order.

The semantic dump (types, name bindings, witness tables, diagnostics, elaborated witnesses) of the 216 files of the compiler's tests and workloads is identical with and without `sigrounds`.

## Cost

- Code without dependencies between signatures: one round, plus one copy-on-write of the buffers that the round mutates.
- A chain of *d* dependent signatures: *d* + 2 rounds, each computing every signature of the module once.
- About 150 lines. The earlier mechanisms (`givencheck`, the cycle rule of `extorder`, `memberskip`; about 260 lines) are switched off by `sigrounds` and can be deleted.

## Limits

- The fixed point is computed from the empty table. A program can have a consistent reading that this iteration does not reach, and it is then rejected; a second reading that is not reachable from the empty table is never seen. Lookup is not monotone (a new candidate can make an answer ambiguous, or shadow another), so no stronger statement holds.
- The message of a rejected cyclic program can name a different declaration of the cycle depending on the order, for cycles between type aliases only (`design-order/tests/10-alias-cycle.hylo`): the verdict is the same.
- Whether a program whose signatures depend on each other *should* be accepted when a stable table exists is a question for the language designers (`follow-up/designs/order.md`, section 7). A stricter rule can be added as a check on the stable table.

## Programs

`test-programs/declaration-order/` (129 programs), `follow-up/sigrounds/tests/`, and the 23 programs of the design.
