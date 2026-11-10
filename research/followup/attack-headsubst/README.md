# Attack on `headsubst`

## What was asked

Find programs on which `headsubst` is wrong. The mechanism: in a call, an associated type of a requirement of the callee that occurs in its parameters or result (`fun pick<T where T is P>(t: T) -> T.X`) is replaced by a type variable, which is equated with the associated type selected through the witness found for that requirement once the callee has been elaborated. It also adds a unification rule (two associated types selected through the same declared witness unify if the types of the witness do), instantiates the members of extensions with the witnesses of the extension's requirements, and decides a premise of a given or of an extension from a projection in its head.

Nothing was built and `/home/user/hylo-impl` was only read.

## What was done

- 164 programs in `p/`. Each starts with a comment that says what it tests and what the correct verdict is. A name ending in `c`, `-ctl` or `d` is a control that differs from its neighbour in one place; `n`/`-neg` is the invalid twin of a valid program.
- Every program was run with binary `eq34-6718f1de213f` (source commit `784fe85`) under `base`, `FULL`, `NEW`, `NEW+selfcheck`, NEW without `headsubst` and FULL with `headsubst`. `RESULTS.md` has one row per program and one column per configuration; `results.jsonl` has every diagnostic and the `headsubst.*` counters.
- The task named binary `eq22`; `headsubst` was corrected twice after it, so the newer binaries were used. Every program was run again under FULL, NEW and `NEW+selfcheck` on `eq37-be83f527b895`, the latest binary: all verdicts and numbers of diagnostics are those of `eq34`. The programs `a*` and `b*` were also run on `eq30-ae138265e872` (commit `4da70d3`), the last binary before the corrections; the difference is in the last section. `results.jsonl` holds the runs on all of these binaries (field `bin`).
- Declaration order: 198 permutations of the top-level declarations of 22 programs under NEW (`permute.py`, `permute.jsonl`). Where-clause and type-parameter order: `p/i07-where-permutation-{a,b,c,d}`, `p/n03-caller-where-{a,b,c,d}`, `p/f04-infer-order-{a,b}`.
- The 114 positive and 78 negative tests of `Tests/CompilerTests` and the 14 tests of `../headsubst/tests` under FULL, NEW and NEW without `headsubst` on `eq34` (`screen.py`, `screen.jsonl`).
- To attribute a finding, its programs were also run under NEW without `assocsubst`, without `premsubst` and without `abstractstrict`.
- For each value-level finding, the witnesses chosen at each call were read in a `trace` run.

## Findings

| # | Kind | Program (control) | base | FULL | NEW | NEW − `headsubst` | FULL + `headsubst` |
|---|---|---|---|---|---|---|---|
| 1 | UNSOUND | `p/f02-refinement-value.hylo` (`p/f01c…`), `p/s01v-trait-given-value.hylo` (`p/s01c…`), `p/t02-conditional-over-refinement.hylo` (`p/t02c…`), `p/i04…`, `p/m01…` | reject | reject | **accept** | reject | reject |
| 1 | UNSOUND, and FULL rejects for the right reason | `p/s02-extension-member-refinement.hylo` (`p/s02c…`) | reject | reject | **accept** | reject | reject |
| 2 | UNSOUND | `p/k07-function-value-shadow.hylo` (`p/k07c…`, `p/k04d…`), `p/c01-leak-function-value.hylo` (`p/c01c…`), `p/c03…` | reject | reject | **accept** | reject | **accept** |
| 2 | UNSOUND, also in base | `p/c04-leak-function-last.hylo` | accept | accept | accept | accept | accept |
| 3 | REGRESSION | `p/r01-regress-recursion-equality.hylo` (`p/r01c…`, `p/r01d…`), `p/r01b…`, `p/r02…`, `p/r02b…` | accept | accept | **reject** | accept | **reject** |
| 3 | REGRESSION against FULL | `p/r03-regress-recursion-inferred.hylo` | reject | accept | **reject** | reject | **reject** |
| 4 | INCOMPLETE | `p/d01-equality-nested-arg.hylo` (`p/d01c…`), `p/n05-bare-param-variable-arg.hylo` (`p/n05b…`), `p/d03…`, `p/n04…`, `p/r04-part1`, `p/r04-part2` (`p/r04-part3`, `-part4`) | reject | reject | reject | reject | reject |
| 5 | INCOMPLETE | `p/f03-refinement-callee.hylo`, `p/i01c-nested-given-one-witness.hylo`, `p/i03…`, `p/m02-refinement-valid-uses.hylo` | reject | reject | reject | reject | reject |
| 6 | INCOMPLETE | `p/e09-witness-with-variable.hylo`, `p/h02-extension-head-concrete.hylo`, `p/h03…` | reject | reject | reject | reject | reject |
| 7 | QUESTION | `p/f05b-infer-shadow-value.hylo`, `p/f05-infer-shadow.hylo`, `p/e03…` (`p/f05c…`) | reject | reject | accept / reject | reject | accept / reject |

