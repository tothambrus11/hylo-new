# Overload resolution: design of a speed-up, and its review

## What was asked

A call to an overloaded function makes the constraint solver fork once per candidate, and n such calls with k candidates each can cost kⁿ forks. An earlier optimization was fast but changed results. The first task was to establish exactly what the existing solver does, and to design a speed-up that returns the same solution and the same diagnostics, for an engineer to implement behind runtime flags. The second task was an adversarial review of that design: check its reading of the code, try to break it with programs, check that it can be built, check its tests, and revise the document.

Building or modifying the compiler was not allowed in either task. During the review the design was implemented by someone else (hylo-impl commit `9dc04d7`, binary `exp/bin/eq25-c7cbd846a05c`); the review ran that binary.

## The result in short

The design has three flags. After review:

| Flag | Idea | Preserves results? | Effect measured on the implementation |
|---|---|---|---|
| `twins` | Two candidates of one overload set with the same type lead to identical searches; the second reuses the result of the first. | Yes, on every program compared. | `a + a + … + a` with ten operators: 2,046 forks → 65. With rule T4, added by the review and run only in the model so far: 10. |
| `cleanfirst` | Search first for a solution without diagnostics, cancelling at the first error; fall back to the existing search if there is none. | **No.** The solution of the search is the existing one, but the verdict of the program can change. | `ovl-4-8`: 3,184 forks → 32. |
| `lookahead` | During that search, abandon a branch when a pending goal with closed types is certain to fail. | **No**, for the same reason. | `ovr-3-8`: 9,840 → 24; `ovl-ret-9`: 349,524 → 36. |

Why the last two change results: the existing solver runs the fork of a wrong candidate to the end, and what that fork asks the type checker (a member lookup, a coercion) can compute the type of a declaration for the first time. Which declaration of a group is computed first decides, today, whether some programs are accepted. `tests/a01` is accepted today and rejected with `cleanfirst`; `tests/a03` is rejected today and accepted with it; `tests/a07`, which has no circular definition, is rejected today and accepted with `lookahead`. This holds under base and FULL. With `sigrounds` (signatures computed in rounds) these verdicts are stable; what still changes there is which alias of a circular definition the error message names (`tests/a12`).

**Recommendation of the review:** keep `twins` and complete it with rule T4; take `cleanfirst` and `lookahead` out of every configuration that is meant to preserve results. They may be reconsidered together with `sigrounds`, as a separate decision (`DESIGN.md`, sections 5.5, 7.2 and 9.5).

## What is here

| File | Content |
|---|---|
| `DESIGN.md` | The design, revised by the review: the problem, what the existing solver does, the options, the algorithm with its Swift code and anchors, the correctness argument and where it stops, the test plan, the steps that remain, the questions for the language designers, and the review (section 9). |
| `tests/` | 46 Hylo programs. Each starts with the outcome expected after the change, the reason, and the outcome on the binary today under base and FULL. `a01` to `a12` are the review's attack programs. |
| `scripts/model.py` | An executable model of the solver's search (goal stack, error count, scoring, `best`, `viable`, ranking, ambiguity) and of the proposed algorithm, rule T4 included. It has no type checker in it, so it cannot show the problem of `cleanfirst`. |
| `scripts/mutants.py` | Deliberately wrong variants of the algorithm, to check that the random systems of the model detect a mistake. |
| `scripts/model_vs_binary.py` | Compares the model's fork counts and diagnostic counts with the binary's, test by test. |
| `scripts/make_tests.py`, `scripts/review_tests.py` | Write `tests/` (the first 34 programs, and the twelve of the review) and record the binary's verdicts. |
| `scripts/review_check.py` | Runs every file of `tests/` as it is on disk and compares with the comments in the file. |
| `scripts/review_impl.py` | Compares the implementation (binary `eq25`) with the existing search: verdict, messages, semantic dump, counters. |
| `scripts/scaling.py`, `scripts/tc.sh` | Counters of the named workloads and of chains of `+`; a one-line runner. |
| `results/*.jsonl` | Raw results. Files named `review-*` are the review's. |

To reproduce (every command that runs `tc-bench` runs one process at a time):

