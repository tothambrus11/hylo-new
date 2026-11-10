# Attack on `premsubst`

## What was asked

`premsubst` proves a requirement that mentions another requirement of the same clause (`where T is P, T.X is Q`) after that other requirement, with the witness found for it substituted into its type (design: `../design-engine/DESIGN.md`, sections 3 and 4). The task was to find programs on which it is wrong: ill-typed programs that it accepts, well-typed programs that the previous configuration accepts and it rejects, verdicts that depend on an order that should not matter, self-check violations, and well-typed programs of the intended shape that are still rejected.

## What was done

- 141 attack programs in `p/`. Each starts with a comment that says what it tests and what the correct verdict is. Names ending in `c`, `-ctl`, `v`, `d`, `f`, `n` after the number are controls that differ from the finding in one place.
- Every program was run with binary `eq22-554540c3a507` under FULL, NEW, NEW + `selfcheck`, NEW without `premsubst`, and FULL + `premsubst`; and under NEW without `eqeager`, without `absmodel`, and without `index` and `eqindex`, to see whether a result-preserving flag changes a verdict when premises are deferred. Other flags were removed where a finding had to be attributed (`assocsubst`, `headsubst`, `abstractstrict`).
- For every finding about a value reaching the wrong type, the witnesses passed at the call were read from a `trace` run. Nothing was executed: the type checker binary does not lower programs, so "runs the `show` of C on a B" is what the elaborated call says, not an observed run.
- 48 permutations of where clauses (`wperm.py`, three clauses, every order in which a requirement follows the ones it mentions), 96 permutations of top-level declarations of 8 programs (`permute.py`), and 33 clauses called with the same type for two parameters (`sametype.py`).
- 138 existing programs with a requirement on a projection (the 76 research test programs, `../design-engine/tests/s1-*`, `../headsubst/tests`, two compiler tests) under FULL, NEW and NEW without `premsubst` (`corpus.py`).
- The ten main findings were run once more on `eq28-0b06496b23f3`, the most recent binary in `research/exp/bin`: same verdicts.

`/home/user/hylo-impl` was only read. Its working tree has uncommitted changes in `Typer.swift`, `Solver.swift` and `TypeStore.swift`; the code cited below is the committed version (`git show HEAD:…`), which is what the binaries contain as far as the flags and counters show.

A review of the design by a second engineer exists (`../design-engine/DESIGN.md`, section 11, with programs `../design-engine/tests/s1-attack-*`). Findings 1, 6, 7a and 7b below were already recorded there, with corrections designed but not built. They are confirmed here on NEW, and what this work adds to each is said. Findings 2, 3, 4, 5 and 8 are not in that review.

## Findings

| # | Kind | Program (controls) | FULL | NEW | NEW − `premsubst` | Recorded before |
|---|---|---|---|---|---|---|
| 1 | UNSOUND | `p/c09b-a7-nested-where.hylo` (`c09f`, `c09c`); with values `p/c08-a7-alias-capture-value.hylo` (`c08c`, `c08d`, `c08v`); `c09`, `c10`, `c09d` | reject | **accept** | reject | yes (capture), three points added |
| 2 | UNSOUND | `p/e07-premise-dropped-closed.hylo` (`e07c`, `e07d`), `p/e08-premise-dropped-where.hylo`, `p/e06-premise-dropped-value.hylo` | reject | **accept** | reject | no |
| 3 | UNSOUND | `p/q01-chain-head-two-witnesses.hylo` (`q01c`, `q02`) | reject | **accept** | reject | no |
| 4 | REGRESSION | `p/j05-recursion-shadow-tie.hylo` (`j05b`, `j04`), `p/j01-probe-local-given-block.hylo`, `p/j02-probe-nested-function.hylo` | accept | **reject** | accept | no |
| 5 | INCOMPLETE and ORDER | `p/u02-same-type-twice.hylo` (`u02c`, `u02n`), `p/u02g-same-type-twice-generic.hylo`; order pair `p/u01a-order-same-type-accept.hylo` / `p/u01b-order-same-type-reject.hylo` | reject | **reject** (`u01a`: accept) | reject | no |
| 6 | ORDER | `p/h04a-order-bound.hylo` / `p/h04b-order-bound-swapped.hylo` | reject | accept / **reject** | reject | yes |
| 7 | INCOMPLETE | a: `p/n04-method-own-parameter.hylo`, `n05`, `n02`; b: `p/a08-mentioned-by-coercion.hylo`, `a08b`; c: `p/e05-generic-conformance-projection.hylo`, `e05b`, `e07d`; d: `p/t01-open-witness.hylo` (`t01c`) | reject | **reject** | reject | a, b yes; c, d no |
| 8 | COST | `p/s03-cost-ambiguous-chain-4x9.hylo`, `p/s01-cost-ambiguous-chain.hylo` (`s01c`) | reject, 46 subgoals | reject, 9,886 and 87,436 subgoals (budget) | reject | partly |
| 9 | QUESTION | `p/b02c-shadowed-requirement-result-ctl.hylo` (`b02`) | reject | accept | reject | yes (question 4) |

