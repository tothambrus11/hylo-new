# Round 2: review results, sound replacements, and fixes

Date: 2026-11-05. Baseline binary: `4587ce9e1a23` (tc/research). New binary: `impl4-b25069294a8b`, which is `tc/research` plus `impl/*.patch`.

## 1. Verdicts on the round-1 flags

Details: `review/RESULTS-round2.md` for these topics and `review/RESULTS-partial.md` for names. Every finding below major severity was checked by an independent skeptic.

| Flag | Verdict | Key evidence | Action |
|---|---|---|---|
| unify | sound in release builds | Closed set of value-type TypeTree conformers, so a tag test is equivalent to `as?`; 32/32 review programs identical. The baseline's debug-only assert on two LiteralTypes is the broken side. | keep |
| index | sound | Skipped threads die at their first match; canDeriveCoercion compares up to α-equivalence. Perf caveat: it falls back on any coercion source (index-2) and is unavailable while a declaration is on the stack (index-3). | keep; refine (index-2) |
| absmodel | **was unsound** | Subsumption treated ⊤ as a constant under a repeated variable (t02, t03, t23 refuted derivable goals). No occurs check: SIGSEGV on valid programs t01 and t18. File-level model shared across files with different imports. Variable-renaming collision. | **fixed** (see §2) |
| names | unsound | Skipping `applies()` changes the order in which extendees and givens are first memoized: n04, n11, n12 rejected; n01, n05, n17 changed. | **replaced by memberskip** |
| solver | unsound | S1: a valid program is rejected (parking under `T == U`). S2: most-constrained-first changes the outer ranking. S3: overload-priority alias sugar. Plus coercion-witness and diagnostic differences. No stdlib benefit (0 pruned). | redesign (see HANDOFF step 3) |
| loopcheck | unsound | LC-1: a different witness, via a shared-lemma pending premise. LC-2: a success turned into "no given instance". LC-3: an ambiguity disappears. The Bol–Apt–Klop argument does not apply with pending premises, BFS layers and penalties. Redundant with absmodel on every workload. | retire |

## 2. New code (impl/*.patch)

All of it is behind runtime flags in `TyperExperiments`.

### symindex

`initializeStandardLibraryCaches` builds one inverted index over the stdlib syntax instead of making 24 full scans with `as? any Annotatable` casts. This is exact: the visit order and the predicate are the same.

### coesrc

Remembers each given whose declared type is error-free and whose head can never form a coercion (neither `<T> T` nor `T ~ U`). `canDeriveCoercions` skips those givens: for them `canDeriveCoercion` returns `0b00`, which leaves the accumulator unchanged. Classification is recorded only when no implicit is on the stack. On the stdlib it skips 511k calls. The judged `givenfacts` idea generalizes it.

### traitindex

A per-scope index from identifier to the visible traits that declare that identifier, built in the same order as `traits(visibleFrom:)`. This is exact: a trait without the identifier has an empty lookup entry and contributes nothing, with no side effects.

### memberskip

The sound replacement for names. In `resolve(_:declaredIn:applyingTo:)`, an extension that does not declare `n` is skipped only if `applies(e, q, s)` provably has no observable effect:
- `e`'s extendee type is already memoized (it is read, never evaluated); and
- either:
  - (a) the match fails at the root: the heads are of different kinds, or are distinct nominal or machine types, and none is a variable, an alias or a generic parameter. Unification then reports only the root pair, and `match` returns `.next([])` without touching the givens; or
  - (b) every given visible from `s` is settled (its type is memoized, including those on the stack), so resolution only reads memos, allocates fresh variables and fills caches.

Results:
- members-big: 4,007,000 skips (the same as names). Typing takes 2.0 s, vs 1.6 s for names and 24 s for the baseline.
- stdlib: 36 `applies` calls remain (names: 32).
- Identical to the baseline on all 47 names counterexamples (names: 12 mismatches).

### absmodel fixes

- **subsumes:** a repeated variable never matches a term containing ⊤.
- **unify:** occurs ⇒ bind to ⊤. This over-approximates the rational solution the concrete unifier could build, and substitutions are never cyclic.
- **File-level models** are keyed by (module, imports).
- **Fact variables** are renamed to disjoint negative numbers.
- **absDepth** now defaults to 2: k=3 made the stdlib about 10× slower with no extra refutations.

