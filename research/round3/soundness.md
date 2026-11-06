# Baseline soundness bugs: investigation (round 3), after adversarial review

Five defects in the baseline type checker were investigated. Each one exists in `tc/research` with all flags off. The first version of this document was then attacked by an adversarial review workflow (run `wf_45540cb8-a9c`): for each bug, one skeptic on the claimed cause, one on the fix, and a judge who re-ran every major or critical issue. The sections below are the judges' corrected texts. They include only confirmed corrections.
- Raw reports: `soundness/review/results.json`.
- The reviewers' programs and outputs: `soundness/review/<bug>-<cause|fix|judge>/`.

## Review verdicts

| # | Defect | Cause (judge) | Fix (judge) | Most important corrections |
|---|---|---|---|---|
| 1 | Bogus equality derivations (`fixsubst`, `eqrefute`) | confirmed-with-corrections | sound-but-insufficient | A **single** equality suffices at call sites and given premises: `g<D, V>()` with only `V == W` is accepted. Congruence extends it (`Box<D.X>` as `Box<A.X>`). **`eqrefute` is unsound**: it rejects the valid `v-abs-7.hylo`, because associated types with an abstract qualification unify through their qualification. Some fixed configurations exhaust memory instead of rejecting. |
| 2 | Equality chains need a procedure | confirmed-with-corrections | sound-but-insufficient | Rejection beyond 4 links is a **depth-cap cliff**: a genuine proof costs about 2 match steps per link, so trans-5 needs a cap of 12. A procedure needs decomposition (injectivity of nominal constructors), not only congruence closure. `canDeriveCoercions` pre-filters congruence-derivable goals. |
| 3 | Projections not reduced (was: `where T.X == B`) | partially-wrong | sound-but-insufficient | Broader than stated: **any associated-type projection in an instantiated generic signature fails** (parameter types, return types, generic callers). The qualification is a reference to the callee's using, not "abstract". `eqrefute` does apply, wrongly, to generic callers. The proposed fix does not reach them. |
| 4 | Cyclic substitution crash (`occurs`) | confirmed-with-corrections | sound-but-insufficient | `occurs` is **not** invisible: it changes inferred types and diagnostics on some non-crashing programs. **`fixsubst` alone introduces new SIGSEGVs** and requires `occurs`. The crash is also reachable from plain expression inference. |
| 5 | Order-dependent memoization (`cyclecut`) | confirmed-with-corrections | **unsound** | `cyclecut` **accepts an ill-formed (ambiguous) program the baseline rejects** (`amb1.hylo`). Its skip path accepts programs that are ambiguous by the checker's own rules, depending on order. Rolled-back transactions are expensive and repeated. The 192-test oracle does not exercise it. |

Reviewer verdicts:
- §1: confirmed-with-corrections, partially-wrong
- §2: confirmed-with-corrections, confirmed-with-corrections
- §3: partially-wrong, partially-wrong
- §4: confirmed-with-corrections, confirmed-with-corrections
- §5: confirmed-with-corrections, partially-wrong

I re-ran four of the confirmed issues myself:

| Repro | Baseline | Fixed configuration |
|---|---|---|
| `review/eqsubst-cause/c01-single-eq-call.hylo` | accepted (wrong) | `fixsubst,eqrefute` rejects |
| `review/eqsubst-fix/v-abs-7.hylo` (valid) | accepted | `fixsubst` accepts; `fixsubst,eqrefute` rejects (wrong) |
| `review/occurs-fix/c1-cycle-plus-coercion.hylo` | 1 diagnostic | `fixsubst` exits 139 (SIGSEGV); `occurs,fixsubst` gives 1 diagnostic |
| `review/cyclecut-fix/amb1.hylo` (ambiguous) | rejected | `cyclecut` accepts (wrong) |

**Tracing tool.** `HYLO_TC_EXPERIMENTS=trace` prints, for every completed resolution, the minimal results and the derivation log of each completed thread.

---

## 1. Unrelated equalities make types interchangeable (unsound)