No `[selfcheck] VIOLATION` line was printed in 1,157 runs of `p/` (141 of them with `selfcheck`), and `premsubst.stuck` was never positive there, in the 414 runs of the corpus or in the 177 runs of permutations. No crash. One timeout: `s03` under NEW + `selfcheck` (finding 8).

### 1. A type argument that mentions the callee's own requirement is rewritten to another witness (UNSOUND)

```hylo
trait P { type X }
trait Q {}
trait R {}
fun f<T, V where T is P, T.X is Q, V is R>() {
  type TX = T.X
  fun inner<where T is P, T.X is Q, T.X is R>() {
    f<T, TX>()                                        // p/c09b
  }
}
```

`TX` is `T.X` selected through f's requirement `T is P`. `inner` has its own requirement `T is P`, a second witness, and by `Tests/CompilerTests/negative/associated-type-inequality.hylo` the `X` of two witnesses are different types. The call `f<T, TX>()` needs `TX is R`. Nothing states it: f knows `TX is Q`, and inner's `T.X is R` is about the `X` of inner's requirement. FULL rejects. NEW accepts, with the elaboration `f<T, TX>($v)($12)($19)` where `$v`, `$12`, `$19` are inner's three requirements: the witness passed for `V is R` at `V = TX` proves `R` for another type.

Controls: the same call to a copy `k` of `f` (`p/c09f`) is rejected by NEW, which shows that inner's facts are not facts about `TX`; the call outside any nearer witness (`p/c09c`) is rejected.

`p/c08-a7-alias-capture-value.hylo` is the same with values and a nearer local conformance (`given T is P { type X = C }`, `C is Q`, `C is R`): from `main`, `T = A`, `A.X = B`, and the inner call is elaborated as `f<T, TX>(local conformance)(C is Q)(C is R)`, so `v.show()` in the callee uses the `show` of `C` on a value of type `B`. (Elaboration read from `./tc.sh NEW+trace p/c08-a7-alias-capture-value.hylo`.) NEW without `premsubst` rejects; FULL + `premsubst` accepts.

Cause: `Typer.formThread`, the block "Bind the usings after `h` that refer to it to the premise just assumed". It replaces every witness equal to `(.reference(binder), type: h)` in the later usings. In a call of the function to itself with explicit type arguments, the type arguments have already been substituted into the usings, and a reference that the caller wrote to the function's own requirement is the same witness expression as the clause's own reference. The released requirement is then about whichever witness discharges the premise, and every witness is tried.

This is the capture that the design review recorded (`s1-attack-capture-recursion.hylo`, DESIGN 11.2 item 1); its correction is not in any binary. Three points are added here:

- It does not need a conformance at all: the requirement of a nested function is enough (`c09b`).
- It does not need a dependent requirement. In `p/c09d-a7-head-binder.hylo` the clause is `where T is P, V is R` and only the result type mentions `T.X`. `Typer.introduce(types:usings:into:)` records the binder for `headsubst`, and `formThread` rewrites the later usings whenever a binder is recorded. NEW accepts; NEW without `premsubst` and NEW without `headsubst` both reject. So the capture reaches every generic function with two requirements whose signature mentions an associated type.
- It needs an explicit type argument. With an inferred one (`p/c07-a7-block-capture-value.hylo`) the usings are rewritten while the parameter is still a variable, and the program is correctly rejected.

### 2. The associated type of a conditional conformance is read without the witnesses of its premises (UNSOUND)