Refutation counters are unchanged: stdlib 225, div-* 21.

## 3. Oracle results

- **Corpus:** the 192 tests plus the workloads, 216 files in all. Each new flag alone, `absmodel` alone, and the sound set `{symindex, coesrc, traitindex, memberskip, unify, index, absmodel}` are all **216/216 identical** to the baseline.
- **Review programs:**
  - `review/names/**`: memberskip 47/47 identical.
  - `review/absmodel/*` without t08: the fixed absmodel is 25/25 identical at k=2 and k=3; the old binary was 22/25, with t01 and t18 crashing.

## 4. Timing

Best of `--repeat 3`, pinned with `taskset`, machine idle (load ≈1.3). Typing time in ms; this is an indicative single run, not the planned factorial.

| Workload | Baseline | Sound set | Round-1 all six (unsound) |
|---|---|---|---|
| stdlib | 952 | **291** | 355 |
| chain8 | 31.0 | 3.5 | 3.5 |
| breadth40 | 9001 | 101 | 95 |
| members | 4676 | 164 | 134 |
| ovl-4-8 | 7392 | 262 | 5.3 |
| ovr-3-8 | 375 | 323 | 4.1 |
| div-loop-20 | 195 | 4.8 | 5.0 |
| div-grow-20 | 200 | 5.0 | 5.1 |
| div-dead-20 | 187 | 4.8 | 4.9 |

The sound set beats the round-1 set on the stdlib (symindex, coesrc and memberskip more than make up for dropping names). The overload workloads need a sound solver.

## 5. Answer to the original question, as corrected

- **A cheap, sound "resolution will fail" test exists:** the depth-k abstract least model (k=2) with the fixes above.
  - It never refutes a derivable goal on any program tested.
  - It costs about 1.4k facts on the stdlib.
  - It refutes all three divergence patterns in the workloads.
- **It must not be confused with a loop check.** The ancestor-equality check (loopcheck) is unsound here, because pending sibling premises, the BFS layering and penalties break the grafting argument.
- **The depth cap is a separate semantic problem.** It counts BFS steps (proof size with sharing), not height. It already rejects copying a 5-tuple of Bool (claims C1, C2). Fixing it is a semantic change and belongs in its own PR.

## 6. Corrections to REPORT.md (from the claims review)

- **C1**: Depth cap counts BFS steps (proof size with sharing), not height; §6.1 wording and the min-height recommendation are wrong or ineffective
- **C2**: Depth cap rejects realistic code: copying a 5-tuple of Bool fails (impact understated as a synthetic chain)
- **C3**: loopcheck soundness argument (§5.5, attributed to Bol–Apt–Klop) is false for this engine
- **C4**: Recommendation 1 rests on names being 'semantics-preserving by construction' — false; headline 461→156 ms depends on names
- **C5**: solver claims 'original order of decisions is preserved' / 'stdlib unchanged' not supported
- **C6**: HYLO_TC_ABSDEPTH defaults to 3, not the recommended k=2 → stdlib typing ~10× slower by default
- **C7**: 'Refutes all three divergence patterns' and 'abstract model/loop check handle the divergent ones' overstated; cap cannot be removed safely
- **C8**: Literature attributions: minor misattributions / missing preconditions
- **C9**: HANDOFF/PR #11: 't08-equality makes absmodel use >4.8 GB' misattributes a baseline blow-up
- **C10**: Artifacts and methodology claims not reproducible from the repo
- **C11**: Small numeric inconsistencies
- **C12**: Pre-existing crash in negative/illegal-enum-case.hylo confirmed; only reachable because tc-bench ignores earlier-stage errors
- **C13**: Leftover repo copy from the interrupted attempt (rule violation) in review/claims

See `review/RESULTS-round2.md` (section claims) for evidence and fixes.

## 7. Infrastructure changes

- **Workflows:** `workflows/review.js` and `workflows/ideas.js` take `topics`/`lenses` and `maxVerify`, and know about this machine (no perf; reuse earlier files).
- **`tcx.py`:**
  - `freeze` supports Linux's `.resources` bundle.
  - `semtest`'s baseline cache is keyed by path plus content (absmodel-7, LC-5).
- **Cleanup:** the repo copy left by an interrupted reviewer (`review/claims/hylo-depth11`, 848 files) was removed.
