# An independent reference for implicit resolution, and differential testing against it

## What was asked

Until now, the expected verdicts of the programs used to validate the type-checker fixes were decided by the people who wrote the fixes. This directory provides an independent source of expected verdicts for a fragment of the language:

1. a written specification of resolution for that fragment (`spec.md`), with the points on which the intended semantics is a guess listed as open questions;
2. a reference resolver that implements the specification directly (`reference.py`);
3. a printer from abstract problems to Hylo programs (`to_hylo.py`);
4. a generator and a harness that compare the compiler with the reference on random problems (`fuzz.py`), under the configurations base, FIX and FULL of `BRIEF.md`;
5. minimised examples of every class of disagreement, each checked against the specification by reasoning.

An independent review of every claim below is in `JUDGEMENT.md`. Where it corrected this text, the correction is marked "(review)".

## Summary of the findings

- **FIX and FULL are unsound in two places.** Each is shown below with a program of a few lines.
  - *Generic conformances whose associated type mentions a parameter* (`given <A where ...> => A is P { type X = A }`): the associated type is not instantiated, so `T.X` and `U.X` are the same type for all `T` and `U`. A value of type `St0.X1` (which is `St0`) is accepted where `St1.X1` (which is `St1`) is expected. The existing checker (base) has the same defect. The generator produces 43 such queries, all with a bare parameter as head. (review) The defect is not limited to bare-parameter heads: it also holds for `given <A> => Box<A> is P { type X = A }`, and with methods in the trait a value of one struct is passed where another is expected (`judge/p/u1-confusion.hylo`, accepted by base, FIX and FULL).
  - *`Self.X` inside a trait*: the rule that equates `Self.X` with `T.X` lets a program convert `W.X` into `V.X` when `V == W` and both conform, which is exactly what `negative/associated-type-inequality.hylo` forbids. Accepted by FIX and FULL; base does not terminate on it. Found by reasoning from the specification, outside the generated fragment. (review) The rule is in the existing unifier, and base accepts the unsound definition alone; `eqsolve` implements the same rule and is what makes the whole program go through (FIX without `eqsolve` rejects the call).
- **Outside those two places, no unsoundness was found in the generated fragment.** On the 20,000 generated queries of the seven other kinds, FIX and FULL accept no goal that the specification cannot derive. That includes 181 goals that are valid only with injectivity, all rejected: the implementation has no injectivity, as its documentation says. (review) This is a statement about the generated shapes only: both unsound places were found, or widened, by hand in constructs the generator never produces (trait bodies, methods, type aliases).
- **FIX and FULL give the same verdict on all 21,500 generated queries.**
- **FIX and FULL reject many derivable goals**: 735 of the 9,975 generated goals that have exactly one derivation (7.4%), plus 87 whose where clause is not written in the order the compiler requires. The rejections are not explained by the depth bound (no generated derivation has more than 5 conformance steps, so the bound of 10 was never approached). They fall into six classes. (review) Base rejects an example of every class too (`JUDGEMENT.md` names the program for each): these are limits of the existing checker that the fixes keep, not regressions. Three hypotheses about the implementation separate rejected from accepted goals almost exactly: 473 goals are predicted rejected and all are rejected; of the 8,995 goals with no predicted cause, 2 are rejected. Where only parameters are equated, nothing is rejected: all 1,611 goals with one derivation of the kind `eq-param` and all 1,322 of the kind `cond` (conditional conformances whose premises need coercions) are accepted.
- **An equality goal and the coercion between the same two types can have different verdicts** under FIX and FULL: `needEq<C, Box<B>>()` is accepted and passing a `C` where a `Box<B>` is expected is rejected, in the same scope.
- **Whether an ambiguity is reported depends on how the equalities are written.** Of 800 goals built to have two derivations exchanged by a symmetry of the problem, FIX and FULL accept 408 and reject 392.
- **The resource bound of `budget` is reached on problems of two declarations** (17 queries), always for goals that are underivable, so the verdicts are right; the diagnostic is "implicit resolution is too complex".

Section "Open questions" lists what the language designers must decide before these can be called defects or features.

## The fragment

`spec.md` is the reference document; in short:

