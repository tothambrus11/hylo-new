# Equality by normalization: design study

## What was asked

Type equalities from where clauses (`A == B`, `T.X == U.X`) are used today through coercions inside implicit resolution, and four mechanisms exist because of that (`fixsubst`, `eqsolve`, `eqmgu`, `absquotient`), plus special cases in the index of givens and in `canDeriveCoercions`. The question was whether computing the equality classes of each scope once, and rewriting types to a canonical representative, would be simpler and at least as sound and complete; and if not, how the current congruence-closure procedure should be restructured.

## What was done

- The compiler source was read to find every place where an equality is consumed.
- About 75 small programs were written and run on the frozen type-checker binary under the existing checker (`base`) and with every technique enabled (`FULL`), some with the trace flag.
- A design was written: `DESIGN.md`.
- A test plan was prepared: `tests/`, 41 programs, each with the expected verdict after each stage of the design and its current verdict.

No compiler code was written or built.

## What was found

1. **Rewriting types to representatives is not safe in this checker.** Hylo selects a conformance by how the type is spelled. With `T == U`, `T is P` and `U is P` in scope, `T.X` and `U.X` are different types, and a compiler test requires it. After rewriting `T` and `U` to one representative, resolution has two candidates of equal rank, and an accepted compiler test becomes ambiguous. Swift can normalize because it assumes one conformance per type.
2. **The useful part of normalization needs no representative.** An equality between two closed types can be decided when the two types are compared, in `match`, and need never become a hypothesis that the search proves later. Types stay as the user wrote them.
3. **The current mechanisms reject three kinds of valid programs**, under both configurations unless noted:
   - a match with eight or more differing type arguments, each equal by a where clause (rejected by the depth bound under `FULL`; out of memory under `base`);
   - equalities that need a congruence step, or an equality between compound types used inside another type (`C == Box<A>`, `A == B`, value of type `C` passed as `Box<B>`);
   - a parameter or associated type stated equal to a concrete type, when a generic conformance of that concrete type is needed (`T.Element == Box<A>`, `given <T> => Box<T> is P`).
4. **One equality in scope switches the index of givens off** for every goal of that scope (4480 candidate matches instead of 1640 in a scope with 40 conformances).
5. **The choice between two conformances that apply through equalities depends on accidents**: on which side of `==` a type is written, and on how many arguments differ.

## The proposal, in one paragraph

Keep the congruence closure and stop routing closed equalities through the search. Stage 1 (about 110 lines, two flags) keeps the index enabled under ground equalities and decides the equalities of a match immediately with the existing `solveEquality`; by construction it returns what `FULL` returns today, except that programs rejected by the depth bound are accepted. Stage 2 caches the closure per scope and uses it as the exact test in place of the syntactic filter. Stage 3 matches types with unification variables against equality classes. Stage 4 removes the emulation of the search's ranking, if the language designers agree. The amount of code ends about where it is today; the gain is in behaviour, not in size.

## Files

| File | Content |
|---|---|
| `DESIGN.md` | The design: problem, inventory, options, hooks, correctness argument, test plan, implementation order, open questions. |
| `tests/*.hylo` | The test plan. The first comment of each program gives the expected verdict per stage; the line `// currently:` gives the verdict and counters under `base` and `FULL`. |
| `tests/current.jsonl` | Raw results behind the `// currently:` lines. |
| `record.py` | Runs the binary on `tests/` (one process at a time, restartable) and rewrites the `// currently:` lines. |
| `experiments/*.hylo` | Exploratory programs cited in `DESIGN.md` (member lookup, solver paths, trait syntax, widths 2 to 12). |
| `results.jsonl` | Raw results of the exploratory runs. |
| `run.py` | Runs programs under named configurations; `--trace` prints the derivations of the user module only. |

To reproduce a verdict: `python3 run.py --configs base,FULL --force tests/gain-04-congruence-then-fact.hylo`. To see a derivation: `python3 run.py --trace --configs FULL tests/rank-05-fewer-parts-first.hylo`.

## What remains uncertain

- Nothing in the design has been compiled. The claim that stage 1 preserves results rests on an argument and on traces; the design includes a self-check (run each resolution both ways and compare) to test it.
- Stage 2 lets givens match that could not match before. One constructed program becomes ambiguous for that reason; how often real code would is unknown.
- Eight questions are left to the language designers (section 9 of `DESIGN.md`). The first one, whether conformances are coherent across equal types, decides whether this design or true normalization is the right one.
- Traits cannot state equalities between associated types yet. When they can, those equalities will not be ground, and neither the current code nor this design handles them; the design says where the mechanism would go and why termination is the hard part.
- Timings were not measured: the machine was shared. Costs are given as work counters.