No `[selfcheck] VIOLATION`, no crash, no timeout, and no verdict that depends on the order of declarations, of requirements or of type parameters was found.

### 1. A projection through a conformance declared in a trait becomes the error type, which is equal to itself

```hylo
trait P { type X; fun get() -> X; fun put(x: X) }
trait R refines P {}
fun pick<T where T is P>(t: T) -> T.X { t.get() }
fun take<T where T is P>(t: T, x: T.X) { t.put(x) }
fun g<U, V where U is R, V is R>(u: U, v: V) { take(u, pick(v)) }      // p/f01
```

`pick(v)` is a `V.X` and `take(u, _)` expects a `U.X`; nothing relates `U` and `V`. NEW accepts. `p/f02-refinement-value.hylo` adds `A is R` with `X = S0`, `B is R` with `X = S1` and `main` calling `g(A(), B())`: the `S1` returned by `B.get` is given to `A.put(x: S0)`. The control with `U is P, V is P` (`p/f01c`) is rejected with "cannot pass value of type '(V::P).X' to parameter '(U::P).X'".

The same happens whenever the witness of the callee's requirement is derived from a conformance that a trait declares:

- a given in the body of a trait, which is how an associated type is constrained: `trait P { type X; given X is Q … }`, callee `far<Z where Z is Q>(z: Z) -> Z.Y`, caller `g<U, V where U is P, V is P>` with `feed(u.get(), far(v.get()))` (`p/s01`, complete program `p/s01v`: an `S1` reaches `M0.eat(y: S0)`);
- members of `extension <T where T is P> T` used on `U is R`: `u.two(v.one())` (`p/s02`). base and FULL reject this program with the right message, so NEW is less sound than FULL here;
- a conditional conformance over a refinement, with concrete types only: `given <T where T is R> => Box<T> is P { type X = T.X … }`, `take(Box<A>(…), pick(Box<B>(…)))` (`p/t02`);
- the projection nested in a type constructor (`p/i04`), and inside the refinement itself (`p/m01`).

Valid programs of the same shape are accepted for the same wrong reason (`p/f01d`), or rejected with a message about the type `#!` when the other side is a concrete type or a projection written in the source (`p/m02`: `let x: U.X = pick(u)` gives "no coercion from '#!' to '(U::P).X'"; `p/g01`).

Cause, read in the source. `Solver.resolve(_:elaboratedBy:at:)` substitutes the witness into the projection and calls `Typer.normalizingProjections`. For a witness whose declaration is a conformance without members (the conformance that `trait R refines P` or `given X is Q` declares), `typeOfImplementation(satisfying:in:)` under `assocsubst` returns the same projection ("the associated type is the one selected through this very witness"). `normalizingProjections` replaces the projection by itself, never reaches a fixed point, and after 8 rounds returns `.error` (counter `premsubst.normalized` = 8 per projection in these programs). The variable is then equated with `.error` without a diagnostic. Two variables resolved this way are the same type; a variable and a concrete type are not, which is why only projection-against-projection is accepted. Both flags are needed: FULL + `headsubst` and NEW without `assocsubst` reject `p/f01` and `p/s02` with the right message, because without `assocsubst` the projection is left as it is. NEW without `premsubst` or without `abstractstrict` accepts them.