**Repro.** `soundness/bug-assoc-eq-two-links.hylo` and the variants `soundness/eqbug-1..4.hylo`:
```hylo
trait P { type X }
fun check<T>(x: T) {}
fun f<A, B, C, D where A is P, B is P, C is P, D is P, A.X == B.X, C.X == D.X>(x: D.X) {
  check<A.X>(x)   // accepted, but nothing relates A.X and D.X
}
```

**Which programs are affected.** The baseline proves an equality goal `L ~ R` whenever `R` is a side of some equality in scope.
- `L` can be any type when the goal is a call-site `where` requirement or a given's premise. That includes a type mentioned in no equality, or a concrete struct. Examples, with one equality each:
  - `fun f<V, W, D where V == W>() { g<D, V>() }`, where `g<T, U where T == U>`;
  - `fun f<V where V == S>() { g<Q, S>() }`;
  - `given <X where X == V> => X is P` proving `D is P`.
- When the goal comes from coercing an argument or annotation, `coerced()` first checks `canDeriveCoercions` on the outer pair. That check also requires `L` to be a side of some equality. This is why the repro above needs a second equality (`C.X == D.X`), and why the repro's comment "with a single equality the program is correctly rejected" holds only for that path.
- The sides can be generic parameters (`A == B, C == D`), associated types of unrelated traits (`D.Y`, eqbug-3), or nominal types.
- Types built from them are also interchangeable, for example `Box<D.X>` passed as `Box<A.X>`.
- The bogus derivation needs 7 resolution layers. At a depth cap of 6 or less, the program is rejected. When testing with small caps, use the impl binary with flags off: the frozen baseline binary ignores `HYLO_TC_MAXDEPTH`.

**The derivation the baseline accepts** (from the `trace` tool):
```
goal D.X ~ A.X  <- transitivity<T0 = D.X, T1 = ?e, T2 = A.X>
  premise ?e ~ A.X  <- the given A.X ~ B.X, coerced: unify (A.X ~ B.X) with (?e ~ A.X)
                        binds ?e := A.X, assumes B.X ~ A.X (proven by symmetry)
  premise D.X ~ ?e  <- reflexivity   (?e := D.X !)
result: transitivity<D.X, D.X, A.X>(reflexivity<D.X>)(coercion($A.X~B.X))(x)
```
The second premise is discharged last, because pending premises are discharged last-in, first-out.

**Root cause.** `Typer.match` (Typer.swift, "assume non-syntactic equalities between pairwise nested parts"):
- Unification of the witness's type with the goal records coercions for the parts that do not match.
- If those coercions may be derivable, it continues with `thread.environment.assuming(givens: gs)`. That environment **keeps the old substitutions and drops the `substitutions` that this very unification computed**.
- The success path (`coercions.isEmpty`) merges them correctly with `environment.substitutions.union(substitutions)`.

So a variable bound while proving one premise (`?e := A.X`) is free again when the next premise is proven, and can be bound to something else (`?e := D.X`).

Other paths checked, none of which drops substitutions:
- `threadContinuation`;
- `applyContinuation`;
- `formThread`, which reifies under the environment;
- `canDeriveCoercions`, which is only a necessary-condition filter.

**Fix (`fixsubst`).** Continue with `thread.environment.substitutions.union(substitutions)` in the coercion path as well.
- **Why `union` is safe.** `formThread` reifies both the witness and the query before matching, so the two tables bind disjoint variables.
- Identical on all 192 tests and on the standard library (same counters, no diagnostic).
- Rejects eqbug-1..4 at depth cap 7, in about 1.4 s each. At the default cap of 10 it is very slow: one run took 155 s and others exceeded 600 s (`eqbug-results.txt`).
- Rejects every other ill-typed variant tried: single equality, plain parameters, `Box<...>`, three equalities, and the generated `assocneg-N` workloads.
- Still accepts the valid control eqbug-5 (`B.X` used as `A.X` with `A.X == B.X`).

