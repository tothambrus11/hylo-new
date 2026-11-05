# `absmodel`: depth-k abstract least model (a sound "resolution will fail" test)

This is the answer to the original question: a sound and cheap procedure that conservatively decides when implicit resolution will fail.

## How it works

Every given `<X…> A1, …, An ==> H` is read as a definite Horn clause `H :- A1, …, An` over first-order terms:
- nominal types and type applications become function symbols;
- tuples become cons/empty;
- generic parameters of the given become variables;
- every other type (arrows, associated types, existentials, higher-kinded heads, …) becomes `⊤`, meaning "any term".

Whatever `summon` derives is a ground instance in the least Herbrand model of these clauses, whatever the search order and the depth cap. That model is infinite (`P<Z>`, `P<S<Z>>`, …), so it is computed in the finite domain of **terms truncated at depth k** (Sato–Tamaki). Below depth k, subterms become `⊤`.

**Saturation.**
- It is semi-naive bottom-up Datalog evaluation.
- Facts are bucketed by head constructor and kept modulo subsumption.
- Models are incremental along the scope tree: a child starts from its parent's model, which is valid because least models are monotone.
- File-level models are shared between files that import the same modules.

**Use.** At every subgoal, `mayDerive(goal)` is consulted. If the goal unifies with no fact, the subgoal is refuted, and no thread is formed for it.

**Conservative cases.**
- Equality goals are never refuted.
- Equality premises are assumed to hold.
- Any user given whose head is an equality or a bare variable makes the model inconclusive, so that model refutes nothing.

## Why it is sound

1. **Over-approximation.** Truncation is monotone, and `⊤` unifies with everything. Dropping premises only adds facts. So every concrete derivation maps to an abstract one, and refuting the abstract goal implies the concrete goal is underivable.
2. **Fixed in round 2:** subsumption must not treat `⊤` as a constant. A fact `R(v, v)` used to subsume `R(⊤, ⊤)`, but the two `⊤`s denote unrelated terms. A repeated variable now never matches a term containing `⊤`. Counterexamples t02, t03 and t23 were refuting derivable goals.
3. **Fixed in round 2: no cyclic substitutions.** Bottom-up saturation can unify `T` with `S<T>`, which the concrete (top-down) search never does when no such goal is posed. Without an occurs check this built a cyclic substitution and overflowed the stack (t01 and t18 crashed). Binding a variable to a term containing it now binds it to `⊤`, which over-approximates the rational solution.
4. **Fixed in round 2: file models keyed by imports.** Visible givens depend on each file's imports, so a model built for one file must not be reused by a file that imports more.
5. **Fixed in round 2: renaming apart.** Fact variables are renamed to negative numbers, so they can no longer collide with clause variables (≥ 0) on long saturations.
6. **Result-preserving pruning.** Refuted subgoals have no derivation, so they contribute no result in any layer, and pruning them leaves the selected result, the penalties and any ambiguity unchanged.
   - What changes: fewer BFS layers. A goal that the baseline rejects after exhausting the depth cap is rejected immediately.
   - Is the diagnostic still the same? Yes: `summon` reports nothing itself, and the caller reports "no given instance" in both cases.

Oracle:
- identical on all 216 corpus files;
- identical on the 25 absmodel review programs at k=2 and k=3 (the pre-fix binary failed on t01, t03 and t18).

## What it speeds up

Failing or divergent resolution. Those searches no longer run to the depth cap:

| Workload | Baseline | `absmodel` |
|---|---:|---:|
| div-loop-20 (`P<T> ⇒ P<T>` loops) | 195 ms | ≈5 ms |
| div-grow-20 (`P<S<T>> ⇒ P<T>`) | 200 ms | ≈5 ms |
| div-dead-20 (mutual dependency, no base case) | 187 ms | ≈5 ms |
| stdlib: subgoals refuted | — | 225 |

Measured alone (`../round3/bench.md`):
- stdlib 1007 → 787 ms (1.3×);
- members-big 20.1 → 15.4 s;
- div-loop-20 191 → 16 ms;
- **div-branch 2220 → 15 ms (150×)**.

The depth-cap scan (`../round3/README.md` §4) shows that with `absmodel` the cost of refutable failures no longer depends on the cap: div-branch takes 44.5 s at cap 14 in the baseline and 3 ms with the sound set.

**Limit.** A base fact deeper than k makes the model derive `P(⊤)`, and then nothing headed by `P` can be refuted (`round3/depth/div-branch-trunc.hylo`). The search keeps pruning inner branches (24× fewer matches) but stays exponential in the cap.

It does nothing for:
- successful searches, which are only pruned where a sibling branch is dead;
- equality reasoning: goals are never refuted, and any `T ~ U` given makes the model inconclusive.

## Costs

- Saturation at k=2: ≈1.4k facts on the stdlib (a few ms), up to ≈6.5k facts on breadth80 (≈5% of its typing).
- k=3 explodes on tuple cons lists (≈14k facts, ≈10× slower stdlib) and refutes nothing more, so the default is now k=2 (`HYLO_TC_ABSDEPTH`).
- One `mayDerive` call per subgoal: a bucket scan with unification.
