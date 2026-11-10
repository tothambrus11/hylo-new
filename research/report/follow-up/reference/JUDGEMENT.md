# Judgement of the reference-testing campaign

This file gives an independent verdict on every defect and class of disagreement that `README.md` claims. Each program was rerun alone under base, FIX and FULL, the correct verdict was decided by reasoning from the language's own tests, and the likely cause was located in `/home/user/hylo-impl/Sources/FrontEnd`.

## Summary

- **Both unsoundness claims are real.** The first is wider and more serious than the campaign reported: it affects every generic conformance, not only those declared for a bare parameter, and it lets a value of one struct be passed where another struct is expected.
- **All six incompleteness classes are real, and all are in the existing checker (base) as well.** None is a regression of FIX or FULL. One of them (I4) is a consequence of another (I3), not a separate class.
- **One statement in the README was wrong** and has been corrected there: the hand case said to be "accepted by base and rejected by FIX and FULL" is accepted by base through its known unsound derivation, not through the missing rule.
- **The campaign's numbers reproduce exactly** from its raw data with a tabulation that shares no code with its scripts.
- **The claim that nothing else is unsound is supported for goals without associated types** (8,192 invalid goals, all rejected, checked against a second independent model). For goals with associated types it rests on the campaign's reference alone, and the fragment is small.

## Verdicts

"In base" says whether the existing checker has the same behaviour.

| # | Claim | Verdict | Affected | In base |
|---|---|---|---|---|
| U1 | Associated type of a generic conformance is not instantiated | **Confirmed, unsound.** Wider than claimed (see below) | base, FIX, FULL | yes |
| U2 | `Self.X` is equated with `T.X`, which converts `W.X` into `V.X` | **Confirmed, unsound** with respect to `negative/associated-type-inequality.hylo` | FIX, FULL (whole program) | the unsound step yes; the whole program does not finish in 60 s |
| I1 | An equality between compound types is not used under a constructor | **Confirmed, incomplete** | base, FIX, FULL | yes |
| I2 | Coercion refused when a type is equal by congruence but not written in the where clause; equality goal and coercion disagree | **Confirmed, incomplete** | base, FIX, FULL | yes |
| I3 | A generic conformance declaration is not found through an equality | **Confirmed, incomplete** | base, FIX, FULL | yes |
| I4 | `T.X` not found when `T` equals a generic type | **Confirmed, but not a separate defect**: it is I3 seen from member lookup | base, FIX, FULL | yes |
| I5 | `T.X1 == T` rejected for a generic conformance with `type X1 = A` | **Confirmed, incomplete.** Same cause as U1 | base, FIX, FULL | yes |
| I6 | The order of requirements in a where clause changes the verdict | **Open question.** Behaviour confirmed | base, FIX, FULL | yes |
| A1 | Ambiguity depends on the direction in which equalities are written | **Confirmed inconsistency**; which verdict is right is an open question | base, FIX, FULL | yes |
| B1 | The `budget` bound is reached on a two-declaration program | **Confirmed cost problem.** The verdict is right | FIX, FULL | yes, worse: about 55 s to reject, no bound |
| S1 | Congruence on the tail of a tuple | **Not a defect** (sound). Open question on tuples | FIX, FULL | not established (base times out on the file) |
| - | 6 acceptances of goals whose `A.X` is ambiguous (ILLFORMED-accept) | **Not a defect.** All six compare a type with itself | FIX, FULL | - |
| - | 12 acceptances in scopes with no solution (BEYOND-SPEC) | Same cause as U1; not counted separately | FIX, FULL | - |
| - | "Accepted by base, rejected by FIX and FULL" (`hand/ematch.hylo`, third query) | **Not a regression.** Base accepts the same goal with the declaration removed | - | - |

## Confirmed defects

### U1. The associated type of a generic conformance is the same type for every instance (base, FIX, FULL)

`typeOfImplementation(satisfying:in:)` in `Typer.swift` handles a witness that refers to a conformance declaration by returning `declaredType(of:)` of the `type X = ...` member as written. It discards the type arguments of the witness. The lookup of members of extensions, a few lines away, does substitute them (`w.typeArguments(appliedTo:)`). So with `type X1 = A`, every `T.X1` is the alias to the declaration's own parameter `A`.

The campaign reported this for conformances declared for a bare parameter and wrote that a value of the confused type is hard to obtain. Both points understate the defect:

- It also holds for `given <A> => Box<A> is Tr1 { type X1 = A }`, reached through a type alias (`judge/p/u1-alias.hylo`: `B0.X1` is accepted where `B1.X1` is expected, with `type B0 = Box<St0>`, `type B1 = Box<St1>`).
- With methods in the trait, a value crosses. `judge/p/u1-confusion.hylo` is accepted by base, FIX and FULL:

