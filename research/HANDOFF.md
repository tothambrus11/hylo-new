# Handoff: Hylo type-checker performance research

Read this first: it is the entry point for the next agent.

## The question

It comes from a letter from Dimi to Arnaud (not committed; ask the user for it if needed): find a sound, cheap procedure that conservatively decides when implicit (type-class) resolution will fail. View the givens as a bipartite rule/type graph: cycles mean divergence. Two examples:
- `f: ∀T. P T ⇒ Q T`, `g: ∀T. P T ⇒ P T`, `x: P Int`, with the query `Q Bool`, diverges.
- Resolution must stay deterministic and pick the smallest proof term.

A further goal: speed up type checking and name lookup in general.

## Branches (fork tothambrus11/hylo-new)

All six branches are pushed:
- `tc/infra`: the `tc-bench` harness, the `TyperCounters` / `TyperExperiments` flags (`HYLO_TC_EXPERIMENTS=a,b`), and `Program.semanticDump` (the soundness oracle).
- One branch per optimization, each stacked on `tc/infra` and behind a runtime flag:
  - `tc/names`: `names`;
  - `tc/unify`: `unify`;
  - `tc/solver`: `solver`;
  - `tc/resolution`: `index`, `absmodel` and `loopcheck`.
- `tc/research`: all of the above merged, plus this `research/` directory.

## What is in research/

| Path | Contents |
|---|---|
| `REPORT.md` | First-round report. Some claims are now known to be wrong; see the status below. |
| `lit-*.md` | Literature studies (about 60 sources). `papers/REFERENCES.md` lists the PDFs; they are not committed. |
| `exp/tcx.py` and `exp/README.md` | Restartable experiment harness: freeze, semtest, queue, resume, status, analyze. It covers factorial, GA and neighbourhood designs, and a bootstrap analysis. |
| `workflows/review.js`, `workflows/ideas.js` | Dynamic workflow scripts. Run them with the Workflow tool, `{scriptPath, args: {repo, binid, perf, topics}}`. |
| `review/` | Reviewers' test programs and outputs. `review/RESULTS-partial.md` has the finished results. |
| `ideas/` | Brainstorm outputs. `ideas/RESULTS-partial.md` has the finished lens. |
| `scripts/` | The workload generator `gen.py` and older helpers. Some contain absolute paths under `/home/hylo/hylo-tc`; fix them before use. |
| `workloads/` | The stress workloads. |
| `profile/*.txt` | Symbolized perf profiles with all six flags on. |

## Status (2026-11-05)

1. **Semantic oracle.** `tcx.py semtest` compares, against the baseline, the dump of every type, binding (including implicit/witness arguments) and witness table, plus the diagnostics. It is much stronger than the old diagnostics-only differential test.
   - It found that `solver` changes the elaboration of `Tests/CompilerTests/positive/overload-priority.hylo`: node 0:75 is typed `X` in the baseline and `A<Void>` with `solver`.
   - All other flags alone are identical on the 192 tests and the workloads.
2. **The review of `names` is complete** (`review/RESULTS-partial.md`).
   - `names` is *not* sound in general. Skipping `applies()` also skips its side effects: it forces and memoizes `extendeeType(e)` and, on its slow path, the types of givens, under `declarationsOnStack`. Skipping it changes evaluation order, and therefore the elaboration of programs with cyclic extendee dependencies.
   - Counterexamples are in `review/names/`: n04, n11 and n12 are programs `names` wrongly rejects; n01, n05 and n17 are spurious baseline cycle errors that `names` happens to fix.
   - The proper fix is in the baseline: do not memoize results computed under a cycle cut (a taint counter). `REPORT.md` §5.1 ("applies only fills a cache") must be corrected.
3. **The other reviews did not finish:** unify, index, absmodel, solver, loopcheck and claims. The workflow was interrupted by machine crashes.
   - A reviewer's absmodel test (`review/absmodel/t08-equality.hylo`) used more than 4.8 GB with `absmodel`. The baseline times out on it.
4. **Brainstorm.** Only the "algorithms" lens finished. Its ideas: `dtree`, `symindex`, `memberindex`, `probereuse`, and `knuthtable` (a semantic change).
   - Profile hotspots with all flags on (stdlib):
     - `Program.initializeStandardLibraryCaches` is ≈14%: one full syntax scan per stdlib entity. A single pass would fix it.
     - `canDeriveCoercions` is ≈13%.
     - `swift_dynamicCast` is ≈18% inclusive.
5. **Not started yet:**
   - fixing the review findings;
   - implementing the new ideas;
   - the large factorial/GA experiment.

## Machine constraints (important)

- Never let several agents compile in parallel. Each release build of FrontEnd uses 1.3–3.5 GB and a clean build takes about 18 minutes. Parallel builds crashed the machine (WSL out of memory).
- Build serially, in one worktree per task. An incremental build takes 2–6 minutes.
- `tcx.py` caps child processes at 2.5 GB (`RLIMIT_AS`). The frozen `bin/<id>/tc-bench` is a wrapper that applies `ulimit -v`.
- Copying a `.build` directory into another worktree breaks the build (it ends up with mixed paths).
- Never run `pkill -f tcx.py ...`: it matches your own shell. Kill by the PID in `runs/NAME/pid` instead.

## How to continue

1. Build and freeze a binary:
   ```sh
   swift build -c release --product tc-bench
   python3 research/exp/tcx.py freeze
   ```
   `freeze` prints the binary id.
2. Re-run the oracle on everything:
   ```sh
   python3 research/exp/tcx.py semtest --bin ID --env '{"HYLO_TC_ABSDEPTH":"2"}' \
     --configs "names;unify;index;absmodel;solver;loopcheck" --corpus all --jobs 4
   ```
3. Resume the review for the remaining topics with the Workflow tool:
   - script: `research/workflows/review.js`;
   - args: `{repo: <abs path>, binid: ID, topics: ["unify","index","absmodel","solver","loopcheck","claims"]}`.
4. Run the brainstorm: `research/workflows/ideas.js`, with args `{repo, binid, perf}`.
5. Fix the confirmed findings. Then implement the judged ideas, each as a new flag, **one build at a time**, and gate each one with semtest.
6. Large experiment:
   - Write a spec in `research/exp/specs/` for a full factorial over all sound flags if there are 8 or fewer (otherwise `"design": {"kind":"ga"}`).
   - Workloads: stdlib (metric `type.stdlib`), chain8, breadth40, members, ovl-4-8, ovr-3-8, div-loop-20, div-grow-20, div-dead-20. Set `cpu` to pin the runs and use 5 reps.
   - Start it with `python3 research/exp/tcx.py queue specs/X.json`. After a crash, run `python3 research/exp/tcx.py resume`. The report is `runs/X/report.md`, which includes leave-one-out and add-one tests, the parsimonious choice and the factorial interactions.
