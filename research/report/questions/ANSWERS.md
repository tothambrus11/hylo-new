# Answers of the language designer, and what follows from them

The eighteen questions of `../START-HERE.html` were answered on 13 November 2026. This document records each answer as given, what it means for the fixes, what was checked, and what was changed. Three of the answers contradict an assumption of the fixes (2, 8, 13), two expose a defect in them that is not yet repaired (6 and 10 together), and three ask for something that neither the existing implementation nor the fixes do (4, 13, 14).

## Summary

| # | Question | Answer | Assumed by the fixes | Consequence |
|---|---|---|---|---|
| 1 | Are conformances coherent across equal types? | No | No | None |
| 2 | Is `Self.X` equal to `T.X` when `T == Self` and `T is P`? | Yes; the answer depends on the shape of the proof, not on the presence of a witness | No | **Open.** With the answer as stated, a program converts a `C` into a `B`; see below |
| 3 | What do equalities between concrete types mean? | `A == B` is the type of a witness; a clause that cannot be satisfied cannot be called. Injectivity is not implemented. Congruence closure is a concern (undecidable) | Same | None for the behaviour; the concern is answered below |
| 4 | Are the members of `A` available on a `T` when `T == A`? | Yes | Not addressed | **New work**: today such a member is not found |
| 5 | How should a trait state an equality? | No syntax yet; probably `given A == B` | Not addressed | Such equalities are not closed; see question 3 |
| 6 | Does anything depend on the shape of an equality proof? | Yes: the size of a proof is a disambiguation criterion | No | **Defect found, open**: the equality procedure changes the ranking; a correction exists but costs too much; see below |
| 7 | Is the order of requirements significant? | Yes | Yes | None |
| 8 | Which witness does a requirement get? | Whichever satisfies the whole clause | The one that resolving it alone gives | **Changed**: `premcommit` is removed from the recommended configuration |
| 9 | Is an associated type through a declared conformance equal to its definition? | Yes | Yes | None |
| 10 | Is the ranking through equalities intended? | Yes; symmetry makes the proof longer | Yes | Same defect as question 6 |
| 11 | Is the bound of ten steps part of the language? | No | Kept as it is | Valid programs rejected at the bound are defects; the bound should become an error or disappear |
| 12 | May the types of extensions and givens depend on each other? | Yes | Yes | None |
| 13 | May a given be a candidate in its own initializer? What is a given with an inferred type worth? | No; it is worth the value of its initializer | Not fixed | **Implemented as an experiment** (option 5 of `../experiments/inferred-givens`) |
| 14 | Does the order of givens in a body matter? May a where clause name a declaration of the body? | No and no | No; not addressed | **New work** for the second part: today such a clause is accepted |
| 15 | Is the nested ranking of overloads intended? | Yes, closest wins | Preserved | None |
| 16 | Should a solution with more errors stay viable? | It does not matter | Preserved | Freedom to prune |
| 17 | Should a member and the requirement it implements be two candidates? | Probably not | Both kept | Removing one at the source makes `twins` unnecessary |
| 18 | Are the diagnostics of an ill-typed statement part of the contract? | Needs examples | Preserved | Examples provided below |

## Question 2: `Self.X` and `T.X`

The answer is yes, with the remark that what matters is the shape of the proof that selects `X`, not whether a witness is present.

The fix (`abstractstrict`) already follows a rule of that kind: inside a trait, `Self.X` is equal to `T.X` when `T.X` is selected through the trait's own witness, transported along `T == Self`. That is the case when `T == Self` is the only requirement, since the trait's witness is then the only proof of `T is P`:

- `follow-up/r2b`: `fun cast<T where T == Self>(x: T.X) -> X { x }` is accepted by the existing implementation and by the fix, and a caller that passes a value of another type is rejected.
- `follow-up/r2c`: the same with a value of the right type is accepted.

The question was about the other case, where `T is P` is written as a second requirement. Then `T.X` is selected through that requirement, which is the nearest and shortest proof of `T is P`, and the caller satisfies it independently of the receiver's conformance. If `Self.X` and `T.X` are equal there, the following program is well typed (`follow-up/r2a`):

