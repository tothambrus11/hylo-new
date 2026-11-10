# Overload resolution (`twins`, `cleanfirst`, `lookahead`)

**Kind:** `twins` is result-preserving. `cleanfirst` and `lookahead` return the solution of the existing search, but are result-preserving for whole programs only together with the order-independence fix (`../soundness/5-declaration-order.md`); see "What the review found". About 250 lines. Design, proof, executable model and adversarial review: `../follow-up/designs/overload.md`.

## The problem

The constraint solver forks once per candidate when it reaches an overloaded name, and each fork solves everything that remains. Overloaded names therefore nest, and *n* of them with *k* candidates each can cost *kⁿ* forks. Three shapes are exponential today, the first in ordinary code:

| Shape | Example | Forks today |
|---|---|---:|
| Two candidates of the same type at every step | `a + a + … + a` on `Int`, 14 operators: each `+` is both a member of `Int` and a requirement of `AdditiveArithmetic` | 32,766 |
| A wrong candidate is explored to the end, because nothing is cancelled before a first complete solution exists | eight calls of a function with four overloads that differ in their parameter type | 3,184 |
| Candidates that differ only in their result type are rejected by a goal examined after every overloaded name | eight nested calls with three such overloads; nine with four | 9,840; 349,524 |

An earlier attempt to defer overloaded names was faster but changed which solution is selected; it was rejected. The meaning of a program depends on the order in which goals are examined, on the order of the candidates, and on the exact bound that each fork inherits, so a sound optimization must leave all three alone.

## How it works

**`twins`.** Two candidates of one overloaded name that have the same type lead to the same search: the two forks differ only in the declaration bound to the name, which the solver never reads. The second candidate reuses the result of the first, with the name rebound, when both start from the same bound, or under any bound when the first search met no failure at all (its result then does not depend on the bound).

**`cleanfirst`.** Before a first complete solution exists the existing search cancels nothing. At the first overloaded name of a system, the solver first looks for a solution *without diagnostics*: the existing search with the bound "no error" from the start. Each overloaded name discards solutions that have a diagnostic until it finds a clean one, and from then on runs the unchanged code, in the state the existing search is in after it has found a clean solution. If the first overloaded name has no clean candidate, the attempt is dropped and the existing search runs unchanged.

**`lookahead`.** During that search, when an overloaded name is reached, the goals still pending are inspected: if one of them has closed types and is certain to fail (an equality between two different closed types, a coercion that cannot be derived, a call whose argument cannot be passed), the branch is abandoned. Under the bound "no error" such a branch would be cancelled when it reaches that goal anyway.

## Why results are preserved

- `twins`: identical state up to a field that is never read gives an identical search.
- `cleanfirst`: the design proves that when the attempt returns a solution, the list of viable candidates it built is, element by element, the list the existing search builds; the selection among them is then the same. The proof does not rely on any property of the preference between candidates. When the attempt fails, the existing search runs from the unmodified state.
- `lookahead`: a goal whose failure is decided by what is already assigned fails in every continuation of the branch.

## What the review found

`cleanfirst` and `lookahead` skip queries to the type checker that the existing search makes in branches it later discards, and `lookahead` makes one earlier. In the existing implementation the answers of the type checker depend on the order of queries: a lookup made by a wrong candidate's branch decides which declaration is computed first. An adversarial review constructed five programs on which a verdict or a diagnostic changes for that reason (one accepted program becomes rejected, two rejected ones accepted). The in-process self-check cannot see this, because its second run makes the missing queries.

With `sigrounds`, which removes that order dependence for extensions and givens, the verdicts of these programs are stable; only the alias named in the diagnostic of a true alias cycle still differs. No argument excludes a verdict change through aliases, which are still computed on demand.

`twins` only skips repetitions of queries just made from the same state and is not affected. With the rule for searches without failure it makes operator chains linear on its own.

Recommendation: adopt `twins` unconditionally; adopt `cleanfirst` and `lookahead` only together with `sigrounds`.

Evidence:
- an executable model of the solver's bookkeeping predicts the fork counts of the implementation on 18 programs, and the proposed algorithm returns the existing solution on 1.2 million random systems; six deliberately wrong variants are all detected;
- on the 25 programs written to show the delicate cases (a candidate with a diagnostic that wins over a clean one, results that depend on the inherited bound, ambiguities that depend on the order of candidates), verdicts and messages are identical under every combination of the flags;
- the self-checking mode solves every system with an overloaded name a second time with the existing search and compares diagnostics and name bindings.

## Measurements

Forks, on the revised implementation (`follow-up/overload/`, `follow-up/design-overload/tests/`):

| Program | Without | `twins` | all three |
|---|---:|---:|---:|
| `a + … + a`, 6 operators | 126 | 6 | 6 |
| 10 operators | 2,046 | 10 | 10 |
| 14 operators | 32,766 | 14 | 14 |
| Four overloads by parameter type, eight calls (`ovl-4-8`) | 3,184 | 3,184 | 32 |
| Three overloads by result type, eight calls (`ovr-3-8`) | 9,840 | 9,840 | 24 |
| Four overloads by result type, nine calls | 349,524 | 349,524 | 36 |

These are the fork counts that the design's model predicted before the implementation existed.

## What it does not fix

- Ill-typed statements: the existing search runs after a failed attempt, with the same diagnostics and up to twice the forks.
- Independent overloaded names that each have several clean candidates of different types (`s09`): 126 forks before and after. Solving independent groups of constraints separately would fix it, at about 300 lines; it is not needed by any measured workload.
