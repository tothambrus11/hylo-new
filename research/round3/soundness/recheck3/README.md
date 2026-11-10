# Soundness re-check: undecidability and context-dependent resolution

This note re-examines the final configuration against two concerns:
- Implicit resolution is undecidable in general.
- The same goal can resolve differently in different contexts: under different assumed givens, inside different generic instantiations, or at different points of the evaluation order.

The question for each technique is whether its argument holds *per context* or only per scope. The re-check found five defects; all are fixed in binary `eq8-acc8f2fdf588` (patch 0012):

| Technique | Defect | Reachable today? | Fix |
|---|---|---|---|
| `absquotient` | Opacity was per *type*. A type outside the equalities, or an instance of a clause with variables, can be equal to a member of a non-trivial class without being abstracted as `⊤`. | Not through the current search (see §1.2), but the argument was wrong. | Opacity is per *constructor*. |
| `absquotient` | A nested scope whose parent used the quotient model, and which has a non-ground equality, reused the file-level model. That model ignores every local given. | Yes, if such a given can be written. | A nested scope never reuses the file model. |
| `eqsolve` (abstract projections) | The "unique concrete class" rule was computed from the goal's term graph, including assumed givens. It was context-dependent and non-monotone: assuming more could retract an equality. | Yes, in principle. | The rule is decided from the scope's givens only. |
| `eqsolve` (premise projections) | A premise resolved ahead of time could see variables bound differently later. A projection left unresolved (nesting limit, ambiguity) still let `eqsolve` *refute*. | Yes, in principle. | Closed environments only. A refutation that depends on an unresolved projection is not trusted, and search decides. |
| `givencheck` | The post-check matched the skipped given with an empty environment, although the skip happened under assumed givens. | Yes, in principle (a missed circularity). | The environment is kept with the record. |

## 1. `absquotient`

### 1.1 What must hold

`absmodel` refutes a subgoal `G`, posed in scope `s` under assumed givens `H`, when `G`'s abstraction unifies with no fact of the model of `s`. The model ignores `H`. That is sound by a **cut argument**:
- Every assumed given is discharged before a thread completes, either as a premise or as a coercion assumption made by `match`. Each is discharged from the givens assumed before it, and the oldest from none.
- So in a completed thread, every element of `H` is derivable from the givens of `s`. Then `G` is too: replace each use of a hypothesis by its derivation.
- If `G` is not derivable from `s`, every thread that needs `G` fails, and pruning it changes no result, no penalty and no layer that has results.

The model must therefore over-approximate derivability from `s` alone, in the theory used by resolution, which includes the equalities of `s`. Two properties hold whatever the context:
- **Undecidability is not an issue for soundness.** The model is an over-approximation computed in a finite domain (depth-k truncation); it never claims a goal *is* derivable.
- **The depth cap only removes derivations**, so over-approximating cap-free derivability is enough.

### 1.2 The defect

With ground equalities `E`, a term `X` and a term `Y` that are equal in the congruence closure of `E` must get unifiable abstractions. The first version abstracted as `⊤` exactly the *types* that occur in a non-trivial class of the closure of the subterms of `E`. That is not enough:
- `E = {Box<X> == Opt<Y>, Z == X}`. `Box<Z>` is not a subterm of `E`, but it equals `Box<X>`, which equals `Opt<Y>`. `Box<Z>` was abstracted as `Box(⊤)` and `Opt<Y>` as `⊤`. Here they still unify, but:
- With the clause `<T where Opt<T> is Q> Wrap<T> is P` and the fact `<T> Box<T> is Q`, the premise `Q(Opt(v))` never unifies with the fact `Q(Box(v))`. Yet for `T := Y`, `Opt<Y>` equals `Box<X>`. The model refutes `P<Wrap<Y>>`, which is derivable in the theory.

This is the "different contexts" problem in its pure form. Whether two terms are equal depends on which instance of a clause is considered. The opaque set was computed for the terms of the equalities, not for every term a derivation can build.

