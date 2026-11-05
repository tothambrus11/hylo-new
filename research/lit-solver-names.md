# Literature study: speeding up Hylo's constraint solver (overloading) and name resolution

Date: 2026-11-05. Scope: `Sources/FrontEnd/Typer/Solver.swift`, `Constraint.swift`,
`SubstitutionTable.swift`, name resolution in `Typer.swift` (approx. lines 4045-4720), `Scoper.swift`.
Legend: **[verified]** means the claim was checked against the paper text or the primary web page during
this study. **[unverified]** means it comes from memory or a secondary source and still needs checking.
Local PDFs are in `/home/hylo/hylo-tc/research/papers/`, with markdown in `.../papers/md/`.

---

## 0. What Hylo does today (grounding)

Observations from reading the code. The code was not modified.

**Solver (`Solver.swift`)**
- Goals live in one array (`goals`). `fresh` is a LIFO work stack and `stale` holds postponed goals.
  `postpone(_:)` is used when a callee, qualification or parent type is still a type variable.
- `assume(_:equals:)` assigns a substitution and then calls `refresh()`. That call **re-reifies every
  stale goal** to find the ones that changed, so each assignment costs O(|stale| x type size). There is no
  index from type variables to the goals that mention them (no constraint graph and no watch lists).
- `OverloadConstraint` is branched on **as soon as it is popped** from `fresh`. Nothing waits for the
  deterministic constraints to reach a fixpoint first. `solve(overload:)` forks the whole solver
  (`Self(forking:)`, a value copy of `goals`, `outcomes`, `substitutions`, `bindings` and so on) once per
  candidate. Each fork then re-solves every constraint still pending. With k overload sets of n_i
  candidates in one expression, the search is the product of the n_i, **even when the sets do not
  interact**. There is no connected-component split.
- Pruning is branch-and-bound on `SolutionScore` (errors << 32 | penalties). A branch is cut only when
  `current > best`. Even after a zero-error solution is found, every candidate is still tried so that
  ambiguity can be detected. `penalties` is carried along but no branch currently increments it.
- `SubstitutionTable` is union-find **without path compression or union by rank**. `subscript` and
  `walk` follow chains, and the chains are only flattened at the end (`optimized()`).
- Candidates are pre-filtered before the solver runs, in `Typer.assume(_:boundTo:...)` and
  `filterInPlace(_:callable:withLabels:)`, by call style and argument labels only.
- The system is bidirectional to a degree: `InferenceContext.expectedType` and `role` are already
  threaded through.

**Name resolution (`Typer.swift`)**
- `lookup(_:unqualifiedIn:)` walks the scope chain (`program.scopes(from:)`), checking a per-scope hash
  table `declarations(lexicallyIn:)` (memoized as `scopeToLookupTable`). It then checks the other files
  of the module, then the imports. **The result per (scope, name) is not memoized**, so every use of a
  name repeats the walk.
- `resolve(_:memberInExtensionOf:...)` calls `extensions(visibleFrom:)`, which returns **all** extensions
  visible from the scope. It is memoized per scope, but the arrays are copied and appended down the
  scope chain. Then `resolve(_:declaredIn:applyingTo:...)` runs **`applies(e, to: q, in:)`, an
  implicit-resolution match, for every extension before checking whether `e` declares the name `n`**.
  `applies` is memoized only for closed types and only when no implicit is on the stack.
- `resolve(_:inheritedMemberOf:...)` does filter traits by name first (`lookup(_:memberOfTraitVisibleFrom:)`)
  and then calls `summon`.
- `Scoper.visit` already builds scope tables in parallel, one task per file. `Typer.apply()` checks
  top-level declarations sequentially and computes declared types on demand, with memoization and
  `declarationsOnStack` for cycles.

---

## A1. Constraint graphs and decomposition

### A1.1 Swift type checker design doc (constraint graph, connected components, union-find, ranking)
- Citation: Swift project, *Type Checker Design and Implementation* (`docs/TypeChecker.md`).
  URL: https://github.com/swiftlang/swift/blob/main/docs/TypeChecker.md **[verified]**
- The constraint graph has type variables as vertices and constraints as (hyper)edges. The solver
  "compute[s] the connected components within the constraint graph" and solves each one separately.
- Type-variable equivalence classes are merged with "a basic union-find algorithm". A binding is
  chosen for the representative only.
- Each disjunction term is "visited separately". Cheaper choices are tried first.
- Scores are integer vectors compared lexicographically. Ties fall back to a second ranking step that
  compares overload choices.
- **Applicability to Hylo:** add a lightweight constraint graph to `Solver`, as a map from
  `TypeVariable.ID` to the set of `GoalIdentity` values that mention it. (1) `refresh()` would visit
  only the goals adjacent to the newly bound variable (its watch list) instead of reifying all of
  `stale`. (2) Before branching in `solve(overload:)`, the residual goals would be partitioned into
  connected components (by shared type variables, with `OverloadConstraint.type` as the link). Each
  component would be solved independently and the solutions merged (union of `substitutions` and
  `bindings`, sum of scores). Independent overload sets would then cost the sum of their sizes instead
  of the product. Hylo's `SolutionScore` is additive (errors and penalties), so merging is
  straightforward.