```hylo
trait Tr1 { type X1
  fun get() -> X1
  fun put(x: X1) }
given <A> => A is Tr1 { type X1 = A
  fun get() -> A { self }
  fun put(x: A) {} }
fun q0(a: St0, b: St1) { b.put(a.get()) }     // an St0 reaches code that expects an St1
```

The control with two ground conformances (`judge/p/u1-confusion-ctl.hylo`) rejects the same call. `judge/p/u1-confusion-box.hylo` shows the same with `Box<A>`.

The campaign's own programs (`hand/blanket-5.hylo`, `minimized/unsound-blanket.hylo`) are accepted by all three configurations as stated. All 43 UNSOUND queries were read: each compares the associated type of the generic conformance on two different types.

### U2. Inside a trait, `Self.X` equals `T.X` for any other witness of a type equal to `Self` (FIX, FULL)

`hand/self/launder-5.hylo` is accepted by FIX and FULL. A trace shows what the campaign said: in the body of `cast`, `U ~ Self.X` is proved from `T.X == U` and from `T.X ~ Self.X` taken as reflexivity; at the call, `T is P` is discharged with `W`'s requirement and `Self` with `V`'s. The direct conversion (`judge/p/u2-c.hylo`) is rejected by all three configurations, as the negative test requires.

Two places hold the rule. `TypeStore.unifiable(_: AssociatedType, _: AssociatedType, ...)` unifies two projections of the same associated type when either qualification is abstract and the qualified types unify, whatever the other witness is. `Typer.solveEquality` binds an abstract projection to the projection through the only conformance given of the scope whose type equals `Self`. The caller chooses that witness independently of `Self`'s, so the equation does not hold.

The attribution needs care. The unsound step, accepting the body of `cast`, is in base (`hand/self/launder-5-def.hylo` and `hand/self/cast-only.hylo` are accepted by base). The whole program is accepted only with `eqsolve`: FIX without `eqsolve` rejects the call site (its message is the failure to discharge the three requirements of the call, which are in fact derivable), and base does not finish in 60 s. No program was found that passes a value of one concrete type as another.

### I1. An equality between compound types is not used under a constructor (base, FIX, FULL)

`minimized/inc-coerce-nested.hylo` and `minimized/inc-conf-eq-app.hylo` are rejected by all three configurations. Both goals follow from a requirement and congruence alone and are valid in every model. `TypeStore.unifiable` descends into two types of the same shape and hands only the innermost mismatching pair to the coercion handler of `Typer.match` (`T0` and `T1`), never the enclosing pair `St2<T0>`, `St2<T1>` for which the requirement exists. The remaining path in `coerced` tests only the two whole types against the requirements.

### I2. Types equal by congruence but not written in the where clause (base, FIX, FULL)

`minimized/inc-prefilter-coerce.hylo` is rejected by all three. The smallest form is `judge/p/i2-var.hylo`: under `where T0 == St1, T1 == St2<T0>`, a `T1` is not accepted where `St2<St1>` is expected, in either direction, although `needEq<T1, St2<St1>>()` is accepted and the conversion in two steps through `St2<T0>` is accepted. `Typer.canDeriveCoercions` refuses to attempt a coercion unless each of the two types is, syntactically, a side of some equality given; `St2<St1>` is not. The equality goal does not pass through that filter, which is why the two goals disagree. Base shows the same disagreement (`judge/p/ga-q0.hylo` accepted, `ga-q1.hylo` rejected). This class is ordinary transitivity through a type application, so it matters for real code.

### I3 and I4. A generic conformance is not found through an equality (base, FIX, FULL)

`minimized/inc-decl-head.hylo` is rejected by all three, in both orientations of the equality and also with a ground argument (`judge/p/i3-var.hylo`: `T0 == St2<St1>` with `given <A> => St2<A> is Tr0`). A ground declaration is found (`judge/p/i3-ground.hylo`). `Typer.match` records the pair `(St2<%a>, T0)` and asks `canDeriveCoercions`; `canDeriveCoercion` compares with `Typer.unifiable(_:_:)`, which is identity up to renaming of a universal context, not unification. The pattern `St2<%a>` with the declaration's open variable therefore never equals the side `St2<T1>`, and the declaration is dropped in the first layer.

I4 (`hand/proj-through-application.hylo`) is the same failure: the lookup of `T.X` summons `P<T>`, and `needP<T>()` in the same scope is rejected too (third query of that file). If I3 were fixed, the associated type would still be wrong because of U1.

The README said that one case of this class is "accepted by base and rejected by FIX and FULL". Base accepts that query with the conformance declaration deleted (`judge/p/ematch-q2neg.hylo`), where the goal is false. That is base's known unsoundness with unrelated equalities, not evidence that base has the rule.

### I5. `T.X1 == T` is rejected for a generic conformance with `type X1 = A` (base, FIX, FULL)

