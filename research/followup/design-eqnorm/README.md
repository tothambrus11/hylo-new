# Equality by normalization: design study and review

## What was asked

Type equalities from where clauses (`A == B`, `T.X == U.X`) are used today through coercions inside implicit resolution, and four mechanisms exist because of that (`fixsubst`, `eqsolve`, `eqmgu`, `absquotient`), plus special cases in the index of givens and in `canDeriveCoercions`. The question was whether computing the equality classes of each scope once, and rewriting types to a canonical representative, would be simpler and at least as sound and complete; and if not, how the current congruence-closure procedure should be restructured.

A second task was to review the resulting design adversarially: check its account of the code, try to break it with programs, check that it can be implemented, and verify its test plan.

## What was done

- The compiler source was read to find every place where an equality is consumed.
- About 75 small programs were run on the frozen type-checker binary under the existing checker (`base`) and with every technique enabled (`FULL`).
- A design in four stages was written: `DESIGN.md`. Its first stage (flags `eqindex` and `eqeager`) was then implemented in the compiler by the coordinator.
- The review read the design against the source, ran the 41 programs of the test plan again, ran them on the binary that has stage 1, and wrote 44 more programs to attack each stage. Ten of them were added to the test plan (`tests/attack-*`). The design was corrected in place; its section 11 is the review.

No compiler code was written or built in this directory's work.

## What was found

1. **Rewriting types to representatives is not safe in this checker.** Hylo selects a conformance by how the type is spelled. With `T == U`, `T is P` and `U is P` in scope, `T.X` and `U.X` are different types, and a compiler test requires it. After rewriting `T` and `U` to one representative, resolution has two candidates of equal rank, and an accepted compiler test becomes ambiguous. Swift can normalize because it assumes one conformance per type.
2. **The useful part of normalization needs no representative.** An equality between two closed types can be decided when the two types are compared, in `match`, and need never become a hypothesis that the search proves later.
3. **The current mechanisms reject valid programs** of three kinds: a match with eight or more differing type arguments (depth bound); equalities that need a congruence step or relate compound types; a generic conformance used through an equality with a concrete type (`T.Element == Box<A>` and `given <T> => Box<T> is P`). A non-generic conformance used that way (`T.Element == I`, `given I is P`) is accepted today.
4. **One equality in scope switches the index of givens off** (4480 candidate matches instead of 1640 in a scope with 40 conformances; 1680 with `eqindex`).
5. **Stage 1 as first implemented has three defects**, none visible in the comparison on the corpus or to the self-check:
   - `eqindex` rejects a program that `FULL` accepts, when a given has a type alias as its type (`tests/attack-01`). The cause is in the existing `match`: an alias at the root of a type defeats its test for "the whole types differ", so the equality of the whole types is assumed. The index did not know.
   - `eqeager` rejects a program that `FULL` accepts, when a search that does not terminate goes through an equality (`tests/attack-04`). The depth bound used to stop that search silently; it now runs deeper, exceeds the budget, and the budget reports an error.
   - `eqeager` does nothing inside the initializer of a local binding, so the same call is accepted in a `return` and rejected in a `let` (`tests/attack-05`, `attack-06`).
   Each has a correction of a few lines (step 4b of the design).
6. **The later stages change the meaning of accepted programs.** Stage 2 (exact test by a closure cached per scope) can make a program ambiguous (`rank-06`) and can replace the selected conformance with no diagnostic (`attack-07`). Stage 3 (matching a type with variables against an equality class) has to choose a spelling among the members of the class, which is the question the design set out to avoid (`attack-08`).

## Recommendation of the review

Implement only the first stage, and make the four corrections of step 4b before `eqindex` or `eqeager` is added to a configuration that is compared, measured or shipped. Building the cached closure and checking it against `solveEquality` (step 5) changes no behaviour and can follow. The stages that change which conformance is selected should wait for the language designers' answers to questions 1 and 4 of the design.

## Files

| File | Content |
|---|---|
| `DESIGN.md` | The design, corrected by the review: problem, inventory, options, hooks, correctness argument, test plan, implementation order, open questions, and the review (section 11). |
| `tests/*.hylo` | The test plan, 51 programs. The first comment of each gives the expected verdict per stage; the line `// currently:` gives the verdict and counters today. `attack-*` are the programs added by the review. |
| `tests/current.jsonl` | Raw results behind the `// currently:` lines of the first 41 programs. |
| `record.py` | Runs the frozen binary on `tests/` (one process at a time, restartable) and rewrites the `// currently:` lines. |
| `review.py` | Runs programs under `base` and `FULL` on the frozen binary and under `FULL`, `FULL,eqindex,eqeager` and the same with `selfcheck` on the binary that has stage 1 (eq15). `--verify` compares with `tests/current.jsonl`; `--record` rewrites the `// currently:` line of the `attack-*` programs; `--trace` prints derivations. |
| `review.jsonl`, `review-base-long.jsonl` | Raw results of the review on `tests/` (five configurations; two base runs repeated with a longer time limit). |
| `experiments/*.hylo`, `results.jsonl`, `run.py` | Exploratory programs of the design and their results. |
| `experiments/review/` | Exploratory programs of the review, with `results.jsonl`. |

To reproduce a verdict: `python3 review.py --force --configs FULL,S1,S1check tests/attack-04-budget-beyond-depth.hylo`. To see a derivation: `python3 review.py --trace --configs FULL tests/attack-07-newcomer-wins-silently.hylo`.

## What remains uncertain

- The corrections of step 4b are not built. That they restore "every program accepted by `FULL` is accepted" rests on reading the code.
- With `eqeager`, a resolution that used to end at the depth bound can succeed, and an extension or overload that did not apply then applies (`tests/attack-10`). No program was found that this rejects or whose meaning it visibly changes; there is no argument that none exists.
- The cost of the deeper searches was measured on one constructed program only (four to five times more subgoals); not on real code.
- Stages 2 to 4 are not compiled. How often stage 2 changes the selected conformance in real code is unknown.
- Traits cannot state equalities between associated types yet. When they can, those equalities will not be ground, and neither the current code nor this design handles them.
- Eight questions are left to the language designers (section 9 of `DESIGN.md`). The first, whether conformances are coherent across equal types, decides between this design and true normalization. The fifth now includes the alias behaviour of `match`: which of `attack-01` and `attack-02` is intended.
- Timings were not measured: the machine was shared. Costs are given as work counters.
