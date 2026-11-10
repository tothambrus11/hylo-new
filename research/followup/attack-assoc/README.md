# Attack on `assocsubst` and `abstractstrict`

## What was asked

Find programs on which two mechanisms added to the Hylo type checker today are wrong:

- `assocsubst`: the associated type read from a generic conformance is instantiated with the type arguments of the witness (fix of U1 in `../reference/JUDGEMENT.md`).
- `abstractstrict`: inside a trait, `Self.X` is only equal to a selection through the witness the trait declares (fix of U2).

The programs were run with binary `eq22-554540c3a507` under `base`, `FULL`, `NEW` and `NEW+selfcheck`, and, to attribute a difference, under `NEW` without one flag and `FULL` with one flag. Nothing was built and `/home/user/hylo-impl` was only read.

## What was done

- 120 attack programs in `p/`, each with a first comment that says what it tests and what the correct verdict is. Programs named `…c` or `…-ctl` are controls that differ in one place; `…n`/`…-neg` are the invalid twins of valid programs and `…v` the valid twins of invalid ones.
- 24 permutations of the where clause and of the parameter list of one program in `p/wo/`.
- 121 permutations of the top-level declarations of 14 programs in `perm/` (`permute.py`).
- The 26 positive tests of `Tests/CompilerTests` that declare a trait, the six tests with associated types, and the programs of `../reference/hand/self` and `../reference/judge/p/u*`, under FULL and NEW.
- For each value-level finding, the witnesses chosen at each call were read in a `trace` run, to make sure the program does what its comment says.

`RESULTS.md` has one row per program of `p/` and one column per configuration. `results.jsonl` has every diagnostic, and also the runs of the compiler tests and of the reference programs, which are not in the table.

## Findings

No `[selfcheck] VIOLATION`, no crash, no timeout, and no verdict that depends on the order of declarations, requirements or parameters was found. The defects are in what is accepted and rejected.

| # | Kind | Program (control) | base | FULL | NEW | Flag responsible |
|---|---|---|---|---|---|---|
| 1 | UNSOUND, new in NEW | `p/e04-extension-twin-value.hylo` (`p/e02c…`, `p/e02d…`) | reject | reject | **accept** | `headsubst` (defeats `abstractstrict`) |
| 2 | UNSOUND, new in NEW | `p/c02-capture-value.hylo`, `p/c01-capture.hylo` (`p/c01c…`) | reject | reject | **accept** | `assocsubst` |
| 3 | UNSOUND, U1 not closed | `p/a04-nested-scopes.hylo` (`p/a04c…`), `p/a03-value-crossing.hylo` | accept | accept | **accept** | `assocsubst` drops the premises of the witness |
| 4 | UNSOUND, U2 not closed | `p/b11-refinement-twin-value.hylo`, `p/b12-launder-refinement.hylo` (`p/b10c…`, `p/b12c…`) | accept | accept | **accept** | `abstractstrict` does not cover refinement |
| 5 | REGRESSION | `p/r22-method-on-assoc-value.hylo`, `p/r01-nested-given.hylo` (`p/r22c…`, `p/r01c…`), `r13`, `r25` | accept | accept | **reject** | `abstractstrict` |
| 6 | REGRESSION | `p/r05-trait-calls-extension.hylo`, `p/r26…`, `p/r11…` | accept | accept | **reject** | `abstractstrict` |
| 7 | UNSOUND, outside the mechanism | `p/a14d-member-alias-value.hylo`, `p/a13-struct-in-conformance.hylo` (`p/a15…`) | accept | accept | **accept** | none (member declarations of generic types) |
| 8 | QUESTION | `p/a05e-param-not-in-head-lets.hylo` (`p/a05f…`), `p/a27…` | reject | reject | **accept** | `assocsubst` |
| 9 | INCOMPLETE | `p/a01-term-witness.hylo`, `p/e05-extension-concrete.hylo`, `p/k07-chain-2.hylo` | reject | reject | reject | - |

### 1. An extension of the conforming types converts `W.X` into `V.X` (new in NEW)

```hylo
trait P { type X
  fun get() -> X
  fun put(x: X) }
extension <T where T is P> T {
  fun one() -> T.X { self.get() }
  fun two(x: T.X) { self.put(x) } }
fun f<V, W where V == W, V is P, W is P>(v: V, w: W) { v.two(w.one()) }     // p/e02
```

`w.one()` is a `W.X` selected through the witness of `W is P`; `v.two` expects a `V.X` selected through the witness of `V is P`. `negative/associated-type-inequality.hylo` says these are different types although `V == W`. base and FULL reject; NEW accepts, and so does FULL + `headsubst`; NEW without `headsubst` rejects. The control with `v.put(w.get())` (`p/e02c`) and the one without `V == W` (`p/e02d`) are rejected by NEW. All 24 permutations of the where clause and of the parameters (`p/wo/`) are accepted.