```hylo
trait P {
  type X
  fun cast<T where T == Self, T is P>(x: T.X) -> X { x }   // (1)
}
struct A { public memberwise init }
struct B { public memberwise init }
struct C { public memberwise init }
given A is P { type X = B }
fun h<S where S is P, S == A>(s: S, c: C) -> S.X {
  given A is P { type X = C }
  return s.cast<A>(c)                                      // (2)
}
fun top(a: A, c: C) -> B { h<A>(a, c) }                    // (3)
```

`top` receives a `C` and returns it as a `B`. In (3) the requirement `S is P` is the module's conformance, for which `A.X` is `B`. In (2) the receiver carries that conformance, and `T is P` is satisfied by the local one, for which `A.X` is `C`. In (1) a `T.X` is returned as a `Self.X`.

| Configuration | `r2a` |
|---|---|
| Existing implementation | rejected at (2): "cannot pass value of type 'C' to parameter '(A::P).X'" |
| Fixes, with the original rule for `Self.X` | **accepted** |
| Fixes, with `abstractstrict` | rejected at (1) |

The existing implementation rejects the program for a reason unrelated to the rule: it does not reduce an associated type in the signature of a callee, which is the limitation described in `../completeness/2-projections-in-signatures.md`. Once callers can use such signatures, which the answer to question 9 requires, the original rule accepts the program.

So one of the three lines must be an error. The fix chose (1). If the intended answer is that (1) is well typed, then (2) must be rejected, which needs a rule that is not in the implementation: when `T == Self`, the requirement `T is P` may only be satisfied by the receiver's own conformance. **This is the question to return to the designer**, with the program. `abstractstrict` stays in the recommended configuration until it is settled, because the alternative is unsound as implemented.

## Question 3: congruence closure and decidability

The concern is justified in general and does not apply to what is implemented. The procedure computes a congruence closure only over the *closed* equalities visible from a scope and the subterms of the two closed types of the goal: the word problem for finitely many ground equations, which is decidable. It uses no injectivity, as the search uses none. It does not apply, and the search runs as before, when:

- the goal contains unification variables;
- an equality in scope is generic or conditional (`given <T> => F<T> == G<T>`), which is the undecidable case;
- a given in scope could conclude any type.

An equality stated by a trait (question 5, `given A == B` inside a trait) is of the second kind: it holds for every conforming type. Scopes that see such an equality fall outside the procedure, and the techniques that rely on closed equalities (`eqindex`, `coeset`) fall back as well. How such equalities should be decided, and with what bound, is open.

## Questions 6 and 10: the size of a proof

The answers say that derivations are ranked by their size and that a proof using symmetry is longer. The fixes were meant to preserve the ranking, and the report says that they do. **They did not.**

In the existing implementation, a derivation completes at the layer equal to the number of givens it uses, and the first layer with a result wins. An equality proved by search takes one layer per rule: a fact used as written takes one, a fact used backwards takes two (symmetry, then the fact), a chain takes more. The decision procedure (`eqsolve`) returned its proof in one layer whatever its size, so a derivation that needs a non-trivial equality completed earlier than it would have, and could beat a derivation that it should tie with or lose to.

`../test-programs/equalities/pen-ref-3.hylo` shows it:

```hylo
trait P { type X }
trait Q1 refines P {}
trait Q2 refines Q1 {}
trait Q3 refines Q2 {}
struct A { public memberwise init }
fun f<V, W where W == V, W is Q3>() {
  given V is P { type X = A }
  let z: W.X = A()
}
```

`W is P` has two derivations: through the three refinements, and through the local given coerced along `W == V` used backwards. The existing implementation completes both in the fourth layer and reports the ambiguity. With `eqsolve` the second completed one layer earlier and the program was accepted. The index of that folder has recorded the difference since the procedure was written; it was not recognized as a change of ranking.

**A correction was tried (`eqsize`, about 40 lines) and is not adopted.** A proof returned by the procedure waits as many layers as its derivation has steps, so that it completes where search would have completed it; the waiting layers do not count against the depth bound. On the 1,696 programs of the corpus:

- `pen-ref-3` is ambiguous again, as in the existing implementation; `pen-ref-1`, `2` and `4` and the programs of question 10 are unchanged; the output on the compiler's tests is identical (216 of 216 files);
- two programs that were accepted are rejected (`../test-programs/performance/pending-var-3` and `pending-var-4`). While the proof waits, the search for the other goals of the resolution, which the early answer used to cut short, runs on: `pending-var-4` goes from 782 candidate matches to 171,221 and ends at the work budget, where the existing implementation accepts it after 102,150.

