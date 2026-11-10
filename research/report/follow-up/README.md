# Review of the type-checker work, and a plan for what to do next

This document reviews the optimization and soundness work critically, using five checks that were run for this review, and proposes follow-up experiments. The goal is to understand the problem space better, and to adopt only the optimizations whose benefit is established and whose complexity is justified.

## 1. Conclusions

1. **Five small techniques produce the entire gain on real code.** On the standard library, `index`, skipping extensions that do not declare the requested name, `typevec`, `symindex` and `traitindex` take type checking from 526 ms to 126 ms. The other thirteen flags add nothing measurable there. About 300 lines of code carry the result; about 2,400 lines do not contribute to it.
2. **The remaining techniques are justified only by adversarial workloads or by soundness.** `absmodel`, `absquotient` and `eqsolve` each remove an exponential behaviour, but none of these behaviours occurs in the code available today. Whether they are worth their complexity depends on questions this project has not yet asked: how often resolution fails in practice, and how much code will use equality constraints.
3. **The claim of order independence is false.** A declaration-order fuzzer written for this review found seven programs whose acceptance still depends on declaration order under the final configuration. The existing checker has 52 such programs in the same set, so the fixes help, but the design does not achieve the property that the report claims.
4. **The soundness fixes are almost untested by the compiler's test suite.** The equality procedure runs in 4 of 216 corpus files and never refutes anything there. The cycle checks and `eqmgu` never run. "216/216 identical" therefore says nothing about them: their validation rests on programs written during this project, whose expected verdicts have no independent source.
5. **Timings are too noisy to judge constant-factor techniques.** Single measurements vary by about ±20% between sessions. `unify`, `coesrc` and `reifymemo` cannot be told apart from noise in the full configuration.
6. **The comparison with the existing checker had a gap, now closed.** It did not record which witness was selected at coercion and implicit-argument sites. With that added, the results are identical once equality proofs are erased (11,817 sites).

The recommendation: land the five techniques as small, independent, result-preserving changes. Treat everything else as research until the experiments of section 5 are done, and redesign the order-dependence fix instead of extending it.

## 2. Evidence gathered for this review

All scripts and raw data are in this folder.

### 2.1 Which techniques matter on real code

Greedy forward selection on standard-library type checking: start with nothing, repeatedly add the technique that helps most, stop when nothing improves the time by more than 2%. Times are the minimum of 12 runs (`greedy.py`).

| Step | Technique added | Time (ms) | Cumulative speed-up |
|---|---|---:|---:|
| 0 | none | 517 | 1.0× |
| 1 | `index` | 233 | 2.2× |
| 2 | skip extensions that do not declare the name (part of `extorder`) | 177 | 2.9× |
| 3 | `typevec` | 158 | 3.3× |
| 4 | `symindex` | 138 | 3.7× |
| 5 | `traitindex` | 126 | 4.1× |
| – | all 18 techniques | 130 | 4.0× |

Step 2 changes the meaning of some cyclic programs. Its result-preserving equivalent, `memberskip`, gives 141 ms in its place (3.7× in total). Adding `absmodel` to the five gives 128 ms: no gain.

### 2.2 What each technique contributes once the others are enabled

Leave-one-out ablation on ten workloads (`ablation.py`, `ablation.jsonl`). Only effects larger than the noise are listed.

| Removed | Effect |
|---|---|
| `eqsolve` | trans-8 405× slower and wrongly rejected; assoceq-8 7.5× slower and wrongly rejected; conditional extension 2.7× slower and rejected |
| `absmodel` | div-branch 89× slower; divergence-with-equality 660× slower and rejected by the budget |
| `absquotient` | divergence-with-equality 600× slower and rejected by the budget |
| `index` | breadth40 9.5× slower; nestwide-8 2.6×; div-branch 2.4× |
| `extorder` | members-big 2.2× slower; assoceq-8 2.9×; conditional extension 2.3× |
| `typevec` | 1.2–1.7× slower on most workloads |
| `symindex` | standard library 1.2× slower |
| `coesrc`, `memberskip`, `unify`, `reifymemo`, `traitindex`, `eqmgu`, `givencheck`, `budget`, `occurs`, `arrowenv`, `fixsubst` | nothing above the noise on these ten workloads |

