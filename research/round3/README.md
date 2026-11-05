# Round 3: equality reasoning, nested givens, and the depth cap

Date: 2026-11-05. Binary: `impl6-5828e269cba4`, i.e. `tc/research` plus `research/impl/*.patch`, which includes `typevec`, `coercememo` and `HYLO_TC_MAXDEPTH`.

All the numbers here are user-typing times in ms on a 4-core cloud VM. They are single runs: treat differences under about 10% as noise. Per-flag numbers are in `bench.md`, and the technique documents are in `../techniques/`.

## 1. Interesting existing tests and how they scale

| Existing test | What it exercises | Scaled generator (`../workloads/round3/gen3.py`) |
|---|---|---|
| `positive/associated-type-equality.hylo` | `where T == U, T.X == U.X` | `assoceq N`: N+1 conforming parameters with a chain of `Ti.X == Ti+1.X` |
| `negative/associated-type-inequality.hylo` | `T == U` with distinct conformances does not make `T.X == U.X` | `assocneg N`: `assoceq N` with the middle link missing (must be rejected) |
| `positive/conformance-via-equivalence.hylo` | `P<U>` from `T ~ U` and `P<T>` | `transconf N`: `P<TN>` from `T0 is P` and a chain `T0 == T1 == … == TN`; `trans N` adds an associated type |
| — (negative of the above) | | `transneg N`: two conformances along a chain whose associated types must not be identified |
| `positive/nested-given-1.hylo` | refinement as a nested given; `trait R { given Void is P }` | `refine N`: refinement chain `QN refines … Q1 refines P`; `nestwide N`: N traits each with a nested given |
| `positive/coercion-derivability-cache.hylo` | coercion memo under assumptions | (used as is: it is already expensive) |

The generated files for N ∈ {2, 3, 5, 8} are in `../workloads/round3/`, together with copies of the originals (`orig-*.hylo`).

Baseline vs the sound set `{symindex, coesrc, traitindex, memberskip, unify, index, absmodel}` (before `typevec`). Each cell is time / summon matches:

| Workload | Baseline | Sound set |
|---|---:|---:|
| orig assoc-eq | 94 / 2929 | 82 / 1576 |
| orig assoc-ineq (negative) | 38 / 447 | 4.7 / 147 |
| orig conf-equiv | 56 / 146 | 7.7 / 146 |
| orig nested-1 | 60 / 374 | 6.1 / 10 |
| **orig coercion-derivability-cache** | **4331 / 128802** | **4397 / 128802** |
| refine-8 | 85 / 713 | 11 / 11 |
| nestwide-8 | 108 / 1392 | 16 / 88 |
| transneg-8 (negative) | 44 / 489 | 8.8 / 161 |
| **transconf-8** | **857 / 30637** | **951 / 30637** |
| **trans-8** | **1829 / 61676** | **1755 / 61352** |
| **assoceq-5** | **2705 / 91512** | **3538 / 91180** |
| **assoceq-8** | **5879 / 153018** | **5864 / 152662** |
| **assocneg-8** | **5143 / 131895** | **5293 / 131543** |

**Findings.**
- **Nested givens and refinement chains are cheap and scale linearly.** The existing flags already take them to a few ms (`index` + `memberskip`).
- **Equality reasoning is the expensive pattern, and no existing flag helps it.** The cost jumps at chain length 3 (trans-2: 2.3k matches; trans-3: 29.8k) and then grows linearly. The existing test `coercion-derivability-cache.hylo` alone takes 4.3 s.
  - `index` and `absmodel` disable themselves as soon as a coercion source (`T ~ U`) is visible.
  - The search itself is driven by the built-in symmetry and transitivity givens. `<T0,T1,T2> T0 ~ T1, T1 ~ T2 ⇒ T0 ~ T2` introduces a fresh middle variable that matches every equality and the reflexivity given, at every layer.

## 2. Equality reasoning: what was tried