`p/e04-extension-twin-value.hylo` makes the two witnesses different: `mid<T where T == A, T is P>` declares a local `given A is P { type X = S0 … }` and calls `f<A, T>`; `h` declares a local `given A is P { type X = S1 … }` and calls `mid<A>`. The trace confirms that `f` receives the conformance of line 16 for `V` and the requirement of `mid` for `W`, which `h` discharges with the conformance of line 22. The `S1` returned by one `get` is passed to the `put(x: S0)` of the other. NEW accepts.

Suspected cause: `TypeStore.unifiable(_: AssociatedType, …)`, the `sameReference` rule of `headsubst`. The type of a member of the extension keeps the extension's own requirement as the qualification, with the type arguments substituted: `(V::r).X` and `(W::r).X` with the same `r`. The rule treats one declared requirement as one witness; here it stands for two. This is the conversion that `abstractstrict` was written to remove, reached by another route, so NEW as a whole is less sound than FULL on this point.

### 2. The substitution of the associated type captures a parameter of a generic requirement (new in NEW)

```hylo
trait P { type X
  fun get() -> X
  fun m<U>(u: U, b: Box<U>) -> X {
    let r: S0 = b.m<S0>(S0(), Box<S0>(t: S0()))      // p/c01: invalid, the call returns a U
    return self.get() } }
given <T> => Box<T> is P { type X = T
  fun get() -> T { self.t } }
```

In the body of `m`, `b` is a `Box<U>`, so `Box<U>.X` is this `U`. The type of `b.m` seen through the conformance is "for all U′, (U′, Box<U′>) → U", but its binder is the same declaration `U`, and `X` is replaced by `U` under it without renaming. `b.m<S0>(…)` therefore gets the result type `S0`. base and FULL reject `p/c01`; NEW and FULL + `assocsubst` accept it. The valid form (`let r: U = …`, `p/c01v`) is rejected by NEW with "no coercion from 'S0' to 'U'". The control `p/c01c`, where the called requirement has its own parameter `W`, behaves correctly. `p/c02-capture-value.hylo` calls `m<S1>` from `main`: the `S1` stored in `b` is passed to `takeS0`; NEW accepts.

Suspected cause: `Typer.declaredType(of:seenThrough:)` applies `aliasesInConformance` with `TypeStore.substitute`, which does not avoid capture. Before `assocsubst` the value substituted for `X` could not mention a parameter of the requirement.

### 3. The associated type of a conditional conformance ignores the witnesses of its premises (U1 is not closed)

```hylo
given <T where T is Q> => Box<T> is P { type X = T.Y
  fun get() -> T.Y { self.t.make() }
  fun put(x: T.Y) { self.t.eat(x) } }
```

With `assocsubst`, `Box<A>.X` is `(A::q).Y`, where `q` is the requirement `T is Q` of the conformance declaration, not the witness with which the conformance is used. It is the same type whatever conformance `A` has to `Q`. In `p/a04-nested-scopes.hylo`, `outer` declares `given A is Q { type Y = S0 … }` and a nested function `inner` declares `given A is Q { type Y = S1 … }`; the `S0` returned by `get` in `outer` is passed to `put` in `inner`, which gives it to `eat(y: S1)`. The trace confirms that each scope uses its own given. Accepted by every configuration, including FULL + `assocsubst` alone. The control with a ground conformance of `Box<A>` in each scope (`p/a04c`) is rejected.

`p/a02`/`p/a03` are the same defect with two type parameters (`V == W`): FULL + `assocsubst` rejects them, NEW accepts them again through the `sameReference` rule of finding 1.

The same cause makes valid programs fail: `Box<A>.X` is not `S0` when `A.Y = S0` (`p/a01`, `p/a17`, `p/a22`).

Suspected cause: `Typer.typeOfImplementation(satisfying:in:)` walks the witness and skips `.termApplication(f, _)`, keeping only type arguments. The premise witnesses should replace the references to the conformance's requirements in the definition, followed by normalisation.

### 4. `Self.X` is still converted through a refinement (U2 is not closed)

```hylo
trait P { type X
  fun get() -> X
  fun put(x: X) }
trait R refines P {}
fun g<V, W where V == W, V is R, W is R>(v: V, w: W) { v.put(w.get()) }      // p/b10
```

Accepted by every configuration, base included. The control with `V is P, W is P` (`p/b10c`) and the one without `V == W` (`p/b10d`) are rejected. `p/b11-refinement-twin-value.hylo` uses local givens as in finding 1: an `S1` reaches `put(x: S0)`; the trace confirms the witnesses. `p/b12-launder-refinement.hylo` is `launder-5` with `T is R` instead of `T is P` in `cast`: NEW accepts it and rejects the control `p/b12c`.