`hand/blanket-4.hylo` is rejected by FIX and FULL; the coercion forms (`judge/p/u1-a.hylo`, first two queries) are rejected by base too. Same cause as U1.

### A1. Selection between two symmetric witnesses depends on how `==` is written (base, FIX, FULL)

`hand/e01b-both-direct.hylo` is rejected and `hand/e01-orient-amb.hylo` accepted by all three. The trace shows two derivations in both; in the first they have equal penalties (ambiguity), in the second one is cheaper. `takeSummonResultsUnchecked` keeps the derivations completed in the first successful layer with the smallest penalty, and the cost of using an equality requirement depends on its orientation (a symmetry step). All 800 `twin` goals were checked with a second model: each has exactly two derivations. No associated type is involved, so this is not a type-safety problem; which witness is used does change.

### B1. Exponential search on a two-declaration program (FIX, FULL; base worse)

`hand/budget.hylo`, first query alone: 89,588 candidate matches, then the budget message, under FIX and under FULL. Base rejects the same query after about 55 s (indicative) with no bound. The premise `A == S0` of the declaration is assumed with `A` still open; `solveEquality` returns "not applicable" as soon as an equality given contains a variable, so the underivable `S0 ~ U` is searched with the built-in symmetry and transitivity rules. The abstract model of FULL does not refute it. No derivable goal of the campaign was rejected with this message (17 of 17 are invalid goals).

## Open questions, not defects

- **I6, order of requirements.** `where T.X == S, T is P` is rejected with "type 'T' has no static member 'X'" by FIX and FULL, and by base in the coercion form (`judge/p/wo-q1c.hylo`). Requirements are given their meaning left to right. Whether the language intends that is for its designers.
- **S1, tuple tail.** Accepting `{A, B, C} == {A, D, E}` from `{B, C} == {D, E}` is sound. It is inconsistent with the rejection of the coercion between the same types (I2) and of the mirrored goal.
- **Ranking in general.** The 324 goals with several derivations outside the `twin` kind have no expected verdict.

## Coverage, checked against the raw data

- `judge/tabulate.py` recomputes the tables from `problems.jsonl` and `results.jsonl` without the campaign's code. Every number checked agrees: 3,650 problems and 21,500 queries; FIX and FULL equal on all 21,500; 822 rejections of goals with one derivation (735 + 87); 43 + 12 + 6 acceptances of underivable or ill-formed goals, all in the `blanket` kind; 181 of 181 injectivity goals rejected; 17 budget messages; base on 920 queries with 4 unsound acceptances and 24 timeouts. `report.py --markdown` regenerates `tables.md` byte for byte.
- Batches: 525 (problem, configuration) pairs have both a batch run and a run alone, with no difference. I reran alone 24 more pairs chosen at random among those with only a batch run (`judge/recheck.py`): no difference.
- `judge/model.py` is a second model, written without the campaign's code, for the 17,600 queries without associated types. It agrees with the reference's grade on all of them. FIX and FULL accept none of the 8,192 invalid goals. No goal that the reference calls derivable is invalid.
- The absence of other unsoundness is therefore well supported for conformance and equality goals without associated types, in the generated shapes. For the 3,900 queries with associated types it rests on the reference alone. Of those I read the 43 unsound acceptances, the 6 acceptances graded ill-formed and 14 rejections of derivable goals, and found the reference's answer right in each. The 12 acceptances graded vacuous have the shape of U1, but I did not verify that their scopes have no solution, and the acceptances that the reference agrees with were not sampled.

What the campaign does not cover, and should not be read as cleared:

- Base ran on 920 queries, 720 of them without any equality. The campaign did not establish which incompleteness classes are in base; the reruns above do, for the minimised examples only.
- Smallest derivations have at most 5 conformance steps, so the depth bound of 10 was never approached. "The depth bound is not the cause" is true of these rejections and says nothing about deeper programs.
- Never generated: trait bodies and methods, extensions, type aliases, inferred type arguments, givens inside functions, generic equality givens, refinement, overloading, associated types on compound types, more than one associated type per trait. U2 and the wider form of U1 were both found by hand in exactly these gaps, so "outside those two places, no unsoundness was found" describes the generated fragment only.
- The 1,124 goals with several derivations test nothing except in the `twin` kind.

## Files of the judgement

| File | Content |
|---|---|
| `judge/run.py`, `judge/runs.jsonl` | reruns of single programs under the three configurations, with raw diagnostics |
| `judge/p/*.hylo` | the additional programs named above |
| `judge/tabulate.py` | independent tabulation of the raw results |
| `judge/model.py` | independent validity check for queries without associated types |
| `judge/recheck.py`, `judge/recheck.jsonl` | random reruns of batch-only problems |
| `judge/show.py` | prints the Hylo text of a generated query |