Two redundancies explain most of the last row:
- **`memberskip` is dead code in the final configuration.** `extorder` skips the same extensions earlier, unconditionally. The report lists both as contributing.
- **`coesrc` is subsumed by `index`**, which keeps its own list of coercion sources.

`reifymemo` and `eqmgu` each matter on one adversarial program (shared bindings, open equalities) that is not among these ten.

### 2.3 How much of each technique the test suite exercises

Activation counts over the 216 corpus files, all techniques enabled:

| Technique | Activations | Files |
|---|---:|---:|
| `index`: candidates skipped | 600,781 | 90 |
| `coesrc`: givens skipped | 193,655 | 45 |
| `absmodel`: subgoals refuted | 684 | 90 |
| `absquotient`: models built | 6 | 4 |
| `eqsolve`: equalities proved | 11 | 4 |
| `eqsolve`: equalities refuted | 0 | 0 |
| `eqmgu` | 0 | 0 |
| `extorder`: cycle groups checked | 0 | 0 |
| `givencheck`: reports | 0 | 0 |
| `budget` | 0 | 0 |

On the standard library alone, `eqsolve`, `eqmgu` and `absquotient` never run.

### 2.4 Declaration-order fuzzing

`permute.py` splits a program into its top-level declarations, type-checks up to 24 permutations, and compares the verdicts. Pilot: 704 programs, 11,554 permutations.

| Program set | Programs | Verdict varies, existing checker | Verdict varies, final configuration |
|---|---:|---:|---:|
| declaration-order test programs | 129 | 52 | 7 |
| equalities, cycles and crashes, projections, performance, abstract model | 407 | not run | 0 |
| compiler tests | 168 | not run | 0 |

(Eleven further reports were artefacts of the declaration splitter on multi-line declarations and are excluded.) In 42 more programs the verdict is stable but the diagnostics differ.

The seven failures have two shapes:

```hylo
struct A {}
struct B {}
extension X { type Me = Int }
extension A { type Me = B }
type X = A.Me            // accepted in this order; "definition of 'X' refers to itself" when f comes first
fun f(x: X.Me) {}
```

- **Cycles through a type alias** (`al1`, `al2`, `al3`, `v01`). Entering the cycle at the alias reports an error; entering it at the extension does not. The cycle check added for extensions does not see aliases.
- **Cycles through a given and an extension together** (`n11`, `n12`, `v6`). The checks for givens and for extensions are separate mechanisms, and neither sees the whole cycle.

The cause is structural. Cycles are detected from the state of the evaluation stack at the moment a declaration is re-entered, separately for each kind of declaration. Whether a cycle is seen, and which of its members is blamed, depends on where evaluation started. Each fix so far added a check for one more kind of entry point. A property of the dependency *graph* cannot be decided reliably from one traversal of it.

### 2.5 The output-equivalence check

The dump compared types, name bindings, witness tables and diagnostics. It did not include the witness chosen at an elaborated site (a coercion or an implicit argument), although the report claimed that implicit arguments were identical. With witnesses added (`witness_oracle.py`, 215 comparable files, 11,817 sites):

| Comparison | Fixes only | All techniques | The five techniques |
|---|---|---|---|
| types, bindings, witness tables, diagnostics | identical | identical | identical |
| witnesses, equality proofs erased | identical (1 file differs in the names of leftover type variables) | same | same |
| witnesses, verbatim | 2 files differ in equality proof terms | same | identical |

The claim now holds in the form "identical up to the terms of equality proofs". The two differing files are those in which `eqsolve` builds a proof.

### 2.6 Complexity

The work adds about 2,700 lines to the front end, about 1,900 of them in `Typer.swift`, which grows from about 4,700 to 6,600 lines.