```hylo
given A is P { type X = B … }
given <T where T is P> => Box<T> is P { type X = T.X
  fun get() -> T.X { self.t.get() } }
type BA = Box<A>
type BX = BA.X                          // Box<A>.X through the declared conformance of A: B
given BX is Q { fun use() {} }
fun f<T where T is P, T.X is Q>(t: T) { t.get().use() }
fun h(b: Box<A>) {
  if true {
    given A is P { type X = C … }       // nearer conformance of A; C is not Q
    f<Box<A>>(b)                        // p/e07
  }
}
```

In `h`, `Box<A> is P` is built on the local conformance of `A`, so the `X` of `Box<A>` is `C`, and `f<Box<A>>` needs `C is Q`, which no declaration states. FULL rejects (it cannot call `f` at all). NEW accepts with the elaboration `f<Box<A>>(given15<A>(local conformance))(given BX is Q)`: `get` returns a `C` and `use` is the one declared for `Box<A>.X` of the declared conformance. `p/e08-premise-dropped-where.hylo` has no local conformance: `h<where A is P>` calls `f<Box<A>>(b)`, the conformance of `Box<A>` is built on h's requirement, about whose `X` nothing is known, and NEW accepts with the same global given. `p/e06` states the fact as a requirement of `h`.

Controls: `p/e07c` (no nearer conformance) is well typed and accepted. `p/e07d` replaces `given BX is Q` by `given B is Q` and is rejected by NEW, which shows what the checker takes `Box<A>.X` to be: neither `B` nor `C`, but one opaque type.

Cause: `Typer.normalizingProjections` calls `typeOfImplementation(satisfying:in:)` for the projection `(Box<A>::g<A>(w)).X` of a released requirement. The `assocsubst` branch of that function collects the type arguments on the spine of the witness and ignores the term arguments, so the result is `(A::r).X`, where `r` is the conformance declaration's own requirement, whatever `w` is. All conformances of `Box<A>` share one `X`. The flags responsible are `premsubst` and `assocsubst` together: NEW without either rejects `e07`; NEW without `headsubst` accepts. The hole itself is the one reported as "U1 not closed" in `../attack-assoc/README.md`; what is new is that `premsubst` trusts it to decide a requirement, on a call that FULL rejects. The uncommitted working tree has a function `instantiated(_:declaredIn:through:)` that looks like the correction; it is in no binary.

The same reading makes valid programs fail: finding 7c.

### 3. A result type selected through a dependent requirement is the same type for every witness (UNSOUND)

```hylo
given A is P { type X = B … }
given B is P { type X = C0 … }
fun f<T where T is P, T.X is P>(t: T) -> T.X.X { t.get().get() }
fun h(a: A) {
  var v = f<A>(a)                        // a C0
  if true {
    given B is P { type X = C1 … }
    v = f<A>(a)                          // a C1: p/q01
  }
}
```

The two calls are discharged with different witnesses of `B is P` (trace: the declared conformance, then the local one). The second result is a `C1` and is assigned to a variable that holds a `C0`. FULL rejects both calls. NEW accepts. `p/q02-head-two-witnesses.hylo`, where the result is `T.X` through the first requirement, is correctly rejected by NEW ("no coercion from 'X' to 'X'").

Cause: with `headsubst`, `Solver.resolve(_:elaboratedBy:at:)` builds the binding of the second requirement with the type `P<(A::u0).X>`, in which the first requirement is not yet replaced; `Typer.projection` rewrites inner witnesses first, so the reference to the second requirement no longer equals its binding and stays the callee's own declaration. The result type is `((…).X::u1).X` for every call. Without `headsubst` (NEW − `headsubst`) the program is accepted too, because the head is not bound at all; it is `premsubst` that makes the call acceptable in the first place (NEW − `premsubst` rejects). `p/l01-chain-result.hylo` and `p/l02-chain-result-generic.hylo` are the valid programs that the same defect rejects. Under FULL + `premsubst` even `q02` is accepted: `premsubst` without `headsubst` is unsound for every result type that mentions an associated type. The working tree replaces this code (`Typer.instantiating`, "the replacement is made in order").

### 4. A recursive call in the scope of a nearer conformance becomes ambiguous (REGRESSION)

