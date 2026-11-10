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

Extensions, conformances and given bindings whose type is written are the declarations that lookups and resolutions select *by their type*: the extended type, or the type of the given. Call that type the *signature* of the declaration. `sigrounds` computes all signatures of a module before anything else, in rounds:

- A round computes the signature of every such declaration, starting from the untouched typing state.
- During a round, a lookup or resolution never computes a signature. It reads the signatures from the table that the previous round produced; a declaration without an entry (not computed yet, or erroneous) is ignored. In the first round the table is empty.
- Rounds repeat until two consecutive tables are equal. The state of the last round is kept, and the module is then checked as before, with every signature known.
- If a table repeats an earlier one without being stable, or after `n + 2` rounds for `n` declarations, the declarations whose signatures differ are reported: "the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found".

If no lookup or resolution of the first round ignored a declaration, the first round is final and nothing is recomputed. That is the case for the standard library (72 signatures, one round) and for every program of the compiler's test suite.

For the first example above, round 1 computes `A is P` and fails on `Box<X> is P` (the lookup of `A.E` ignores every conformance); round 2 finds `A is P` in the table, so `X = Int` and `Box<Int> is P`; round 3 computes the same table and stops.

Two kinds of hiding are deliberate scoping rules and are unchanged: a where-clause requirement is invisible while the requirements written before it are typed, and a conformance cannot use itself to satisfy the traits it refines.

Four rules keep everything else a round computes independent of which declaration is visited first. They were added after an adversarial review of the first implementation, which found a program for each.

- **Only written signatures are in the table.** A requirement of a where clause is typed by the clause, in order. A given whose type is inferred from its initializer (`given let w = make()`) can only be typed with the expression that contains it; it is invisible during the rounds, and if a resolution made by a signature could have seen it, the program is rejected: "the type of this given must be written".
- **Enclosing declarations first.** Before the signature of a declaration nested in a function, extension or conformance with a where clause, the signature of the enclosing declaration is computed, so that a where clause is always typed before what it governs.
- **Owner before member.** When a lookup selects a member of an extension or conformance through the table, the signature of that extension or conformance is computed, in the current round, before the member is typed.
- **An alias of an erroneous type is an error.** A signature whose type is an alias that could not be resolved does not enter the table.

## Why the result does not depend on the order

The table after round *k* is a function of the program and of the table after round *k − 1*: a round starts from the same state whatever the order, reads other signatures only from the previous table, and computes each signature from its own expression. By induction no table depends on the order of declarations, and neither does the stopping test, the set of reported declarations, or the state handed to the rest of the checker. The argument needs no approximation of which declaration "could have matched", which is where the earlier fix failed.

After the last round nothing is hidden for a wrong reason: every signature is memoized, so the remaining checks never compute one inside a lookup.

The argument relies on properties of the implementation that are checked in self-checking mode: restoring the state between rounds restores everything a round wrote; every round computes the same table when the declarations are visited in reverse order, and the last round the same diagnostics; and no signature is computed for the first time after the rounds. This check is what exposed three of the four rules above.

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
- A where clause that selects a member through an earlier requirement (`C.Element`) makes a resolution that could see the module's givens, so such code needs two rounds.
- A chain of *d* dependent signatures: *d* + 2 rounds, each computing every signature of the module once, without the index of givens. The work is quadratic in the length of the chain, and one chain taxes the whole module: a chain of 8 next to 32 unrelated generic conformances makes ten times more candidate matches than without `sigrounds`. Recomputing only the signatures that read a changed entry would remove this; it is not implemented.
- About 300 lines. The earlier mechanisms (`givencheck`, the cycle rule of `extorder`, `memberskip`; about 260 lines) are switched off by `sigrounds` and can be deleted.

## Limits

- The fixed point is computed from the empty table. A program can have a consistent reading that this iteration does not reach, and it is then rejected; a second reading that is not reachable from the empty table is never seen. Lookup is not monotone (a new candidate can make an answer ambiguous, or shadow another), so no stronger statement holds.
- The message of a rejected cyclic program can name a different declaration of the cycle depending on the order, for cycles between type aliases only (`design-order/tests/10-alias-cycle.hylo`): the verdict is the same.
- Type aliases are still computed on demand. No program is known whose verdict depends on the order through an alias alone once the four rules are in place, but nothing proves that none exists; the self-check is the safeguard.
- Whether a self-supporting reading is found can depend on how many rounds an intermediate table lasts (`attack-sigrounds/p/h01`, `h02`): both verdicts are the same in every order.
- Whether a program whose signatures depend on each other *should* be accepted when a stable table exists is a question for the language designers (`follow-up/designs/order.md`, section 7). A stricter rule can be added as a check on the stable table.

## Programs

`test-programs/declaration-order/` (129 programs), `follow-up/sigrounds/tests/`, the 42 programs of the design and its review (`follow-up/design-order/tests/`), and the 104 programs of the attack (`follow-up/attack-sigrounds/p/`).