### A1.2 Swift forum: "Roadmap for improving the type checker" (Slava Pestov, 30 Oct 2025)
- URL: https://forums.swift.org/t/roadmap-for-improving-the-type-checker/82952 **[verified]**
- The post describes Swift 6.3 **disjunction selection**, by Pavel Yaskevich ("xedin"). It gathers more
  information to choose the next disjunction and runs inside the solver, replacing "brittle" pre-solving
  passes.
- It describes a **trail** (Swift 6.2) for cheap backtracking and an **arena optimization**
  (`-solver-enable-prepared-overloads`): generic overload type variables and constraints are allocated
  once, not regenerated on every attempt. The post says this can turn exponential space into polynomial
  space.
- Planned work: make connected components with partial-solution merging cheaper, build on the trail,
  and make binding selection O(1) or O(log n) instead of linear (currently quadratic overall). Longer
  term: non-chronological backtracking and SAT-style clause learning.
- Reported results: an invalid `String + Int` case went from about 10 s (6.1) to 1.7 s. An internal
  project went from 42 s to 10 s.
- **Applicability to Hylo:** (a) the trail idea replaces `Self(forking:)` in `solve(overload:)`.
  Each fork currently copies `goals`, `outcomes`, `substitutions`, `bindings`, `elaborations` and so on,
  through COW on the first write. An undo log would let `solution(betterThanOrEqualTo:using:)` record
  changes and roll them back per choice. (b) "Prepared overloads" corresponds to caching
  `choice.type` instantiation (the `fresh()` variables made in `typeOfName` and `resolve(...)`) so it
  happens once per candidate, not once per branch.

### A1.3 Swift forum: "Recent improvements to the type checker" (Slava Pestov, 2 Jun 2026, Swift 6.4)
- URL: https://forums.swift.org/t/recent-improvements-to-the-type-checker/87048 **[verified]**
- **Disjunction pruning** classifies each overload as favored, not favored, or "cannot possibly
  succeed". The last kind is disabled, judged by comparing the overload's declared type with the
  argument and result types known so far.
- **Guaranteed moves:** if exactly one enabled choice remains, it is bound immediately, as unit
  propagation. If none remain, the solver backtracks at once.
- **Binding inference by domains:** subtype and supertype sets for each type variable are intersected.
  A singleton domain is bound with no delay, and an empty domain causes immediate backtracking.
- Reported results: several "too complex" expressions became instant. A filter, map and reduce chain
  went from about 300 ms to about 4 ms.
- **Applicability to Hylo:** this is forward checking and arc consistency applied to disjunctions (see
  A2.3). In `solve(overload:)`, before forking, reify `k.type` and drop every `choice` for which
  `program.types.unifiable(k.type, choice.type)` fails and no coercion could repair it. If one choice is
  left, bind it without forking: call `assume(k.name, boundTo:)` and schedule the equality, exactly as
  `Typer.assume` does for a single candidate. If none is left, fail immediately. Hylo's
  `refreshCoercionAndWideningConstraints()`, which picks bounds when `fresh` empties, plays the role of
  Swift's delayed binding. The 6.4 lesson is to choose overloads **before** defaulting coercions to
  equalities, so that the defaulting does not commit to types too early.

### A1.4 Swift PR #82574 (xedin, June 2025): new favoring algorithm on by default
- URL: https://github.com/swiftlang/swift/pull/82574 **[verified that the PR exists; author's identity
  as Pavel Yaskevich unverified]**
- Favoring is now the default. The old hacks sit behind `-enable-constraint-solver-performance-hacks`.
- **Applicability to Hylo:** favoring maps onto *ordering* `k.candidates` in `solve(overload:)`. Try
  first the candidates whose parameter types exactly match known argument types, then candidates
  preferred by `isPreferred`. Combined with branch-and-bound on `best`, a good first solution cuts later
  branches.

### A1.5 Swift trail PRs (Slava Pestov, Oct 2024)
- URLs: https://github.com/swiftlang/swift/pull/76879, https://github.com/swiftlang/swift/pull/77174,
  https://github.com/swiftlang/swift/pull/77152 **[verified as existing; release mapping unverified]**
- These move solver state into `SolverTrail`: types of AST nodes, resolved overloads, contextual types
  and retired constraints. Undo replays the changes in reverse recording order.
- **Applicability to Hylo:** the template for replacing `Solver.init(forking:)`. The logged state would
  be `substitutions.assign`, `bindings[n] =`, `outcomes[g] =`, `fresh` and `stale` pushes and pops,
  `elaborations.append` and `argumentElaborations.append`. In return, `solve(overload:)` must return
  an extracted `Solution` value, as it already does, rather than a forked solver.

### A1.6 Union-find with path compression (Tarjan 1975) and Rémy / Kiselyov levels
- Tarjan, R. E. "Efficiency of a good but not linear set union algorithm." *JACM* 22(2), 1975.
  DOI 10.1145/321879.321884 **[DOI from memory, unverified]**
- Kiselyov, O. "How OCaml type checker works -- or what polymorphism and garbage collection have in
  common." https://okmij.org/ftp/ML/generalization.html **[verified]**
- Rémy, D. "Extension of ML type system with a sorted equational theory on types." INRIA RR-1766, 1992.
  **[citation from memory, unverified]**
- Pottier, F., Rémy, D. "The Essence of ML Type Inference." Chapter 10 of Pierce (ed.), *Advanced
  Topics in Types and Programming Languages*, MIT Press, 2005. **[citation from memory]**
