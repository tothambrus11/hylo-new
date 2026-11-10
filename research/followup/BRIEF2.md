# Addendum to the brief: the mechanisms added during the follow-up

Read `BRIEF.md` first; its rules apply unchanged (never build, never modify `/home/user/hylo-impl`, one `tc-bench` at a time under `timeout`, write only inside your output directory).

## Binary and configurations

```
B=/home/user/hylo-new/research/exp/bin/eq22-554540c3a507/tc-bench
python3 /home/user/hylo-new/research/followup/tcrun.py eq22-554540c3a507 "FULL;NEW;NEW+selfcheck" FILE.hylo... [--counters prefix,prefix]
```

`tcrun.py` prints one line per (program, configuration): verdict, selected counters, first message. Configurations: `base`, `FIX`, `FULL` as in `BRIEF.md`, and

- **NEW** = FULL + `sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict`.

A configuration can be followed by `+flag+flag`; a bare list of flags is also accepted (`occurs+premsubst`). Add `+selfcheck` to re-do pruned work and report `[selfcheck] VIOLATION` lines; add `+trace` (run the binary directly) to print every resolution.

## The new flags

All are in `/home/user/hylo-impl/Sources/FrontEnd` (commit `git -C /home/user/hylo-impl log -5`). Search for the flag name to find every site.

| Flag | What it does | Where |
|---|---|---|
| `sigrounds` | Before a module is checked, the signatures of all its extensions, conformances and given bindings are computed in rounds. Each round starts from the pristine typing state and lets lookups and resolutions read these signatures from the table of the previous round only; rounds repeat until the table is stable. Replaces the cycle rule of `extorder` and `givencheck`. Intended property: the verdict does not depend on the order of declarations. | `Typer.settleSignatures`, `signatureRound`, `isVisible`, the extension loop of `resolve(_:declaredIn:applyingTo:in:statically:)`, `applies`, `declaredType(of: Given)`; design in `design-order/DESIGN.md` |
| `assocsubst` | The associated type read from a generic conformance is instantiated with the type arguments of the witness: with `given <T> => Box<T> is P { type X = T }`, `Box<A>.X` is `A`. Without it `Box<A>.X` and `Box<C>.X` are one type (unsound, also in base). | `Typer.typeOfImplementation(satisfying:in:)`, `TypeStore.substituteThroughAliases` |
| `premsubst` | A requirement that mentions another requirement of the same clause (`where T is P, T.X is Q`) is proved after it, with the witness found for it substituted into its type. | `Implication.binders`, `Typer.introduce(types:usings:into:)`, `formThread`, `threadContinuation`, `solvedWitnesses`, `withoutAssumed`, `normalizingProjections`; design in `design-engine/DESIGN.md` |
| `headsubst` | In a call, an associated type of a requirement of the callee that occurs in its parameters or result (`fun pick<T where T is P>(t: T) -> T.X`) is abstracted by a type variable, which is equated with the associated type selected through the witness found for that requirement once the callee is elaborated. Also: two associated types selected through the same declared witness unify if the types of the witness do. | `Solver.solve(call:)`, `Solver.resolve(_:elaboratedBy:at:)`, `Solver.solve(coercion:)`, `Typer.abstractingProjections`, `Typer.projection`, `TypeStore.openWithBinders`, `TypeStore.unifiable(_: AssociatedType, …)` |
| `abstractstrict` | Inside a trait, `Self.X` (selected through the witness the trait declares) is only equal to a selection through that same witness. Without it, it is equated with `T.X` for another witness `T is P` when `T == Self`, which converts `W.X` into `V.X` under `V == W` (unsound). | `TypeStore.unifiable(_: AssociatedType, …)`, `Typer.solveEquality` (`abstractBindings`) |
| `eqindex`, `eqeager` | Result-preserving: keep the index of givens under ground equalities; decide the closed equalities of a match at once. | `indexedSummon`, `eagerlyCoerced`; design in `design-eqnorm/DESIGN.md` |

## What is known

- `Tests/CompilerTests` and the research workloads: the semantic dump with `sigrounds`, `eqindex`, `eqeager` is identical to the one without.
- Declaration order: 129 programs, 2,876 permutations under FULL + `sigrounds`: no program has two verdicts (FULL: 7).
- Test programs written for each mechanism: `design-order/tests`, `sigrounds/tests`, `design-engine/tests` (`s1-*`), `headsubst/tests`, `reference/hand`, `reference/judge/p`.
- Syntax notes: parameters have no label unless one is written, so `fun f(t: T)` is called `f(x)`; `Foo<Int>.F` is not accepted as a type expression (write `type FI = Foo<Int>` and `FI.F`); a conditional conformance is written `given <T where T is Q> => Box<T> is P { … }`.