`JUDGEMENT.md` says of U2 that no program passing a value of one concrete type as another was found; `p/b11` is one, and it does not need `eqsolve`.

Suspected cause: for a witness of `P<V>` obtained through the given nested in `R`, `typeOfImplementation` finds a conformance declaration without a definition of `X` and returns the error type; `aliasesInConformance` then substitutes `Self` but not `Self.X`, leaving `(P<V>::abstract).X`, an abstract selection outside the trait. The strict rule accepts two abstract selections whose types unify, and `P<V>` unifies with `P<W>` under `V == W`. The rule assumes that an abstract selection only exists inside the trait.

### 5 and 6. Valid programs rejected by `abstractstrict`

None of these needs two witnesses to be equal: each has a single conformance to `P` in scope. All are accepted by base, FULL and NEW without `abstractstrict`, and rejected by NEW and by FULL + `abstractstrict`.

| Program | Shape | Message under NEW |
|---|---|---|
| `p/r22-method-on-assoc-value.hylo` | `trait P { type X ; given X is Q … }`, `fun f<T where T is P>(t: T) { t.get().q() }` | type '(T::P).X' has no member 'q' |
| `p/r01-nested-given.hylo` | same, `needQ<T.X>()` | no coercion from 'Q<(T::P).X> ==> …' |
| `p/r13-nested-given-in-extension.hylo` | same goal in `extension <T where T is P> T` | same |
| `p/r25-nested-given-compound.hylo` | `given Box<X> is Q` nested in the trait | same |
| `p/r05-trait-calls-extension.hylo` | a method of the trait calls `self.twice(x)`, declared in `extension <T where T is P> T` with `x: T.X` | cannot pass value of type '(Self::P).X' to parameter '(Self::P).X' |
| `p/r26-extension-of-box-from-trait.hylo` | same with `extension <T where T is P> Box<T>` and a `Box<Self>` | same |
| `p/r11-conditional-given-on-assoc.hylo` | `given <T where T is P> => Holder<T.X> is Q`, used in the trait at `Holder<X>` | no coercion from 'Q<Holder<(Self::P).X>> ==> …' |

The first group is the important one: a given nested in a trait is how an associated type is constrained, and with NEW it can only be used inside the trait (`p/r22c`, `p/r01c` are accepted). `negative/missing-associated-type-conformance.hylo` shows it too: NEW reports a second error on `f(x)`. The type of the nested given mentions `(Self::abstract).X`; to apply it to `T is P` it must be matched with `(T::r).X`, which the liberal rule allowed and the strict one refuses. The second group is the mirror image: the member of the extension has type `(Self::r).X` where `r` is the extension's requirement, discharged by the trait's own witness.

`p/r16-conditional-conformance-on-self.hylo` is in the same family but is not a regression against FULL: FULL rejects it, FULL + `assocsubst` accepts it, NEW rejects it.

### The five programs `v-abs-1, -2, -3, -4, -7`