**Performance consequence.** With the bogus derivation gone, rejecting an ill-typed program means searching to the depth cap.
- eqbug-1 takes 3.3M matches and 155 s on an idle machine, and more than 600 s under load.
- Some ill-typed programs exceed the harness's 2.5 GB memory cap at the default depth instead of being rejected, for example `A == B, C == D` with `x: D` passed as `A`.

**Companion `eqrefute`** (meant to be used only together with `fixsubst`) restores fast rejection.
- **What it does.** Before searching for a closed equality goal `a ~ b` whose sides are atoms (generic parameters, associated types, or nominal types without arguments), it:
  1. collects the ground equality givens in scope, including the assumed ones;
  2. computes their equivalence classes with union-find, merging unifiable atoms;
  3. refutes the goal when `a` and `b` are in different classes.
- **When it gives up.**
  - a given can derive equalities from its own parameters: a quantified equality, a conditional equality (one with usings), or a `<T> T` head;
  - a fact has a structured side, where congruence could relate classes;
  - an assumed given still mentions variables, because assumed givens are not reified;
  - the goal has open variables.
- **It is not sound as implemented.** It rejects a valid program that the baseline and `fixsubst` both accept:
  ```hylo
  fun need<A, B where A == B>() {}
  trait P { type X; fun f<T, U where T == Self, T is P, T.X == U>() { need<X, U>() } }
  ```
  `fixsubst` derives `(Self::P).X ~ U` from `$t : (T::P).X ~ U` by a coercion that assumes `T ~ Self`. This works because unifying two associated types whose qualification is abstract unifies their qualification types (`TypeStore.unifiable(AssociatedType, AssociatedType)`).
- **Where the soundness argument fails.** The argument said that coercions between equality witnesses only require equalities between the sides, so every derivable equality lies within the closure. That is false for associated types: the premise can relate their qualifications. `equalityIsRefuted` treats associated types as atoms and never merges `(Self::P).X` with `(T::P).X`.
- **Required fix.** Give up when a side is an associated type with an abstract qualification, or close the union-find under qualification congruence. Add this program as a positive test, because the 192 tests do not cover it.
- **Also not handled.** With a structured side (`A == Box<B>, C == D`), `eqrefute` gives up, and the program still exceeds the memory cap.

Results:

| Program | Baseline | `fixsubst,eqrefute` |
|---|---|---|
| eqbug-1..4 | accepted (wrong), ≈1.4 s | rejected, ≈135 ms |
| assocneg-3 | accepted (wrong), 1.3 s | rejected, 133 ms |
| assocneg-8 | accepted (wrong), 4.4 s | rejected, 484 ms |
| single-equality call-site variants (`g<D, V>()`, `g<Q, S>()`) | accepted (wrong) | rejected, < 1 s |
| `A == Box<B>, C == D`, `x: D` as `A` | accepted (wrong) | exceeds the 2.5 GB memory cap |
| eqbug-5 (valid) | accepted, 140 ms | accepted, 137 ms |
| coercion-derivability-cache (valid) | accepted, 3.9 s | accepted, 3.9 s |
| `T == Self, T.X == U` ⊢ `X == U` (valid) | accepted | **rejected (wrong)** |

## 2. Equality chains need an equality procedure, not search

Bug #1 also explains why valid equality chains were "fast". The baseline's proofs of them are bogus, with the right conclusion by luck. For `trans-4`, `T0 ~ T4` is "proved" without ever using `T1 ~ T2`: `transitivity<T0, ?e, T4>` proves `?e ~ T4` by coercing `T2 ~ T3` (assuming `T3 ~ T4`), and then, through the same dropped binding, closes `T0 ~ ?e` by reflexivity or by `T0 ~ T1`. These bogus proofs have a fixed size (about 7 match steps, 8 for the call) whatever the chain length, so the baseline cost stays nearly flat.

With `fixsubst`, every proof is genuine, and a genuine proof costs about **2 match steps per link**: 2n+2 for trans-n, 2n+1 for assoceq-n. The resolution "depth" cap bounds the **size** of a derivation, not its height: each BFS layer advances every thread by one match, and pending premises are discharged one after another. Each extra step multiplies the work by about 4-5:

| Chain | Baseline (bogus proof) | `fixsubst` (genuine search) |
|---|---|---|
| trans-3 | 731 ms, 30k matches | 745 ms, 30k matches (needs cap 8) |
| trans-4 | 918 ms, 35k matches | **13-20 s, 640k matches** (needs cap 10; cap 9 rejects) |
| trans-5 | 1.2 s, 41k matches | needs 12 steps, so rejected by the default cap of 10. Under the standard 2.5 GB limit it **crashes out of memory** (about 35 s). With the limit raised: 51-79 s, rejected |
| assoceq-5, trans-8 | 2.7 s / 1.9 s | need 11 and 18 steps. **Out-of-memory crash** after about 35 s |

The search space explored per layer is the same with and without `fixsubst` (for example trans-3 at cap 8: 29.8k vs 29.7k matches). The slowdown comes entirely from having to go deeper. The existing performance flags do not change this: on trans-4, `loopcheck` halves the matches (337k) and `eqrefute` leaves them unchanged (640k).

**Conclusion.** `fixsubst` alone is correct but makes the equality fragment unusable:
- chains of 3-4 links become slow;
- chains of 5 or more links are rejected outright by the cap, or crash the compiler, however fast the search is.

Equalities need a decision procedure that answers an equality subgoal in one step, instead of SLD search with built-in symmetry and transitivity givens. Requirements on that procedure:
- **Theory.** Congruence closure over the equalities in scope, **plus decomposition (injectivity) of nominal type constructors**. `match` poses the innermost mismatched parts as subgoals. For example, `Box<A> == Box<B>, Box<A> is P` needs `A ~ B` to use `P<Box<B>>`, and congruence alone does not give that (`decomp-2`, `quant-4` are rejected today in every configuration). Clash detection between distinct constructors gives the negative answers.
- **Atoms.** Associated types are opaque atoms identified by their qualifying conformance witness, not functions of their base type. `T == U` must not give `T.X == U.X` (`negative/associated-type-inequality.hylo`).
- **Pre-filter.** It must also replace the "may a coercion be derivable" test in `canDeriveCoercions`/`coerced`. That test requires each side to unify with a side of some equality given, so it rejects congruence-derivable goals before any search: `C == Box<A>, A == B` with `x: C` used as `Box<B>` is rejected after 1 match (`quant-2`, `quant-2c`).
- **Ground goals.** Union-find decides `a ~ b` and produces the proof term from the path.
- **Open goals.** Unify syntactically, then check the mismatched pairs against the closure. In general this is rigid E-unification, not a single unification against a class representative, so validate any change in inferred bindings with the oracle.

This is a design change: the proof terms change, and equality subproofs no longer count toward the depth cap. It should land together with `fixsubst`. `eqrefute` above is only a narrow first step towards the negative half. It works only when **every** equality in scope is between atoms, and it gives up for all goals as soon as any structured, conditional or quantified equality is visible, even an unrelated one. For example, eqbug-1 plus an unrelated `Box<Z> == W` is no longer refuted, and with `fixsubst,eqrefute` it crashes out of memory (`review/eqchain-fix/eqbug1-struct.hylo`).

## 3. Associated-type projections in an instantiated generic signature are never reduced (incomplete, then explodes)

**Repro.** `soundness/assoc-eq-call-incomplete.hylo`, minimized:
```hylo
trait P { type X }
struct A {}
struct B { public memberwise init }
given A is P { type X = B }
fun f2<T where T is P, T.X == B>() {}
public fun main() { f2<A>() }     // valid, but rejected / runs out of memory
```

`let y: A.X = B()` works, so projection during name resolution is fine. The call `f2<A>()` needs the implicit arguments `(P<A>, ((A::P).X ~ B))`. `P<A>` is found (the given `A is P`), but the second goal stays `(A::P).X ~ B` and is never reduced to `B ~ B`.