Profile (gdb sampling, assoceq-8, all-sound flags):
- `takeSummonResults`/`match`: 86%;
- `formThread` (opening the built-in givens' universals, substitution): 40%;
- `StableSet.subscript.getter`: 37%;
- generic-metadata instantiation: 26%;
- `canDeriveCoercions`: 26%.

| Attempt | Result |
|---|---|
| `coercememo`: memoize `canDeriveCoercions` under assumptions | sound; 6–15k hits; **no time gain** (negative result, see `techniques/coercememo.md`) |
| `typevec`: contiguous storage for type projections | sound; **−15 to −20%** on these workloads and on the stdlib (see `techniques/typevec.md`) |

What would really help is an algorithmic change. Ideas for the next round:
- **Equivalence-class refutation of equality goals.** Compute the congruence closure of the equalities in scope; refute `a ~ b` when `a` and `b` are in different classes and no wildcard source exists.
  - This would make every negative equality goal O(1).
  - **But it is not sound with respect to the baseline today**, because the baseline accepts equalities outside the closure (§3). It must wait until that bug is fixed, or ship as part of the fix.
- **Thread deduplication within a BFS layer.** Threads that are identical up to variable renaming (same witness type, goal, environment and continuation shape) are expanded repeatedly.
  - Deduplicating them is result-preserving only if their proof terms are also identical; otherwise ambiguity reporting would change.
  - Needs a careful argument.
- **Union-find for equalities** instead of searching with symmetry and transitivity. This is a semantic change: the proof terms change. It belongs with the depth-cap redesign.

## 3. A baseline soundness bug: unrelated equalities make associated types equal

`../workloads/round3/bug-assoc-eq-two-links.hylo`:
```hylo
trait P { type X }
fun check<T>(x: T) {}
fun f<A, B, C, D where A is P, B is P, C is P, D is P, A.X == B.X, C.X == D.X>(x: D.X) {
  check<A.X>(x)   // accepted by the baseline, but nothing relates A.X to D.X
}
```

Variants, each run against the baseline (`4587ce9e1a23`); 0 diagnostics means accepted:

| Variant | Diagnostics |
|---|---:|
| one equality (`A.X == B.X`), pass `C.X` | 1 (correct) |
| two unrelated equalities, pass `D.X` or `C.X` | **0 (wrong)** |
| second equality over another trait (`C.Y == D.Y`), pass `D.Y` as `A.X` | **0 (wrong)** |
| two equalities, pass `E.X` where `E` appears in no equality | 1 (correct) |
| two equalities, pass `Bool` | 1 (correct) |
| two equalities, pass `D` itself | 1 (correct) |

So any type that appears as a side of *some* equality can be coerced into any other such type, once there are at least two equalities in scope. The generated `assocneg N` workloads (N ≥ 3) are accepted for the same reason.

Hypothesis, not verified: `match` turns nested mismatches into *assumed* equality givens (`environment.assuming(givens:)`). These are discharged one at a time in `threadContinuation`, but while one is being discharged, the remaining ones are still visible as candidates. Together with the built-in symmetry and transitivity (whose middle variable matches anything), this allows a circular proof. A resolution trace of `bug-assoc-eq-two-links.hylo` would confirm or refute this.

This affects the correctness of the baseline, not of any flag. It should be reported upstream.

## 4. The depth cap

`HYLO_TC_MAXDEPTH` (new; default 10) overrides `maxImplicitDepth`. It changes semantics and exists only for measurements.

### 4.1 The test corpus never reaches the cap

`depth/scan.jsonl` (`depth/depthscan.py`) ran all 192 tests plus the round-3 workloads at caps 10, 12, 15 and 20. Every file has **identical match counts and diagnostics** at every cap, and `summon.depthExhausted` is 0 everywhere. The apparent >2× slowdowns in the raw data are load noise: the match counts are unchanged.

### 4.2 Programs whose outcome depends on the cap

`depth/scan2.jsonl` (`depth/depthscan2.py`; summary in `depth/scan2-summary.txt`). Each program is run at caps 6–20, with the baseline and with the sound set.

| Program | Smallest cap at which it is accepted | Notes |
|---|---:|---|
| `wide-tuple-3` (copy a 3-tuple of Bool, …) | 8 | |
| `wide-tuple-4` | 10 | |
| `wide-tuple-5` | **12**: rejected by today's compiler | copying a 5-tuple fails at cap 10 |
| `wide-tuple-6` | 14 | |
| `wide-tuple-7` | 16 | |
| `wide-given-8` / `-9` / `-10` / `-11` | 10 / 12 / 12 / 14 | one given with N premises |
| `chain8` / `chain9` / `chain10` / `chain12` | 10 / 12 / 12 / 14 | |

The cap counts BFS steps along a thread, which is roughly the proof size. A wide but shallow proof hits it as easily as a deep one.

### 4.3 Failing programs: cost vs cap

| Program | Cap 6 | Cap 10 | Cap 14 | Cap 20 | With `absmodel` (any cap) |
|---|---:|---:|---:|---:|---:|
| div-loop-20 (20 queries, `P<T> ⇐ P<T>`) | 130 | 202 | 288 | 392 | ≈5 |
| div-grow-20 (`T is P ⇐ S<T> is P`) | 126 | 217 | 316 | 401 | ≈6 |
| div-dead-20 (mutual dependency) | 126 | 210 | 268 | 436 | ≈5 |
| **div-branch** (two looping givens) | 157 | **2296** | **44543** | timeout (≥ cap 16) | **≈3.5 (1 match)** |
| div-branch-pair (two premises) | 54 | 64 | 83 | 97 (cap 18) | ≈3.3 |
| **div-branch-trunc** (div-branch plus a base fact deeper than k) | 152 | 2551 | — | — | 16 / 324 / 1180 at caps 6 / 10 / 12 |

`depth/div-branch.hylo` is ten lines. Its baseline cost is **exponential in the cap**: matches grow 4× per +2 (6.8k → 27.5k → 110k → 442k → 1.77M). Today, at cap 10, it already takes 2.3 s to report a type error. Raising the cap to 14 makes that 44.5 s.

**With `absmodel`, the cap no longer matters for refutable failures.** The root goal is refuted before any search: 1 match, about 3 ms at every cap. That makes raising the cap safe for those programs.

**The limit of `absmodel`** is `depth/div-branch-trunc.hylo`. A base fact deeper than k = 2 (`S<S<Xi>> is P`) truncates to `P(S(S(⊤)))`, which lets the model derive `P(⊤)`, so the root goal cannot be refuted.
- The model still prunes the `R<…>` branches: 24× fewer matches.
- The cost is still exponential in the cap.
- k = 3 adds about 5 s of saturation and does not help.
- Tabling would not help either, because every subgoal is distinct (`S^a R^b …`).

### 4.4 Recommendations

1. Land `absmodel` (k = 2) before touching the cap. Then a larger cap costs nothing for failing programs the model refutes.
2. Do not raise the cap blindly. Branching failures that the model cannot refute (`div-branch-trunc`) are exponential in it.
3. Replace the BFS step count with a per-thread **height** bound, plus a global budget on matches. That accepts `wide-tuple-N` and `wide-given-N` for any N without making divergent searches longer. This is a semantic change (review C1/C2) and belongs in a separate PR.

## 5. Headline numbers (`bench.md`)

All sound flags (`symindex, coesrc, traitindex, memberskip, unify, index, absmodel, typevec`) against the baseline:

| Workload | Baseline | Sound set | Speed-up |
|---|---:|---:|---:|
| stdlib | 1007 | 235 | 4.3× |
| members-big | 20109 | 959 | 21× |
| breadth40 | 7424 | 79 | 94× |
| div-loop-20 | 191 | 5 | 42× |
| div-branch | 2220 | 3 | 864× |
| wide-tuple-5 | 85 | 5 | 18× |
| trans-8 | 1855 | 1375 | 1.3× |
| assoceq-5 | 2619 | 2000 | 1.3× |
| coerc-cache | 3532 | 2771 | 1.3× |
| refine-8 | 78 | 6 | 13× |
| nestwide-8 | 99 | 9 | 11× |

## 6. New code in this round (`research/impl/0005-*.patch`, `0006-*.patch`)

| Flag | What | Sound | Measured |
|---|---|---|---|
| `typevec` | contiguous array for type projections | yes: 216/216 identical | stdlib −20%; equality workloads −15 to −19% |
| `coercememo` | memo of `canDeriveCoercions` under assumptions | yes (argument in its doc) | no gain |
| `HYLO_TC_MAXDEPTH` | override of the depth cap (semantic knob) | — | used for §4 |
