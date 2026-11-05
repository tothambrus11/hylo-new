# Speeding up type checking and name resolution in Hylo: a graph-theoretic study

Branch: `tc-perf-research` in `/home/hylo/hylo-tc/hylo-new` (uncommitted working tree; full patch in
`research/tc-experiments.patch`). Date: 2026-11-05.

## 1. Summary

The compiler front end was instrumented and profiled. Six optimizations, each grounded in a
graph-theoretic reading of the type checker, were implemented behind run-time flags
(`HYLO_TC_EXPERIMENTS=names,unify,index,absmodel,solver,loopcheck`). Every flag combination
produces **diagnostics identical to the baseline** on all 192 single-file compiler tests.

| Workload | Baseline | All experiments | Speed-up | Main lever |
|---|---:|---:|---:|---|
| Standard library (type checking) | 461 ms | 160 ms | 2.9× | names + index + unify |
| 8-way overload × 8 args, one call | 38 663 ms | 31 ms | ~1 200× | solver (forward checking) |
| return-type overloads 3 × 10 | 1 765 ms | 19 ms | ~90× | solver |
| 80 traits × 80 types (6 400 givens), 80 queries | 49 898 ms | 141 ms¹ | ~350× | index |
| 500 extensions, 500 member uses | 2 015 ms | 73 ms | 27× | names |
| 2 000 extensions, 1 000 member uses | 9 582 ms | 372 ms | 26× | names |
| intro.md divergence `∀T. P T ⇒ P T`, 20 queries | 101 ms | 2.5 ms | 40× | absmodel / loopcheck |
| growing divergence `∀T. P (S T) ⇒ P T`, 20 queries | 107 ms | 2.6 ms | 41× | absmodel |
| resolution chain of depth 8 | 12.1 ms | 1.7 ms | 7× | index |

¹ `index` alone; the full combination was not re-run on this 50-second workload.

Answer to the question in `intro.md`: yes, a cheap and sound "this resolution will fail" check
exists. It is the emptiness test of a *depth-k abstract least model* of the givens. That model is
the bottom-up (hypergraph-reachability) counterpart of the bipartite rule/type graph in the letter,
extended to universally quantified rules by truncating terms at depth k. At k = 2 it costs about
2–4 ms for the whole standard library, refutes all three divergence patterns before any search,
and is sound once equality premises are handled (see §5.4: differential testing caught an
unsound first version).

## 2. Methodology

* **Harness.** `Sources/tc-bench` (new executable target) loads the bundled stdlib plus user files
  and times parse, scope, stdlib typing and user typing separately, keeping the best of N runs
  (release build, Swift 6.4, WSL2 x86-64). `--count` enables event counters
  (`Sources/FrontEnd/Typer/TyperCounters.swift`). Counters are off and cost one branch when
  disabled.
* **Profiling.** `perf record -g` (frame pointers). The local `perf` build cannot symbolize, so
  `research/scripts/perfsym.py` resolves addresses with `nm` and aggregates self and inclusive
  time.
* **Workloads.** `research/scripts/gen.py` generates synthetic programs: resolution chains,
  breadth (many givens), the three divergence shapes from `intro.md`, overload sets, and member
  lookup through extensions. They are in `research/workloads/`.
* **Correctness.** `research/scripts/difftest.sh` runs every `Tests/CompilerTests/{positive,negative}/*.hylo`
  under each configuration and diffs the sorted diagnostics against the baseline. One test,
  `negative/illegal-enum-case.hylo`, crashes the harness in the baseline as well
  (`Typer.declaredType(of:)` force-unwrap at Typer.swift:1367). It is excluded as pre-existing.
* **Unit tests.** `swift test -c release --filter FrontEndTests` with every experiment enabled:
  128 tests, 0 failures.
* **Literature.** Two literature surveys, about 60 sources in total, are in
  `research/lit-resolution.md` and `research/lit-solver-names.md`. 20 PDFs are in
  `research/papers/`, with Markdown conversions in `research/papers/md/`; they were fetched with
  `scihub-cli`, which tries OpenAlex, arXiv and Unpaywall before Sci-Hub.