Two things are wrong independently: the projection through such a witness should be left alone (it is already normal), and `resolve` should never produce `.error` silently (the 8-round limit and `headsubst.unexpectedElaboration` do the same).

### 2. A generic function used as a value keeps the projection through its own requirement

```hylo
fun call3<U, V>(f: [](let U, let V, let Bool) -> Void, u: U, v: V) { f(u, v, false) }
fun rec<T where T is P>(t: T, x: T.X, again: Bool) {
  t.put(x)
  if again {
    given T is P { type X = S1 … }          // shadows the requirement in this block
    call3(rec, t, x)                         // p/k07
  }
}
public fun main() { rec(A(), S0(), true) }  // A is P with X = S0
```

The argument `rec` is coerced to `[](let T, let (T::r).X, let Bool) -> Void`, where `r` is the requirement of `rec`, and elaborated with the witness of `T is P` found in the block: the local conformance (trace: `rec<T>($<ConformanceDeclaration at …:21.5>)`, `call3<T, (T::P).X>`). Its second parameter is really an `S1`. `call3` passes it the caller's `x`, a `T.X` of the requirement, an `S0` in `main`, which reaches the local `put(x: S1)`. base, FULL and NEW without `headsubst` reject; NEW and FULL + `headsubst` accept. The control with a direct call `rec(t, x, false)` (`p/k04d`) is rejected by NEW ("cannot pass value of type '(T::P).X' to parameter 'X'"), and the control without the local conformance (`p/k07c`) is accepted.

`p/c01` and `p/c03` are the same defect with two conformances of a concrete type (`A is P` with `X = S0` outside, `X = S1` in a nested block) and a function `io<T where T is P>(t: T, x: Opt<T.X>) -> T.X` passed twice to `apply2`: the result of the first use has the type `(A::r).X`, which cannot be written but is inferred for `v`, and is accepted by the second use.

Cause. The abstraction of `Solver.solve(call:)` only covers the callee of a call. A generic function coerced to a function type goes through `Typer.coerced` with an `.identity` witness; the opened type `(%T::r).X` is matched with the expected type by the new rule of `TypeStore.unifiable(_: AssociatedType, …)` (`sameReference`), and the result is a type that mentions `r` at a type argument, for which `r` stands for whatever witness the elaboration picked. The rule assumes that such a type never leaves the callee.

The hole is older than `headsubst`: base accepts `p/c04-leak-function-last.hylo`, which is `p/c01` with the function as the last parameter of the higher-order function (the function is then coerced before the type of the other argument is known, and no unification of two projections is needed), and it accepts the inner call of `p/k08-function-value-shadow-last.hylo` (its only diagnostic there is on the call in `main`). `headsubst` makes the defect independent of the parameter order, and it makes the functions concerned callable at all.

### 3. Recursion in a function whose where clause fixes its projection is rejected

```hylo
fun rec<T where T is P, T.X == S1>(t: T, x: T.X) -> T.X { rec<T>(t, S1()) }                      // p/r01
fun rec<T where T is P, T.X == S1>(t: T, b: Box<T.X>, c: Box<S1>) { rec<T>(t, c, c) }           // p/r02b
```

base, FULL and NEW without `headsubst` accept both; NEW and FULL + `headsubst` reject them with "type 'S1' is not compatible with '(T::P).X'". `p/r03` (the second one without `<T>`) is accepted by FULL and rejected by NEW. The controls `p/r01c` (no result) and `p/r01d` (no equality) are accepted.