- Path compression with union by rank gives near-constant amortized `find`.
- Levels: each type variable records the `let` depth that owns it. Generalization quantifies only the
  variables whose level is deeper than the current one, so the environment is never scanned. Kiselyov's
  "sound_lazy" variant also delays level updates and the occurs check, so unifying with a free variable
  takes O(1) **[verified on the page]**.
- Pottier and Rémy present inference as constraint generation followed by solving with a stack of
  scopes and union-find multi-equations. Generalization is per-let "rank" processing.
- **Applicability to Hylo:** `SubstitutionTable.subscript` and `walk` should compress paths, which
  requires either a mutating `find` or a separate `parent` array indexed by `TypeVariable.ID` bits.
  `assign` should union by rank. This cuts the repeated chain walks in `program.types.reify(...)`, which
  is called on every goal pop and in every `refresh()`. With a persistent or trailed union-find
  (Conchon and Filliâtre, "A persistent union-find data structure", ML Workshop 2007,
  **[unverified citation]**), forks stay cheap. Levels matter less: Hylo appears not to generalize local
  bindings, so this is low priority.

---

## A2. Overload-resolution complexity and pruning

### A2.1 Hardness results
- Palsberg, J. "Overloading is NP-complete: A tutorial dedicated to Dexter Kozen." In *Logic and
  Program Semantics*, LNCS 7230, Springer 2012. **[title and venue verified via a listing; LNCS number
  and DOI unverified]**
- Kaes, S. "Parametric overloading in polymorphic programming languages." ESOP 1988.
  DOI 10.1007/3-540-19027-9_9 **[DOI verified via search]**
- Volpano, D. "Lower bounds on type checking overloading." *IPL* 57(1), 1996.
  DOI 10.1016/0020-0190(95)00184-0 **[verified via search]**
- Lippert, E. "Lambda expressions vs. anonymous methods, part five" (C# overload resolution with
  lambdas encodes 3-SAT).
  https://learn.microsoft.com/archive/blogs/ericlippert/lambda-expressions-vs-anonymous-methods-part-five
  **[URL found; content from memory]**
- Unrestricted overloading combined with type inference that carries information both ways (generics
  or closures) reduces from 3-SAT. Each overloaded name is a variable with a finite domain, and the
  shared type variables are the constraints.
- The hardness comes from **shared type variables that create cycles** in the constraint graph. A pure
  expression tree with monomorphic candidates is easy (see A2.2).
- **Applicability to Hylo:** keep the exponential search, but use the structure. Most expressions are
  tree-shaped, so decomposition and propagation (A1.1, A1.3, A2.3) should make the common case
  near-linear. Keep a counter of `solve(overload:)` forks per `discharge` call. Use it as a
  "too complex" budget (Swift caps at about 1M disjunction choices) and as a performance-test metric
  (Swift's 6.4 tests assert operation counts).

### A2.2 Polynomial cases: Ada two-pass and one-pass overload resolution
- Persch, G., Winterstein, G., Dausmann, M., Drossopoulou, S. "Overloading in preliminary Ada."
  SIGPLAN Notices 15(11), 1980. DOI 10.1145/800227.806880 **[DOI from memory, unverified]**
- Baker, T. P. "A one-pass algorithm for overload resolution in Ada." *TOPLAS* 4(4):601-614, 1982.
  DOI 10.1145/69622.69623 **[verified via search; PDF download failed]**
- Moss, A. *C∀ Type System Implementation.* PhD thesis, University of Waterloo, 2019.
  https://uwspace.uwaterloo.ca/items/2ad9e91b-d4a6-4c13-a44c-92e9fc488093 **[existence and abstract
  verified]**
- Ada uses a bottom-up pass that computes the set of possible result types of each subexpression,
  then a top-down pass that selects the interpretation matching the context. Baker gets one pass by
  building a DAG of interpretations.
- In CSP terms this is directional arc consistency on a tree, which Freuder (A3.2) shows is
  backtrack-free. It is polynomial because each node's candidate set is filtered by its children's
  feasible result types.
- Moss compares C∀ resolution strategies (bottom-up, top-down and deferred). The abstract says
  expression resolution is the main bottleneck and introduces a new union-find variant for type
  environments **[abstract verified; details unverified]**.
- **Applicability to Hylo:** a cheap bottom-up pre-pass in `Typer` before `discharge`. For a call
  `f(a, b)` whose callee is an `OverloadConstraint` and whose arguments have already been inferred,
  drop the candidates whose parameter count, labels and (when concrete) parameter type heads cannot
  accept the argument types. This generalizes `filterInPlace(_:callable:withLabels:)` from labels to
  argument types. A top-down filter by `InferenceContext.expectedType` would prune by result type. This
  shrinks domains before `Solver` is created.

### A2.3 Arc consistency, forward checking and fail-first (CSP)
- Mackworth, A. "Consistency in networks of relations." *Artificial Intelligence* 8(1), 1977.
  DOI 10.1016/0004-3702(77)90007-8 **[DOI from memory]**
- Haralick, R., Elliott, G. "Increasing tree search efficiency for constraint satisfaction problems."
  *AI* 14(3), 1980. DOI 10.1016/0004-3702(80)90051-X **[DOI from memory]**