All five are rejected by NEW. In each, the method has both `T == Self` and `T is P`, and the body needs `Self.X` (the trait's witness) to equal `T.X` (the witness of the requirement `T is P`): two witnesses. Rejecting them loses nothing that is valid without that assumption:

| Program | Needs | Variant with one witness | NEW |
|---|---|---|---|
| v-abs-1 | `Self.X == T.X` | `p/v1c.hylo` (no `T is P`) | accept |
| v-abs-2 | a `Self.X` passed as `T.X` | `p/v2c.hylo` | accept |
| v-abs-3 | `X == T.X` | `p/v1c.hylo`, `p/v4c.hylo` | accept |
| v-abs-4 | `X == T.X` with `T == U, U == Self` | `p/v4c.hylo` | accept |
| v-abs-7 | `X == U` from `T.X == U` | `p/v7c.hylo` (no `T is P`); `p/v7d.hylo` (with `T.X == X` stated) | accept |

The same holds for `cast-only`, `cast-two`, `launder-5-def`, `launder-6`, `u2-b` and `e2-abs-qual-distinct-conf`, which NEW also rejects. `p/r04`, `p/r06`, `p/r07`, `p/r08`, `p/r10`, `p/r12`, `p/r24` are further valid trait bodies that NEW accepts.

### 7. Member aliases and structs of generic declarations are one type for every instance (outside the mechanism)

`given <T> => Box<T> is P { type X = Self.Elem … }` with `struct Box<T> { type Elem = T … }` (`p/a14d`), and a struct declared inside the generic conformance that holds a `T` (`p/a13`): `b.put(a.get())` with `a: Box<S0>`, `b: Box<S1>` is accepted by every configuration. The definition of `X` does not mention the conformance's parameter, so `assocsubst` has nothing to substitute. The cause is not in the mechanism: `p/a14c` and `p/a13c` show the same confusion with a member alias and a nested struct of a generic struct and no trait at all, in base. It is listed because it is the U1 symptom ("`Box<A>.X` and `Box<C>.X` are one type") surviving in NEW. The control with an alias chain inside the conformance (`p/a15`) is rejected correctly.

### 8. A parameter of the conformance that its head does not determine (question)

`given <T, U> => Box<T> is P { type X = U … }`. In `p/a05e`, `let y: S1 = a.get()` followed by `let z: S0 = a.get()` on the same `a: Box<S0>` is accepted by NEW without any diagnostic; base and FULL reject both lines. With `assocsubst`, `U` is an open variable of the witness, fresh at each use (the error type when the associated type is named, `p/a05`, `p/a05b`). No value can cross, since nothing can produce a `U`. Whether the declaration should be an error is a language question; today nothing reports it. When `U` is determined by a premise the result is right (`p/a25`, `p/a26`); when the premise has two solutions, the expected type chooses (`p/a27`: lines 16 and 17 accepted, base rejects all three).

### 9. Incomplete (three shapes)

1. The associated type is defined by an associated type of a parameter (`type X = T.Y`, `type X = Box<T.X>`): `Box<A>.X` is not reduced to the definition in `A`'s conformance (`p/a01`, `p/a17`, `p/a22`). Same cause as finding 3.
2. `T.X` in the signature of a member of `extension <T where T is P> T` is not resolved at the use: at an instance of a generic conformance it stays `(Box<S0>::P).X` instead of `S0` (`p/e05`), and in a generic function it is not the caller's `V.X` (`p/e01`, `p/r26b`). Also in base.
3. `T.X.X` in the parameters of a callee with requirements `T is P, T.X is P`: only the first selection is resolved (`p/k07`, `p/k08`, `p/k06`, and `p/k09` for a generic caller). Likely `Solver.resolve(_:elaboratedBy:at:)`: the binding of the second requirement is compared with a witness whose type has already been rewritten.

Also seen: a conformance found through a refinement gives the error type for `B.X` without a diagnostic at the declaration (`p/a11`, `p/a11b`, in base too).

## What held

- Instantiation itself: two parameters in either order, a parameter twice in the head, nested heads, `Box<Box<A>>`, a bare parameter, tuples and function types, alias chains, generic aliases, a trait with a parameter, equality premises, a tuple head, a parameter determined by a premise, mutual definitions, the conformance used inside its own body at `Box<Box<T>>`, default methods of the trait seen through a generic conformance, members declared in any order (`a06`–`a09`, `a12`, `a15`, `a16`, `a18`–`a21`, `a24`–`a26`, `d01`–`d03`, `d05`, `k02`, `k05`, `o03`, `r09`, each with an invalid twin that is rejected with the right number of errors).
- The reference programs of U1 and U2 are all rejected by NEW, except `confusion-3`, which is valid (the local given shadows the global one) and now accepted.
- `abstractstrict` in the trait body: every `launder`/`cast` variant with `T is P` is rejected; the one-witness variants are accepted.
- Order: 121 permutations of top-level declarations of 14 programs (including conformance and extension heads written with an instantiated associated type, `o01`, and dependent premises, `o02`) and 24 permutations of a where clause: one verdict per program.
- Self-check: no violation in 120 programs. No crash or timeout, including cyclic and growing definitions (`k01`–`k04`).
- The 26 positive compiler tests that declare a trait are accepted by NEW.

## What could not be tested

- Universal types written inside an associated type definition: no syntax was found. Capture was reached through a generic requirement instead (finding 2).
- Conformances declared inside a generic struct or extension: they are not visible from outside (`p/n01`, `p/n02`).
- Adjunct conformances with an associated type: base reports "no implementation of associated type requirement" (`p/a10`).
- A struct with a where clause ("where clause is not allowed here"), a conformance whose head is a generic alias (`p/d04`, not found by base either).
- Run-time behaviour: findings are stated from the types and the witnesses in the trace; nothing was executed.
- Times: the machine was shared; no cost claim is made.

## Files

| File | Content |
|---|---|
| `p/*.hylo`, `p/wo/*.hylo` | the programs |
| `run.py`, `results.jsonl` | runner (restartable, one process at a time) and raw results |
| `permute.py`, `permute.jsonl`, `perm/` | permutations of declarations under NEW |
| `tabulate.py`, `RESULTS.md` | results table |

Reproduce one line: `python3 run.py p/e04-extension-twin-value.hylo` (eight configurations) or `python3 run.py --configs "FULL;NEW;NEW-headsubst" FILE`.