**Why no program shows it today.** For a conformance goal, `match` decomposes `Q<Box<X>>` against `Q<Opt<Y>>` down to the constructor pair `(Box, Opt)`, and `canDeriveCoercions(Box, Opt)` is false. So the current search never exploits an equality between two compound types with different constructors (`recheck3/probe2.hylo`: the baseline and every configuration reject `needq<Opt<Y>>()` under `Box<X> == Opt<Y>, Box<X> is Q`). The coercions search can form always have a side in a non-trivial class, which the old opacity did cover. So the old flag was sound only because of an incompleteness of search, and it would become unsound as soon as search improved. `recheck3/aq*.hylo` are the programs of the argument.

### 1.3 The fix

A *constructor* is opaque if some member of a non-trivial class is built with it: a nominal type, a generic parameter, a tuple cons, the empty tuple, a trait application. Every application of an opaque constructor is abstracted as `⊤`, in clauses, in facts and in queries.

**Soundness.** Let `X ≡ Y` in the congruence closure of `E`, and normalize terms by the closure.
- At the topmost position `p` where `X` and `Y` differ, both `X|p` and `Y|p` normalize to one non-trivial class `C`.
- `X|p` is either a member of `C`, or congruent to one, and then built with the same constructor. Either way, its constructor is the constructor of a member of `C`, so it is opaque. The same holds for `Y|p`.
- So the abstractions of `X` and `Y` are equal above `p` and `⊤` at `p`, and they unify.

The abstraction depends only on the constructor at each node, so it commutes with substitution: `α(t[σ]) = α(t)[α ∘ σ]`. Every instance of a clause therefore maps to an instance of the abstract clause, and the least-model argument of `absmodel` goes through unchanged. Assumed givens are covered by the cut argument of §1.1.

**Cost.** The fix is coarser. `Box<X> == Opt<Y>` erases every `Box` and every `Opt` term in that scope. An equality between generic parameters (`A == B`, by far the common case) only erases `A` and `B`, as before. `div-eq-ovl-b3-1` still takes 4.7 ms under FULL.

### 1.4 The nested-scope defect

A nested scope can have a non-ground equality given while its parent has only ground ones. Before the fix, the parent's model had an opaque set, so it was not reused, and the code fell through to the *file-level* model. That model lacks every local given, so it under-approximates the scope and can refute derivable goals.

A nested scope now never takes the file-level model. It builds its model from scratch, and the non-ground equality makes that model inconclusive.

## 2. `eqsolve`

### 2.1 The base theory is decidable, and refutation is exact for it

Equality of ground terms in the congruence closure of finitely many ground equations is decidable (Nelson–Oppen, Downey–Sethi–Tarjan). That is the only thing `eqsolve` decides.

Every source of undecidability makes it give up (`notApplicable`), and search decides instead, as in the baseline:
- open variables in the goal, which would be rigid E-unification;
- quantified or conditional equality givens, which would be the word problem;
- a given with a bare-variable head.

The facts include the *assumed* equalities of the context. They are hypotheses, and the cut argument of §1.1 applies: a proof that uses them is valid only if they are discharged. So deciding with them is resolving *in that context*, which is what search does too.

### 2.2 Abstract projections: a context-dependent rule (fixed)

`(Self::P).X` is equal to some concrete projection `(T::w).X`; `v-abs-7.hylo` needs this. But if it were equal to *every* one with `T == Self`, then `T.X == U.X` would follow for two distinct witnesses, which `associated-type-inequality.hylo` forbids. Review2 therefore made the merge conditional on a *unique* concrete class. That rule was computed from the graph of the goal, which also contains the assumed givens and their subterms. The result:
- **It was context-dependent.** The same goal `X ~ T.X` in the same scope was proved in one thread and refuted in another, depending on whether an assumed equality happened to mention `U.X`.
- **It was non-monotone.** Assuming more could retract an equality, which breaks the cut argument: a subgoal derivable from the scope was refuted under hypotheses.

The rule is now decided from the scope alone:
1. Compute the closure of the scope's own equality givens, without the assumed ones and without the goal.
2. Collect the scope's conformance givens to `P`, excluding the trait's own abstract `Self` given.
3. If **exactly one** of them has a type `P<T>` with `T` equal to `Self`, then `(Self::P).X ≡ (T::w).X` is added as a fact.
4. Otherwise no merge is made: a conditional, generic or wildcard given to `P` counts as ambiguous.

