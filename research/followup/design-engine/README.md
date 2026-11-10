# Design of improvements to the resolution engine

## What was asked

Three ideas for the engine of implicit resolution were outstanding after the review (`../REVIEW-AND-PLAN.md`, phase 4):

1. substitute the witness found for a requirement into the requirements that mention it, and discharge requirements in an order that makes this possible;
2. share repeated subgoals by tabling;
3. replace the bound on the size of a derivation by a principled bound.

The task was to study each against the code and with experiments on the type-checker binary, to say which one to implement first, to design that one completely, and to treat the other two more briefly. No compiler code was written or built.

The design of the first idea was then implemented by the coordinator (flag `premsubst`, commit `0bbd27e` of `/home/user/hylo-impl`), and a second engineer was asked to break the design: to check its account of the code, to construct programs on which it gives a wrong or order-dependent result, to verify its test plan, and to correct the document.

## What is here

| Path | Content |
|---|---|
| `DESIGN.md` | The deliverable: priority, the complete design of idea 1 (sections 1 to 7), the shorter treatments of tabling (8) and of the bound (9), and the review (11). Corrections made by the review are marked "(review)" in the text. |
| `tests/` | 57 Hylo programs. Each starts with the expected verdict after the change, the reason, and a line `// currently:` with the verdict and counters under base and FULL on the binary `eq9`, which has none of the design. The `s1-*` programs also have a line `// observed:` with what the implementation of the first version of the design does (binary `eq25`). `s1-*` belong to idea 1, `s2-*` to tabling, `s3-*` to the bound; 27 of them were added by the review, of which the 15 named `s1-attack-*` are programs written to break the design (the comment of each explains the attack). `tests/current.jsonl` and `tests/observed.jsonl` hold the raw results. |
| `scripts/run.py` | Runs programs under named configurations and bounds, one `tc-bench` process at a time (a lock file serializes all scripts of this directory). `--trace` prints the resolution trace of the user module. |
| `scripts/record.py` | Writes the `// currently:` line of each test. |
| `scripts/review_run.py` | Like `run.py`, for any binary and any set of flags (`--bin eq25-c7cbd846a05c --configs FULL,FULL+premsubst`). Used by the review. |
| `scripts/record_observed.py` | Writes the `// observed:` line of each `s1-*` test. |
| `review/` | The review's raw results: the tests of the first version re-run on `eq9` (`tests-eq9.jsonl`) and on `eq25` (`tests-eq25.jsonl`), the 76 research programs with a requirement on a projection, and 5 others, under FULL and FULL + `premsubst` (`corpus-files.txt`, `corpus-eq25.jsonl`), and the candidate attack programs with their results (`attacks/`, `attacks.jsonl`). `review/test_table.py` prints the table of section 5 of the design. |
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

## What the review found

The mechanism works as designed. Every prediction of the first version was confirmed on the implementation: the nine programs of the problem statement are accepted, the programs that must stay accepted or rejected do, exactly the predicted research programs change, the 60 recorded current verdicts are reproducible, and about 1,000 programs run without a requirement left waiting.

Four defects were found, each with a minimal program in `tests/`, and the design was corrected for each. The corrections are not implemented.

1. **A program is accepted that must be rejected** (`s1-attack-capture-recursion.hylo`). In a recursive call with explicit type arguments, a type argument can mention the function's own requirement. The design could not tell that reference from the ones the where clause makes to itself, rewrote it, and accepted the call with a witness of the wrong type. The existing checker rejects the program and the self-check mode does not notice. The correction is a rule of about 20 lines (section 3.4 of the design): where the caller can name the requirement, the call must use that very requirement.
2. **Valid programs are still rejected when the first requirement is found through an equality** (`s1-attack-coerced-witness.hylo`). Name resolution removes a coercion before selecting an associated type; the design did not. Five lines (section 3.7).
3. **Methods, initializers and trait requirements with such a where clause are still rejected** (`s1-attack-method.hylo` and two more), because the implementation left out one field that the design specified. About 20 lines (section 3.2).
4. **The design chooses the conformance of a requirement by whether the later requirements hold.** A conformance that is shadowed at the call site, or farther away, is selected when the nearest one does not satisfy the dependent requirement (`s1-attack-shadowed-*.hylo`). With the headers also bound, `f<A>()` then has a type that differs from the type its signature gives at the call site. The first version had noticed only the case of two conformances of equal rank. This is a question for the language designers; the review designed the alternative (each requirement gets the conformance it would get alone, section 3.10, about 35 lines, its own flag) and recommends it. The choice also decides whether the analogue of the compiler's negative test `associated-type-inequality.hylo` stays rejected once defect 2 is fixed.

Smaller findings: two dependent requirements can still make a verdict depend on their order through the depth bound (`s1-attack-where-order-a/b.hylo`), as two ordinary requirements do today; the argument that makes tabling exact does not hold for a requirement whose witness is substituted into others (section 8.2); the budget of a height bound must fail with an error, not silently (section 9.2).

Recommendation: keep the implementation, implement the correction of defect 1 before the flag is used in any evaluated configuration, then the other three.

## What remains uncertain

- The first version of the design was built and run; the corrections of the review were not. Their expected verdicts (the bold rows of the table in section 5 of the design) are derived by hand from traces.
- The correction of defect 1 relies on an argument about what a caller can write (assumption A7 of the design), not on a check: inside the engine, a reference made by the where clause and the same reference made by the caller are the same expression.
- Whether a requirement's conformance is chosen alone or together with the requirements that depend on it is undecided (question 4 of the design).
- The binary does not list the subgoals of failing branches, so repetition was measured on completed derivations and through totals.
- The effect of a height bound was estimated by raising the size bound, which accepts a superset.
- Seven questions need the language designers (`DESIGN.md`, section 7, and section 9.4), among them whether pending requirements are meant to be hypotheses at all.