Cause. The variable standing for `T.X` is bound to `S1` before the callee is elaborated, and `resolve` then states an `EqualityConstraint` between it and `(T::r).X`; that constraint is solved by unification alone, so the equality `T.X == S1` of the where clause is not used. An argument coercion would have used it. The variable is bound early in two ways:

- the projection is nested in the parameter type (`Box<T.X>`): `Solver.solve(coercion:)` postpones a coercion only if its right-hand side is the variable itself;
- the projection is also the result: the equality between the result and the output of the call assigns the projection's variable to the output variable, the parameter type becomes that other variable, which is not in `unresolvedProjections`, and the argument coercion is solved at once.

### 4. The same cause rejects valid calls from a generic caller (incomplete)

`fun g<U where U is P, U.X == S1>(u: U, …)` calling `wrap(u, b)` with `b: Box<S1>` for `Box<T.X>` (`p/d01`), a lambda `[](let S1) -> Void` for `[](let T.X) -> Void` (`p/d03`), or `wantS1(take(u, s))` where `take` returns `T.X` (`p/n05`, `p/n04`, `p/r04-part2`). The controls with a bare projection parameter and no projection in the result are accepted (`p/d01c`, `p/n05b`), so the verdict depends on where the projection occurs in the callee's signature. FULL rejects all of these, so this is not a regression.

### 5. Projections through a refinement or a trait's given are not handled (incomplete)

- In the callee's own signature: `fun pickR<T where T is R>(t: T) -> T.X` (`p/f03`), `fun far<T where T is P>(t: T) -> T.X.Y` with `given X is Q` in `P` (`p/i01c`, `p/i03`). The callee cannot be coerced ("no coercion from '<T> R<T> ==> …'"): the unification rule for two selections through the same witness only applies when the witness is a plain reference to a requirement, not when it is derived from one.
- In the caller: every valid use is rejected (`p/m02`), by the defect of finding 1.
- Members of an extension of the types conforming to a refinement, or to a trait with a given on its associated type, cannot be used with their own associated type (`p/u02`, `p/u03`, `p/u04`). Every configuration rejects these; in the existing checker `T.X` is already the error type when `T` conforms through a refinement, without a diagnostic at the declaration.

### 6. Other valid programs that are still rejected

- The witness has an open variable when the callee is elaborated: `wantS0(pick(none()))` with `none<T>() -> Box0<T>` and `Box0<T>.X = T` (`p/e09`). The projection is equated with `(Box0<%Z>::P).X`, which is not normalised when `%Z` becomes known.
- An extension or a conformance whose head mentions the projection of its own premise (`extension <T where T is P> Wrap<T, T.X>`) is found for `Wrap<U, U.X>` in a generic context but not for `Wrap<A, S0>` (`p/h02`, `p/h03`; the generic cases of `p/h01` are right).

### 7. A type argument that occurs only under the projection is taken from the nearest conformance (question)

`fun only<T where T is P>(x: T.X)`. With a global `A is P` (`X = S0`) and a local `B is P` (`X = S1`), `only(S1())` is accepted with `T = B` (`p/f05b`) and `only(S0())` is rejected (`p/f05`), although `T = A` is its only solution. With one conformance in scope `only(S0())` is accepted (`p/e03`); with two in the same scope it is rejected in both orders (`p/f04-infer-order-a`, `-b`). The existing checker infers the type argument of `fun none<T where T is P>()` the same way (`p/f05c`), so this is the behaviour of resolution, not of `headsubst`; whether a call whose type argument is not determined by its arguments should be accepted is a language question.

## What held