The rule is now a fixed axiom set per scope, so it is the same in every context, and adding hypotheses only adds facts (monotone). Results:
- `v-abs-7` is accepted;
- `abs-trans-2/3/4/5` and `ati` are rejected;
- the tautology `Box<X> == Box<X>` no longer changes anything.

### 2.3 Premise projections: resolved ahead of time (made context-stable)

`(T::$k).X`, through a premise `$k : P<T>` that is not discharged yet, is merged with `(T::w).X`, where `w` is the unique result of resolving `P<T>` in the environment in which `$k` will be discharged. That environment is the givens assumed before `$k`, because premises are discharged last-in, first-out. Two gaps remained:
- **Open variables.** `P<T>` or a given of that prefix could contain variables bound later. The early resolution could then pick a witness that the actual discharge, with more variables bound, would not pick. Now `P<T>` and every given of the prefix must be closed after substitution; otherwise the projection stays unresolved.
- **Refuting on an unresolved projection.** A projection the procedure cannot resolve could be refuted: the nesting limit (2) is reached, the resolution is ambiguous, or the environment is open. Whether the goal was refuted then depended on how deeply the query was nested. Now a refutation is trusted only if every premise projection of the graph was resolved. Otherwise `eqsolve` returns `notApplicable`, and search (sound with `fixsubst`) decides.

A related fix: a where-clause using is referred to through its implicit binding (`.reference(v)`, not `.user(d)`). Premise projections are therefore now recognized by comparing *witness values* with those of the visible givens. Before, a visible using could be mistaken for a callee's premise, and the new guard then wrongly distrusted the refutation of `abs-trans-2/3`.

### 2.4 What is still a choice, not a theorem

- `eqsolve` does not use injectivity (`Box<A> == Box<B>` does not give `A == B`), and neither does search. This keeps the two consistent.
- An associated type through a *concrete* conformance (`(Int::w).X`, where the conformance defines `X = Bool`) is an atom. If such a term is not normalized before resolution, `eqsolve` may refute `(Int::w).X ~ Bool`. That is incompleteness (rejection), and the baseline's search does not prove it either.

## 3. `eqmgu`

A goal `?v ~ X`, with `?v` not occurring in `X`, is solved by `?v := X` alone. That binding is the most general solution, and it does not depend on the context.

The baseline would sometimes have bound `?v` to another member of `X`'s class: a visible fact `X ~ B` has a smaller penalty than reflexivity. The types are equal in the theory, and every later implicit goal is transported along proved equalities, so no new program is accepted. But a later step that compares types *syntactically* could see `X` where the baseline saw `B`.

The corpus oracle and the review programs show no such case. It is recorded here as a deliberate deviation in favour of a context-independent choice.

## 4. `extorder` and `givencheck`

Both skip a declaration whose type is being computed, then check the skip once the final types are known, using `mayMatch`. `mayMatch` over-approximates `match`: the heads unify up to coercions that `canDeriveCoercions` does not rule out.

- **`extorder`.** Its lookups run outside any resolution, so the empty environment is exact. The verdict is computed per cycle group from final extendees, so it does not depend on which member was entered first (see `techniques/extorder.md`).
- **`givencheck`.** The skip happened inside a resolution with assumed givens. `canDeriveCoercions` with an empty environment can say "no" where that environment would say "yes", which would miss a circularity. The environment is now recorded with the skip and used by the check.

## 5. `budget`

Abandoning a resolution is reported as an error, so it can only reject the program, in every context. Whether a resolution reaches the limit depends on the configuration: FIX has no `absmodel` to prune. That is the one place where FIX and FULL can disagree, and both outcomes are sound.

## 6. Re-validation

All figures are for binary `eq8-acc8f2fdf588`:
- **Oracle.** 216/216 identical for FIX and FULL (`../oracle-final-config.txt`).
- **Review programs.** The sweep over the 520 programs is in `../regress-final.md`.
- **Key verdicts:**
  - `v-abs-7`, `x10b`, `o2b`, `e04`, `e06` and `gvalid` are accepted;
  - `abs-trans-2/3/4/5`, `ati`, `absinst-0`, `gz1`, `gx1` and `ge1` are rejected;
  - performance cases are unchanged (`div-eq-ovl-b3-1` 4.7 ms, `p02` 59 ms, `open-wide-4` 222 ms).
