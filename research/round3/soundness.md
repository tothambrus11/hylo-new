# Baseline soundness bugs: investigation (round 3)

Five defects in the baseline type checker were investigated. Each one exists in `tc/research` with all flags off, and upstream as far as the code is shared:

| # | Defect | Kind | Status |
|---|---|---|---|
| 1 | Unrelated equalities make types interchangeable | **unsound**: accepts ill-typed programs | root cause found; fix `fixsubst` + `eqrefute`; exposes #2 |
| 2 | Equality chains of length ≥ 5 are rejected or take minutes once #1 is fixed | completeness / performance | analysed; needs an equality procedure |
| 3 | `where T.X == B` at a call site with concrete `T` is never discharged | completeness + resource blow-up | analysed; needs dependent requirements |
| 4 | Cyclic substitution in the concrete unifier crashes the compiler (SIGSEGV) | crash | fixed by `occurs` |
| 5 | Results computed across a cycle cut are memoized, so outcomes depend on declaration order | order-dependent rejection of valid programs | partial fix `cyclecut` (6 programs improved, none regressed) |

The fixes are flags in `research/impl/0007-*.patch`. Each is a deliberate **semantic change**: it is meant to differ from the baseline, but only on programs where the baseline is wrong.

**Oracle (192 compiler tests).** Identical to the baseline:
- `fixsubst`;
- `occurs`;
- `occurs,fixsubst`;
- `cyclecut`;
- `cyclecut,fixsubst,occurs`.

The final builds of `fixsubst,eqrefute` and `cyclecut,fixsubst,eqrefute,occurs` are also identical (`soundness/oracle.txt`).

**Tracing tool.** `HYLO_TC_EXPERIMENTS=trace` prints, for every completed resolution, the minimal results and the full derivation log of the winning thread:
- which given was tried for which goal;
- which coercions were assumed;
- the order in which pending premises were discharged.

That log is how bugs #1 and #2 were diagnosed.

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

Any type mentioned on a side of some equality becomes interchangeable with any other such type, once two equalities are in scope. That includes `D.Y` of an unrelated trait (eqbug-3). Types mentioned in no equality are still rejected.

**The derivation the baseline accepts** (from the `trace` tool):
```
goal D.X ~ A.X  <- transitivity<T0 = D.X, T1 = ?e, T2 = A.X>
  premise ?e ~ A.X  <- the given A.X ~ B.X, coerced: unify (A.X ~ B.X) with (?e ~ A.X)
                        binds ?e := A.X, assumes B.X ~ A.X (proven by symmetry)
  premise D.X ~ ?e  <- reflexivity   (?e := D.X !)
result: transitivity<D.X, D.X, A.X>(reflexivity<D.X>)(coercion($A.X~B.X))(x)
```

**Root cause.** `Typer.match` (Typer.swift, "assume non-syntactic equalities between pairwise nested parts"):
- Unification of the witness's type with the goal records coercions for the parts that do not match.
- If those coercions may be derivable, it continues with `thread.environment.assuming(givens: gs)`. That environment **keeps the old substitutions and drops the `substitutions` that this very unification computed**.
- The success path (`coercions.isEmpty`) merges them correctly with `environment.substitutions.union(substitutions)`.

So a variable bound while proving one premise (`?e := A.X`) is free again when the next premise is proven, and can be bound to something else (`?e := D.X`).

**Fix (`fixsubst`).** Continue with `thread.environment.substitutions.union(substitutions)` in the coercion path as well.
- Identical on all 192 tests and on the standard library (same counters, no diagnostic).
- Rejects all four bug variants and the generated `assocneg-N` workloads.
- Still accepts the valid control eqbug-5 (`B.X` used as `A.X` with `A.X == B.X`).

**Performance consequence.** With the bogus derivation gone, rejecting eqbug-1 means searching to the depth cap:
- 3.3M matches and 155 s on an idle machine;
- more than 600 s under load.

