# Questions on the language, with a program for each

The questions are stated in full in `../START-HERE.html`, section "Questions". This file lists the programs and what the type checker does with each. "Existing" is the implementation of `main`; "recommended" is the configuration of the report. `observed.txt` holds the raw output.

## Conformances and equalities

**1. Are conformances coherent across equal types?** (one of the questions that decide most)

With `T == U`, `T is P` and `U is P`, are the two requirements the same witness, so that `T.X` and `U.X` are the same type?

Programs: `q01-coherence.hylo`

- Today: Rejected, by the existing implementation and by the fixes. This is the compiler's negative test `associated-type-inequality`.
- Assumed by the fixes: No: two requirements are two witnesses, which may define `X` differently. Every fix follows this reading.
- Otherwise: If conformances are coherent, problem 7 below is not a defect, types can be rewritten to a representative of their equality class (rejected here as unsafe, because a conformance is selected by the way a type is written), and the restrictions of `abstractstrict` can be lifted.

**2. Inside a trait, is `Self.X` equal to `T.X` when `T == Self` and `T is P`?** (one of the questions that decide most)

`T is P` is a second requirement, which the caller satisfies independently of the witness that the trait stands for.

Programs: `q02a-self-projection.hylo`, `q02b-self-projection-conversion.hylo`

- Today: `q02a`: accepted by the existing implementation, rejected by the fixes. `q02b` uses the rule to convert a `W.X` into a `V.X` under the where clause of question 1: the existing implementation exhausts memory on it; with the equality procedure alone it is accepted; with the fix it is rejected.
- Assumed by the fixes: No, for consistency with question 1: a selection through the trait's own witness equals only a selection through that same witness (`abstractstrict`). Eight test programs of the shape of `q02a` are rejected as a result.
- Otherwise: If they are equal, the rule must be reconciled with question 1, since `q02b` performs exactly the conversion that the negative test forbids.

**3. What do equalities between concrete types mean?**

Does `Box<T> == Box<U>` give `T == U`? Is `where T == A, T == B`, for two distinct structs, an error where it is declared?

Programs: `q03a-injectivity.hylo`, `q03b-two-concrete-types.hylo`

- Today: `q03a` is rejected: type constructors are not injective for equalities. `q03b` is accepted: in the body, an `A` is passed where a `B` is expected. No caller can satisfy the clause. Both behaviours are those of the existing implementation and are unchanged.
- Assumed by the fixes: Nothing is assumed; the equality procedure reproduces both behaviours.
- Otherwise: Injectivity would be a new rule of the congruence closure. Rejecting `q03b` at the declaration would be a new check for clauses that equate two distinct nominal types.

**4. Are the members of `A` available on a `T` when `T == A`?**

Members of a trait are found through an equality; members of a struct, and its extensions, are not.

Programs: `q04a-struct-member-through-equality.hylo`, `q04b-trait-member-through-equality.hylo`

- Today: `q04a` is rejected ("type 'T' has no member 'foo'"), `q04b` is accepted. Unchanged.
- Assumed by the fixes: Nothing is assumed.
- Otherwise: If struct members should be found, member lookup has to consult the equalities in scope.

**5. How should a trait state an equality between its associated types?**

Swift's `Sequence` has `Iterator.Element == Element`. In a survey of the Swift standard library, swift-collections and Rust's iterator library, 6% to 24% of the functions have an equality in scope, mostly through traits.

Programs: `q05-equality-in-trait.hylo`

- Today: A syntax error: "expected 'is'".
- Assumed by the fixes: Nothing is assumed; the feature does not exist.
- Otherwise: An equality stated by a trait holds for every conforming type, so it is not ground. Two of the techniques (`eqindex`, `coeset`) rely on the equalities in scope being ground; they fall back to the general path otherwise and would need to be revisited.

**6. Does anything depend on the shape of an equality proof?**

The decision procedure builds the term of an equality proof differently from the search. On the compiler's tests, this is the only difference in the elaborated output (two files).

- Today: No program: the question is about later phases.
- Assumed by the fixes: No: any proof term of the right type is as good as another.
- Otherwise: If lowering, or a checker of derivations, needs a particular form, the procedure must build that form.

## Requirements of a where clause

**7. Is the order of requirements meant to be significant?**