## 3. Where the time goes (baseline, stdlib, 10 468 samples)

Inclusive time:

| Function | % |
|---|---:|
| `Typer.resolve(_:memberOf:visibleFrom:)` | 71 |
| `Typer.takeSummonResults` / `match` (implicit resolution) | 55 / 53 |
| `Typer.applies(_:to:in:)` (does an extension apply to a type?) | 36 |
| `Typer.resolve(_:inheritedMemberOf:…)` | 31 |
| `Typer.canDeriveCoercions` | 20 |
| `TypeStore.unifiable` | 17 |

Self time is dominated by the Swift runtime: `tryCast` (7.5 %), retain/release (13 %), generic and
tuple metadata caches (about 10 %), `swift_dynamicCast` (2 %), and hashing.

Event counts:
* Implicit resolution made 41 452 match attempts, of which **818 (2 %)** succeeded.
* Member lookup ran the expensive `applies` check about 7 300 times on extensions that **do not
  declare the member** being looked up.

Both are textbook cases for indexing.

### Stdlib typing per configuration (best of 9)

| Configuration | ms |
|---|---:|
| baseline | 461 |
| names | 280 |
| unify | 426 |
| index | 212 |
| absmodel (k = 2) | 360 |
| solver | 463 |
| loopcheck | 456 |
| names + unify + index | 156 |
| all six | 160 |

## 4. The cross-cutting graph view

| Compiler problem | Graph / logic formulation | Classic results used |
|---|---|---|
| Implicit resolution (`summon`) | Givens are definite Horn clauses. The rule/type bipartite graph of `intro.md` is the incidence graph of a **directed B-hypergraph** (one hyperarc per given, tail = premises, head = conclusion). Resolution is a top-down search for a B-hyperpath. | Dowling–Gallier 1984 (linear Horn-SAT); Gallo et al. 1993 (directed hypergraphs) |
| "Pick the smallest term" | **Minimum-weight hyperpath** with a superior weight (size = 1 + Σ sizes). | Knuth 1977 (generalized Dijkstra); Nederhof 2003; Felzenszwalb–McAllester 2007 (A*LD) |
| "Resolution will fail" | **Unreachability** in the hypergraph. With ∀-rules the graph is infinite, so one computes a finite abstraction of the least Herbrand model. | Sato–Tamaki 1984 (depth-k); Frühwirth et al. 1991; Heintze–Jaffar 1990; Gallagher–Puebla 2002; RInGen 2021 |
| Divergence | Cycles in the hypergraph (variant loops), or unbounded term growth. | Bol–Apt–Klop 1991 (loop checking); Lean 4 tabled resolution 2020; Rust's next-generation trait solver |
| Candidate givens per goal | Adjacency lookup by the **head constructor** of the goal, instead of scanning every edge. | GHC `RoughMap`; Lean `DiscrTree`; term indexing (McCune, Graf) |
| Expression inference with overloads | CSP whose disjunctions are the overload sets. Search tree = product of domains unless pruned. | Forward checking / arc consistency; most-constrained-variable first; Freuder 1982 (tree-structured CSPs are polynomial); Swift solver 2025–26 |
| Name lookup | Scope-graph queries; member lookup = reachability through extension edges filtered by label. | Néron et al. 2015; Zwaan et al. 2022 (query specialization); stack graphs |

The same key function, "head constructor of a type", serves the resolution index (§5.3), the
abstract model (§5.4) and the CSP pruning tests.

## 5. Experiments

### 5.1 `names`: label-filter edges before traversing them (name lookup)

* **Idea (scope graphs).** A member query `x.m` should only traverse extension edges that carry
  the label `m`. `resolve(_:declaredIn:applyingTo:…)` ran `applies(e, to: q)`, a unification-based
  resolution thread, for every visible extension *before* checking whether `e` declares `m`.
* **Change.** Check `declarations(lexicallyIn: e)[n.identifier]` first and skip the extension
  otherwise (Typer.swift, in `resolve<S>(_:declaredIn:…)`). Semantics are unchanged by
  construction, since a skipped extension could not contribute candidates and `applies` only fills
  a cache.