So the simple correction gives the ranking back and takes the performance away where an equality with an inferred side is searched next to a decided one. It stays behind its flag as an experiment (`../experiments/proof-size`).

The correction is also not exact. For 298 equalities that both the procedure and a search within its limits prove, search completes in the layer that the procedure reports in 227 cases, earlier in 26 and later in 45: search can prove an equality in ways whose size the procedure does not reproduce, in particular by matching a fact up to a coercion of its parts, whose own proofs are then dropped from the term.

**What is needed** is a definition of the size of a proof that does not depend on how the search happens to explore, so that the procedure can compute it directly: for instance the number of facts, symmetries and transitivities in the smallest derivation. Two questions for the designer follow:

- *Which size?* The layer at which the search completes a derivation, or the size of the smallest derivation in the calculus? They coincide in simple cases only.
- *Term size in name resolution.* Separately from the layers, two candidates of a name at the same lexical distance are ordered by the size of the witness term through which each is found (`elaborationCost`). The procedure builds larger terms than search for the same equality. This criterion decides comparisons in the standard library (19) and in 22 of 1,196 test programs; a coercion is involved in 3 of them. No verdict depends on it in the corpus, but the two measures of size can disagree, and it is not clear which one is meant.

Until then, the known effect on the corpus is one program (`pen-ref-3`), accepted where the language says it is ambiguous.

## Question 8: the witness of a requirement

The answer is the reading that the fixes had rejected: the requirements of a clause are solved together, and any witness that satisfies the whole clause will do. The mechanism for dependent requirements (`premsubst`) was first built that way; the commit rule (`premcommit`) was added after an adversarial review that took the other reading for granted.

`premcommit` is removed from the recommended configuration. On the 1,691 programs of the corpus, 27 change from rejected to accepted and none in the other direction, with no violation in the self-checking mode. They are the programs in which a nearer conformance does not satisfy the clause and a farther one does, among them question 8's `q08`, and:

- **a known limitation disappears**: a recursive call made in a scope that declares a nearer conformance for the function's own requirement (`follow-up/attack-premsubst/p/j04`) is accepted, with the function's own requirements passed for both;
- `g<T, U where T == U, T is P, U is P, T.X is Q>() { f<U>() }`, with `f<V where V is P, V.X is Q>`, is accepted: `V is P` is satisfied by the requirement on `T`, transported along `T == U`.

In one of them (`e07`) the review had predicted that a method would run on a value of the wrong type. The trace shows that the conformance passed is the one that satisfies the clause, so the types are consistent. Soundness does not depend on the choice between the two readings, because an associated type always records the witness through which it is selected; only which programs are accepted does.

## Question 13: a given and its own initializer

The answer has two parts: a given is not a candidate in its own initializer, and a given with an inferred type is as good as any other.

- The second part rules out the first option of `../experiments/inferred-givens` (requiring a written type).
- The first part is not what happens today for a given with a written type. `q13b`, in which a given is the only candidate for the goal of its own initializer, is accepted by the existing implementation and by the fixes: the given is hidden only while its *type* is computed, and a written type needs no computation. By the answer it should be rejected.
- The fourth option of the experiments (inferred givens as entries of the table of signatures, with a check for initialization cycles) makes verdicts independent of declaration order but lets a given see itself, and therefore rejects `q13a`, which by the answer is valid.

What the answer calls for is a lexical rule: a resolution made inside the initializer of a given does not see that given, whatever is being computed at the time. With visibility read from the table everywhere else, this keeps the order independence of the fourth option and accepts `q13a`.

**Implemented as `givenself`** (about 30 lines), after the pattern that the compiler already uses for conformances: `anonymousImplementation` hides a conformance around the one resolution that finds the traits it refines. Combined with the fourth option (`givenself,givennodes,givencycle`):

- `q13a` is accepted, `q13b` is rejected, `q13c` is accepted in all 24 orders;
- 38 programs about givens have one verdict in every order, with no self-check violation;
- on 1,708 programs, 10 verdicts change, all about the initializer of a given; the output on the compiler's tests is identical (216 of 216 files).

It is not yet part of the recommended configuration. Details: `../experiments/inferred-givens/README.md`, option 5.

## Question 14: where clauses and bodies