- **Types:** nominal types of arity 0 to 2, generic parameters (rigid), tuples of two elements, and associated types `T.X` and `S.X` on a parameter or on a nominal type without arguments.
- **Givens:** conformance declarations (ground, generic, conditional, and for a bare parameter), with premises `A is Q` and `A == B`; where-clause requirements `A is P` and `A == B`.
- **Goals:** a conformance goal (`needP<A>()`), an equality goal (`needEq<A, B>()`), and a coercion (`check<B>(x)` with `x: A`).
- **Equality:** reflexivity, symmetry, transitivity, the equalities of the where clause, and congruence. No injectivity. This mirrors the implementation; it is open question 1.
- **Associated types:** an associated type belongs to a *derivation* of a conformance, not to a type. Through a declaration it reduces to its definition; through a where-clause requirement it is opaque; two different derivations give unrelated associated types, even on equal types (the compiler's negative test).

The specification also defines a model (types are finite trees; a function can be called with any types and witnesses that satisfy its where clause) and grades every underivable goal as *invalid* in the model, *valid with injectivity*, or *vacuous* (the where clause has no solution). Only an accepted goal of the first grade is called unsound here.

Not covered: inferred type arguments, givens declared inside functions, equality givens with parameters, trait refinement, extensions, overloading, and the ranking of derivations. Trait bodies (`Self.X`) are specified but covered by hand-written programs only.

## How the comparison works

A *problem* is a set of declarations and about six *queries*. Each query is one generic function: its where clause is the scope and its body is one goal. The compiler's diagnostics are attributed to queries by line number, so one compiler run gives one verdict per query.

For each query the reference returns: derivable or not; for conformance goals the number of distinct derivations; the size of the smallest derivation (conformance steps, number of equality requirements needed, whether congruence is needed); and the grade in the model. Each compiler verdict is then put in a class:

| Class | Reference | Compiler | Meaning |
|---|---|---|---|
| agree | derivable (one derivation) / underivable | accept / reject | |
| UNSOUND | underivable, invalid in the model | accept | candidate unsoundness |
| BEYOND-SPEC | underivable, but valid with injectivity or vacuous | accept | not unsound; outside the specification |
| ILLFORMED-accept | an `A.X` of the goal denotes no type | accept | see "Ambiguity" |
| INCOMPLETE | derivable, one derivation | reject | candidate incompleteness |
| WHERE-ORDER | derivable, one derivation | reject, "no static member" | the where clause uses `T.X` before `T is P` |
| MULTI-accept, MULTI-reject | derivable, several derivations | accept / reject | no verdict predicted: ranking is not specified |
| AMBIGUITY-MISSED | two derivations exchanged by a symmetry | accept | the specification predicts an ambiguity error |
| BUDGET-agree | underivable | reject, "too complex" | right verdict, resource bound reached |
| CRASH, TIMEOUT | any | abnormal termination | |

### Checks made on the reference and on the printer before trusting them

- **Hand-written cases** (`handcases.py`, `validate.py`, `hand-results.jsonl`): 43 cases with 113 queries, each with the verdict I expect from the specification written beside it. The reference agrees with all 113.
- **Printer:** 28 of the cases transcribe an existing program (compiler tests and `test-programs/equalities`). For each, the compiler gives the printed program and the original the same verdict under base, FIX and FULL.
- **Known defects are found again:** on the transcribed programs the harness reports base as unsound on the programs that `soundness/1-unrelated-equalities.md` describes (`c01`, `n-params-2`, `v02`, `v03`, `assocneg-3`), and FIX and FULL as correct on them.
- **Batches:** to save time, FIX and FULL were run on six problems per compiler process, with disjoint names. Before the campaign, 48 problems run both ways gave identical verdicts. After it, every problem with an accepted underivable goal (UNSOUND, BEYOND-SPEC, ILLFORMED-accept) or a budget message was rerun alone, and so was a part of the other problems with a disagreement. 525 (problem, configuration) pairs with a disagreement in a batch were rerun alone; 525 gave the same verdicts for every query. The tables use the run alone where there is one.
- **The classes of rejection are systematic.** The table "Predicted cause" below shows that three syntactic conditions separate accepted from rejected goals almost perfectly. A defect of the reference or of the printer would not produce that pattern.

## What was run

Fixed seeds (`fuzz.py`, `SEED`); `problems.jsonl` holds every problem with the reference answers, `results.jsonl` the raw compiler verdicts. `campaign.sh` is the sequence of commands.

| Kind | Problems | Queries | base: problems / queries | FIX: problems / queries | FULL: problems / queries |
|---|---:|---:|---:|---:|---:|
| conf | 500 | 3000 | 120 / 720 | 500 / 3000 | 500 / 3000 |
| eq-param | 550 | 3300 | 5 / 30 | 550 / 3300 | 550 / 3300 |
| eq-app | 550 | 3300 | 5 / 30 | 550 / 3300 | 550 / 3300 |
| chain | 450 | 2700 | 5 / 30 | 450 / 2700 | 450 / 2700 |
| cond | 500 | 3000 | 5 / 30 | 500 / 3000 | 500 / 3000 |
| assoc | 650 | 3900 | 5 / 30 | 650 / 3900 | 650 / 3900 |
| blanket | 250 | 1500 | 5 / 30 | 250 / 1500 | 250 / 1500 |
| twin | 200 | 800 | 5 / 20 | 200 / 800 | 200 / 800 |
| total | 3650 | 21500 | 155 / 920 | 3650 / 21500 | 3650 / 21500 |

The kinds: `conf`, conformances only; `eq-param`, equalities between parameters; `eq-app`, equalities involving type applications and tuples; `chain`, chains of equalities needing transitivity and congruence; `cond`, conditional conformances whose premises need coercions; `assoc`, associated types; `blanket`, associated types with a conformance declared for a bare parameter (the subject of finding U1); `twin`, goals with two symmetric derivations.

Base was run on a subset only. On scopes with equalities it frequently does not terminate, so each query was run alone with an 8-second limit.

The reference answers of the generated queries ("illformed-goal": an `A.X` of the goal denotes no type, so the goal must be rejected):

| Reference answer | conf | eq-param | eq-app | chain | cond | assoc | blanket | twin | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| derivable, one derivation | 1472 | 1611 | 1614 | 1302 | 1322 | 1919 | 735 | 0 | 9975 |
| derivable, several derivations | 16 | 36 | 28 | 42 | 155 | 32 | 15 | 800 | 1124 |
| illformed-goal | 0 | 0 | 0 | 0 | 0 | 223 | 73 | 0 | 296 |
| underivable, invalid in the model | 1512 | 1653 | 1394 | 1309 | 1523 | 1632 | 604 | 0 | 9627 |
| underivable, scope has no solution | 0 | 0 | 123 | 7 | 0 | 94 | 73 | 0 | 297 |
| underivable, valid with injectivity | 0 | 0 | 141 | 40 | 0 | 0 | 0 | 0 | 181 |

## Results

### Classes of disagreement, by configuration

Number of queries in each class. Base was run on 920 queries only.

| Class | base | FIX | FULL |
|---|---:|---:|---:|
| AMBIGUITY-MISSED | 13 | 408 | 408 |
| BEYOND-SPEC | 0 | 12 | 12 |
| BUDGET-agree | 0 | 17 | 17 |
| ILLFORMED-accept | 0 | 6 | 6 |
| INCOMPLETE | 17 | 735 | 735 |
| MULTI-accept | 6 | 281 | 281 |
| MULTI-reject | 1 | 43 | 43 |
| TIMEOUT | 24 | 0 | 0 |
| UNSOUND | 4 | 43 | 43 |
| WHERE-ORDER | 1 | 87 | 87 |
| agree | 854 | 19868 | 19868 |

The same by kind, as FIX / FULL:

| Class | conf | eq-param | eq-app | chain | cond | assoc | blanket | twin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AMBIGUITY-MISSED | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 408 / 408 |
| BEYOND-SPEC | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 12 / 12 | 0 / 0 |
| BUDGET-agree | 0 / 0 | 1 / 1 | 1 / 1 | 0 / 0 | 15 / 15 | 0 / 0 | 0 / 0 | 0 / 0 |
| ILLFORMED-accept | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 6 / 6 | 0 / 0 |
| INCOMPLETE | 0 / 0 | 0 / 0 | 318 / 318 | 123 / 123 | 0 / 0 | 35 / 35 | 259 / 259 | 0 / 0 |
| MULTI-accept | 16 / 16 | 30 / 30 | 21 / 21 | 39 / 39 | 137 / 137 | 26 / 26 | 12 / 12 | 0 / 0 |
| MULTI-reject | 0 / 0 | 6 / 6 | 7 / 7 | 3 / 3 | 18 / 18 | 6 / 6 | 3 / 3 | 0 / 0 |
| TIMEOUT | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| UNSOUND | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 43 / 43 | 0 / 0 |
| WHERE-ORDER | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 62 / 62 | 25 / 25 | 0 / 0 |
| agree | 2984 / 2984 | 3263 / 3263 | 2953 / 2953 | 2535 / 2535 | 2830 / 2830 | 3771 / 3771 | 1140 / 1140 | 392 / 392 |

FIX and FULL agree on every query:

| FIX verdict | FULL verdict | Queries |
|---|---:|---:|
| accept | accept | 9903 |
| reject | reject | 11597 |

### Derivable goals, by size of the smallest derivation

The compiler abandons a search after 10 steps. To check that this bound is not the reason for the rejections, goals with exactly one derivation are stratified by the size of their smallest derivation. "Equalities needed" is the smallest number of equality requirements with which the goal remains derivable, counted after associated types have been given their meaning.

| Conformance steps | Equalities needed | Congruence needed | base | FIX | FULL |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | no | 9 / 10 | 591 / 670 | 591 / 670 |
| 0 | 1 | no | 3 / 3 | 196 / 200 | 196 / 200 |
| 0 | 1 | yes | 10 / 21 | 2640 / 2888 | 2640 / 2888 |
| 0 | 2 | no | 3 / 3 | 126 / 126 | 126 / 126 |
| 0 | 2 | yes | 7 / 9 | 850 / 977 | 850 / 977 |
| 0 | ≥3 | no | 2 / 2 | 59 / 59 | 59 / 59 |
| 0 | ≥3 | yes | 2 / 2 | 224 / 255 | 224 / 255 |
| 1 | 0 | no | 301 / 301 | 1984 / 2005 | 1984 / 2005 |
| 1 | 1 | no | 5 / 6 | 527 / 563 | 527 / 563 |
| 1 | 1 | yes | 3 / 3 | 251 / 254 | 251 / 254 |
| 1 | 2 | no | 1 / 1 | 175 / 183 | 175 / 183 |
| 1 | 2 | yes |  | 52 / 79 | 52 / 79 |
| 1 | ≥3 | no | 1 / 1 | 28 / 28 | 28 / 28 |
| 1 | ≥3 | yes |  | 9 / 16 | 9 / 16 |
| 2 | 0 | no | 55 / 57 | 563 / 619 | 563 / 619 |
| 2 | 1 | no | 4 / 4 | 485 / 527 | 485 / 527 |
| 2 | 1 | yes |  | 18 / 18 | 18 / 18 |
| 2 | 2 | no | 1 / 1 | 108 / 117 | 108 / 117 |
| 2 | 2 | yes |  | 2 / 5 | 2 / 5 |
| 2 | ≥3 | no | 1 / 1 | 12 / 16 | 12 / 16 |
| 2 | ≥3 | yes |  | 0 / 5 | 0 / 5 |
| ≥3 | 0 | no | 8 / 8 | 133 / 144 | 133 / 144 |
| ≥3 | 1 | no | 1 / 1 | 92 / 102 | 92 / 102 |
| ≥3 | 1 | yes |  | 3 / 3 | 3 / 3 |
| ≥3 | 2 | no |  | 22 / 23 | 22 / 23 |
| ≥3 | 2 | yes |  | 0 / 2 | 0 / 2 |
| ≥3 | ≥3 | no |  | 3 / 3 | 3 / 3 |
| ≥3 | ≥3 | yes |  | 0 / 1 | 0 / 1 |

Acceptance does not fall with the number of conformance steps or of equalities. It falls where congruence is needed, which the next table explains. The first row (nothing needed, yet 79 rejections) consists of goals such as `T.X1 == T` through a bare-parameter conformance (class I5 below).

### What predicts a rejection

`explain.py` encodes hypotheses about the implementation, read from `Typer.match` and `Typer.canDeriveCoercions`, and tags a derivable goal with the hypotheses that predict its rejection. It is a model of the implementation, not part of the specification.

- **DECOMP.** Two types of the same shape are compared part by part, and only the innermost differing parts must be equal. An equality between compound types that is not an equality of their parts is never used.
- **PREFILTER.** A coercion between two differing parts is attempted only if each part is, syntactically, a side of some equality requirement.
- **DECL-HEAD.** The head of a conformance declaration is matched against the goal part by part, so a declaration for `St2<A>` is not found for a parameter `T` with `St2<U> == T`.
- **BLANKET.** The goal or its scope mentions an associated type through a conformance declared for a bare parameter whose definition mentions the parameter.

| Predicted cause | FIX accepted | FIX rejected | FULL accepted | FULL rejected |
|---|---:|---:|---:|---:|
| none (predicted: accepted) | 8993 | 2 | 8993 | 2 |
| BLANKET | 157 | 256 | 157 | 256 |
| BLANKET+DECOMP | 3 | 2 | 3 | 2 |
| BLANKET+PREFILTER | 0 | 2 | 0 | 2 |
| DECL-HEAD | 0 | 30 | 0 | 30 |
| DECL-HEAD+DECOMP | 0 | 2 | 0 | 2 |
| DECOMP | 0 | 346 | 0 | 346 |
| PREFILTER | 0 | 95 | 0 | 95 |

The first three hypotheses are exact on this campaign. BLANKET is only a necessary condition: such goals are accepted when the associated type need not be reduced (`T.X1` to `T.X1`). The two rejections not predicted are both in the `blanket` kind and were examined by hand (`blanket-0016` q4, `blanket-0067` q0): in the first, the conformance needed to look up `T1.X1` is derivable only through a declaration matched by an equality (I3 and I4 below); in the second, the where clause mentions `T1.X1` before `T1 is Tr1`, at a point where the bare-parameter conformance already gives it a meaning.

### Goals with several derivations

The specification does not say which derivation wins, so no verdict is predicted, except for the `twin` kind. `multi.py` tabulates what competes and what the compiler does:

| Problems | Competing derivations | FIX accepted | FIX rejected | FULL accepted | FULL rejected |
|---|---|---:|---:|---:|---:|
| other kinds | declaration + declaration | 163 | 23 | 163 | 23 |
| other kinds | declaration + declaration + declaration | 45 | 6 | 45 | 6 |
| other kinds | declaration + declaration + requirement on an equal type | 3 | 0 | 3 | 0 |
| other kinds | declaration + declaration + requirement on the goal's type | 1 | 0 | 1 | 0 |
| other kinds | declaration + requirement on an equal type | 23 | 5 | 23 | 5 |
| other kinds | declaration + requirement on the goal's type | 23 | 1 | 23 | 1 |
| other kinds | requirement on an equal type + requirement on an equal type | 15 | 8 | 15 | 8 |
| other kinds | requirement on an equal type + requirement on an equal type + requirement on an equal type | 1 | 0 | 1 | 0 |
| other kinds | requirement on an equal type + requirement on the goal's type | 7 | 0 | 7 | 0 |
| symmetric (twin) | declaration + declaration | 35 | 37 | 35 | 37 |
| symmetric (twin) | requirement on an equal type + requirement on an equal type | 373 | 355 | 373 | 355 |

A requirement on the goal's own type wins in 31 of 32 cases; the exception (`blanket-0159` q4) is an instance of I5 below. For the rest the table reveals no rule: the same kind of competition is sometimes accepted and sometimes rejected.

### Base

Base was run on 120 problems of the `conf` kind and on 5 problems of each other kind (155 problems, 920 queries). The table compares it with FIX query by query.

| Reference | base verdict | FIX verdict | Queries |
|---|---:|---:|---:|
| derivable (one) | accept | accept | 417 |
| derivable (one) | reject | accept | 9 |
| derivable (one) | reject | reject | 9 |
| derivable (one) | timeout | accept | 2 |
| derivable (one) | timeout | reject | 2 |
| derivable (several) | accept | accept | 18 |
| derivable (several) | accept | reject | 1 |
| derivable (several) | reject | accept | 1 |
| derivable (several) | reject | reject | 7 |
| illformed-goal | reject | reject | 6 |
| underivable | accept | accept | 1 |
| underivable | accept | reject | 3 |
| underivable | reject | reject | 424 |
| underivable | timeout | reject | 20 |

- The harness finds the known unsoundness of base without help: 4 underivable goals accepted, for example `needEq<T0, T3>()` under `where T0 == T2` (`eq-param-0001` q1). FIX rejects 3 of them; the fourth is U1 below.
- Base does not finish within 8 seconds on 24 queries, 20 of them underivable. Some are of the `conf` kind: a conformance declaration with an equality premise is enough.
- Base rejects 9 goals with one derivation that FIX accepts, and accepts none that FIX rejects.

## Confirmed disagreements of FIX and FULL with the reference

Each example below was minimised (by `minimize.py`, or by hand where stated), run alone, and checked against the rules of `spec.md`. Programs are shown without the declarations of traits, structs and of the helpers `needP`, `needEq` and `check`; the files named contain them.

### U1. Unsound: the associated type of a conformance declared for a bare parameter (base, FIX, FULL)

`minimized/unsound-blanket.hylo` (by `minimize.py` from `blanket-0011` q1):

```hylo
trait Tr1 { type X1 }
struct St1 { public memberwise init }
given <A> => A is Tr1 { type X1 = A }
fun q0<T0>(x: T0.X1) { check<St1.X1>(x) }       // accepted
```

`hand/blanket-5.hylo`, without any generic function (accepted by base, FIX and FULL):

```hylo
given St0 is Tr0 {}
given St1 is Tr0 {}
given <A where A is Tr0> => A is Tr1 { type X1 = A }
fun q0(x: St0.X1) { check<St1.X1>(x) }          // accepted
```

*By the specification:* `Tr1<St0>` has one derivation, the instance `A := St0` of the declaration, so `St0.X1 == St0` by PROJ-DECL; likewise `St1.X1 == St1`. `St0 == St1` is not derivable and is false in the model. The goal does not depend on any of the guesses of the specification.

*What the compiler does:* it prints the type as `X1`, for every instance, and treats it as one opaque type. The same defect makes it reject the valid `needEq<T.X1, T>()` (`hand/blanket-4.hylo`, class I5).

(review) A value of the confused type is easy to obtain once the trait has methods, and the defect does not need a bare-parameter head. Both programs below are accepted by base, FIX and FULL, and the same calls are rejected when the conformances are ground (`judge/p/u1-confusion-ctl.hylo`):

```hylo
trait Tr1 { type X1
  fun get() -> X1
  fun put(x: X1) }
given <A> => A is Tr1 { type X1 = A
  fun get() -> A { self }
  fun put(x: A) {} }
fun q0(a: St0, b: St1) { b.put(a.get()) }       // an St0 reaches code that expects an St1   (judge/p/u1-confusion.hylo)

given <A> => Box<A> is Tr1 { type X1 = A }
type B0 = Box<St0>
type B1 = Box<St1>
fun q0(x: B0.X1) { check<B1.X1>(x) }            // accepted   (judge/p/u1-alias.hylo)
```

The cause is `typeOfImplementation(satisfying:in:)`, which returns the declared type of the `type X1 = ...` member without applying the type arguments of the witness.

*Scale:* 43 queries of the `blanket` kind are UNSOUND under FIX and FULL, and 12 more acceptances of the same shape occur in scopes whose where clause has no solution (BEYOND-SPEC). All 55 confuse the associated types of the bare-parameter conformance on two different types: 54 compare them directly, and in one (`blanket-0238` q1) the where clause equates one of them with a parameter.

### U2. Unsound: `Self.X` is equated with `T.X` (FIX, FULL)

`hand/self/launder-5.hylo`, written by hand:

```hylo
fun conv<A, B where A == B>(x: A) -> B { x }
fun check<T>(x: T) {}
trait P {
  type X
  fun cast<T, U where T == Self, T is P, T.X == U>(x: U) -> X { conv<U, X>(x) }
}
fun f0<V, W where V == W, V is P, W is P>(v: V, x: W.X) {
  check<V.X>(v.cast<W, W.X>(x))
}
```

*By the specification (section 5.4):* in `cast`, `T is P` is a second witness, so `T.X` and `Self.X` are unrelated and `conv<U, X>` is rejected. *By the compiler's own negative test:* `f0` has the where clause of `associated-type-inequality.hylo` and uses a `W.X` as a `V.X`, which that test rejects when written directly. The call in `f0` is legitimate once `cast` is accepted (it chooses `Self := V` with `V`'s witness and `T := W` with `W`'s), so the unsound step is the acceptance of the body of `cast`. Two mechanisms accept such bodies: the unifier lets `Self.X` match `T.X` when `T == Self` (`TypeStore.unifiable`, existing code), and the equality procedure of `eqsolve` equates them when the scope has exactly one conformance for a type equal to `Self` (`techniques/eqsolve.md`). The definition of `cast` alone is accepted by all three configurations (`hand/self/launder-5-def.hylo`); the whole program is accepted by FIX and FULL, and base does not finish it in 20 seconds (review: nor in 60). So the unsound step is in the existing checker. Among the flags of FIX, `eqsolve` is the one that makes the whole program accepted: with the other seven flags the call in `f0` is rejected, although its requirements are derivable.

`selfx.py` compares 27 programs about `Self.X` with the verdict that the uniform rule gives:

| Program | Expected | base | FIX | FULL | Reason |
|---|---|---|---|---|---|
| `a01-self-trait.hylo` | accept | accept | accept | accept | T == Self and Self.X == U are facts |
| `e09-trait-self-assoc.hylo` | accept | accept | accept | accept | X == Y and Y == U are facts |
| `absleak-0.hylo` | accept | accept | accept | accept | t.get() instantiates Self's witness with T's requirement |
| `absinst-ok.hylo` | accept | accept | accept | accept | V.X == Bool is a fact |
| `v-abs-1.hylo` | reject | reject | accept | accept | T is P is a second witness: T.X is not Self.X |
| `v-abs-2.hylo` | reject | accept | accept | accept | same |
| `v-abs-3.hylo` | reject | reject | accept | accept | same |
| `v-abs-4.hylo` | reject | reject | accept | accept | same, through T == U == Self |
| `v-abs-5.hylo` | reject | reject | reject | reject | U == T.X, and T.X is not Self.X |
| `v-abs-6.hylo` | reject | reject | reject | reject | same |
| `v-abs-7.hylo` | reject | accept | accept | accept | same (equality goal) |
| `v-abs-8.hylo` | reject | reject | reject | reject | same, in an extension of the trait |
| `v-abs-9.hylo` | reject | reject | reject | reject | same |
| `abs-trans-0.hylo` | reject | reject | reject | reject | T.X and U.X are two witnesses |
| `abs-trans-1.hylo` | reject | reject | reject | reject | same |
| `abs-trans-2.hylo` | reject | accept | reject | reject | same |
| `abs-trans-3.hylo` | reject | accept | reject | reject | same |
| `abs-trans-4.hylo` | reject | timeout | reject | reject | same |
| `abs-trans-5.hylo` | reject | timeout | reject | reject | same |
| `absleak-1.hylo` | reject | reject | reject | reject | t.get() has type T.X, not U.X |
| `absinst-0.hylo` | reject | accept | reject | reject | V.X == Bool is not known, only W.X == Bool |
| `abs-launder.hylo` | reject | reject | reject | reject | the body of cast needs T.X == Self.X |
| `cast-only.hylo` | reject | accept | accept | accept | the body of cast needs T.X == Self.X |
| `cast-two.hylo` | reject | accept | accept | accept | same, with two other witnesses |
| `launder-5-def.hylo` | reject | accept | accept | accept | conv<U, X> needs U == Self.X; only U == T.X is known |
| `launder-5.hylo` | reject | timeout | accept | accept | converts W.X to V.X: the conversion that associated-type-inequality.hylo forbids |
| `launder-6.hylo` | reject | timeout | accept | accept | same |

The rows where the expected verdict and the verdict of FIX differ are open question 6 of the specification. I did not manage to turn U2 into a program that passes a value of one concrete type as another: the steps needed around it are rejected for unrelated reasons (`hand/self/confusion-*.hylo`).

### I1. Incomplete: an equality between compound types is not used under a constructor (DECOMP)

```hylo
fun q0<T0, T1 where St2<T1> == St2<T0>>(x: St2<St2<T0>>) { check<St2<St2<T1>>>(x) }    // rejected (minimized/inc-coerce-nested.hylo)

given St2<St1> is Tr0 {}
fun q0<T0 where St2<St1> == St2<T0>>() { needTr0<St2<T0>>() }                          // rejected (minimized/inc-conf-eq-app.hylo)
```

*By the specification:* `St2<T0> == St2<T1>` by SYM and FACT, then CONG. In the second, the declared conformance of `St2<St1>` is transported along the fact. *The compiler* compares `St2<T0>` with `St2<T1>` part by part and asks for `T0 == T1`, which is not derivable without injectivity. Looking for equalities only at the innermost differing parts is complete in a theory *with* injectivity; the implementation combines it with an equality procedure that has none. `test-programs/equalities/decomp-2.hylo` is an earlier instance. 346 generated queries have this cause alone (267 in `eq-app`, 73 in `chain`, 6 in `assoc`). (review) Base rejects both programs as well.

### I2. Incomplete: types equal by congruence but not written in the where clause (PREFILTER)

```hylo
fun q0<T0, T1 where T0 == St1, T1 == St2<T0>>(x: St3<St0, T1>) { check<St3<St0, St2<St1>>>(x) }   // rejected (minimized/inc-prefilter-coerce.hylo)
```

*By the specification:* `T1 == St2<T0>` (FACT), `St2<T0> == St2<St1>` (CONG), TRANS, CONG. *The compiler* refuses to attempt the coercion from `T1` to `St2<St1>` because `St2<St1>` is not a side of any equality requirement (`canDeriveCoercions`). The equality procedure of `eqsolve` is not consulted. This gives the following pair, in one scope (`hand/goal-agreement.hylo`, FIX and FULL):

```hylo
fun q0<A, B, C where Box<A> == C, A == B>() { needEq<C, Box<B>>() }            // accepted
fun q1<A, B, C where Box<A> == C, A == B>(x: C) { check<Box<B>>(x) }           // rejected
```

95 generated queries have this cause alone. (review) Base rejects the minimised program and shows the same disagreement between the two goals (`judge/p/ga-q0.hylo` accepted, `judge/p/ga-q1.hylo` rejected). The smallest form is `where T0 == St1, T1 == St2<T0>`: a `T1` is not accepted where `St2<St1>` is expected (`judge/p/i2-var.hylo`).

### I3. Incomplete: a declaration is not found through an equality (DECL-HEAD)

```hylo
given <A> => St2<A> is Tr0 {}
fun q0<T0, T1 where St2<T1> == T0>() { needTr0<T0>() }       // rejected (minimized/inc-decl-head.hylo)
```

*By the specification:* DECL with `A := T1`; `St2<T1> == T0` is a fact. Every `St2<_>` conforms and `T0` is one. 32 generated queries. Base rejects the minimised program too. One hand-written case of this class is accepted by base and rejected by FIX and FULL (`hand/ematch.hylo`, third query: `Box<T> == U, V is P, V == T`, goal `P<U>`). (review) That is not a regression: base accepts the same query when the conformance declaration is deleted and the goal is false (`judge/p/ematch-q2neg.hylo`), so it accepts through its known unsound use of unrelated equalities, not through this rule. The cause of the class is that `canDeriveCoercion` compares the open pattern `St2<%a>` with the sides of the equalities syntactically (`Typer.unifiable(_:_:)` is identity up to renaming, not unification), so `match` drops the declaration.

### I4. Incomplete: `T.X` is not found when `T` equals a generic type (FIX, FULL, base)

```hylo
given <A> => Box<A> is P { type X = A }
fun q0<T, U where T == Box<U>>() { needEq<T.X, U>() }        // rejected: type 'T' has no static member 'X'  (hand/proj-through-application.hylo)
```

With `T == S` for a type `S` without arguments, the same lookup succeeds (`positive/associated-type-equality.hylo`). Hand-written only: the printer cannot write `Box<U>.X`, which this compiler does not accept in type position, so the generator reaches this class rarely. (review) This is I3 seen from member lookup, not a separate class: `needP<T>()` in the same scope is rejected as well (third query of the same file), and the lookup of `T.X` asks exactly that.

### I5. Incomplete: the other face of U1

```hylo
given <A where A is Tr0> => A is Tr1 { type X1 = A }
fun q0<T where T is Tr0>() { needEq<T.X1, T>() }             // rejected (hand/blanket-4.hylo)
```

260 rejected queries have this cause: 253 of the `blanket` kind and 7 of the `assoc` kind.

### I6. The order of the requirements in a where clause matters (WHERE-ORDER)

```hylo
fun q0<T where T is P, T.X == S>() { needEq<T.X, S>() }      // accepted
fun q1<T where T.X == S, T is P>() { needEq<T.X, S>() }      // rejected: type 'T' has no static member 'X'   (hand/where-order.hylo)
```

The specification makes the order irrelevant (rule SCOPE, a guess). 87 generated queries. This may be intended; it is open question 7.

### A1. Ambiguity depends on the orientation of equalities (AMBIGUITY-MISSED)

```hylo
fun f<A, B, C where B is P, C is P, B == A, C == A>() { g<A>() }      // rejected  (equalities/e01b-both-direct.hylo)
fun f<A, B, C where B is P, C is P, B == A, A == C>() { g<A>() }      // accepted  (equalities/e01-orient-amb.hylo)
```

Both have two derivations, from `B`'s requirement and from `C`'s, and exchanging `B` and `C` maps each problem to itself up to the direction of one equality. Rule SYM makes that direction irrelevant, so either both are ambiguous or the ranking violates symmetry. The existing checker behaves the same; the fixes did not change it.

The `twin` kind builds such goals by duplicating, in a problem whose goal has one derivation, every parameter that the goal does not mention, together with its requirements, and then writing each equality in a random direction. Each of the 800 goals has exactly two derivations, and the symmetry exchanges them: a derivation that it left in place would use no duplicated requirement, so it would be a second derivation of the original problem. FIX and FULL accept 408 of the 800.

### B1. The resource bound is reached on a two-declaration program (BUDGET-agree)

```hylo
given S1 is P {}
given <A where A == S0, A is P> => S3<S0, A> is P {}
fun q0<T, U where U == T>() { needP<S3<U, S0>>() }     // rejected, with "implicit resolution is too complex: more than 100000 candidate derivations"
fun q1<T, U>() { needP<S3<U, S0>>() }                   // rejected normally
```

(`hand/budget.hylo`, FIX and FULL.) The goal is underivable, so the verdict is right. But one equality on a parameter of the goal turns a failing search into one that exhausts the budget, also under FULL, where the abstract model is meant to cut such searches. 17 generated queries, 15 of them in the `cond` kind. No derivable goal was rejected for this reason. (review) Base has the same search without the bound: it rejects `q0` alone after about 55 s (indicative), against 89,588 candidate matches under FIX and FULL.

### S1. Beyond the specification: congruence on the tail of a tuple

```hylo
fun q0<A, B, C, D, E where {B, C} == {D, E}>() { needEq<{A, B, C}, {A, D, E}>() }      // accepted by FIX and FULL
fun q1<A, B, C, D, E where {B, C} == {D, E}>(x: {A, B, C}) { check<{A, D, E}>(x) }      // rejected
fun q2<A, B, C, D, E where {B, C} == {D, E}>() { needEq<{B, C, A}, {D, E, A}>() }      // rejected
```

(`hand/tuple-tail.hylo`.) Not derivable with tuples as constructors of fixed arity; valid in the model. It follows from the representation of tuples as lists. Open question 8.

### Ambiguity inside an associated type (ILLFORMED-accept)

In 6 queries of the `blanket` kind the reference finds that an `A.X` of the goal has two possible witnesses, none stated on `A` itself, and so denotes no type; the compiler picks one. All 6 goals compare a type with itself (`needEq<T1.X1, T1.X1>()`), so they hold whichever witness is picked. They are instances of the ranking question, not defects.

## Open questions for the language designers

The full list, with the rule each one affects, is section 9 of `spec.md`. The campaign adds evidence to the following ones (numbered as in `spec.md`):

1. **Injectivity.** The implementation has none (181 of 181 goals needing it are rejected), yet its matching strategy (I1) is only complete with it. Either add injectivity to the theory, which makes I1 disappear and is sound in the model, or keep it out and match modulo the equalities.
2. **How complete must the checker be?** I1, I2, I3 and I4 are all rejections of goals derivable by congruence. If they are acceptable, the language needs a rule that says which uses of an equality are accepted; "the two types are written in the where clause" is today's rule, and it makes `needEq` and a coercion disagree.
3. **Ranking and ambiguity** (A1 and the table of competing derivations).
4. **Is a requirement on the type itself preferred**, for associated types and for conformance goals? The negative test assumes so, and the compiler behaves so in the generated cases (31 of 32, see above).
6. **`Self.X`** (U2). The current rule is unsound in the model. The uniform rule rejects five programs of `test-programs/equalities` that FIX and FULL accept (`v-abs-1`, `-2`, `-3`, `-4` and `-7`).
7. **Order of requirements in a where clause** (I6).
8. **Tuples** (S1).
9. **The depth bound** played no role in this campaign.
10. **Where `A.X` is looked up** (I4).

## What remains uncertain

- **The specification contains eight guesses**, marked in `spec.md`. A verdict of the reference is only as good as they are. U1 and I5 use only the rule that an associated type through a declaration is its definition. I1 and I2 use only the five equality rules, and their goals stay valid if injectivity is added. I3 uses matching modulo equality (guess 3). U2 depends on reading the negative test as a rule about witnesses, which its own comment states.
- **The fragment is small.** One associated type per trait; associated types only on parameters and on nominal types without arguments; definitions of associated types without associated types; no givens inside functions; no trait bodies in generated problems. The reference has no ranking, so the 1,124 goals with several derivations test nothing except in the `twin` kind.
- **The grade "invalid in the model"** is exact without associated types. With them, it is computed after the reference has given the associated types their meaning, so it inherits guesses 6 and 7.
- **Base was run on a small subset**, with an 8-second limit per query; a timeout there is not a statement about longer runs. 720 of its 920 queries are of the `conf` kind, without any equality, so the campaign itself does not show which classes of rejection base shares. The review reran the minimised examples under base (`JUDGEMENT.md`): it shares all of them.
- **The absence of other unsoundness is a statement about the generated shapes.** The review checked the 17,600 queries without associated types against a second, independent model (`judge/model.py`): the two models agree everywhere and FIX and FULL accept none of the 8,192 invalid goals. The answers for the 3,900 queries with associated types rest on `reference.py` alone.
- **Not every disagreement was rerun alone.** About 1,650 (problem, configuration) pairs with a rejection of a derivable goal, a goal with several derivations or a missed ambiguity have only their batch run. Every pair that was rerun gave the same verdicts, and every class has a minimised example that was run alone.
- **`explain.py` is a model fitted to this campaign.** Its hypotheses come from reading two functions of the implementation and from the observed rejections. It predicts well here; it has not been tested on anything else.
- **Wall-clock time was not measured.** The machine was shared, and the campaign only records verdicts.

## Files

| File | Content |
|---|---|
| `spec.md` | the specification, with its open questions |
| `reference.py` | the reference resolver; `python3 reference.py problem.json` |
| `dsl.py`, `handcases.py`, `validate.py` | hand-written cases in a compact notation, and their check; results in `hand-results.jsonl`, programs in `hand/` |
| `to_hylo.py` | the printer |
| `tc.py`, `harness.py` | running the compiler (one process at a time, through a lock) and attributing verdicts |
| `fuzz.py` | generator (`gen`), runs (`run`), reruns alone (`confirm`); `problems.jsonl`, `results.jsonl` |
| `report.py` | classes and tables; `--list CLASS` shows examples; `--markdown` prints the tables of this README (`tables.md`) |
| `explain.py` | the model of the implementation's rejections |
| `multi.py` | the table of competing derivations |
| `minimize.py` | delta debugging of one disagreement; results in `minimized/` |
| `selfx.py` | the programs about `Self.X`; `self-results.jsonl`, programs in `hand/self/` |
| `campaign.sh` | the commands of the campaign, in order |
| `JUDGEMENT.md`, `judge/` | the independent review: verdict and cause for each claim, its reruns, its additional programs and its own tabulation and model |

To reproduce: `./campaign.sh` (several hours on a shared machine; restartable), `python3 validate.py`, `python3 selfx.py`.