* **Result.** Stdlib 452 → 267 ms (−41 %); `applies` calls 7 332 → 32. On members-big,
  9.6 s → 0.54 s.
* **Next step.** An inverted index name → [extension], so that lookup costs O(hits) instead of
  O(#extensions).

### 5.2 `unify`: tag-first dispatch in unification (constant factor)

* **Problem.** `TypeStore.unifiable` matched `switch (self[a], self[b])` against about 20
  `(let t as X, let u as X)` patterns. Each attempt builds a tuple of existentials and runs dynamic
  casts. That is the source of the `TupleCacheEntry`, `tryCast` and metadata entries in the profile.
* **Change.** Compare the operands' dynamic types first, then cast each operand once
  (`unifiableSameShape`, TypeStore.swift).
* **Result.** Stdlib −10 % alone, and it compounds with the others.
* **Next step.** A dense tag array beside the type store, so that `tag(of:)` needs no existential
  projection. `Docs/Misc.md` lists the analogous change for syntax trees as done.

### 5.3 `index`: head-constructor index of givens (resolution and coercions)

* **Idea (GHC `RoughMap`, Lean `DiscrTree`).** For each scope, bucket the visible givens by the
  nominal head constructor of their conclusion (for `A is P` the trait `P`; for `S<T>`, `S`). A
  subgoal only forms threads for its own bucket plus "wildcard" givens whose head is not nominal.
* **Second use.** The same index records the **coercion sources**: givens with `T ~ U` heads or
  bare-variable heads. `canDeriveCoercions` previously scanned every visible given for every
  structural mismatch, which made a query O(givens²). It now iterates only over the sources, which
  is usually an empty list.
* **Soundness.** When no coercion source is visible, a thread whose head constructor differs from
  the goal's fails at its first `match` step:
  * a top-level mismatch fails immediately;
  * a mismatched trait under a `TypeApplication` triggers `canDeriveCoercions`, which then returns
    `false`.

  Skipping such threads therefore leaves the results and the BFS layering unchanged. When coercion
  sources exist (or assumed equalities are pending), the code falls back to the full scan. Group
  offsets, and with them penalties, are preserved. The index is only used and cached when no
  declaration is on the typing stack, mirroring the existing `notOnStack` filter.
* **Results.**

  | Workload | Before | After |
  |---|---|---|
  | Stdlib match attempts | 41 452 | 15 051 (alone), 4 057 (with `names`) |
  | Stdlib time | 452 ms | 217 ms (−52 %, alone) |
  | breadth80 | 49.9 s | 0.14 s |

### 5.4 `absmodel`: depth-k abstract least model ("resolution will fail")

This is the direct answer to `intro.md`.

* **Formulation.** A given `<X…> A1, …, An ==> H` is read as the Horn clause `H :- A1, …, An`.
  Anything `summon` derives is a ground instance in the least Herbrand model of the visible
  clauses: the engine only returns real derivations, so this holds whatever the size ordering or
  the depth limit. The model is infinite (`P Z, P (S Z), …`), so it is computed bottom-up in the
  domain of terms **truncated at depth k** (subterms below depth k become `⊤`). This domain is
  finite, so semi-naive Datalog saturation terminates. A goal that unifies with no fact of the
  abstract model is **definitely underivable**.
* **Design.** `Sources/FrontEnd/Typer/AbstractResolution.swift`:
  * Terms: `⊤`, variables, and nodes keyed by nominal constructor, tuple cons/empty and equality.
  * Facts are bucketed by head key and kept modulo subsumption.
  * Saturation is semi-naive: after the first round, at least one premise must match a fact from
    the previous round's delta.
  * The model is incremental along the scope tree: a child scope starts from the parent's
    saturated model and fires only its new clauses. This is valid because least models are
    monotone in the clause set. The top-level model is shared by all files of a module.
  * It is consulted at every subgoal in `summon(...where:)`, so whole sub-searches are pruned, not
    only root queries.
* **Over-approximations, all sound.**
  * Higher-kinded heads, associated types, arrows and other non-first-order types become `⊤`.
  * Premises that are themselves quantified or conditional are dropped.
  * Variables shared between premises keep their correlation.
* **Soundness bug found by differential testing.** The first version refuted `T ~ T` in
  `positive/equality.hylo`. Equalities are proven by the *built-in* reflexivity, symmetry and
  transitivity givens, which the model did not contain. The fix:
  * equality goals always answer "may derive";
  * equality premises are treated as satisfied;
  * any user given with an equality or bare-variable head makes the model inconclusive.

  After the fix, all 192 tests match the baseline.
* **Results.**

  | Depth k | Saturation cost (stdlib, all scopes) | Facts | Subgoals refuted |
  |---:|---:|---:|---:|
  | 1 | 0.5–3 ms | 198 | 0 |
  | 2 | 2–4 ms | 1 399 | 225 |
  | 3 | 5.5 s | 14 082 | 224 |

  k = 2 is the sweet spot. k = 3 explodes because tuple cons-lists (`{T, ...U} is Movable`)
  multiply facts, and buys nothing over k = 2 on the stdlib. Alone at k = 2, stdlib typing drops
  from 452 to 349 ms (−23 %); on top of the index it adds no further gain there.

  On the `intro.md` patterns (20 queries each), every query is refuted up front: 0 BFS layers
  instead of hitting the depth limit 21 times. Loop: 101 → 6.7 ms. Growing: 107 → 7.8 ms. Dead
  mutual dependency: 89 → 6.9 ms.
* **Relation to the letter's idea of propagating `X = Int` downward.** That idea is top-down,
  goal-directed constraint propagation. This model works the other way: it ascends from facts and
  is computed once per scope. Both are sound. The literature (`lit-resolution.md` §6a.1)
  suggests adding the goal-directed variant: unfold from the goal by unifying heads, truncate at
  depth k, then run Dowling–Gallier counters. It is exact for "regular" givens and handles goals
  with open variables more precisely. A follow-up from the same paper is a **minimum-height bound**
  (Knuth's algorithm over the same hypergraph with `1 + max`). If the abstract minimum height
  exceeds `maxImplicitDepth`, resolution must hit the depth cap, so that failure is predicted too.

### 5.5 `loopcheck`: ancestor loop check

* **Idea (Bol–Apt–Klop; Lean and Rust cycle handling).** In a smallest derivation, no subgoal is
  identical to one of its ancestors. If it were, the ancestor's derivation could be replaced by the
  subgoal's, giving a smaller term that completes in an earlier BFS layer. Such threads can never
  produce the selected result.
* **Implementation detail.** Ancestry is tracked **per pending premise**
  (`Environment.ancestry[assumedID]`), not per thread. Pending sibling premises share one stack,
  so a per-thread chain would wrongly count siblings as ancestors and prune valid proofs. Only
  identical goals (after reification) are pruned, not variants.
* **Results.** Loop: 101 → 19 ms. Dead: 89 → 25 ms. Growing: no effect, because that shape is not
  a cycle and needs the abstract model. Diagnostics are identical on all tests.

### 5.6 `solver`: deferred overload branching with forward checking

* **Problem (CSP view).** `Solver.solve(overload:)` forked the whole system for each candidate as
  soon as the overload goal was popped. Each fork carried every other overload set, so an
  expression with n independent overloaded calls explored up to kⁿ branches (36 128 forks for
  8 × 8), even though each call's argument alone fixes its overload.
* **Change** (Solver.swift, `resolveParked`, `probe`):
  1. Park overload constraints until the other goals have been processed (fresh queue empty).
  2. For each parked set, **probe** each candidate: fork, bind, and propagate to quiescence without
     branching on other sets. This is forward checking.
  3. If some candidate probes with 0 errors, drop candidates with more errors. Errors are
     monotone, so a dropped candidate cannot lead to an error-free solution.
  4. If exactly one candidate survives, **commit in place without forking**. Otherwise branch on
     the set with the fewest survivors (most-constrained first).
  5. If no candidate is error-free, fall back to full branching, so diagnostics for erroneous
     programs are unchanged.

  Coercion and widening defaulting (`refreshCoercionAndWideningConstraints`) only happens after
  parked sets are resolved, so the original order of decisions is preserved.
* **Results.**

  | Workload | Before | After |
  |---|---|---|
  | 4 × 8 | 3 361 ms | 26 ms |
  | 8 × 8 | 38 663 ms | 31 ms (64 probes, 8 commits, 0 forks) |
  | return-type 3 × 10 | 1 765 ms | 19 ms |
  | stdlib | unchanged | unchanged (few overloads) |

* **Next step.** When several sets keep 2 or more survivors and are independent, split the
  remaining constraints into **connected components** of the variable–constraint graph (as Swift
  does) so their costs add instead of multiply. Freuder's result says tree-shaped expressions are
  then polynomial.

## 6. Findings beyond performance

1. **The depth cap rejects valid programs.** `need<where S⁹<Z> is P>()` with
   `given <T where T is P> => S<T> is P` fails with "no coercion…": the proof needs more than
   `maxImplicitDepth = 10` BFS layers, although it is finite and unique. The cap measures thread
   steps, not term size. Tabling with Knuth ordering (`lit-resolution.md` §6b.3) would remove the
   need for the cap for terminating searches, and the abstract model/loop check handle the
   divergent ones.
2. **Pre-existing crash.** `negative/illegal-enum-case.hylo` crashes the typer when typed directly
   (force-unwrap in `declaredType(of:)`, Typer.swift:1367). The driver may stop earlier in normal
   runs.
3. **Exclusivity pitfall.** `program.types.f(declaredType(of: g))` evaluates `program.types`
   *before* the mutating argument creates new types. This caused an out-of-range crash in my first
   index prototype. The same pattern elsewhere in the Typer is worth auditing.

## 7. Recommendations (ranked by payoff / risk)

1. **Land `names`** (5 lines, semantics-preserving by construction) and **`index`** (about 150
   lines, falls back whenever coercions are possible). Together with `unify`: stdlib 461 → 156 ms (−66 %).
2. **Land `solver` forward checking.** It turns observed exponential blow-ups into linear time and
   falls back to old behavior for erroneous programs. Then add component decomposition.
3. **Adopt `absmodel` at k = 2 plus `loopcheck`** as the fail-fast layer for resolution. Then add
   the minimum-height bound so depth-cap failures are predicted too.
4. **Replace BFS-with-depth-cap by tabled resolution in Knuth order**, with capped counting for
   ambiguity. This keeps the smallest-term semantics, shares subgoals, and fixes finding 1.
5. **Representation work:**
   * a dense tag array for types;
   * an inverted name → extension index;
   * path compression in `SubstitutionTable`;
   * a variable → goals map so `refresh()` does not rescan every stale goal;
   * congruence closure for equalities, which would make `canDeriveCoercions` exact and the index
     unconditional.

## 8. Artifacts

| Path | Content |
|---|---|
| `research/REPORT.md` | this report |
| `research/lit-resolution.md` | literature: Horn/hypergraphs, Knuth, regular abstractions, type-class engines, indexing |
| `research/lit-solver-names.md` | literature: constraint graphs, overload CSPs, scope graphs, incremental compilation |
| `research/papers/` | downloaded PDFs and Markdown conversions |
| `research/scripts/gen.py` | workload generator |
| `research/scripts/matrix.sh` | experiment runner |
| `research/scripts/difftest.sh` | differential correctness test |
| `research/scripts/perfsym.py` | perf symbolizer |
| `research/scripts/patch_*.py` | scripts that applied the experiments |
| `research/workloads/` | generated programs |
| `research/diff/` | per-configuration diagnostics for all compiler tests |
| `research/tc-experiments.patch` | full source diff on `tc-perf-research` |
| `hylo-new/Sources/tc-bench/` | benchmark harness |
| `hylo-new/Sources/FrontEnd/Typer/AbstractResolution.swift` | abstract least model |
| `hylo-new/Sources/FrontEnd/Typer/TyperCounters.swift` | counters and experiment flags |