| Technique | Lines (approx.) | Invariants its correctness depends on |
|---|---:|---|
| `eqsolve` and `eqmgu` | 460 | the equality theory of the search; the discharge order of premises; determinism of resolution; the `Self` projection rule |
| `absmodel` | 560 | over-approximation; every assumption is eventually discharged; four subtle points in unification and subsumption |
| `absquotient` | 100 | the congruence lemma; consistency with `eqsolve`'s theory |
| `index` | 100 | no coercion can reconcile two distinct heads |
| `memberskip` | 90 | which computations an applicability test can force |
| `extorder` cycle rule | 80 | cycles only pass through extensions (false, see 2.4) |
| `traitindex` | 60 | none beyond ordering |
| `givencheck` | 50 | hidden givens are the only source of order dependence (false) |
| `typevec`, `symindex`, `unify`, `reifymemo`, `coesrc`, `budget`, `occurs`, `fixsubst` | 10–40 each | local |

In addition, six rejected experiments are still in the code behind flags (`names`, `loopcheck`, `solver`, `eqrefute`, `cyclecut`, `coercememo`), and `solveEquality` is a single function of 380 lines.

### 2.7 Measurement noise

The same configuration measured in different sessions gave 130, 151 and 167 ms for the standard library. In the ablation, removing a technique often appeared to make the checker 20% *faster*. The method used throughout (minimum of three runs in one process) cannot resolve differences below about 20%. The greedy selection used the minimum of 12 runs across 4 processes, and there a technique that never runs still appeared to give 3%.

## 3. Assessment of each technique

| Technique | Benefit on real code | Benefit elsewhere | Changes results? | Assessment |
|---|---|---|---|---|
| `index` | 2.2× | 9.5× with many givens | no | Adopt. |
| `typevec` | 1.12× | 1.2–1.7× | no | Adopt. |
| `symindex` | 1.15× | – | no | Adopt. |
| `traitindex` | 1.10× | – | no | Adopt. |
| `memberskip` | 1.3× (alternative to the next row) | 15× with many extensions | no | Adopt now; it is the result-preserving form. |
| name skip in `extorder` | 1.3× | same | yes, on cyclic programs | Adopt only together with a decision on cycles (section 4). It makes `memberskip` unnecessary. |
| `reifymemo` | none | removes one exponential | no | Adopt: 25 lines, obviously correct. |
| `occurs`, `arrowenv` | – | crash becomes error | yes, slightly | Adopt early; independent of everything else. |
| `absmodel` | none measurable | removes exponential failure | no | Hold. Decide with the error-path experiment (5.2). |
| `absquotient` | never runs | needed for `absmodel` under equalities | no | Hold with `absmodel`. |
| `coesrc` | none once `index` is on | – | no | Drop, unless careful timing shows a gain while declarations are hidden. |
| `unify` | not measurable | – | no | Re-measure; drop if under 2%. |
| `fixsubst`, `eqsolve`, `eqmgu` | never run | soundness; removes exponential equality search | yes | Not ready. Needs a written specification, independent tests and a design review (4.2, 5.3). |
| `givencheck`, `extorder` cycle rule | never run | reduce order dependence from 52 to 7 programs | yes | Redesign (5.4). Do not extend. |
| `budget` | never runs | crash becomes error | yes | A language decision (4.1). |

## 4. What we do not yet understand

### 4.1 What the intended semantics are

Several fixes embed decisions that belong to the language designers, and that nobody outside this project has reviewed:
- **`Self.X`.** It equals `T.X` when the scope has exactly one conformance for a type equal to `Self`. Two existing tests conflict if the rule is applied freely; the chosen rule is one of several consistent ones.
- **The depth bound.** `eqsolve` proves equalities that the search rejects for exceeding 10 steps. Is the bound part of the language, or a safeguard?
- **Inferred arguments.** `eqmgu` binds `?u := A` where the existing checker might bind another type equal to `A`.
- **Cyclic extensions.** Are extensions whose extended types depend on each other's members legal at all? If not, most of the order-dependence problem disappears by fiat.
- **The resource bound.** A program's acceptance should not depend on how well an optimization prunes.
- **Ranking.** Penalties and search layers decide which derivation wins. `eqsolve` imitates them with path costs; nothing states what the ranking is *meant* to be.

Without a written specification of resolution, "sound" can only mean "agrees with the existing implementation where we believe it" — which is what the adversarial tests measured.

### 4.2 Whether equality reasoning needs this machinery