**Companion `eqrefute`** (sound only together with `fixsubst`) restores fast rejection.
- **What it does.** Before searching for a closed equality goal `a ~ b` whose sides are atoms (generic parameters, associated types, or nominal types without arguments), it:
  1. collects the ground equality givens in scope, including the assumed ones;
  2. computes their equivalence classes with union-find, merging unifiable atoms;
  3. refutes the goal when `a` and `b` are in different classes.
- **When it gives up.**
  - a given can derive equalities from its own parameters: a quantified equality, or a `<T> T` head;
  - a fact has a structured side, where congruence could relate classes;
  - the goal has open variables.
- **Why it is sound** (relative to `fixsubst`). Every derivation of an equality between atoms uses only:
  - reflexivity (or unifiability);
  - symmetry;
  - transitivity;
  - the ground equality facts;
  - coercions of one equality witness into another, which require proving equalities between the sides, i.e. again within the closure.

  Under those preconditions every derivable equality between atoms lies within the closure.

Results:

| Program | Baseline | `fixsubst,eqrefute` |
|---|---|---|
| eqbug-1..4 | accepted (wrong), ≈1.4 s | rejected, ≈135 ms |
| assocneg-3 | accepted (wrong), 1.3 s | rejected, 133 ms |
| assocneg-8 | accepted (wrong), 4.4 s | rejected, 484 ms |
| eqbug-5 (valid) | accepted, 140 ms | accepted, 137 ms |
| coercion-derivability-cache (valid) | accepted, 3.9 s | accepted, 3.9 s |

## 2. Equality chains need an equality procedure, not search

Bug #1 also explains why valid equality chains were "fast". The baseline's proofs of them are bogus, with the right conclusion by luck. For `trans-4`, `T0 ~ T4` is "proved" from `T2 ~ T3` and `T3 ~ T4` alone, via the same dropped binding. With `fixsubst`, the genuine BFS over symmetry and transitivity is exponential in the chain length:

| Chain | Baseline (bogus proof) | `fixsubst` (genuine search) |
|---|---|---|
| trans-3 | 731 ms, 30k matches | 745 ms, 30k matches |
| trans-4 | 918 ms, 35k matches | **19.7 s, 640k matches** |
| trans-5 | 1.2 s, 41k matches | **79 s, rejected** (depth cap) |
| assoceq-5, trans-8 | 2.7 s / 1.9 s | timeout (> 120 s) |

**Conclusion.** `fixsubst` alone is correct but makes the equality fragment unusable beyond chains of about 4. Equalities need a decision procedure instead of SLD search with built-in symmetry and transitivity givens, for example congruence closure over the equalities in scope:
- with a ground goal, union-find decides `a ~ b` and produces the proof term from the path;
- with open variables, unify the goal against class representatives.

This is a design change: the proof terms change, and the depth cap no longer applies to equalities. It should land together with `fixsubst`. `eqrefute` above is the "negative" half of that procedure.

## 3. `where T.X == B` at a call site is never discharged (incomplete, then explodes)

**Repro.** `soundness/assoc-eq-call-incomplete.hylo`, minimized:
```hylo
trait P { type X }
struct A {}
struct B { public memberwise init }
given A is P { type X = B }
fun f2<T where T is P, T.X == B>() {}
public fun main() { f2<A>() }     // valid, but rejected / runs out of memory
```

`let y: A.X = B()` works, so associated-type projection itself is fine. The call `f2<A>()` needs the implicit arguments `(P<A>, ((A::P).X ~ B))`.
- **The defect.** The second requirement is summoned with an *abstract* qualification `A::P`, not the witness found for the first requirement (the given `A is P`). So `X` cannot be reduced to `B`.
- **The blow-up.** The resolver then searches the equality built-ins until the cap:
  - caps 5–7: 7.3k → 23k → 82k matches, "no coercion" error;
  - default cap 10: runs out of memory, after more than 4.8 GB (review t08/t24).

**Fix (not implemented).**
- Resolve requirements in order, and substitute each witness into the later requirements before summoning them. Then `(A::P).X` becomes `(A::<given A is P>).X = B`.
- Alternatively, normalize associated types with concrete qualifications through the conformance before an equality goal is searched.

`eqrefute` does not apply, because the goal side `(A::P).X` is unifiable with nothing in scope.