- AC-3 keeps a queue of arcs. It removes domain values that have no support and re-enqueues the
  neighbours of each variable whose domain changed. That is O(e d^3).
- Forward checking: after each assignment, remove the inconsistent values of the neighbouring
  variables. Fail-first / MRV: branch on the variable with the smallest remaining domain.
- An empty domain proves failure without search. A singleton domain is a forced move.
- **Applicability to Hylo:** (1) In the main loop of `solution(betterThanOrEqualTo:using:)`, do not
  branch on an `OverloadConstraint` when it is popped. Move it to a `disjunctions` list and only branch
  once `fresh` is empty, so deterministic constraints have propagated first. Then (2) re-filter every
  pending disjunction's candidates against the reified `k.type` (forward checking), (3) bind singletons
  directly, and (4) branch on the disjunction with the **fewest** surviving candidates (MRV). Today each
  fork re-solves all pending deterministic goals k times, and dead candidates are discovered only after
  a full fork.

### A2.4 SAT-style search: non-chronological backtracking and learning
- Marques-Silva, J., Sakallah, K. "GRASP: A search algorithm for propositional satisfiability." *IEEE
  Trans. Computers* 48(5), 1999. DOI 10.1109/12.769433 **[DOI from memory]**
- Conflict analysis finds the set of decisions responsible for a failure. Backjumping skips the
  irrelevant choice points, and learned nogoods prevent the same conflict from recurring.
- Swift lists this as long-term work (A1.2).
- **Applicability to Hylo:** this is a longer-term option for `solve(overload:)`. When a fork fails,
  record which overload choices (`bindings` entries) the failed goals depended on. Doing so needs the
  constraint graph from A1.1 to track which goals were derived from which choices. The effort is high,
  so it only pays off once A1.1 and A2.3 are in place.

### A2.5 Bidirectional type checking
- Dunfield, J., Krishnaswami, N. "Bidirectional Typing." *ACM Computing Surveys* 54(5), 2021.
  DOI 10.1145/3450952 (arXiv 1908.05839). Local PDF:
  `/home/hylo/hylo-tc/research/papers/[2019] - Bidirectional Typing.pdf` **[verified]**
- Pierce, B., Turner, D. "Local type inference." *TOPLAS* 22(1), 2000. DOI 10.1145/345099.345100
  **[DOI from memory]**
- Checking mode pushes a known type into a term. Synthesis mode infers it. Annotations sit at the
  boundaries between the two.
- Checking mode makes the expected type available early, which prunes overloads by result type and
  types lambdas without search.
- **Applicability to Hylo:** this is already present (`InferenceContext.expectedType`). The remaining
  gap is to *use* `expectedType` in `Typer.assume(_:boundTo:for:at:in:)` and `filterInPlace` to drop
  candidates whose result type can never coerce to the expected type. Today only `role` (style and
  labels) is used to filter.

### A2.6 Other languages (TypeScript, Kotlin, C#, Rust)
- TypeScript (`checker.ts`, `chooseOverload`): candidates are tried in declaration order in two
  relation passes (subtype, then assignability), and the first match wins. There is no global
  backtracking across calls. TypeScript 7 (Go port, GA July 2026) runs `--checkers` workers in parallel
  (four by default). https://visualstudiomagazine.com/articles/2026/07/08/typescript-7-arrives-to-rock-vs-code-with-go-powered-speed.aspx
  **[parallel flag verified; the details of chooseOverload are from memory]**
- Kotlin spec, "Overload resolution": resolution walks a tower of receiver and scope *levels* and stops
  at the first level with an applicable candidate, then picks the most specific candidate.
  https://kotlinlang.org/spec/overload-resolution.html **[from memory, unverified]**
- C#: resolution is greedy per call, but lambdas are rebound for each candidate delegate type, which
  is exponential in nested lambdas (Lippert).
- Rust (rustc `fast_reject::SimplifiedType`): impls are indexed by the simplified head of their self
  type (`non_blanket_impls`), so lookup checks only the matching bucket plus the blanket impls.
  **[from memory, unverified]**
- **Applicability to Hylo:** (a) the Kotlin-style "stop at the first scope level with a viable
  candidate" rule is a semantic choice. Hylo's `lookup(_:unqualifiedIn:)` already does it for
  non-overloadable declarations. Applying it inside `solve(overload:)` would let the solver try inner
  candidates first and skip outer ones once an inner candidate succeeds. That changes semantics, so it
  is for the language designers. (b) The Rust-style head index is item B2.3.

---

## A3. Ordering by dependency and structural decomposition

### A3.1 Tarjan SCCs and topological ordering for (parallel) declaration checking
- Tarjan, R. E. "Depth-first search and linear graph algorithms." *SIAM J. Comput.* 1(2), 1972.
  DOI 10.1137/0201010 **[DOI from memory]**
- SCCs of the declaration dependency graph (whose signature or body mentions which declaration) give
  a DAG. Each SCC can be checked once all the SCCs it depends on are done, and independent SCCs can be
  checked in parallel.