**The defect.** It lies in how a generic signature is instantiated, not in the equality requirement specifically:
- Inside `f2`, `T.X` is resolved through the witness for `T is P`. That witness is a *reference to `f2`'s own where-clause binding* (`$i` in the trace), not the abstract witness. `typeOfImplementation` therefore builds an opaque `AssociatedType(X, qualification: ref(<f2's using>) : P<T>)`.
- Instantiating `f2<A>` substitutes `A` for `T` in the types only, so the qualification is still `ref(<f2's using>) : P<A>`. That reference is meaningless at the call site.
- `TypeStore.unifiable(AssociatedType, AssociatedType)` unifies two projections only when one qualification is `.abstract`, so this projection unifies with nothing else.
- Nothing links the using declaration to the premise `$0` that witnesses it: `introduce(types:usings:)` stores only the usings' types. The witness found for `$0` is therefore never substituted anywhere.
- The printer shows only `(A::P).X`, so projections with different qualifications print identically. An error message or trace showing `(A::P).X` does not reveal which witness it holds.

The equality requirement is one instance. The same failure, fast and on the baseline too, happens with no equality at all:
- `fun f3<T where T is P>(x: T.X)` called as `f3<A>(B())`: "cannot pass value of type 'B' to parameter '(A::P).X'".
- `fun f6<T where T is P>() -> T.X` with `let y: B = f6<A>()`: "no coercion from '(A::P).X' to 'B'".
- A generic caller, `fun g<U where U is P>(y: U.X) { h<U>(y) }` with `h<T where T is P>(x: T.X)`: "cannot pass value of type '(U::P).X' to parameter '(U::P).X'".

Only reflexive requirements (`T.X == T.X`) are discharged.

**The blow-up.** Without `eqrefute`, the resolver searches the equality built-ins until the cap:
- caps 5–7: 7.3k → 23k → 82k matches, "no coercion" error;
- default cap 10: runs out of memory, after more than 4.8 GB (review t08/t24), on the baseline and with `fixsubst` alone.

With `eqrefute`, the blow-up disappears: both sides are atoms in different classes, so the goal is refuted immediately (292 matches, about 30 ms, "no coercion" at any cap). The rejection is still wrong, because `eqrefute` refutes an equality that is true and that this procedure cannot derive.

**Interaction with #1.** In a generic caller, `fun h<U where U is P, U.X == B>() { f2<U>() }`, the baseline *accepts* the call (0 diagnostics, 92k matches, 1.7 s). The only reason is a bogus derivation through symmetry and transitivity with an unbound middle variable, which is the bug #1 path. `h`'s own given, printed as the same `(U::P).X ~ B`, does not match the goal directly. Under `fixsubst,eqrefute` the call is rejected, and with `fixsubst` alone it runs out of memory. So landing `fixsubst`/`eqrefute` without this fix turns an accidental acceptance of a valid program into a rejection.

**Fix (not implemented): dependent requirements.**
- Record, for each premise of an instantiated signature, which using declaration it witnesses.
- When premise `$i` is solved with witness `w`, substitute `w` for references to that using throughout the instantiated callee type, in the head (parameter and result types) as well as the remaining premises. Then reduce each projection whose qualification is now a conformance declaration: `(A::P).X` becomes `(A::<given A is P>).X = B`. In a generic caller, `w` is the caller's own binding, so `h<U>`'s `U.X` and `g`'s `U.X` become the same type.
- This needs two changes:
  - Premises are currently discharged last-first (`threadContinuation` pops `givens.last`), so the equality is attempted before the conformance it depends on. Discharge them in forward order, or rewrite pending goals' types when an earlier premise is solved.
  - The head is matched before any premise is discharged, so the substitution must happen before argument and result constraints are solved, or those constraints must be re-checked afterwards.
- The reduction must run before `equalityIsRefuted`, or `eqrefute` will keep refuting these goals.
- Merely "normalizing associated types with concrete qualifications through the conformance" is not enough: it does not cover generic callers, whose qualification type is `P<U>`.
- Unverified caveat: `typeOfImplementation` reads an implementation's declared type without applying a generic conformance's type arguments, so `type X = T` in `given <T> => Box<T> is P` may also need instantiation. Projections such as `Box<B>.X` currently fail earlier, at type-expression resolution, so this could not be tested.

## 4. Cyclic substitutions crash the compiler (no occurs check)

**Cause.** `TypeStore.unifiable` has no occurs check. Its variable cases bind a variable to a type that contains that variable. Reifying the resulting cyclic substitution recurses until the stack overflows: SIGSEGV, exit 139. The unifier is shared, so two paths reach the crash:
- implicit resolution, through `Typer.match`;
- ordinary expression inference, through the solver and `Typer.commit`.

**Repro, resolution.** `soundness/cyclic-query-segfault.hylo` (review t25). Givens `<U> U is P<U>` and `<T where T is P<S<T>>> T is R`, and a query `needR()` with an inferred `T`.
- `Typer.match` unifies the given's instantiated head `P<?u, ?u>` with the premise `P<?t, S<?t>>`. This binds `?u := ?t`, then `?t := S<?t>`, in match's local substitution table.
- No coercion is recorded, so match merges that table into the thread environment (`union`) and reifies the witness (Typer.swift:3762 on `tc/research`).
- That reify recurses forever.

**Repro, expression inference.** No givens are needed. Each of these crashes the baseline the same way (`review/occurs-fix/s2-tuple.hylo`, `s3-generic.hylo`):
- `fun same<T>(x: T, y: T) {}` with `let f = fun[](a) { same(a, (a, a)) }`;
- `same(a, mk(a))` with `mk<T>(x: T) -> S<T>`.

**Fix (`occurs`).** An occurs check in both variable cases of `TypeStore.unifiable`: binding a variable to a type that contains it, under the current local table, makes `unifiable` return `false`.
- Solver equalities then fail normally.
- Inside `Typer.match` the Bool result is ignored. A nested failure becomes a coercion on the nearest enclosing compound pair, which match then rejects.
- A top-level failure with no coercion would take match's success path with the binding missing. It is not reached in any test, but it should be guarded explicitly by reporting `(a, b)` as a coercion.

Results:
- t25 is rejected ("no coercion …") in tens of ms. The lambda repros give "cannot pass value of type `#!` …", a poor diagnostic but no crash.
- No program was found that still crashes with `occurs` on.
- Identical on all 192 tests.
- Cost: a walk of the bound type, only when it has variables. No measurable difference on the test suite.

**`occurs` is not invisible.** When a match would create a cycle *and* records a coercion, the baseline silently drops match's substitutions (including the cycle). It keeps a bogus derivation, then fails later with "not enough context to infer a type". `occurs` rejects that derivation instead ("no coercion …"), which changes inferred types and diagnostics: semtest reports MISMATCH on `review/occurs-fix/c1-cycle-plus-coercion.hylo` and `c3-accept-change.hylo`. No accept/reject flip was observed. Add these to the regression set.

**`fixsubst` depends on `occurs`.** `fixsubst` keeps match's substitutions on the coercion path, so the dropped cycle is now reified. With `fixsubst` alone, `c1`, `c3` and `c5-order2` crash (exit 139). With the baseline or with `occurs,fixsubst` they do not. `fixsubst` must never be enabled without `occurs`.

**Limits.** `occurs` prevents cycles created during unification. `SubstitutionTable.union`/`assign` remain unchecked; they are safe only because the inputs to match and to the solver are reified under the environment substitutions first. Latent gaps in `TypeStore.occurs`, none reachable from source so far:
- no `Bundle` case;
- the `hasVariable` early exit does not see `Arrow.environment`.

(Recommendation 1 should read: land `occurs` as a crash fix that also rejects some bogus derivations. Land it before, or together with, `fixsubst`.)

## 5. Order-dependent memoization across cycle cuts

**Mechanism** (review names-1/names-2). While a declaration `X` is being typed (`declarationsOnStack`), two things can go wrong.

1. **Self-reference.** Evaluating something that refers back to `X` reports "refers to itself" and returns `.error`. The enclosing computation memoizes it permanently: the extendee of an extension, the type of a conformance, alias or binding, the types of its expressions, and the diagnostic.
2. **Silent skip.** Lookups skip any extension that is on the stack, with no diagnostic (baseline Typer.swift:4681). The result of the lookup is memoized too.

Which extension's extendee evaluation is entered first decides the outcome. It stays on the stack while the others are evaluated, and within one lookup that order is declaration order.

The cycles are often spurious. Member lookup always works out the extendee of *every* visible extension, even when a native member exists and even for extensions that declare no member of that name.

Examples:
- `type X = A.Foo; extension X {…}` reports a spurious cycle (n01), through the self-reference path. Evaluating `A.Foo` forces the extendee of `extension X`, which is `X`, on the stack. The memo that gets poisoned is that extendee (`#!`); `X` itself is fine. The reordered versions v02 and v04 are accepted.
- n05 goes wrong in two independent ways: through the extension's extendee (n05_nogiven) and through the given's conformance type (n05_givenonly).
- Swapping two extensions turns acceptance into rejection (n04 vs v2_swapped). This goes only through the silent skip: no "refers to itself" fires, and `early` plays no part.
- **The skip can also hide a competing candidate**, so the checker accepts a program that is ambiguous by its own rules. Take `struct A { type Foo = Int }` and `struct C { type Bar = A }`.
  - With `extension C.Bar { type Foo = Bool }` declared before `extension A.Foo { fun g() {} }`, the baseline accepts (amb_e2first).
  - In the other order it rejects `A.Foo` as not denoting a type (amb_e1first). A direct `extension A { type Foo = Bool }` is rejected the same way.
  - In one program, `A.Foo` in E1's extendee resolves to `Int`, while the same `A.Foo` in `fun k(y: A.Foo)` is rejected (amb_e2first_use).

So #5 is order-dependent **acceptance and rejection**, not only rejection of valid programs.

**Fix attempt (`cyclecut`): transactional speculation.**
- Member lookup needs an extension's extendee that is not yet memoized, or resolution needs a given's type that is not yet memoized. The typer:
  1. snapshots `(program, cache)`. These are value types, so taking the snapshot is O(1);
  2. evaluates;
  3. if the global counter of cuts changed meanwhile, restores the snapshot and treats the extension or given as not applicable for this query. Only the four "refers to itself" sites count as cuts.
- Only the snapshot restore has any effect. The `speculating`/`heldDiagnostics` machinery and the guarded `setType` calls are dead code, because `speculating` is never incremented.

Results on the 47 programs of `review/names/**` (diagnostic counts, baseline → `cyclecut`):

| Improved | Unchanged order-dependent |
|---|---|
| n01 2→0, n05 2→0, n17 3→2, v01 2→0, v06 2→0, v08 2→0 | t01, t02, t09, v2_swapped, v6_summon_swapped, n17 (one error left) |

No program in `names/**` gets more errors.

Identical on all 192 tests, but that holds **by construction**. Until the first cut, `cyclecut` runs the baseline's code, and the baseline reports "refers to itself" at every cut. So only programs the baseline rejects with that error can change, and the tests barely exercise the transaction path.

**Limitations of `cyclecut`, found with targeted programs** (`review/cyclecut-fix/`):
- **It accepts an ill-formed program the baseline rejects.**
  - The program, amb1: `extension A { type Me = A }; type X = A.Me; extension X { type Me = Int }`.
  - Under `cyclecut`, X resolves to A while `extension X` is skipped. Once X = A, that extension applies to A and `A.Me` is ambiguous (amb0, amb2), so the program has no consistent reading.
  - The baseline already accepts the reordered amb3. `cyclecut` extends this unsound skip rule to more declaration orders.
  - A sound version needs a post-check that every skipped extension really does not apply once its extendee is known.
- **Order dependence remains even without mutually dependent extendees.**
  - The cut counter is global and never reset, so a cut handled by an inner transaction also aborts every enclosing one.
  - casc1 (a use before `type X = A.Inner` and two `extension X`) still fails, with `Inner has no member h` and no cycle diagnostic. Declaring the use last (casc2) gives 0.
  - g1/g2 do the same with a conformance `given X is P`.
- **The rolled-back decision is final for the current query.** The query that saw the rollback is never re-checked, so the order dependence becomes a silently missing extension or given, followed by a misleading 'no member' or 'no coercion' error.
- **Cost.**
  - Discarded transactions are not memoized, so every later query repeats them, and each one costs several milliseconds (probably copy-on-write of the shared buffers).
  - perf_g16 (16 uses before the alias, extension and given): type-checking the user module takes 115 ms in the baseline and 6.9 s under `cyclecut` (824 discarded transactions). The stdlib is about 10% slower (noisy).
  - The fix is to memoize the "cut here" verdict per (declaration, stack base).

**A stronger variant (`cyclecut,cyclecutstack`)** also treats "skipped an extension that was already being typed when the transaction started" as a cut.
- It fixes t01, t02, t09 and v2_swapped.
- It newly rejects n02, n03, n04, t03, v1, v3, v4 and v5, which the baseline accepts.
- On the ambiguity case it only moves the acceptance to the other order: amb_e2first goes 0→2 and amb_e1first 2→0.

n02–n04, t01 and v2_swapped have **genuinely mutually dependent extendees**: E2's extendee needs a member of E1, and E1's extendee lookup must decide whether E2 applies. Any local rule picks *some* evaluation order, so the outcome stays order-dependent. Removing the dependence requires a language decision:
- (a) extendees are resolved in a pre-pass that does not consider extension members (simple, predictable, rejects some programs);
- (b) a fixpoint over extendee bindings (accepts the most, costs iterations).

The use-before-declaration cases (casc1, g1) and the missing consistency check (amb1) are implementation defects, not part of that language question.

`cyclecutstack` is kept only as a documented experiment.

`cyclecut` composes with `memberskip`: same results, since `memberskip` never skips an extension whose extendee is unmemoized.

(Summary table row for #5: "Results computed across a cycle cut or a skipped extension are memoized, so outcomes depend on declaration order | order-dependent rejection of valid programs **and acceptance of ambiguous ones** | partial fix `cyclecut`: 6 programs improved, but one ill-formed program newly accepted and large slowdowns on use-before-declaration programs".)

---

## Also confirmed

- **`negative/illegal-enum-case.hylo` crashes the typer** (force unwrap in `declaredType(of: EnumCaseDeclaration)`, Typer.swift ≈1367). It is reachable only from `tc-bench`, because the driver stops after scoping errors. Fix: return `.error` when the case has no enclosing enum.


## Recommendations (revised after review)

1. **`occurs`**: land it before, or together with, `fixsubst`. It fixes SIGSEGVs in implicit resolution and in expression inference. It is a semantic change that also removes some bogus derivations, so it changes some inferred types and diagnostics. It is identical on the 192 tests.
2. **`fixsubst`**: this is the correct fix of bug #1's root cause, but **only together with `occurs`**: alone it creates new crashes. It also makes equality chains longer than 4 hit the depth cap, and some programs exhaust memory. So it must land with a real equality procedure: union-find or congruence closure **with decomposition**, treating associated types as atoms keyed by their conformance, and without counting towards the depth cap.
3. **`eqrefute`**: **do not land as implemented.** It is unsound (`v-abs-7.hylo`), because it merges atoms with plain unification, while associated types with an abstract qualification are equal when their qualifications are equal under the very equalities being closed. It also gives up for every goal as soon as one structured equality is visible. It should become the negative half of the procedure in (2).
4. **Projection reduction (#3)**: the problem is wider than `where` clauses. Associated-type projections in instantiated generic signatures must be reduced through the witness found for the corresponding using, including for generic callers. This needs a link from using to position, which the proposed fix does not have.
5. **`cyclecut`**: **do not land.** It accepts an ambiguous program the baseline rejects, it is order-dependent itself, and its rollbacks are expensive. The language needs a rule for extendees that depend on members of other extensions (a pre-pass ignoring extension members, or a fixpoint) before any implementation.
6. Report #1, #3 and #4 upstream with the repros in `soundness/` and `soundness/review/`.