```hylo
given C is Q { fun use() {} }
fun f<T where T is P, T.X is Q>(t: T) {
  t.get().use()
  if true {
    given T is P { type X = C … }
    f<T>(t)                              // p/j05
  }
}
```

Well typed in two consistent ways: the local conformance with `C is Q`, or f's own two requirements. FULL accepts, NEW rejects ("no coercion from '(P<T>, Q<(T::P).X>) ==> …'"); NEW without `premsubst` accepts, FULL + `premsubst` rejects. The trace of NEW shows `3 layers, 2 done, 2 minimal`: both derivations have penalty 2 (nearest conformance 0 + module-level given 2; requirement 1 + requirement 1). `p/j05b` declares `C is Q` in the block and is accepted; `p/j01` and `p/j02` are the same program without values and with a nested function.

FULL's acceptance is not a correct elaboration either: its trace shows `f<T>(local conformance)(f's requirement T.X is Q)`, the conformance of one witness paired with a fact about the `X` of another. `p/j04-recursion-shadow-value.hylo` (C is not Q) is elaborated that way by FULL and correctly by NEW (`f<T>($l)($s)`, f's own two requirements). So for free functions `premsubst` repairs a wrong pairing of the existing checker, and the price is this ambiguity. For methods the wrong pairing remains under NEW, because binders are dropped (finding 7a): `p/n07-method-recursion-shadow.hylo` is elaborated by NEW as `self.m<T>(local conformance)(m's requirement)`.

Cause: derivations are ranked by the sum of the penalties of all steps (`takeSummonResults`), so a nearer witness for the first requirement can be offset by a farther one for the second. Whether the first requirement should choose its witness alone is question 4 of the design.

### 5. A function over two types cannot be called with the same type twice; the verdict depends on the order of the clause (INCOMPLETE, ORDER)

```hylo
given A is P { type X = B }
given B is Q {}
given B is R2 {}
fun f<T, U where T is P, U is P, T.X is Q, U.X is R2, T.X == U.X>() {}
public fun main() { f<A, A>() }          // p/u02: rejected by NEW
```

Well typed. The trace shows `6 layers, 2 done, 2 minimal`, with two results of penalty 5 that are the same witness, `f<A, A>(c)(c)(B is Q)(B is R2)(…)`. `p/u02c` (`f<A, A2>()`, two types with the same `X`) is accepted; `p/u02n` (the same shape with requirements on `T` and `U` themselves) is accepted by every configuration; `p/u02g` (`f<V, V>()` from a generic caller) is rejected like `u02`.

`sametype.py` runs 33 clauses at `f<A, A>()`: 7 are rejected, all with two requirements on different traits and an equality (`y2`, `y3`, `y5`, `y6`, `z3`, `z6`, `z7` in `same-type/`); the same clause with one trait for both (`z1`, `z2`) is accepted. With a fifth requirement the verdict depends on the order: of the 16 orders of `T is P, U is P, T.X == U.X, T.X is Q, W<U.X> is R` called at `f<A, A>()`, 6 are accepted and 10 rejected (`wperm.py`, case `mixed`; `p/u01a` and `p/u01b` differ in the order of the last two requirements). All are 6 or 7 steps, far from the size bound.

Cause: `U is P` has two derivations, the declared conformance and the pending hypothesis `T is P`, which has the same type. In the second, the witness of `U` is a placeholder until `T is P` is discharged, so the requirements that mention `U` are released later (`threadContinuation`, the release loop) and are discharged with another number of pending hypotheses, which changes their penalties. The two sums happen to be equal for some clauses and orders. The two results are equal witnesses but are not recognized as one.

### 6. The order of two dependent requirements decides the verdict near the size bound (ORDER)

`p/h04a-order-bound.hylo` (`where T is P, T.X is Q, S<T.X> is R`) is accepted and `p/h04b` (the last two swapped) is rejected with `summon.depthExhausted=1`: released together, the later requirement is discharged first with the earlier one as a hypothesis, so `B is Q` (5 steps) is proved once or twice. Recorded by the review (`s1-attack-where-order-a/b`); the existing checker has the same phenomenon for independent requirements.

### 7. Well-typed programs of the intended shape that NEW rejects (INCOMPLETE)

a. **Methods and initializers.** `p/n04-method-own-parameter.hylo` (`fun m<T where T is P, T.X is Q>(x: T)` in a struct, called `k.m(u)`), `p/n05` (in an extension), `p/n02` (requirements on the type's parameter). `premsubst.binders=2`, `premsubst.bound=0`: `TypeStore.asBoundMemberFunction` and `asConstructor` rebuild the type with `contextAndHead` and `introduce`, which drop `Implication.binders`. Recorded by the review (`s1-attack-method`).

b. **The first requirement is proved through an equality.** `p/a08-mentioned-by-coercion.hylo`: `g<U, V where U == V, V is P, U.X is Q>() { f<U>() }`. The caller's `U.X` is `(V::r).X` (name resolution removes the coercion), the released requirement is about `(U::coerce(r)).X`. Recorded by the review (`s1-attack-coerced-witness`).

c. **The associated type of a conditional conformance is a projection.** `p/e05-generic-conformance-projection.hylo`: `given <T where T is P> => Box<T> is P { type X = T.X }`, `A.X = B`, `B is Q`, `f<Box<A>>()` is rejected; `p/e05b` from a generic caller; `p/e07d` with values. Same cause as finding 2. Not recorded.

d. **The witness is still open when the requirement is released.** `p/t01-open-witness.hylo`: `given <T, V where V is P, V.X == T> => Wrap<T> is R`, `given <Y> => Box<Y> is P { type X = Y }`, `need<Wrap<B>>()` (V = `Box<B>`). `normalizingProjections` skips a witness that has variables and the projection is never read again. `p/t01c`, where the only conformance is closed, is accepted. Not recorded; an unusual shape.

Also rejected, as the design says: a requirement of a member that mentions a requirement of the enclosing extension (`p/i03`), and a member of a conditional extension whose result is `T.X` (`p/v03`: "no coercion from '(A::P).X' to 'B'").

The three most important are a, b and finding 5: each rejects ordinary generic code.

### 8. A failing call explores every combination of witnesses (COST)

`p/s01-cost-ambiguous-chain.hylo`: a chain of 8 dependent requirements, 3 conformances per level, the last requirement fails. FULL: 46 subgoals. NEW: 9,886 subgoals, 12,697 matches, about 1 s (indicative). `p/s03-cost-ambiguous-chain-4x9.hylo` (4 conformances, 9 levels): NEW stops at the budget after 87,436 subgoals with "implicit resolution is too complex", and NEW + `selfcheck` does not finish in 60 s. With one conformance per level (`p/s01c`) the cost is that of FULL. The review measured failing calls on three programs with one witness per requirement and found a rise of at most 2 subgoals; with several witnesses the rise is exponential in the length of the chain. The programs are artificial.

### 9. A shadowed conformance is selected (QUESTION, recorded)

`p/b02c`: in `g<where A is P>`, `f<A>(a)` is accepted through the module's conformance although g's own requirement is nearer, and its result is a `B`, not g's `A.X` (`p/b02` is rejected for that reason). This is question 4 of the design ("joint reading"); nothing new.

### Outside the mechanism

- `p/t02-trait-nested-given-bound.hylo` (`trait P { type X; given X is Q }`, `g<U where U is P>() { f<U>() }`) is accepted by FULL and rejected by NEW. The flag responsible is `abstractstrict` (FULL + `abstractstrict` rejects, NEW − `abstractstrict` accepts), not `premsubst`.
- `p/v03b-extension-member-result-shadow.hylo`: the result `T.X` of a member of a conditional extension is the same type for two witnesses, and NEW accepts the assignment of a `C` to a variable holding a `B`. The control without a dependent requirement (`p/v03c`) is accepted by FULL too: the hole is in the types of extension members, and `premsubst` only makes extensions with dependent requirements applicable.

## What held

- **Invariant I2.** `premsubst.stuck` stayed 0 on every run: a dependent requirement in the middle (`a02`), written first (`a03`: rejected at the declaration), mentioning two earlier requirements (`a04`, `a05`), chains of 4 and 5 (`a06*`), a mentioned premise discharged by a pending hypothesis (`a07`, `u01*`), by a coercion (`a08`: rejected, but not stuck; also without `eqeager`), by a given with its own dependent requirements, nested three deep (`a09*`), two usings of one type (`a01`: rejected at the declaration; `u01*`, `u02*`: same type after instantiation), three kinds of dependent requirement in one clause (`w01`).
- **Invariants I1 and I3.** No assumed given in the elaborations of ten accepted programs (semantic dump), and the self-check of results never fired.
- **Pairing of witnesses under ambiguity.** With two conformances of which one satisfies the dependent requirement, the elaboration passes that conformance and the matching fact, for a function (`b01`, order of the givens swapped in `b01c`), for two parameters at one type (`v01`), for a conditional given (`v04`), and with a parameter typed by the projection (`p01`, `p01c`). Two that both satisfy it are rejected (`b01b`, `v02`). Crossed facts are rejected (`b03`, `a05b`).
- **Programs that FULL accepts.** Of the 39 corpus programs accepted by FULL, 37 are accepted by NEW and the other two (`v-abs-7`, `eq-unsound-v-abs-7`) are rejected by NEW without `premsubst` as well (`abstractstrict`). The equality workaround never fires under NEW (`eqsolve.premises` is 0 on every NEW run), and the programs it accepted keep their witness (`g06`: f receives g's requirement under both). The five research programs that become accepted because of `premsubst` are well typed.
- **Projections through declared conformances.** A conformance without the definition, defined by itself, or through two conformances that define each other: rejected, no loop, no crash (`e01`, `e02`, `e03`). A generic conformance with `X = T`: correct in both directions (`e04`, `e04b`, `k02`, `m01`, `m02`).
- **A false equality as a hypothesis.** A released equality that does not hold (`C == B`) is a hypothesis while the next requirement is proved; nothing proved under it survives (`r03`, `r03b`: two errors each, in both orders of the calls).
- **Abstract model, index, `eqeager`.** NEW without `absmodel`, without `index` and `eqindex`, and without `eqeager` gives the verdict and the number of errors of NEW on every program of `p/`, except that `s01` reaches the budget without the index.
- **Order.** 96 permutations of the top-level declarations of 8 programs: one verdict each. The 16 orders of a clause with two parameters, two traits and a requirement on both projections, permuted in the callee and in the caller: all accepted.
- **Type arguments.** An alias as type argument (`k01`, `k02`), a context bound (`i01`), a trait with a parameter (`r04`), a blanket conformance that FULL already used (`r05`), a wide requirement that mentions a chain 216 times (`x01`).

## What could not be tested

- Requirements through a refining trait (`p/i02*`): `T.X` is not found through `T is P2` in any configuration, so the mechanism is never reached.
- A local conformance declared directly in the body of the function whose requirement it shadows (`p/c01`, `c02`, `c03`): the function's own signature becomes ambiguous or erroneous in every configuration. The conformance has to be in a nested block. A nested function cannot capture a local value (`p/c04`: "illegal implicit capture"), which is why the capture programs use a local type alias.
- Trait requirements with a generic clause, bundles and subscripts: no program that the existing checker accepts was obtained.
- Runtime behaviour: only the type checker was run.
- Separately compiled modules (binders are not in archives built without the flag).
- The uncommitted working tree of the compiler, which changes the code behind findings 2 and 3.

## Files

| Path | Content |
|---|---|
| `p/` | The 141 attack programs. |
| `RESULTS.md` | One row per program: verdict under the five configurations, first message under NEW, what the program tests. Written by `tabulate.py --md`. |
| `results.jsonl` | Raw results of `p/` (program, content hash, configuration, verdict, messages, counters). |
| `run.py` | Runs programs under configurations; `NEW-flag` is NEW without a flag. Restartable. `tc.sh CONFIG FILE` prints one run in full (`NEW+trace` for the witnesses). |
| `wperm.py`, `wperm/`, `wperm.jsonl` | Where-clause permutations. |
| `permute.py`, `perm/`, `permute.jsonl` | Declaration-order permutations. |
| `sametype.py`, `same-type/`, `sametype.jsonl` | Clauses called with one type for two parameters. |
| `corpus.py`, `corpus.jsonl` | Existing programs under FULL, NEW, NEW without `premsubst`; `corpus.py --report` lists the verdicts that differ. |

To reproduce a finding: `./tc.sh NEW p/c09b-a7-nested-where.hylo` (prints `diagnostics: 0`), `./tc.sh FULL …` (one error), `./tc.sh NEW+trace … | grep penalty` (the witnesses).