- Haskell and ML use the same idea for binding-group analysis.
- **Applicability to Hylo:** `Typer.apply()` loops over `topLevelDeclarations` sequentially, and
  `declaredType` and `check(_:)` pull dependencies on demand (memoized, with cycle detection through
  `declarationsOnStack`). Hylo is already demand-driven. What it lacks is *parallelism*. Pass one would
  compute declared types (signatures) on demand. Pass two would check bodies (`check(FunctionDeclaration.ID)`),
  which are independent given the signatures, across tasks, the way `Scoper.visit` already parallelizes
  per file. That requires splitting `Typer`'s `Memos` into shared read-mostly tables and per-task tables
  (see B1.3). The effort is high.

### A3.2 Freuder: backtrack-free search on tree-structured CSPs; width
- Freuder, E. C. "A sufficient condition for backtrack-free search." *JACM* 29(1), 1982.
  DOI 10.1145/322290.322292 **[DOI accepted by the resolver; PDF download failed]**
- If the constraint graph has width w under some ordering and strong (w+1)-consistency holds, search
  along that ordering is backtrack-free. Trees have width 1, so directional arc consistency is enough.
- This is the formal reason Ada-style two-pass resolution is polynomial.
- **Applicability to Hylo:** this is a design guide for A2.2 and A2.3. When the overload-interaction
  graph (overload sets connected by shared type variables) of an expression is a tree, which is typical
  for nested calls without shared generic parameters, a leaves-to-root AC pass followed by a root-down
  selection needs no backtracking. `solve(overload:)` could detect this case: when every component is
  tree-shaped, skip forking.

### A3.3 Dechter and Pearl: tree clustering and tree decomposition
- Dechter, R., Pearl, J. "Tree clustering for constraint networks." *AI* 38(3), 1989.
  DOI 10.1016/0004-3702(89)90037-4 **[DOI from memory]**
- Dechter, R. *Constraint Processing.* Morgan Kaufmann, 2003.
- A CSP whose graph has treewidth w can be solved in O(n d^(w+1)), using a tree decomposition and
  dynamic programming over the bags. Cycle-cutset conditioning is the alternative.