```
python3 scripts/review_check.py                      # 92 recorded verdicts, binary eq9, a few minutes
python3 scripts/model_vs_binary.py > results/review-model-vs-binary.jsonl
python3 scripts/model.py workloads > results/review-model-workloads.jsonl
for s in 12 13 14 15 21; do python3 scripts/model.py fuzz 50000 $s results/review-model-fuzz.jsonl; done
python3 scripts/mutants.py 30000 1 > results/review-model-mutants.jsonl
python3 scripts/review_impl.py results/review-impl-tests.jsonl "base;FULL" \
  "twins;twins+cleanfirst;twins+cleanfirst+lookahead;twins+cleanfirst+lookahead+selfcheck" tests   # about 40 minutes
```

## What was found

**The existing solver.** Goals are popped from a stack in the order the type checker generated them. The solver forks when it pops an overload constraint, once per candidate in declaration order, and each fork solves everything that remains, so overload sets nest in pop order. A fork is cancelled when it has more failed goals than the best complete solution has diagnostics; before a first complete solution exists, nothing is cancelled. A solution that is not strictly better than the best one is kept as well, even if it is worse. The preferred candidate among the kept ones wins; without a unique preferred one, the first is kept and an ambiguity is reported. The review checked this account against the source and found it right.

Consequences confirmed on the binary, which constrain any optimization:
- the result of a branch depends on the best score it inherits (`tests/m06` is accepted; `tests/m07`, the same call placed after another overloaded call, is rejected);
- a candidate whose solution has a diagnostic can win over a clean one (`tests/m04`, `m05`);
- in an ill-typed statement, the solver reports ambiguities that depend on the declaration order of the candidates (`tests/e01` against `e02`);
- the verdict can depend on a query made in a fork whose result is thrown away (`tests/a01` against `a02`). The first version of the design did not know this one.

**Three sources of exponential cost, one of them in ordinary code.**
- `a + a + … + a` on `Int` visits 2ⁿ − 1 overload sets for n operators: 32,766 forks and about 2.5 s for 14 operators. Each `+` has two candidates of the same type, the member of `Int` and the requirement of `AdditiveArithmetic`. Any method that a struct declares and a trait requires behaves the same way. Every overload set of the standard library has this shape (133 sets; with `twins,cleanfirst` each costs one fork and one reuse).
- A wrong candidate that fails at its own argument is still explored to the end until a first complete solution exists (`ovl-4-8`).
- Candidates that differ only in their return type are rejected by a goal that is popped after every overload set (`ovr-3-8`, `ovl-ret-9`).

**Evidence for the search logic.** The model's version of the existing solver gives the binary's forks, overload sets and diagnostics on 19 test programs. In the model, the proposed algorithm returns exactly the existing solution on 470,000 random systems. The implementation has the fork counts that the model predicted and, wherever the type checker's answers are the same, the existing dump: on the 46 tests under three configurations the only differences are the three programs named above, `a05` under base, and the message of `a12`; on 429 other programs under FULL (the compiler's tests, the earlier review's solver programs, the declaration-order programs) and 184 under the configuration with `sigrounds` there is none.

## What remains uncertain

- **Rule T4 is not built.** It is in the model (270,000 random systems, no difference) and in `DESIGN.md` as Swift, about 15 lines.
- **How many real programs `cleanfirst` and `lookahead` would change is not known.** The attack programs were constructed; none of the 429 existing programs compared changes. `DESIGN.md` 4.5 describes two counters that measure the exposure in the existing search; they are not implemented.
- **With `sigrounds`, no verdict was seen to change, but nothing excludes it.** Aliases are still computed on demand there.
- **`twins` rests on one assumption about the type checker**: repeating at once a query sequence that has just been made changes nothing. Dump comparisons support it; nothing proves it.
- **The dump cannot tell which of two same-named declarations a name is bound to.** The implementation's self-check compares bindings and reports no violation, but the two-process comparison is blind to it until the dump prints the declaration.
- **A counted failure without a diagnostic** would break `cleanfirst`'s argument. The code can produce one under `headsubst` in principle; no program was found, and the assertion that would catch it is not in the implementation.
- **Ill-typed statements are not faster**: same diagnostics, up to twice the forks with `cleanfirst` alone.
- One shape stays exponential under every flag: independent overload sets that each have several clean candidates of different types (`tests/s09`).