## 4. Cyclic substitutions crash the compiler (no occurs check)

**Repro.** `soundness/cyclic-query-segfault.hylo` (review t25). Givens `<U> U is P<U>` and `<T where T is P<S<T>>> T is R`, and a query `needR()` with an inferred `T`.
- Unifying the premise `P<?t, S<?t>>` with `P<U, U>` binds `U := ?t`, then `?t := S<?t>`.
- `TypeStore.reify` then recurses forever: SIGSEGV, exit 139.

**Fix (`occurs`).** An occurs check in the variable cases of `TypeStore.unifiable`: binding a variable to a type that contains it fails to unify.
- The program is then rejected ("no coercion …") in 31 ms.
- Identical on all 192 tests.
- Cost: a walk of the bound type, only when it has variables.

## 5. Order-dependent memoization across cycle cuts

**Mechanism** (review names-1/names-2). While a declaration `X` is being typed (`declarationsOnStack`), evaluating something that refers back to `X` reports "refers to itself" and yields `.error`. The `.error`, or a lookup that silently skipped an extension being typed, is then **memoized permanently** by the enclosing computation. Whichever lookup first forces an extendee or a given's type therefore decides the result.

Examples:
- `type X = A.Foo; extension X {…}` reports a spurious cycle (n01);
- swapping two extensions turns acceptance into rejection (n04 vs v2_swapped).

**Fix attempt (`cyclecut`): transactional speculation.**
- Member lookup needs an extension's extendee that is not yet memoized, or resolution needs a given's type that is not yet memoized. The typer:
  1. snapshots `(program, cache)`, which are value types, so the snapshot is O(1);
  2. evaluates;
  3. if a cycle was cut meanwhile (counted at the four "refers to itself" sites), restores the snapshot, which removes every memo write, type insertion and diagnostic, and treats the extension or given as not applicable for this query.
- The real evaluation happens later, outside the cycle.

Results on the 47 programs of `review/names/**` (diagnostic counts, baseline → `cyclecut`):

| Fixed (spurious errors removed) | Unchanged order-dependent | Regressions |
|---|---|---|
| n01 2→0, n05 2→0, n17 3→2, v01 2→0, v06 2→0, v08 2→0 | t01, v2_swapped, v6_summon_swapped, n17 (one error left) | none |

Identical on all 192 tests.

**A stronger variant (`cyclecut,cyclecutstack`)** also treats "skipped an extension that was already being typed when the transaction started" as a cut.
- It fixes t01 and v2_swapped.
- It newly rejects n02, n03, n04, t03, v1, v3, v4 and v5, which the baseline accepts.

Those programs have **genuinely mutually dependent extendees**: E2's extendee needs a member of E1, and E1's extendee lookup must decide whether E2 applies. Any local rule picks *some* evaluation order, so the outcome stays order-dependent. Removing the dependence requires a language decision:
- (a) extendees are resolved in a pre-pass that does not consider extension members (simple, predictable, rejects some programs);
- (b) a fixpoint over extendee bindings (accepts the most, costs iterations).

`cyclecutstack` is kept only as a documented experiment.

`cyclecut` composes with `memberskip`: same results, since `memberskip` never skips an extension whose extendee is unmemoized.

---

## Also confirmed

- **`negative/illegal-enum-case.hylo` crashes the typer** (force unwrap in `declaredType(of: EnumCaseDeclaration)`, Typer.swift ≈1367). It is reachable only from `tc-bench`, because the driver stops after scoping errors. Fix: return `.error` when the case has no enclosing enum.

## Recommendations

1. Land `occurs`: a crash fix with no visible change.
2. Land `fixsubst` **together with** an equality procedure: congruence closure, with `eqrefute` as its first half. `fixsubst` alone makes equality chains longer than 4 unusable.
3. Fix requirement discharge at call sites (#3) by substituting earlier witnesses into later requirements.
4. Land `cyclecut` as an improvement. Decide the language rule for mutually dependent extendees (#5) before going further.
5. Report #1, #3 and #4 upstream with the repros in `soundness/`.