- **Applicability to Hylo:** this is theoretical guidance more than an implementation plan. For
  expressions where operators share a generic type parameter (for example chains of `+` over one
  `T: Numeric`), the interaction graph has small width. Conditioning on the cut-set variable (branching
  on the shared type variable's binding first, then solving the remaining tree with AC) is cheaper than
  branching on every operator. In practice, branching on the most-constrained disjunction (MRV, A2.3)
  approximates this ordering. Not recommended as a first step.

---

## B1. Scope graphs

### B1.1 Néron, Tolmach, Visser, Wachsmuth. "A Theory of Name Resolution." ESOP 2015
- DOI 10.1007/978-3-662-46669-8_9. Local PDF: `/home/hylo/hylo-tc/research/papers/esop15.pdf`
  (markdown: `papers/md/esop15.md`) **[verified]**
- Name resolution has two stages. First, a language-independent *scope graph* is built: scopes, with
  declarations, references, parent (P) edges and import (I) edges. Second, *resolution* finds paths
  from a reference to a declaration.
- Visibility is captured by well-formed paths (a regular expression over edge labels). Shadowing is
  captured by a *specificity* order on paths (for example local before parent before import).
- This is a uniform model for lexical scoping, modules and imports, with a declarative semantics and a
  resolution algorithm.
- **Applicability to Hylo:** Hylo's lookup is already a scope-graph walk with a fixed label order.
  `lookup(_:unqualifiedIn:containedIn:)` follows P edges via `program.scopes(from:)`. Then come the
  "sibling file" edges (the `sourceFileIdentities` loop), then I edges (`imports(of:)`). Shadowing is
  `append(_:)`'s "stop unless all overloadable" rule. Making this graph explicit, with a
  `ScopeIdentity` to edge-list map, would let lookup results be memoized per (scope, name). See B1.4
  and B2.

### B1.2 van Antwerpen, Bach Poulsen, Rouvoet, Visser. "Scopes as Types." OOPSLA 2018
- DOI 10.1145/3276484 **[DOI from memory; not downloaded]**
- Introduces Statix. Scope graphs model types too: a record or class type *is* its scope, and member
  lookup is a query in that scope.
- Queries are parameterized by a path well-formedness regex, a label order and a data predicate.
- **Applicability to Hylo:** the conceptual match is `declarations(nativeMembersOf:)`. Treating a
  nominal type's scope as its "type scope", with extension scopes attached by "extends" edges, unifies
  `resolve(_:nativeMemberOf:)`, `resolve(_:memberInExtensionOf:)` and `resolve(_:inheritedMemberOf:)`
  as three edge labels of one query. That structure is the basis for B2.3.

### B1.3 Rouvoet, van Antwerpen, Bach Poulsen, Krebbers, Visser. "Knowing When to Ask." OOPSLA 2020
- DOI 10.1145/3428248. Local PDF (extended): `/home/hylo/hylo-tc/research/papers/RouvoetAPKV20-ext.pdf`
  **[verified]**
- Type checkers interleave building binding information with querying it. A query answered in a
  *partial* scope graph is stable iff the complete graph has **no critical edges** for that query. A
  critical edge is a later-added edge that would create a new reaching path.
- That condition cannot be checked directly, so the paper uses a sufficient, checkable approximation:
  *weakly critical edges*, where a scope stays "open" for a label until the extensions that could add
  such edges are done.
- Using this, the Statix solver delays unstable queries automatically and is sound by construction.
- **Applicability to Hylo:** Hylo sidesteps the problem because `Scoper` builds the whole scope
  structure before `Typer` runs. But type-dependent lookups, meaning `extensions(visibleFrom:)` plus
  `applies`, and `summon` over givens, depend on *types* that are still being inferred. The critical-edge
  idea justifies Hylo's existing practice of not memoizing `applies` and `canDeriveCoercion` results
  while `hasImplicitOnStack()` is true or the key has variables. It is also the correctness criterion
  for widening those caches: a memo is safe iff no future inference step can add a "critical" extension
  or given. It is also the safety criterion needed for parallel body checking (A3.1).

### B1.4 van Antwerpen, Visser. "Scope States: Guarding Safety of Name Resolution in Parallel Type Checkers." ECOOP 2021
- DOI 10.4230/LIPIcs.ECOOP.2021.1. Local PDF:
  `/home/hylo/hylo-tc/research/papers/[2021] - Scope States_ Guarding Safety of Name Resolution in Parallel Type Checkers.pdf`
  **[verified]**
- Compilation units form a hierarchy. Each scope carries a *scope state* (open, then closed per edge
  label, with *sharing* for scopes that several units can extend). A query proceeds only when the
  relevant scope states are closed.
- Implemented with actors in Java, with fine-grained deadlock detection to break cycles of waiting
  units.
- Parallel Statix gained up to 5.0x on 8 cores on real code bases (abstract) and about 3x on 6 cores in
  another setup.
- **Applicability to Hylo:** this is the blueprint if Hylo parallelizes `Typer` across files or
  declarations (A3.1). The scope structure is already final after `Scoper`, so only the type-level
  "edges" need states: extensions applying to a type, conformances and givens. Concretely, a per-module
  "extensions and conformances are collected" barrier lets `extensions(visibleAtTopLevelOf:)` and
  `summon` run concurrently without locks. Effort is medium to high.

### B1.5 Zwaan, van Antwerpen, Visser. "Incremental Type-Checking for Free." OOPSLA 2022
- DOI 10.1145/3563303. Local PDF (extended): `/home/hylo/hylo-tc/research/papers/oopsla22-extended.pdf`
  **[verified]**
- Incrementality is derived from the scope-graph query log. Each unit records the queries it issued
  that *crossed into other units' scopes*. After an edit, **query confirmation** recomputes only those
  queries against an *environment diff* of the scope graph. A unit whose queries all confirm is
  "released" and its previous result is reused.
- Only queries with non-local path targets need confirmation, which keeps the log small.
- Reported speedups: up to 147x on synthetic benchmarks and up to 21x on real projects.
- **Applicability to Hylo:** this applies to a future incremental or IDE mode. `Typer.Memos` is
  already saved per module (`program.typingCache[m]`). Recording per declaration which cross-file
  (name, scope) queries `lookup(_:unqualifiedIn:)` and `resolve(_:memberOf:...)` answered, and the
  answers, would let an edited module re-check only the declarations whose recorded answers changed.
  This is low priority for batch compile speed.

### B1.6 Zwaan. "Specializing Scope Graph Resolution Queries." SLE 2022
- DOI 10.1145/3567512.3567523 **[DOI from memory]**; arXiv 2210.06121. Local PDF:
  `/home/hylo/hylo-tc/research/papers/[2022] - Specializing Scope Graph Resolution Queries_ Extended Edition.pdf`
  **[verified]**
- Profiling Commons IO showed that "almost 50% of the total query resolution time is spent on
  computing derivatives and checking label orders". These computations are repeated at every traversed
  scope, quadratic in the number of labels.
- Partial evaluation of a query's (regex, label order) pair yields a small state machine with
  `resolve`, `subenv`, `merge` and `shadow` operations. Query resolution became up to 7.7x faster on
  average, and whole Statix checking 38-48% faster on Java projects.
- **Applicability to Hylo:** Hylo's policy is already hand-specialized code, not an interpreted query,
  so the direct gain is nil. The transferable lesson is to **hoist per-query invariant work out of the
  per-scope loop**. In `lookup(_:unqualifiedIn:)`, `refineLookupResults` and the
  `ds.allSatisfy(program.isOverloadable)` test in `append` run at every scope on the chain. In
  `resolve(_:declaredIn:applyingTo:...)`, the per-extension `applies` call is the analogous hot spot
  (B2.3).

### B1.7 Zwaan, van Antwerpen. "Scope Graphs: The Story so Far." EVCS 2023
- DOI 10.4230/OASIcs.EVCS.2023.32. Local PDF: `/home/hylo/hylo-tc/research/papers/OASIcs.EVCS.2023.32.pdf`
  **[verified]**
- A survey covering NaBL to NaBL2 to Statix, editor services, refactorings and incrementality.
- It names open problems: resolution works "on single references or queries. This inhibits caching,
  resulting in poor performance, as many parts of the graph are traversed multiple times". It also
  says Statix checkers are "still an order of magnitude slower than hand-written ones".
- **Applicability to Hylo:** this confirms that the main remaining name-resolution win is
  **cross-query sharing**: memoizing (scope, name) results and indexing extensions, not a smarter
  single-query algorithm. See B2.

### B1.8 Zwaan, Bach Poulsen. "Defining Name Accessibility using Scope Graphs." ECOOP 2024
- DOI 10.4230/LIPIcs.ECOOP.2024.47; arXiv 2407.09320 **[DOI verified via search; not downloaded]**
- Accessibility (public, private, protected, internal) is modelled as a predicate on resolution
  *paths*, and checked against the C#, Java and Rust compilers.
- **Applicability to Hylo:** this matters when Hylo adds access modifiers to `lookup` and `resolve`.
  Evaluate accessibility as a path predicate during the walk, which prunes early, instead of
  post-filtering candidate lists. The performance effect is minor.

### B1.9 Creager, van Antwerpen. "Stack graphs: Name resolution at scale." EVCS 2023
- arXiv 2211.01224; DOI 10.4230/OASIcs.EVCS.2023.8 **[DOI unverified]**. Local PDF:
  `/home/hylo/hylo-tc/research/papers/[2022] - Stack graphs_ Name resolution at scale.pdf`
  **[verified]**
- Scope graphs are extended with push and pop symbol stacks, so that member access through types is
  graph reachability. Each file's subgraph is built **in isolation** (file-incremental). *Partial
  paths* are precomputed per file and stitched together at query time. Results are keyed by the git
  blob ID.
- Used at GitHub scale for code navigation.
- **Applicability to Hylo:** a per-file "exports summary". For each source file, precompute the
  identifier to top-level declarations table once. `cache.moduleToIdentifierToDeclaration` does this
  per module for imported modules, but **not** for the sibling files of the current module, which
  `lookup(_:unqualifiedIn:)` re-scans file by file. A per-module merged table would make that loop one
  hash probe.

### B1.10 de Groot, A. "Memoising Scope Graph Query Resolution." MSc thesis, TU Delft, 2025
- https://repository.tudelft.nl/record/uuid:7c5ea32b-d4de-4c69-a5be-c866d6250547 **[existence and
  abstract verified]**