Four techniques exist because equalities are handled by coercions inside the search: `fixsubst`, `eqsolve`, `eqmgu` and `absquotient`, plus the coercion parts of `index` and `coesrc`. An alternative design removes the problem at its root: **normalize every type to a canonical representative of its equality class when it enters a scope**, as Swift's requirement machine does. Resolution then never sees two different spellings of equal types, and needs no coercions for ground equalities. One mechanism of perhaps 200 lines might replace about 700, and would also give the abstract model and the index exact answers under equalities. This is the most promising simplification, and it has not been explored.

### 4.3 What real programs look like

The standard library is the only real code measured, and it uses no equality constraints and has no failing resolutions. Unknown:
- the share of type checking in total compile time;
- where the remaining 126 ms goes;
- how many givens, extensions and equality constraints typical generic code has;
- how often resolution fails. This matters for editors, which type-check erroneous code continuously.

### 4.4 Whether order independence is achievable in the current architecture

Types of declarations are computed on demand, with the declaration hidden meanwhile and all results memoized. Section 2.4 shows that patching this per declaration kind does not converge. The literature on scheduling name resolution (Rouvoet et al. 2020; van Antwerpen and Visser 2021) and query-based compilers (Rust's cycle handling) suggests the principled alternatives: make dependencies explicit and detect cycles on the graph, or forbid the dependencies by a language rule.

## 5. Plan

Each experiment states the question it answers and the decision it informs. Costs are rough working days.

### Phase 0: corrections and hygiene (2 days)

- **0.1 Correct the report.** Withdraw the order-independence claim (done in this revision; see section 6). State the output-equivalence result in its verified form. Replace stand-alone speed-ups by the marginal contributions of 2.1.
- **0.2 Remove dead code.** Delete the six rejected experiments, and `coesrc` and `memberskip` according to 5.1. Split `solveEquality`.
- **0.3 Fix the measurement method.** At least 20 interleaved runs per configuration, across processes, reporting medians and confidence intervals, with a memory column. Every later timing uses it.
- **0.4 Make the stronger checks permanent.** Fold the witness dump into the oracle. Run the oracle for each technique alone and for each leave-one-out configuration, so that every technique can be adopted independently.

### Phase 1: adopt what is established (3 days)

- **1.1** Five separate result-preserving changes, each with the full oracle: `index`, `typevec`, `symindex`, `traitindex`, `memberskip`. Then `reifymemo` and the occurs check.
- **Expected outcome:** 3.7× on the standard library for about 350 lines.
- **Stop condition:** a technique whose careful timing (0.3) shows less than 2% on every real workload is not adopted, however small.

### Phase 2: understand the problem space (2 weeks)

- **2.1 Census of real code** (2 days).
  - *Question:* what do resolution workloads look like outside stress tests?
  - *Method:* instrument the checker to record, per resolution: visible givens, candidates tried, depth, outcome, and whether an equality was involved. Run on every Hylo program available (standard library, compiler tests, examples, ported programs).
  - *Informs:* every later priority.
- **2.2 Error-path benchmark** (2 days).
  - *Question:* how expensive is failing resolution in realistic erroneous code, and does `absmodel` change it?
  - *Method:* mutation: delete one conformance, one requirement or one argument at a time from the standard library and the tests; measure the time to report the error, with and without `absmodel`.
  - *Decision:* adopt `absmodel` (660 lines with `absquotient`) only if a meaningful share of mutants becomes much faster, say more than 1% of mutants by more than 10×. Otherwise keep only a resource bound.
- **2.3 End-to-end share and profile** (1 day).
  - *Question:* how much of a full compilation is type checking, and what dominates after phase 1?
  - *Informs:* whether further type-checker work is worth doing at all compared with other phases.
- **2.4 Scaling curves** (2 days).
  - *Question:* what are the asymptotics, before and after?
  - *Method:* for each workload family, vary one size parameter over a decade or more and fit the growth.
  - *Informs:* the "exponential to polynomial" claims, which currently rest on single points.
- **2.5 Equality usage forecast** (1 day).
  - *Question:* how much will Hylo code use equality constraints?
  - *Method:* count associated-type equalities in comparable libraries (Swift's standard library and collections, Rust's iterator traits), and in the Hylo roadmap.
  - *Informs:* how much to invest in 3.2.

### Phase 3: correctness on a principled footing (3–4 weeks)

- **3.1 Specification and reference implementation** (1 week).
  - Write resolution down as inference rules, including ranking, hypotheses, coercions and the points of 4.1, and get the language designers to review it.
  - Implement it directly, favouring clarity over speed (exhaustive search, large depth bound).
  - *Why:* it gives an independent source of expected verdicts, which the project lacks.
- **3.2 Equality by normalization** (1 week, prototype).
  - *Question:* can canonical representatives per scope replace `fixsubst`, `eqsolve`, `eqmgu`, `absquotient` and the coercion machinery?
  - *Success criterion:* same verdicts as the reference implementation on the equality tests, less code than the current fix set, and no search for ground equalities.
  - *Fallback:* keep `eqsolve`, restructured, and validated against 3.1.
- **3.3 Differential and metamorphic testing** (1 week, then continuous).
  - Generate random well-scoped programs from a grammar and compare the checker with the reference implementation.
  - Check metamorphic relations, each of which already caught a real defect once by hand:
    - permuting declarations;
    - permuting requirements in a where clause;
    - adding a tautology such as `X == X`;
    - expanding or introducing aliases;
    - renaming.
  - The declaration-order fuzzer of 2.4 is the first of these; it found seven defects in 25 minutes of machine time.
- **3.4 Self-checking mode** (2 days).
  - In a debug configuration, every pruning decision is verified by doing the work it avoided:
    - a goal refuted by the model is searched anyway and must fail;
    - a candidate skipped by the index must fail to match;
    - an extension skipped by name must contribute no candidate;
    - an equality decided by the procedure must agree with the search wherever the search terminates.
  - Run the whole corpus and the generated programs in this mode. This tests the correctness arguments on every execution, not only on final outputs.
- **3.5 Order independence by design** (1 week, design first).
  - *Options:* (a) a language rule that forbids extended types, alias definitions and given types from depending on extension members or implicit resolution involving themselves; (b) explicit dependency tracking with cycle detection on the graph, with one mechanism for all declaration kinds; (c) a fixed-point computation.
  - *Decision input:* the census (2.1) shows whether real code needs such dependencies at all. If it does not, (a) is the simplest and removes `givencheck` and the cycle rule entirely.
  - *Acceptance test:* zero order-dependent verdicts under the fuzzer, on all test programs and on generated ones.
- **3.6 Mechanize the two central lemmas** (optional, 1 week): the over-approximation of the abstract model under hypotheses, and the congruence lemma of `absquotient`. Only if `absmodel` survives 2.2.

### Phase 4: further optimization, in order of expected value

Ordered by what is known today; to be re-ordered after phase 2.

1. **Overload resolution.** The largest known exponential behaviour that ordinary-looking code can reach. It needs the redesign sketched in the report: keep the solver's branching order, and prune by a lower bound.
2. **Whatever the profile of 2.3 shows.** After phase 1 the profile is unknown; the next factor of two may be elsewhere.
3. **Tabling of subgoals** (Selsam et al. 2020). Sharing repeated subgoals between alternatives would address diamonds and cycles more generally than the abstract model, and might replace both the depth bound and the resource bound. It is a larger change, and interacts with ranking.
4. **Substituting discharged premises** into pending ones, which fixes the unreduced-projection problem in general, and removes the ahead-of-time resolution in `eqsolve`.

### Decision rules

- A technique is adopted when it is result-preserving under the extended oracle and the self-checking mode, and it either gains at least 2% on real code under the careful timing or removes a super-polynomial behaviour that the census or the error-path benchmark shows to be reachable.
- A semantic fix is adopted when its behaviour follows from the reviewed specification and it agrees with the reference implementation on generated programs.
- Complexity is counted in lines and in invariants (2.6). A technique that depends on an invariant of another component must assert it in the self-checking mode.

## 6. Corrections made to the report with this review

- The statement that verdicts no longer depend on declaration order is replaced by the measured result (52 → 7 order-dependent programs), with the two remaining shapes listed under Limitations.
- The validation section states output equivalence as verified: identical up to the terms of equality proofs.
- `memberskip` is described as the result-preserving alternative to the name skip in `extorder`, not as an additional gain.
- A note states that per-technique speed-ups are measured in isolation, and gives the cumulative contributions of section 2.1.