A requirement is an assumption for the requirements written after it, so reordering a clause changes how many steps a call needs.

Programs: `q07a-where-order.hylo`, `q07b-where-order-swapped.hylo`

- Today: `q07a` is accepted (8 steps); `q07b`, the same program with the two requirements swapped, is rejected (12 steps, past the bound of question 11). Unchanged.
- Assumed by the fixes: The existing rule is kept.
- Otherwise: If the order should not matter, the requirements must be assumptions for each other in both directions, or in neither. The experiment `heightbound` accepts both programs by changing the bound instead.

**8. Which witness does a requirement get when another requirement mentions it?** (one of the questions that decide most)

For `where T is P, T.X is Q`: is the witness of `T is P` the one that resolving it alone gives, or may the second requirement select among the conformances in scope?

Programs: `q08-which-witness.hylo`

- Today: Rejected by both. The existing implementation rejects every call whose requirements mention an associated type of another requirement. The fix rejects this one because `A is P` alone resolves to the local conformance, for which `A.X` is `C`, and `C` is not `Q`.
- Assumed by the fixes: On its own: the requirement is resolved first, a tie is an ambiguity, and the dependent requirement is then proved for that witness (`premcommit`).
- Otherwise: Solving the requirements together accepts `q08` through the shadowed conformance of the module. Five programs of the test corpus differ between the two readings.

**9. Is an associated type selected through a declared conformance equal to its definition?**

In particular for a generic conformance, where the definition mentions the conformance's own parameters.

Programs: `q09a-generic-conformance-unsound.hylo`, `q09b-generic-conformance-valid.hylo`

- Today: `q09a` is accepted by the existing implementation: an `A` is passed where a `C` is expected. `q09b`, which is valid, is rejected by it. The fix reverses both.
- Assumed by the fixes: Yes: `A.X` through `given <T> => T is P { type X = T }` is `A`, with the arguments and the witnesses of the conformance substituted into the definition (`assocsubst`).
- Otherwise: Probably uncontroversial. One related case has no diagnostic: a parameter of a conformance that neither its head nor its requirements determine (`given <T, U> => Box<T> is P { type X = U }`) yields a fresh type at each use. Should it be an error at the declaration?

## Ranking and the bound on derivations

**10. Is the ranking of derivations through equalities intended?**

Which of two conformances wins depends on the side on which an equality is written, because penalties count pending requirements and a derivation that uses symmetry is longer.

Programs: `q10a-ranking.hylo`, `q10b-ranking-other-side.hylo`

- Today: `q10a` (`B == A, A == C`) is accepted; `q10b` (`B == A, C == A`) is rejected as ambiguous. Of 800 generated goals with two symmetric derivations, 408 are accepted and 392 reported as ambiguous. Unchanged: the fixes reproduce the ranking exactly.
- Assumed by the fixes: The ranking is treated as part of the language, and every technique was required to preserve it.
- Otherwise: If symmetric derivations should always be ambiguous (or never), the ranking can be defined on the equality classes, and the techniques no longer need to reproduce step counts.

**11. Is the bound of ten steps part of the language?** (one of the questions that decide most)

Does it bound the size of a derivation (all the givens used for a call) or its depth? Do the steps that prove equalities count? Is reaching it an error, or a silent failure after which another extension or overload is selected?

Programs: `q11a-bound-four.hylo`, `q11b-bound-five.hylo`, `q11c-bound-selects-member.hylo`

- Today: `q11a` (9 givens) is accepted. `q11b` (11 givens, valid) is rejected with "no coercion", without mention of the bound. In `q11c` two extensions apply, and proving so needs nine equalities for the first and eight for the second: the existing implementation exhausts memory; with the equality procedure alone the member of the second extension is called; in the recommended configuration, where equalities proved by the procedure are not counted, the member of the first is.
- Assumed by the fixes: The bound is kept as it is, on the size of a derivation, with silent failure. Equalities decided by the procedure are not counted (`eqeager`), which is the one intended change of behaviour among the performance techniques.
- Otherwise: The experiment `heightbound` bounds the depth instead and accepts `q11b` and `q07b`. If reaching the bound were an error, `q11c` would have one meaning.

## Declaration order

**12. May the types of extensions and givens depend on each other?**