- Memoizes data seen while traversing a scope graph across queries. The abstract notes a large
  increase in memory use.
- **Applicability to Hylo:** this is direct support for memoizing (scope, name) lookups (B2.2). Keep
  memory bounded by caching only at the scope where resolution actually *terminated*, or only for scopes
  that declare nothing (see B2.2).

---

## B2. Demand-driven compilation, memoization and indexes

### B2.1 Mokhov, Mitchell, Peyton Jones. "Build Systems à la Carte." ICFP 2018 (and JFP 2020)
- DOI 10.1145/3236774 (JFP: 10.1017/S0956796820000088 **[JFP DOI from memory]**). Local PDF (MSR
  version): `/home/hylo/hylo-tc/research/papers/build-systems.pdf` **[verified]**
- A build system factors into a *scheduler* (topological, restarting or suspending) and a *rebuilder*
  (dirty bit, verifying traces, constructive traces or deep constructive traces).
- *Early cutoff*: if a recomputed task's value is unchanged, its dependents are not rebuilt.
- A query-based compiler is a build system with dynamic dependencies and a suspending scheduler. That
  is how Hylo's `declaredType` and `check` already behave.
- **Applicability to Hylo:** this gives the vocabulary for `Typer.Memos`. Today Hylo uses a suspending
  scheduler (recursive demand) with no rebuilder, since caches are never invalidated within a run. For
  incremental mode, verifying traces (record each memo entry's dependencies plus a hash) and early
  cutoff on `declaredType(of:)` results would make signature-preserving edits cheap.

### B2.2 Salsa / rust-analyzer red-green incremental computation and durability
- rustc dev guide, "Incremental compilation in detail" (red-green algorithm).
  https://rustc-dev-guide.rust-lang.org/queries/incremental-compilation-in-detail.html
  **[URL from memory]**
- Matklad et al., "Durable Incrementality", rust-analyzer blog, 24 Jul 2023.
  https://rust-analyzer.github.io/blog/2023/07/24/durable-incrementality.html **[verified]**
- Hammer, M. et al. "Adapton: Composable, demand-driven incremental computation." PLDI 2014.
  DOI 10.1145/2594291.2594324 **[DOI from memory]**
- Queries are memoized with their dependency edges. On a change, nodes are marked green (verified
  unchanged) or red. Durability tiers (for example the standard library as "high durability") let whole
  subgraphs skip revalidation.
- Adapton gives demand-driven change propagation over a dependency graph, with lazy "dirtying".
- **Applicability to Hylo:**
  (a) **Memoize `lookup(_:unqualifiedIn:)` per (scope, Name)**. The scope tables are immutable after
  `Scoper`, so within a `Typer` run the result is a pure function of (scope, name) and needs no
  invalidation. A cheaper variant, avoiding a cache per block scope: memoize at the nearest scope on the
  chain that is a declaration scope, or memoize only the module-level tail (sibling files plus imports)
  per identifier. That tail is the expensive part, because it is re-scanned for every name not found
  locally.
  (b) Durability maps onto the existing per-module `typingCache`. Caches for the standard library and
  imported modules are high-durability and should be kept across `Typer` instances. Hylo already does
  this (`program.typingCache[m]`).

### B2.3 Inverted index for member lookup through extensions (type head to extensions, name to extensions)
- Sources: Swift's per-nominal `MemberLookupTable` and lazy extension member loading (Swift compiler,
  `NameLookup.cpp` **[from memory]**); rustc `trait_impls_of` and `fast_reject::SimplifiedType` buckets
  (A2.6 **[from memory]**); Scopes as Types (B1.2) for the "extension scope attached to type scope"
  view.
