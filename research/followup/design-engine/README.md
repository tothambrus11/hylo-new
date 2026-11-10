# Design of improvements to the resolution engine

## What was asked

Three ideas for the engine of implicit resolution were outstanding after the review (`../REVIEW-AND-PLAN.md`, phase 4):

1. substitute the witness found for a requirement into the requirements that mention it, and discharge requirements in an order that makes this possible;
2. share repeated subgoals by tabling;
3. replace the bound on the size of a derivation by a principled bound.

The task was to study each against the code and with experiments on the type-checker binary, to say which one to implement first, to design that one completely, and to treat the other two more briefly. No compiler code was written or built.

## What is here

| Path | Content |
|---|---|
| `DESIGN.md` | The deliverable: priority, the complete design of idea 1 (sections 1 to 7), and the shorter treatments of tabling (8) and of the bound (9). |
| `tests/` | 30 Hylo programs. Each starts with the expected verdict after the change, the reason, and a line `// currently:` with the verdict and counters under base and FULL. `s1-*` belong to idea 1, `s2-*` to tabling, `s3-*` to the bound. `tests/current.jsonl` holds the raw results. |
| `scripts/run.py` | Runs programs under named configurations and bounds, one `tc-bench` process at a time (a lock file serializes all scripts of this directory). `--trace` prints the resolution trace of the user module. |
| `scripts/record.py` | Writes the `// currently:` line of each test. |
| `scripts/corpus_scan.py` | Runs the compiler's tests at bounds 10 and 40. Result: `experiments/corpus-scan.jsonl`. |
| `scripts/repeats.py` | Counts repeated subgoals from the trace of the existing checker. Result: `experiments/repeats.jsonl`. |
| `scripts/programs_scan.py` | Runs the research test programs under FULL. Result: `experiments/programs-scan.jsonl`. The programs that reach the bound or the budget are listed in `experiments/reach-bound.txt` and were run again at bound 40 (`experiments/reach-bound.jsonl`). |
| `experiments/p1/`, `p1.jsonl` | Programs with a requirement on an associated type (idea 1). |
| `experiments/p2/`, `p2.jsonl` | The family "a given with *k* premises that each have many derivations" (idea 2). |
| `experiments/p3/`, `p3.jsonl` | Programs over the bound (idea 3), at bounds 10 to 20. |
| `experiments/sem/`, `sem.jsonl` | Programs that show how pending requirements act as hypotheses. |
| `experiments/dependent-programs.txt`, `.jsonl` | The 76 research test programs that have a requirement on a projection, under base and FULL. |
| `experiments/stdlib-trace-*.txt` | The trace of the standard library under base and MIN5. |

All scripts are restartable: a result already in the output file is not computed again.

## What was found

**Idea 1 should be implemented first.** A function, extension or given whose where clause constrains an associated type of another requirement (`where T is P, T.X is Q`) cannot be used: the call is rejected by the existing checker and by the full configuration, for a generic caller with the same requirements and for a concrete one. Nine minimal programs show it (six with a generic caller, three with a concrete one). The only form that works is an equality with a generic caller, through a special case of the equality procedure that resolves the pending requirement ahead of time. The cause is that requirements are discharged last in, first out, so the dependent one is proved before the one it mentions has a witness, and that the type of the callee does not record which declaration a requirement binds.

The design keeps the order of discharge except for a requirement that mentions another: it waits, off the stack of hypotheses, until the other has a witness, which is then substituted into its type. Resolutions without such a requirement are untouched by construction. One declaration in the compiler's tests has a dependent requirement and it is never called, so the tests should be unaffected. The design costs about 330 lines in five steps and adds one field to `Implication` and `ContextClause`.

It does not fix a call whose *parameter type* mentions an associated type of a requirement (`h<U>(y)` with `y: U.X`): that type is opened by the constraint solver before resolution runs.

**The order of discharge is observable today.** A pending requirement is a hypothesis for the requirements proved before it, penalties count the pending requirements, and with the bound this makes a verdict depend on the order of a where clause: `tests/s3-keep-where-order-a.hylo` is accepted and the same program with two requirements swapped (`s3-gain-where-order-b.hylo`) is rejected.

**Tabling has nothing to gain on today's code.** In the standard library 96% of the 5,417 resolutions end after one step and none has more than five; the positive tests are similar. Repeated premises exist (`Movable<Bool>` is derived 17 times) but each costs one step. A synthetic family of valid programs is exponential in the number of premises today (10, 47, 286, 2,102, 17,984 subgoals for 2 to 6 premises, and the resource budget at 7). Full tabling is not compatible with ranking by layer and penalty, with hypotheses and with open subgoals. The largest exact restriction shares closed premises under a key that contains the hypotheses; the dominance argument is in `DESIGN.md`, section 8.

**The bound rejects ordinary programs, and replacing it is invisible in the tests.** Copying a 5-tuple needs 12 steps; a function with three requirements that are each accepted alone needs 16. A bound of 9 on the height of a derivation keeps every result of today and accepts both. No file of the compiler's tests reaches the bound: 768 runs (192 files, base and FULL, bounds 10 and 40) have identical verdicts, diagnostics and match counts. The cost appears in failing searches over givens with several premises, which is why this idea needs a work budget and, eventually, the sharing of idea 2.

## What remains uncertain

- Nothing was compiled. The Swift in `DESIGN.md` is written against the source as it was read; `Typer.swift` changed during the work, so anchors are quoted lines.
- The design relies on the witness recorded for a requirement being syntactically the one that name resolution used in the caller's own types (assumption A3). This is argued from traces and from reading the code, and is the first thing step 2 will test.
- The binary does not list the subgoals of failing branches, so repetition was measured on completed derivations and through totals.
- The effect of a height bound was estimated by raising the size bound, which accepts a superset.
- Seven questions need the language designers (`DESIGN.md`, section 7, and section 9.4), among them whether pending requirements are meant to be hypotheses at all.
