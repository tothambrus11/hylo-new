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

## Status: sound configuration (2026-11-06)

**Read `round3/soundness.md` § "Final configuration" first.**

- **Patches.** `impl/0001`–`0011` on `tc/research`. The worktree used was `/home/user/hylo-impl`, branch `tc/impl-wip`.
- **Final binary.** `eq7-3bbd2b60cb89`, frozen with `tcx.py freeze`.
- **FIX** = `occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget`: semantic fixes only.
- **FULL** = FIX + `symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo`.
- **Oracle.** Both are 216/216 identical to the baseline on the corpus.
- **Review programs.** Every program of both adversarial reviews (520) is re-run in `round3/soundness/regress-final.md`. FIX/FULL have no crash and no out-of-memory, where the baseline has 21 crashes and 42 timeouts. Every changed verdict is a baseline unsoundness, a crash, or a timeout that is now decided. The one exception is the deliberate rejection of mutual extendee cycles (`techniques/extorder.md`, Limitation).
- **Speed.** `round3/soundness/bench-final.md`. For example: stdlib 4×, members-big 32×, breadth40 89×, trans-8 330×, assoceq-8 31×, ovl-4-8 26×.
- **Technique docs.** One per new flag in `techniques/`: `eqsolve`, `eqmgu`, `extorder`, `givencheck`, `occurs` (+`arrowenv`), `absquotient`, `budget`, `reifymemo`. The `techniques/README.md` table has their status.
- **Remaining work**, in priority order:
  1. A sound `solver` for return-type overloads (`ovl-ret-*` stays exponential).
  2. Accepting mutual extendee cycles that have a unique reading, which needs a fixpoint with rollback.
  3. Reducing projections through all premise forms (bug #3 generally).
  4. A model that refutes branching divergence (`div-trunc`), so that `budget` is never reached.

## Soundness investigation (after round 3, adversarially reviewed)

`round3/soundness.md` covers five baseline defects. Each claimed cause and fix was attacked by two skeptics and a judge (`round3/soundness/review/`).

The confirmed corrections:
- **#1, bogus equality derivations.** The root cause holds: `match` drops substitutions in its coercion path. But a single equality suffices at call sites, and `eqrefute` is **unsound**.
- **#4, the `occurs` fix**, changes some results. It is required by `fixsubst`, which alone creates SIGSEGVs.
- **#3** is wider than stated: projections in any instantiated generic signature fail.
- **#5, `cyclecut`, is unsound**: it accepts an ambiguous program. Do not land it.

Recommendation: land `occurs` and `fixsubst` together with a real equality procedure.

## Status after round 3 (2026-11-05)

- **Write-ups.**
  - `round3/README.md`: equality workloads, depth-cap scans, and a new baseline soundness bug.
  - `techniques/`: one document per flag (how it works, why it is sound, what it speeds up, its cost).
- **New flags** (patches 0005–0006):
  - `typevec`: sound; 1.1–1.4× everywhere.
  - `coercememo`: sound, no gain.
  - `HYLO_TC_MAXDEPTH`: a measurement knob.
- **Sound set with `typevec`.** Identical on all 216 corpus files. Speed-ups: stdlib 4.3×, members-big 21×, breadth40 94×, div-branch 864×.
- **Equality reasoning** (`T0 == T1 == …`, `T.X == U.X`) is the remaining slow pattern: 1.3× only, 2–6 s for tiny functions.
- **Baseline bug.** Two unrelated equalities make any two equality-mentioned types interchangeable (`workloads/round3/bug-assoc-eq-two-links.hylo`).
- **Depth cap.**
  - No corpus test reaches it.
  - Branching failures are exponential in the cap (div-branch: 2.3 s at cap 10, 44.5 s at cap 14), except when `absmodel` refutes them (3 ms at any cap).

## Status after round 2 (2026-11-05, later the same day)

Round 2 ran on a fresh cloud machine (4 cores, 15 GB, Swift 6.3 in /opt/swift). The full write-up is `ROUND2.md`; this is the short version.

1. **Both workflows finished.**
   - Review of unify, index, absmodel, solver, loopcheck and claims: `review/RESULTS-round2.md`.
   - Brainstorm (constant-factors, caching and redundancy lenses, plus the judge): `ideas/RESULTS-round2.md`.
2. **Verdicts:**

   | Flag | Verdict |
   |---|---|
   | `unify` | sound (release builds) |
   | `index` | sound |
   | `absmodel` | was unsound: critical subsumption and occurs-check bugs; **fixed in round 2** |
   | `names` | unsound; **replaced by `memberskip`** |
   | `solver` | unsound: 3 confirmed divergences, plus overload-priority |
   | `loopcheck` | unsound: 3 confirmed divergences; also redundant with `absmodel` |

3. **New code**, on local branch `tc/impl-wip`, stored as patches in `impl/`, on top of `tc/research`:
   - `symindex`: single-pass stdlib symbol table.
   - `coesrc`: remembers which givens can never be coercion sources.
   - `traitindex`: per-identifier index of the visible traits; exact.
   - `memberskip`: the sound replacement for `names`. It skips an extension that does not declare the name only when `applies` provably has no effect: the extendee is memoized, and either the heads fail at the root or every visible given is memoized.
   - `absmodel` fixes: no subsumption of ⊤ by a repeated variable; occurs ⇒ ⊤; file models keyed by imports; disjoint renaming of fact variables.
   - `absDepth` now defaults to 2.
4. **Oracle results.**
   - On the 216 corpus files, `symindex`, `coesrc`, `traitindex`, `memberskip` and `absmodel` alone, and the set `{symindex, coesrc, traitindex, memberskip, unify, index, absmodel}`, are all identical to the baseline.
   - `memberskip` is identical on all 47 `names` counterexamples (`names`: 12 mismatches).
   - The fixed `absmodel` is identical on the 25 absmodel review programs at k=2 and k=3 (before: 2 crashes and 1 wrong refutation). Its refutation counts are unchanged.
5. **Speed.** Best of 3, pinned, typing time in ms:

   | Workload | Baseline | Sound set | Round-1 all six (unsound) |
   |---|---|---|---|
   | stdlib | 952 | **291** | 355 |
   | breadth40 | 9000 | 101 | 95 |
   | members | 4676 | 164 | 134 |
   | div-* | ≈195 | ≈5 | ≈5 |
   | ovl-4-8 | 7392 | 262 | 5 |
   | ovr-3-8 | 375 | 323 | 4 |

   The overload workloads still need a sound `solver`.

## Status after round 1 (superseded; kept for history)

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

1. **Toolchain.**
   - Install Swift 6.3 if it is missing: `curl -sSL https://download.swift.org/swift-6.3-release/ubuntu2404/swift-6.3-RELEASE/swift-6.3-RELEASE-ubuntu24.04.tar.gz | tar xz -C /opt/swift --strip-components=1`.
   - Run `git submodule update --init`, which Swifty-LLVM needs for package resolution.
   - A clean `swift build -c release --product tc-bench` takes 16–28 minutes on 4 cores; an incremental one takes 2–4.
2. **Apply the round-2 patches.** On a branch from `tc/research`, run `git am research/impl/*.patch`, then build and `python3 research/exp/tcx.py freeze .build/release LABEL`.
   - On Linux the resource bundle is `Hylo_StandardLibrary.resources`; `freeze` now handles it.
   - `semtest`'s `--files` option consumes the rest of the command line, so put `--jobs` before it.
3. **Make `solver` sound.** This is the largest remaining gap (ovl/ovr).
   - The verifiers' fixes (S1–S3 in `review/RESULTS-round2.md`): do not park; resolve an overload at the point where the baseline pops it; and probe with "stop at the next overload" so the error count is a lower bound.
   - Alternatively, implement `solver1` from `ideas/RESULTS-round2.md`.
   - Gate it with semtest plus `review/solver/*.hylo`.
4. **Retire `names`, `loopcheck` and the current `solver`.**
   - Keep loopcheck only if a restricted version (LC-1..3 fixes: prune only without pending sibling premises) is wanted for termination. `absmodel` already covers every divergence workload.
5. **Next ideas from the judged slate** (`ideas/RESULTS-round2.md`):
   - `typevec`: type-store storage and tag fast paths, about −15% on the stdlib.
   - `givenfacts`: supersedes `coesrc`, and adds settled source lists.
   - `nocopy`.
   - `membermemo`.
   - `index-2`: a finer coercion-source fallback.
6. **The depth cap is a real semantic issue.**
   - Copying a 5-tuple of Bool already fails (review C2). The cap counts BFS steps (proof size), not height (C1).
   - Any fix is a semantic change: a per-thread height cap plus a large global step budget. Keep it as a separate PR.
7. **REPORT.md has known false claims.**
   - names "by construction"; loopcheck/Bol–Apt–Klop; absmodel "all sound"; solver "order preserved"; §6.1 height vs steps.
   - See ROUND2.md §Corrections. Fix them before the report is shared.
8. **Large factorial experiment.** Still not run. Use the sound flags only: symindex, coesrc, traitindex, memberskip, unify, index, absmodel. That is 7 flags, so a full 2^7 factorial is feasible with `tcx.py queue`.