The order of givens in a body does not matter: this is what the fix for declaration order does. A where clause may not name a declaration of the body it governs: today `q14c` is accepted by the existing implementation and by the fixes, and two test programs of the design for declaration order expect that. Rejecting it needs a check in name lookup. It is not implemented.

## Questions 4, 11, 16, 17

- **4.** Members of `A` on a `T` with `T == A`: member lookup has to consult the equalities in scope and coerce the receiver. Not implemented.
- **11.** The bound is not part of the language. The programs that it rejects (`q11b`, `q07b`) are then valid programs wrongly rejected, and a resolution that ends at the bound silently, after which another member is selected (`q11c`), is a defect. The experiment `heightbound` accepts the first two. The cleaner course is to replace the bound by a work budget whose exhaustion is an error, which the flag `budget` already provides for the size of the frontier.
- **16.** Whether an erroneous solution stays viable does not matter, so the search may drop it. Not used yet.
- **17.** If name resolution kept one candidate for a member and the requirement it implements, the solver would not fork on them. `twins` then becomes unnecessary for the operator chains; it still shares work between other candidates of the same type.

## Question 18: examples

`follow-up/r18a`: `g(h(), h())`, where `g` takes an `A0` and a `Z` and no candidate of `h` returns a `Z`. Three diagnostics are reported: "ambiguous use of 'h'" for each of the two calls, and "cannot pass value of type 'A0' to parameter 'Z'". Only the third describes the mistake. In a variant where the type of the parameter is changed so that the last candidate is the matching one, two are reported.

`follow-up/r18b`: seven arguments, one of which cannot be satisfied. Six diagnostics, five of them "ambiguous use of 'h'", after 3,279 forks of the solver. A search that stops at the argument that no candidate satisfies would report one diagnostic after a handful of forks.

The question is whether an implementation may report only the last diagnostic in such cases. The ambiguities exist only because every combination ends with an equally bad score.

## What was checked

| Check | Result |
|---|---|
| Recommended configuration without `premcommit`, against with, 1,691 programs, self-check on | 27 rejected → accepted, none the other way, no violation |
| The same on the compiler's tests: semantic dump against the existing implementation | identical, 216 of 216 files |
| Expected verdicts of 152 regression programs, with the 8 that the joint reading accepts updated | 152 of 152 |
| `r2a` with the original rule for `Self.X` and without it | accepted and rejected, as described under question 2 |
| `eqsize` added, 1,696 programs, self-check on | 3 verdicts change (above), no violation |
| Comparisons of name-resolution candidates decided by witness size | counted on the standard library and 1,196 programs (above) |

Data: `../follow-up/data/answers/`.

## Configuration after the answers

The recommended configuration is the previous one without `premcommit`:

```
index,typevec,symindex,traitindex,memberskip,twins,stackscan,coeset,reifymemo,occurs,fixsubst,eqsolve,eqmgu,arrowenv,budget,sigrounds,assocsubst,abstractstrict,hidecache,aliasargs,premsubst,headsubst,dedup,eqindex,eqeager,cleanfirst,lookahead
```

`abstractstrict` stays until question 2 is settled. `report.html` and the timings in it describe the configuration before the answers; the sections that this document supersedes are "Requirements that mention another requirement" (the commit rule), the limitation "Recursion under a shadowing conformance", and every statement that the fixes preserve the ranking of derivations through equalities.

## Work that the answers call for

| Item | From | Size |
|---|---|---|
| Settle `Self.X` (which of the three lines of `r2a` is the error) | 2 | a question, then a rule of about 20 lines either way |
| A given is invisible in its own initializer; inferred givens as entries of the table | 13 | **done as an experiment** (`givenself,givennodes,givencycle`); to be adopted or not |
| A where clause does not see the declarations of the body it governs | 14 | a check in name lookup |
| Members of `A` on a `T` when `T == A` | 4 | member lookup and receiver coercion; the largest item |
| Replace the bound by a budget that reports an error | 11 | the mechanisms exist (`budget`, `heightbound`); the default must change |
| One candidate for a member and the requirement it implements | 17 | in name resolution |
| Decide what "size of a proof" measures, and make the equality procedure report exactly that without searching | 6, 10 | depends on the answer; the open defect of this document |
| Equalities stated by traits | 5 | syntax, and a decision procedure for non-closed equalities with a bound |
