# Overload resolution: design of a result-preserving speed-up

## What was asked

A call to an overloaded function makes the constraint solver fork once per candidate, and n such calls with k candidates each can cost kⁿ forks. An earlier optimization was fast but changed results. The task was to establish exactly what the existing solver does, and to design a speed-up that returns the same solution and the same diagnostics, for an engineer to implement behind runtime flags. Building or modifying the compiler was not allowed.

## What is here

| File | Content |
|---|---|
| `DESIGN.md` | The deliverable: the problem, what the existing solver does, the options, the design with its Swift code and anchors, the correctness argument, the test plan, the implementation order, and the questions for the language designers. |
| `tests/` | 34 Hylo programs. Each starts with the outcome expected after the change, the reason, and the outcome on the binary today under base and FULL. |
| `scripts/model.py` | An executable model of the solver's search (goal stack, error count, scoring, `best`, `viable`, ranking, ambiguity) and of the proposed algorithm. |
| `scripts/mutants.py` | Six deliberately wrong variants of the algorithm, to check that the random systems of the model can detect a mistake, and one tempting shortcut with a hand-made counterexample. |
| `scripts/model_vs_binary.py` | Compares the model's fork counts and diagnostic counts with the binary's, test by test. |
| `scripts/make_tests.py` | Writes `tests/` and records the binary's verdicts; `--check` re-runs the binary and compares. |
| `scripts/scaling.py`, `scripts/tc.sh` | Counters of the named workloads and of chains of `+`; a one-line runner. |
| `results/*.jsonl` | Raw results of the scripts above. |

To reproduce (the first two commands run `tc-bench`, one process at a time, for a few minutes each; the fuzzer and the mutants take about ten minutes together):

```
python3 scripts/make_tests.py --check
python3 scripts/scaling.py
python3 scripts/model_vs_binary.py > results/model-vs-binary.jsonl
python3 scripts/model.py workloads > results/model-workloads.jsonl
for s in 1 2 3 4; do python3 scripts/model.py fuzz 50000 $s results/model-fuzz.jsonl; done
python3 scripts/mutants.py 30000 1 > results/model-mutants.jsonl
```

## What was found

**The existing solver.** Goals are popped from a stack in the order the type checker generated them. The solver forks when it pops an overload constraint, once per candidate in declaration order, and each fork solves everything that remains, so overload sets nest in pop order. A fork is cancelled when it has more failed goals than the best complete solution has diagnostics; before a first complete solution exists, nothing is cancelled. A solution that is not strictly better than the best one is kept as well, even if it is worse. The preferred candidate among the kept ones wins; without a unique preferred one, the first is kept and an ambiguity is reported.

Three consequences were confirmed on the binary and constrain any optimization:
- the result of a branch depends on the best score it inherits, not only on whether it is cancelled (`tests/m06` is accepted; `tests/m07`, the same call placed after another overloaded call, is rejected);
- a candidate whose solution has a diagnostic can win over a clean one (`tests/m04`, `m05`);
- in an ill-typed statement, the solver reports ambiguities that depend on the declaration order of the candidates (`tests/e01` against `e02`; `e04` has six diagnostics for one bad argument).

**Three sources of exponential cost, one of them in ordinary code.**
- `a + a + … + a` on `Int` visits 2ⁿ − 1 overload sets for n operators: 32,766 forks and about 2.5 s for 14 operators, under base and FULL alike. Each `+` has two candidates of the same type, the member of `Int` and the requirement of `AdditiveArithmetic`, and every combination is a solution. Any method that a struct declares and a trait requires behaves the same way. This was not among the known workloads.
- A wrong candidate that fails at its own argument is still explored to the end until a first complete solution exists (`ovl-4-8`: 3,184 forks; with six calls, 1,932 forks when the right candidate is declared last and 24 when it is declared first).
- Candidates that differ only in their return type are rejected by a goal that is popped after every overload set (`ovr-3-8`: 9,840 forks; `ovl-ret-9`: 349,524).

**The design.** Three changes, each behind a flag, about 220 lines in total with the self-check. None changes the order in which goals are processed or candidates are tried.

| Flag | Idea | Forks, from the model |
|---|---|---|
| `twins` | Two candidates with the same type lead to identical searches; the second reuses the result of the first when the best score is the same. | `+` chain of 14: 32,766 → 119 |
| `cleanfirst` | First search for a solution without diagnostics, cancelling at the first error; if the first overload set has a clean candidate, the result is provably the existing one; otherwise run the existing search unchanged. | `ovl-4-8`: 3,184 → 32; `+` chain of 14: 14 |
| `lookahead` | During that search, abandon a branch when a goal still on the stack has closed types and is certain to fail. | `ovr-3-8`: 9,840 → 24; `ovl-ret-9`: 349,524 → 36 |

**Evidence.** The model's version of the existing solver gives the same number of forks, overload sets and diagnostics as the binary on 18 test programs, including the three delicate ones above; `tests/m07` was predicted from the model before it was run. In the model, the proposed algorithm returns exactly the existing solution on 200,000 random systems for six combinations of the flags (no difference in 1,200,000 comparisons), and six variants that each drop one clause of the correctness argument are all detected.

## What remains uncertain

- **Nothing was built.** The Swift in `DESIGN.md` has not been compiled, and the fork counts after the change come from the model, not from the compiler.
- **The model has no types.** It covers the bookkeeping of scores and candidates, which is where the earlier attempt went wrong. The claims about unification and about how a call is decomposed rest on reading `Solver.swift`; the design adds assertions and a self-check mode for them.
- **One assumption cannot be asserted.** The design skips some queries to the type checker that the existing solver makes in branches it later discards, and makes a few earlier. If answers depended on that, results could change. This is the mechanism of the known dependence on declaration order, so the programs at risk are those with cyclic declarations. None was found; none could be tested.
- **Whether the two candidates of `+` have the identical type identity** was inferred from the code and the fork counts, not observed. If they do not, `twins` does not apply to them (step 1 of the implementation order checks this first).
- **The comparison of dumps cannot tell which of two same-named declarations a name is bound to.** The dump must print it before `twins` is validated.
- **Ill-typed statements are not faster.** They run the existing search after a failed attempt: same diagnostics, up to twice the forks with `cleanfirst` alone.
- **Random testing of the model is not exhaustive.** It missed, in 30,000 systems, the flaw of the simpler variant "start the existing search with the bound at zero and keep a clean result", which a hand-made system shows (it needs a preference relation that is not transitive). The design's argument is the proof in section 5 of `DESIGN.md`, not the fuzzer.
- One shape stays exponential: independent overload sets that each have several clean candidates of different types (`tests/s09`).