Looking up the type that one extension extends can require the other extension, and conversely.

Programs: `q12-mutually-dependent-extensions.hylo`

- Today: The existing implementation accepts `q12` in 12 of the 24 orders of its declarations. The fix accepts it in all 24: it computes these types in rounds until they are stable, and reports the declarations for which no stable reading is found.
- Assumed by the fixes: Yes, when the iteration reaches a stable reading (`sigrounds`).
- Otherwise: A stricter rule, rejecting every such dependency, can be added as a check on the stable result. It would also remove the remaining unproved step in the argument that the overload techniques preserve results.

**13. May a given be a candidate in its own initializer, and what is a given with an inferred type worth outside a function?**

Today a given is hidden while its own type is computed, and a given without a written type is typed on demand, inside the first resolution that meets it.

Programs: `q13a-given-in-own-initializer.hylo`, `q13b-given-initialized-with-itself.hylo`, `q13c-inferred-given-order.hylo`

- Today: `q13a` is accepted: `w` is initialized with `other`. `q13b` is accepted by every configuration: a given with a written type is the only candidate for its own initializer. `q13c` is accepted in 15 of the 24 orders of its declarations, by the existing implementation and by the fixes alike.
- Assumed by the fixes: The fix for declaration order covers declarations whose type is written; `q13c` is not fixed.
- Otherwise: Four options were tried and none is adopted (`experiments/inferred-givens/README.md`). The simplest is a rule: a given declared outside a function must have a written type. The most complete one makes `q13c` independent of the order but rejects `q13a`, because the given then sees itself.

**14. Is the order of givens in a function body meant to matter, and may a where clause name a declaration of the body it governs?**

Givens declared in a body are visible in the whole body, before their declaration.

Programs: `q14a-givens-in-body.hylo`, `q14b-givens-in-body-swapped.hylo`, `q14c-where-clause-uses-body.hylo`

- Today: The existing implementation rejects `q14a` and accepts `q14b`, which differs in the order of two local givens. The fix rejects both: each given can shadow the top-level one that the other needs, and no stable reading is found. `q14c` is accepted by both.
- Assumed by the fixes: Local givens are treated like top-level ones, so their order does not matter.
- Otherwise: If the order in a body is meant to matter, local givens must be excluded from the rounds.

## Overload resolution

**15. Is the nested ranking of overloads intended?**

Only the outermost overloaded name of a statement is ranked across all combinations; the inner ones are ranked inside each choice of the outer one.

Programs: `q15-nested-ranking.hylo`

- Today: Accepted: `k(S.a(), S.b())` is an `X` and `k(S.b(), S.a())` is a `Y`. Unchanged.
- Assumed by the fixes: The existing ranking is preserved exactly.
- Otherwise: A ranking of whole combinations would be independent of the order of arguments.

**16. Should a solution with more errors than the best one stay viable?**

A preferred candidate with an error can win over one whose only diagnostic is a nested ambiguity.

Programs: `q16-erroneous-candidate-wins.hylo`

- Today: Rejected with the error of the preferred candidate ("cannot pass value of type 'B' to parameter 'A'"). Unchanged.
- Assumed by the fixes: The existing behaviour is preserved exactly.
- Otherwise: If only the candidates with the fewest diagnostics stayed viable, more of the search could be cut once a clean solution is known.

**17. Should a member and the trait requirement that it implements be two candidates?**

For a concrete receiver they denote the same function.

Programs: `q17-member-and-requirement.hylo`

- Today: Accepted. The existing solver makes 32,766 forks for 14 operators; with `twins`, which shares the search between two candidates of the same type, 14.
- Assumed by the fixes: Both candidates are kept, and the second reuses the result of the first.
- Otherwise: If name resolution kept one candidate, the exponential cost would disappear at its source and `twins` would not be needed.

**18. Are the diagnostics of an ill-typed statement part of the contract?**

May an implementation report a different, smaller set of errors for a statement that has none of the solutions?

- Today: No program: the question is about what must be preserved.
- Assumed by the fixes: Yes: an erroneous statement is solved by the existing search, so that its diagnostics are unchanged. The overload techniques therefore speed up well-typed statements only.
- Otherwise: If the set of diagnostics may differ, erroneous statements can be made fast as well.