- The idea: precompute `[identifier: [ExtensionDeclaration.ID]]`, the extensions that declare a member
  with that identifier, and/or `[TypeHead: [ExtensionDeclaration.ID]]`, keyed by the extendee's
  nominal head. Generic or blanket extensions go into a separate "matches anything" bucket.
- Lookup then intersects the two indexes and runs the expensive match only on the survivors.
- **Applicability to Hylo:** `resolve(_:declaredIn:applyingTo:in:statically:)` currently calls
  `applies(e, to: q, in: scopeOfUse)` **for every visible extension and only then** looks up
  `declarations(lexicallyIn: e)[n.identifier]`.
  - Step 1 (trivial): check `declarations(lexicallyIn: .init(node: e))[n.identifier]` first, and call
    `applies` only when it is non-empty. The cost of `applies` (implicit resolution via `formThread` and
    `takeSummonResults`) then scales with the number of extensions that declare `n`, not with all
    extensions.
  - Step 2: in `extensions(visibleFrom:)`, store, next to the array, a per-scope (or per-file plus a
    local overlay) `[String: [ExtensionDeclaration.ID]]` built with `extendLookupTable`-style code.
    Arrays are currently re-concatenated per scope, so an overlay of "local extensions plus parent
    pointer" also avoids the O(#extensions) copy per nested scope.
  - Step 3: key by `program.types.head(extendeeType(e))` so that `Array` lookups skip `String`
    extensions without matching.
  - The same name-first idea already exists for traits (`lookup(_:memberOfTraitVisibleFrom:)`), so this
    makes the extension path consistent with it.

---

## Ranked top-5 for Hylo (expected payoff / effort)

1. **Name-first, then head-indexed extension lookup** (B2.3). Function:
   `Typer.resolve(_:declaredIn:applyingTo:in:statically:)`, and `extensions(visibleFrom:)` for the
   index. Effort: a few lines for step 1, about a day for the indexes. Payoff: removes most `applies`
   calls, each an implicit-resolution match, on every member reference and every `MemberConstraint`
   solved inside overload forks. Validate by counting `applies` calls on the standard library.
2. **Propagate before branching, then forward-check and choose by MRV** (A1.3, A2.3, A2.2). Function:
   `Solver.solution(betterThanOrEqualTo:using:)` and `solve(overload:)`. Postpone
   `OverloadConstraint` until `fresh` is empty, filter candidates by `unifiable(k.type, choice.type)`,
   bind singletons without forking, and branch on the smallest domain. Optionally extend
   `Typer.filterInPlace` to argument arity, type heads and `expectedType`. Effort: low to medium.
   Payoff: high. It avoids re-solving deterministic goals in each of the k forks and kills dead
   candidates without a fork. This is the core of Swift's 6.3 and 6.4 gains.
3. **Connected-component decomposition before branching** (A1.1, A1.2, A3.2). Function: a new
   `Solver.components()` used by `solve(overload:)`, plus a solution merge. Effort: medium. It needs
   variable-to-goal adjacency, which also enables item 5. Payoff: turns a product of independent
   overload sets into a sum. That is large for operator-heavy expressions, for example `a + b == c + d`
   with overloaded `+` and `==` but no shared variables.
4. **Dominance and ordering in `solve(overload:)`.** Sort `k.candidates` by `program.isPreferred`
   (and exact-match favoring, A1.4). Once a candidate yields a zero-error solution, skip every
   remaining candidate that it strictly beats under `isPreferred`, because it could never be the
   `least`. Effort: low. Payoff: medium. It removes the "explore everything" tail in the common
   unambiguous case. Caveat: it needs a careful argument that `isPreferred` is transitive and that
   skipping never hides an ambiguity diagnostic **[the soundness argument is my own and unverified]**.
5. **Constraint-graph watch lists, path-compressed union-find, then a trail** (A1.1, A1.5, A1.6).
   Functions: `Solver.refresh()`, re-reifying only the goals that mention the bound variable;
   `SubstitutionTable.assign` and `subscript`, with path compression and union by rank; later, replace
   `Solver.init(forking:)` with an undo trail. Effort: medium (trail: medium to high). Payoff: removes
   the O(|stale|) re-reification per assignment and the copying per fork. These are constant-factor and
   polynomial wins that grow with expression size.

Honorable mentions:
- Memoize the per-identifier module tail (sibling files plus imports) of `lookup(_:unqualifiedIn:)`
  (B2.2a, B1.9). Low effort, low to medium payoff.
- Parallel body checking guarded by scope-state-style barriers (A3.1, B1.4). High effort, high payoff on
  multi-core.
- Query-confirmation incrementality for an IDE mode (B1.5, B2.1).

## Download log
Downloaded (9): esop15, RouvoetAPKV20-ext, Scope States (ECOOP'21), Specializing Scope Graph
Resolution Queries, Stack graphs, oopsla22-extended (Incremental Type-Checking for Free), Scope Graphs:
The Story so Far, Build Systems à la Carte, Bidirectional Typing.
Failed: Baker 1982 (404), Freuder 1982 (403), Scopes as Types (not attempted). Some other PDFs in
`papers/` (COCHIS, Tabled Typeclass Resolution, etc.) were not downloaded by this study.