- The call itself: concrete and generic callers, two requirements, chains, the result as a receiver, as an argument, in a field, in a branch, in a lambda; lambdas whose parameter is inferred from the projection; literals; `inout`, `sink` and defaulted parameters; bundles and subscripts; static methods, methods of generic structs, initialisers, generic methods of conditional extensions and default methods of traits; explicit type arguments stored in a variable; a requirement on a trait with a parameter; a requirement satisfied through an equality, through a conditional conformance (to depth 8) and through the conformance being defined (`a01`, `a04`, `a07`, `a08`, `b01`–`b04`, `b06`, `b09`–`b11`, `e01`, `e02`, `e08`, `e10`–`e12`, `h07`–`h09`, `i06`, `j01`–`j05`, `k01`, `k05`, `k06`, `m05`–`m07`, `n01`, `n02`, each with invalid lines that are rejected).
- Two witnesses of one requirement: two type parameters with and without `U == V`, mutual recursion with exchanged arguments, recursion at another type, a nested block or a lambda that shadows a conformance, a local conformance of the function's own parameter (`d04`–`d08`, `c01b`, `k04d`, `t01`): every crossing by a call is rejected.
- Extension heads and conformance heads that mention the projection of their premise, in a generic context (`h01`, `h03`, `h04`), and members of conditional extensions (`h05`, `h05n`, `h06`).
- Overloads: a candidate with a projection next to one without, overloaded arguments (`e04`–`e06`). The number of forks of a chain of overloaded calls is the same with and without a projection (`m04*` against `m09*`: `solver.forks` is 30, 510, 2046 at depth 4, 8, 10 in both; `python3 ../tcrun.py eq34-6718f1de213f "FULL;NEW" p/m04*.hylo p/m09*.hylo --counters solver.forks`). A chain of 24 calls without overloads abstracts and resolves 24 projections (`m03`).
- Order: no program has two verdicts in the permutations, and the where-clause and type-parameter variants agree.
- Self-check: no violation. No crash or timeout. The counter `headsubst.unexpectedElaboration` is 0 in every run.
- The compiler's positive and negative tests have the same verdict and the same number of diagnostics under FULL, NEW and NEW without `headsubst`. The 14 tests of the mechanism have their expected verdict under NEW.
- Diagnostics are sometimes misleading although the verdict is right: when the variable of a projection is bound by an argument first, the message names the argument's type as the type of the result (`p/h07` line 26, `p/m06`: "cannot pass value of type 'Bool' to parameter 'Int'" for a call whose result is an `Int`).

## What could not be tested

- The branch of `resolve` for an elaboration whose number of witnesses differs from the number of requirements: no program reached it.
- A generic struct or alias with a requirement and a field or body of projection type: the parser rejects the where clause and the context bound on them (`p/k02`, `p/k03`).
- A generic requirement of a trait implemented in a conformance: the existing checker reports "no implementation" (`p/b05`); only default implementations were tested (`p/h07`).
- A function value of a function type written in the source with an explicit type application (`let f: … = take<A>`): rejected by every configuration (`p/b07`).
- Run-time behaviour: the findings are stated from the types and from the witnesses in the trace; nothing was executed.
- Cost: only counters were compared; the machine was shared and no time is reported.

## Defects of the binary `eq30` that `eq31` no longer has

`eq30-ae138265e872` (commit `4da70d3`) accepts `p/a02`, `p/a03`, `p/a05`, `p/a06`: an argument `Box<S1>`, or a lambda taking or returning an `S1`, for a parameter mentioning `A.X` = `S0`. The equality that `resolve` schedules failed without a diagnostic because it was not a subgoal of any goal. It also rejects every valid call of a generic method or initialiser with a projection (`p/b01`, `p/b03`), because the binders were dropped from the type of a member. Both are corrected in commit `c60989c`; the table at the end of `RESULTS.md` lists the programs whose verdict changed.

## Files

| File | Content |
|---|---|
| `p/*.hylo` | the programs |
| `run.py`, `results.jsonl` | runner (restartable, one process at a time) and raw results; `python3 run.py p/k07-function-value-shadow.hylo` prints one line per configuration |
| `show.py` | prints every diagnostic recorded for a program |
| `tabulate.py`, `RESULTS.md` | results table |
| `permute.py`, `permute.jsonl`, `perm/` | permutations of top-level declarations under NEW |
| `screen.py`, `screen.jsonl` | the compiler tests and the mechanism's tests under FULL, NEW, NEW without `headsubst` |
