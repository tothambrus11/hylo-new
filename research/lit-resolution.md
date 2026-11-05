# Literature study: fail-fast pre-checks and faster search for Hylo implicit resolution

Scope: algorithms that (a) cheaply and soundly prove that implicit resolution (`summon`) will **fail**,
and (b) speed up the search itself. Context: `/home/hylo/hylo-tc/intro.md`,
`hylo-new/Docs/State-of-Generics.md` ("Implicit resolution"), and
`hylo-new/Sources/FrontEnd/Typer/Typer.swift` lines ~3440-3995.

Legend: **[verified]** means I checked the bibliographic data (Crossref, arXiv or the publisher)
and read the relevant part of the paper. **[bib verified]** means I checked the citation but did not
read the full text, so the summary comes from abstracts, secondary sources and my own knowledge.
**[unverified]** means the claim comes from memory and I could not confirm it here.
All local PDFs are in `/home/hylo/hylo-tc/research/papers/`, with Markdown conversions in `papers/md/`.

---

## 0. What the Hylo engine actually computes (needed for every soundness argument below)

I read the code (Typer.swift 3440-3995) to pin down the semantics that any pre-check or speed-up has to respect:

* **Rules.** Each `Given` is a Horn clause `∀ᾱ. P1 ∧ … ∧ Pn ⇒ H`, opened in `formThread`
  (fresh variables for `UniversalType`, one assumed given per `Implication` premise).
  The candidates for **every** subgoal are taken from three places (`summon(_:in:where:then:penalties:)`, l. 3614):
  1. all pending assumed givens of the thread (`environment.givens`, one penalty group each),
  2. all givens from all visible scope groups (`givens(visibleFrom:)`), not just the nearest scope,
  3. three built-in coercion givens (reflexivity, symmetry, transitivity).
  Nothing is indexed: every candidate is turned into a thread and then unified in `match`.
* **Cost.** `takeSummonResults` (l. 3791) runs BFS in lock-step. Each `match` call is one step, and a thread that
  finishes at BFS level *d* used *d* steps. So the primary cost is the **number of match steps**,
  i.e. the number of rule applications and coercion insertions in the term. Within the first level that has any
  result, `minimalElements(by: penalties)` breaks ties by **penalties**, which add up over the derivation
  (`penalties + grouping.offset`). The effective order is therefore lexicographic `(steps, Σ penalty)`.
  Several minimal results mean ambiguity (`Solver.swift:242`, `Typer.swift:1016`).
* **Sharing.** Pending sibling and ancestor premises are candidates for later subgoals (item 1 above).
  As a result the step count can be **smaller than the tree size** of the unfolded proof term: a subgoal equal to a
  pending premise costs one step. This matters for any "min size > 10 ⇒ fail" argument (see §2).
* **No tabling.** Only top-level results for closed goals with nothing on the stack are memoized
  (`cache.scopeToSummoned`, l. 3599). Subgoals get no memo and no loop check. With `g: ∀T. P T ⇒ P T` the
  thread for `P Bool` reproduces itself at every level until `maxImplicitDepth = 10` (l. 24).
* **Matching modulo coercions.** `match` (l. 3699) can succeed through derived type equalities
  (`canDeriveCoercions`, l. 3958). That function is already a small fail-fast pre-check for equalities.
  Any new pre-check that uses plain syntactic unification is **unsound** if coercions are possible.

**Key observation for fail-fast.** The engine only ever returns real derivations. So *any* sound proof that
no Horn derivation exists (over a **superset** of the rules) implies failure, whatever selection criterion is used.
The smallest-term semantics only matters for (i) pruning the search and (ii) the depth-limit argument.

---

## 1. Ground case: linear-time Horn / AND-OR reachability

### 1.1 Dowling & Gallier 1984: linear-time Horn-SAT [bib verified]
W. F. Dowling, J. H. Gallier. *Linear-time algorithms for testing the satisfiability of propositional Horn formulae.*
J. Logic Programming 1(3):267-284, 1984. DOI [10.1016/0743-1066(84)90014-1](https://doi.org/10.1016/0743-1066(84)90014-1). Not downloaded.
* Horn-SAT and propositional Horn entailment run in O(N), where N is the total number of literal occurrences.
* Bottom-up version: each clause keeps a counter of unsatisfied premises, and each atom keeps a list of the clauses
  where it occurs. Proving an atom decrements counters, and a counter reaching 0 fires the head. Every edge is
  touched at most once. The paper also gives a top-down, goal-directed variant.
* On intro.md's bipartite graph (R = rules, T = types) this is exactly B-reachability: a type is entailable
  iff it is reached from the premise-free rules, where a rule fires only when **all** of its predecessors are reached.
* **Applicability to Hylo:** this is the core of any ground pre-check. Add a
  `func certainlyUnderivable(_ t: AnyTypeIdentity, in s: ScopeIdentity) -> Bool`, called at the top of
  `summon(_:in:)` (before l. 3594) and memoized per scope like `scopeToPotentialCoercions`. It needs
  per-scope precomputation: the clause list of `givens(visibleFrom:)` together with environment and built-in
  givens, plus a premise→clause occurrence index. It is exact (iff) once rules are ground. Soundness depends
  only on using a superset of the candidates; ignoring `notOnStack` filtering is fine. Non-unique or duplicate
  givens don't affect derivability.

### 1.2 Gallo, Longo, Pallottino, Nguyen 1993: directed hypergraphs [bib verified]
G. Gallo, G. Longo, S. Pallottino, S. Nguyen. *Directed hypergraphs and applications.*
Discrete Applied Mathematics 42(2-3):177-201, 1993. DOI [10.1016/0166-218X(93)90045-P](https://doi.org/10.1016/0166-218X(93)90045-P). Not downloaded.
* Defines B-arcs (many tails, one head), B-connectivity and B-hyperpaths. The B-visit procedure is the linear
  counter algorithm from 1.1, phrased on hypergraphs.
* Shortest hyperpaths under "value functions": additive (sum of tail distances plus arc weight) and bottleneck
  (max). Uses Dijkstra-like SBT procedures with non-negative weights. Applications include Horn satisfiability
  and AND-OR graphs.
* **Applicability to Hylo:** this is the right formal vocabulary for intro.md. Givens are B-arcs and goal types
  are nodes. "Smallest proof term" is a shortest B-hyperpath under the **additive** measure, and "derivation
  height" is the **max** measure (used in §2). Either can be computed on the same per-scope hypergraph as 1.1.

### 1.3 Liu & Smolka 1998: local (goal-directed) linear-time fixpoints [bib verified]
X. Liu, S. A. Smolka. *Simple linear-time algorithms for minimal fixed points.* ICALP 1998, LNCS 1443:53-66.
DOI [10.1007/BFb0055040](https://doi.org/10.1007/BFb0055040). Not downloaded.
* Global and **local** algorithms for least fixpoints on dependency graphs (hypergraphs), both linear in the
  graph size. The local algorithm only explores the part reachable from the query.
* Gives a linear-time **local** algorithm for HORNSAT.
* **Applicability to Hylo:** the hypergraph induced by universally quantified givens is infinite, so it can't be
  built up front. Instead it is unfolded on demand from the goal. Goal-directed instantiation (unify the goal
  with a given's head, then instantiate its premises) is exactly the "propagate X = Int downward" idea in
  intro.md. Liu–Smolka is the algorithm that keeps this linear in the explored part. For `Q Bool` it explores
  `Q Bool` (rule f@Bool) → `P Bool` (rule g@Bool, a self-loop); `x: P Int` doesn't unify. The least fixpoint is
  empty, so the answer is "fail" after visiting 2 nodes and 2 hyperarcs instead of 10 BFS levels.

### 1.4 Ausiello, Italiano, Nanni 1998: hypergraph traversal cost measures [bib verified; claims unverified]
G. Ausiello, G. F. Italiano, U. Nanni. *Hypergraph traversal revisited: cost measures and dynamic algorithms.*
MFCS 1998, LNCS 1450. DOI [10.1007/BFb0055754](https://doi.org/10.1007/BFb0055754). Not downloaded.
* Classifies hyperpath cost measures (rank/height, additive tree size, "size" = number of distinct hyperarcs, …)
  and gives dynamic or incremental algorithms for the tractable ones.
* [unverified, from memory] Minimising the number of *distinct* hyperarcs (DAG size, with sharing) is NP-hard.
  The tree-unfolded additive cost and the height (max) cost are polynomial (Knuth/Dijkstra-like).
* **Applicability to Hylo:** because pending premises are shared (§0), Hylo's step count lies between DAG size and
  tree size. The exact Hylo cost is therefore not a simple superior function. Use **height** as a sound lower
  bound (§2.1) and tree size only as a heuristic, unless the spec is changed to define "size" as tree size.

---

## 2. Smallest derivation = lightest hyperpath (and ambiguity)

### 2.1 Knuth 1977: generalization of Dijkstra (the grammar problem) [bib verified, not downloaded]
D. E. Knuth. *A generalization of Dijkstra's algorithm.* Information Processing Letters 6(1):1-5, 1977.
DOI [10.1016/0020-0190(77)90002-3](https://doi.org/10.1016/0020-0190(77)90002-3). scihub-cli found no PDF.
The content below is confirmed through Nederhof 2003 and Felzenszwalb–McAllester 2007, which restate it.
* Each production `A → f(B1..Bk)` has a weight function f that is **superior**: monotone non-decreasing in every
  argument and `f(x1..xk) ≥ max xi`. Examples: `1 + Σ xi` (tree size), `1 + max xi` (height), and
  lexicographic pairs of these.
* A Dijkstra-like priority queue settles nonterminals in increasing order of their minimal derivation weight.
  Once a node is popped its weight is final. Cycles are fine, and minimal derivations are always acyclic.
  Running time is O(M log N), or O(M + W) with a bucket queue when weights are small integers (here ≤ 11).
* **Applicability to Hylo:** on the instantiated hypergraph of 1.3, Knuth computes the exact minimum of
  `(treeSize, Σpenalty)` for every subgoal (lexicographic, superior because size grows strictly). With
  `1 + max` it computes the **minimum height** h*(G). **Sound depth fail-fast:** the steps of every Hylo thread
  are ≥ h*(G). If you unfold the shared references, each root-to-leaf path visits distinct match steps (a
  pending premise hangs off an ancestor, off the path). So `h*(G) > maxImplicitDepth` ⇒ `takeSummonResults`
  returns `[]`. The tree-size minimum is **not** a sound lower bound because of sharing (§0). Plugging Knuth into
  the search itself would replace the BFS in `takeSummonResults`. Caveats: (i) closed subgoals only, since open
  subgoals thread substitutions between siblings (see 4.1 for answer tables); (ii) to keep the exact current
  semantics, the sharing of pending premises must be modeled or else respecified; (iii) penalties depend on the
  scope of use, so the tables are per scope.

### 2.2 Nederhof 2003: weighted deductive parsing and Knuth's algorithm [verified]
M.-J. Nederhof. *Weighted deductive parsing and Knuth's algorithm.* Computational Linguistics 29(1):135-143, 2003.
DOI [10.1162/089120103321337467](https://doi.org/10.1162/089120103321337467).
Local: `papers/nederhof-2003-weighted-deductive-parsing-knuth.pdf`.
* Separates the *weighted deduction system* (items and inference rules with weight functions) from the
  *algorithm* (Knuth's agenda). The algorithm is generic over the deduction system.
* Correctness needs only superior weight functions. Items get final weights in increasing order, and the search
  stops as soon as the goal is popped. Only items with weight ≤ the goal's weight are processed, whereas Viterbi
  processes all derivable items.
* Compares with Viterbi (needs an a-priori topological order, no cycles). The cost is one log factor for the
  priority queue.
* **Applicability to Hylo:** this is the template. Hylo's resolution rules (§0) form the deduction system and
  `takeSummonResults` becomes a Knuth agenda keyed by `(steps, penalties)`. "Stop when the goal is popped" plus
  "all items at the goal's weight" reproduces BFS's "first non-empty level, minimal penalties" exactly when there
  is no sharing. Expected effect: exponentially many threads (diamonds, cycles) become O(#distinct subgoals ×
  #matching givens).

### 2.3 Felzenszwalb & McAllester 2007: generalized A* (A*LD, HA*LD) [verified]
P. F. Felzenszwalb, D. McAllester. *The Generalized A\* Architecture.* JAIR 29:153-190, 2007.
DOI [10.1613/jair.2187](https://doi.org/10.1613/jair.2187); arXiv:1110.2216.
Local: `papers/[2011] - The Generalized A_ Architecture.pdf`.
* The lightest derivation problem is solved by KLD (Knuth) in O(M log N), and KLD only expands statements with
  d(v) ≤ w\*. A*LD adds a heuristic h (weight of the lightest **context**, i.e. "derivation of the goal with a
  hole") and only expands statements with d(v) + h(v) ≤ w\*.
* **Abstractions give admissible and monotone heuristics.** A map `abs: Σ → Σ'` such that every concrete rule
  `A1..An →v C` has an abstract rule `abs(A1)..abs(An) →v' abs(C)` with v' ≤ v. Then
  ℓ(abs(C)) ≤ ℓ(C) (§5.1 of the paper).
* HA*LD runs a hierarchy of abstractions with a single queue and expands at most 2K statements.
* These are bottom-up (forward chaining), unlike AO\*, which is top-down and needs acyclic rules.
* **Applicability to Hylo:** this is the cleanest theory linking the pre-check and the search. Any homomorphic
  abstraction of types (head-constructor key, depth-k truncation, §3) yields a **lower bound**, and a lower bound
  serves three purposes. (1) Emptiness in the abstraction ⇒ fail (pre-check). (2) Abstract min height > 10 ⇒ fail.
  (3) It is an admissible heuristic to prune threads in `takeSummonResults`: a thread that has taken s steps and
  has pending premises p₁..pₖ needs at least `s + max_i h(p_i)` steps. Drop it when that exceeds the budget. This
  pruning is sound for the current semantics because such threads could never finish within the depth limit.
  Precomputation: the abstract least-weight table per scope.

### 2.4 Goodman 1999: semiring parsing (ambiguity counting) [bib verified; read via thesis]
J. Goodman. *Semiring parsing.* Computational Linguistics 25(4):573-606, 1999. ACL Anthology
[J99-4004](https://aclanthology.org/J99-4004/) (no Crossref DOI found). Local copy: Goodman's PhD thesis
*Parsing Inside-Out* (arXiv cmp-lg/9805007), `papers/goodman-1998-parsing-inside-out-thesis.pdf`, which contains the same framework.
* A single deduction algorithm parameterised by a semiring: Boolean (recognition), counting (number of
  derivations), Viterbi (best weight), Viterbi-n-best, derivation forests. Cycles need ω-continuous semirings
  or special handling of infinite sums.
* **Applicability to Hylo (ambiguity):** pair the Knuth weight with a **count capped at 2** (product of
  min-tropical and counting). When a node is settled, count(v) = Σ over the hyperarcs that reach the minimum of
  Π count(tails), saturating at 2. Then `count(goal) ≥ 2` ⇔ two minimal derivations ⇔ the current "ambiguous"
  outcome. This is well-defined because minimal derivations under a superior cost are acyclic. Caveat: Hylo
  compares results through `SummonResult` equality and `minimalElements`, so syntactically identical witnesses
  reached by different thread orders must be counted once. Count derivations, not threads.

### 2.5 Ramalingam & Reps 1996: incremental grammar problem [bib verified]
G. Ramalingam, T. Reps. *An incremental algorithm for a generalization of the shortest-path problem.*
J. Algorithms 21(2):267-305, 1996. DOI [10.1006/jagm.1996.0046](https://doi.org/10.1006/jagm.1996.0046). Not downloaded.
* Maintains Knuth's superior-function grammar problem under edge insertion and deletion, with cost bounded by
  the size of the "affected" region (‖δ‖ log ‖δ‖).
* **Applicability to Hylo:** nested scopes only **add** givens, so the derivable set grows monotonically. An inner
  scope's table could then be obtained incrementally from its parent's instead of recomputed. Today `summon`
  recomputes from scratch whenever `givens(lexicallyIn:)` is non-empty (l. 3593). Caveat: penalties are
  relative to the scope of use (group offset), so all outer givens' penalties shift when a scope is entered.
  Incrementality is clean for derivability, height and size, but not for penalty tie-breaks.

---

## 3. Universally-quantified rules: regular (tree-automata) over-approximations and failure analysis

Formal reading: a Hylo given `∀ᾱ. P1⟨t1⟩ ∧ … ∧ Pn⟨tn⟩ ⇒ P⟨t⟩` is a definite clause over the Herbrand universe
of types. For a single-parameter trait it is a clause over a **unary** predicate. "Is `Q⟨Bool⟩` derivable?" asks
whether a ground atom is in the least Herbrand model. That is undecidable in general (Horn clauses are
Turing-complete) but decidable for shallow, linear fragments, and any regular over-approximation is a
**sound fail-fast certificate**.

### 3.1 Sato & Tamaki 1984: depth-k abstraction [bib verified]
T. Sato, H. Tamaki. *Enumeration of success patterns in logic programs.* Theoretical Computer Science 34(1-2):227-240, 1984.
DOI [10.1016/0304-3975(84)90119-1](https://doi.org/10.1016/0304-3975(84)90119-1). Not downloaded.
* Approximates the success set by truncating terms at depth k (subterms below depth k become a wildcard).
  The abstract domain is finite, so the fixpoint terminates.
* **Applicability to Hylo:** this is the simplest way to make the goal-directed unfolding of 1.3 finite when
  givens are depth-increasing (e.g. `<T where Array<T> is P> T is P`). Subgoals deeper than k become `P⟨*⟩`,
  which unifies with every head of P. Truncation is a homomorphism into a finite algebra, so the abstract least
  model contains the image of the concrete one (sound), and F&M lower bounds remain valid. k = 2 or 3 separates
  `S<Int>` from `S<Bool>`. Cost is bounded by #traits × #depth-k terms actually reached from the goal.

### 3.2 Heintze & Jaffar 1990: set-based approximation [bib verified]
N. Heintze, J. Jaffar. *A finite presentation theorem for approximating logic programs.* POPL 1990, 197-209.
DOI [10.1145/96709.96729](https://doi.org/10.1145/96709.96729). (The DOI suggested in the brief, `…96734`, is a
different paper, "Parallelism in logic programs"; I checked this on Crossref.) Not downloaded.
* Set-based semantics: each variable ranges independently over a set, ignoring correlations between variables.
  The least model of this approximation is always regular (finitely presentable by tree grammars) and computable.
* **Applicability to Hylo:** this is the bottom-up dual of 3.1. For each trait it computes a regular set (tree
  automaton) of types that might conform. It handles the cases where the goal-directed method stalls: open goals
  `P⟨?x⟩`, and existential premise variables (a given variable that doesn't occur in the head, including the
  middle type of built-in `transitivity`). Cost: worst-case exponential, but small in practice for trait-sized
  programs [unverified]. Recompute per scope (or incrementally, 2.5).

### 3.3 Frühwirth, Shapiro, Vardi, Yardeni 1991: logic programs as types [verified, preliminary version]
T. Frühwirth, E. Shapiro, M. Y. Vardi, E. Yardeni. *Logic programs as types for logic programs.* LICS 1991, 300-309.
DOI [10.1109/LICS.1991.151654](https://doi.org/10.1109/LICS.1991.151654). Local (preliminary report from the
author's site; the Markdown conversion is garbled but readable): `papers/lics91p.pdf`.
* Approximates a program P by a "type program" PT of unary predicates. Success-set membership of PT is
  type(p) for P, and PT over-approximates P (theorem in their §3).
* Defines **regular unary-predicate programs**: heads contain no repeated variables, and each body term is a
  subterm of the head or disjoint from it. These programs correspond to alternating tree automata. Membership
  in the success set is **EXPTIME-complete**, with the lower bound coming from tree-automata intersection.
  Uniform programs can be transformed into regular ones.
* **Applicability to Hylo:** most Hylo givens are already "regular". Take `<T where T is P> S<T> is P`: linear
  shallow head, and the premise is on a subterm. For such givens the goal-directed instantiation of 1.3
  generates only subgoals on **subterms of the goal**. The instantiated hypergraph then has at most
  #traits × #subterms(goal) nodes and the ground Horn-SAT check is exact and linear. The EXPTIME hardness only
  appears with premises on variables **disjoint from the head** (existentials such as `<T, U where U is Q,
  T == U.A>`), and those need intersections. Practical rule: run exact local Horn-SAT (1.3) while subgoals are
  subterms, and use wildcards (3.1/3.2) beyond that. Multi-parameter traits are n-ary predicates; approximate
  them by their Cartesian projection (sound).

### 3.4 Nielson, Nielson, Seidl 2002 (H1) and Goubault-Larrecq 2005 (MSL) [bib verified]
F. Nielson, H. R. Nielson, H. Seidl. *Normalizable Horn clauses, strongly recognizable relations, and Spi.*
SAS 2002, LNCS 2477:20-35. DOI [10.1007/3-540-45789-5_5](https://doi.org/10.1007/3-540-45789-5_5).
J. Goubault-Larrecq. *Deciding H1 by resolution.* IPL 95(3), 2005. DOI [10.1016/j.ipl.2005.04.007](https://doi.org/10.1016/j.ipl.2005.04.007).
Related: A. Teucke, C. Weidenbach, *Decidability of the monadic shallow linear first-order fragment with straight
dismatching constraints*, CADE 2017, DOI [10.1007/978-3-319-63046-5_13](https://doi.org/10.1007/978-3-319-63046-5_13);
and SPASS-AR (JAR 2020, DOI [10.1007/s10817-020-09546-z](https://doi.org/10.1007/s10817-020-09546-z)). None downloaded.
* H1, equivalent to monadic shallow linear (MSL) Horn clauses: the least model is computable and regular
  (normalization is exponential in general). The H3 sub-fragment is **cubic**.
* Teucke–Weidenbach approximate arbitrary first-order clauses **into** MSL (linearize repeated variables,
  shallow-ify deep terms with fresh predicates, project n-ary to monadic) and refine on spurious
  counterexamples (approximation-refinement, SPASS-AR).
* **Applicability to Hylo:** this gives a principled "compile givens to an approximation" step. (1) Flatten deep
  heads such as `Array<Optional<T>> is P` with an auxiliary predicate (exact). (2) Linearize non-linear heads
  such as `Pair<T,T> is P` to `Pair<T,U>` (sound over-approximation). (3) Project multi-parameter traits to
  monadic. The result is MSL, so its least model is a tree automaton, computable once per scope. Fail-fast is
  then automaton membership of the goal: O(|goal| × |states|) for a ground goal after determinization, or
  linear with on-the-fly alternation. [Cubic H3 claim: abstract only.]

### 3.5 Gallagher & Puebla 2002: abstract interpretation over NFTAs [verified]
J. P. Gallagher, G. Puebla. *Abstract interpretation over non-deterministic finite tree automata for set-based
analysis of logic programs.* PADL 2002, LNCS 2257:243-261. DOI [10.1007/3-540-45587-6_16](https://doi.org/10.1007/3-540-45587-6_16).
Local: `papers/gallagher-puebla-padl2002.pdf`.
Related: J. P. Gallagher, K. S. Henriksen, *Abstract domains based on regular types*, ICLP 2004,
DOI [10.1007/978-3-540-27775-0_3](https://doi.org/10.1007/978-3-540-27775-0_3) (not downloaded).
* Follows Cousot & Cousot: set-constraint analysis is abstract interpretation over a **finite** domain of tree
  grammars built from the program. Here it is realised with NFTAs whose states are sets of program-derived
  identifiers, with products represented implicitly.
* Has goal-dependent (query-answer / magic) and goal-independent variants. Emptiness of products is
  EXPTIME-complete (their §6.3), which they avoid in practice with lazy product states.
* Gallagher–Henriksen: pre-chosen regular types (e.g. one state per type constructor) give a cheap,
  **deterministic** finite abstract domain whose fixpoint is computed by ordinary Horn-SAT over "abstract atoms".
* **Applicability to Hylo:** the cheap instance is the **head-constructor algebra**. Map every type to its
  outermost nominal constructor (`Int`, `Bool`, `S`, `Array`, …) and keep `⊤` for type variables and
  projections. The abstract least model `M♯ ⊆ Traits × Ctors` is computed per scope by Dowling–Gallier on
  ground abstract clauses. A given with v variables instantiates over the constructors that occur at those
  positions; usually v ≤ 2. Pre-check: `(P, head(goal)) ∉ M♯` ⇒ fail. On intro.md this proves `Q Bool` fails.
  The same table feeds GHC-style rough-match indexing (§5). Unsound if coercions or type aliases can change a
  head, so compute keys after `dealiased` and merge keys related by equality givens with union-find.

### 3.6 Kafle & Gallagher 2015/2017: tree-automata refinement for Horn clauses [verified]
B. Kafle, J. P. Gallagher. *Tree automata-based refinement with application to Horn clause verification.*
VMCAI 2015, LNCS 8931:209-226. DOI [10.1007/978-3-662-46081-8_12](https://doi.org/10.1007/978-3-662-46081-8_12).
Local: `papers/vmcai_2015_kafle_gallagher.pdf`. Journal version: *Horn clause verification with convex
polyhedral abstraction and tree automata-based refinement*, Computer Languages, Systems & Structures 47:2-18, 2017,
DOI [10.1016/j.cl.2015.11.001](https://doi.org/10.1016/j.cl.2015.11.001).
* The derivations of a Horn clause set are the trees accepted by an FTA whose states are predicates and whose
  transitions are clauses. A spurious abstract counterexample is itself a tree. Determinize, take the
  **difference** to remove it, and re-emit refined clauses (this is the "product/difference" transformation;
  I could not find a paper titled exactly "Horn clause transformation by tree automata products").
* Gallagher's VPT 2016 invited talk (*Finite tree automata in Horn clause transformations*, EPTCS proceedings
  arXiv:1607.01835) surveys this. Related: Kafle–Gallagher–Ganty, *Decomposition by tree dimension*, arXiv:1512.03862.
* **Applicability to Hylo:** this is the CEGAR loop to use if the cheap abstraction (3.5) says "maybe" too often.
  It is probably too heavy to run per `summon`, but could run once per module for goals that hit the timeout
  (as a diagnostic: "this conformance is underivable because …"). The *tree-dimension* idea (bounding the
  non-linearity of derivations) matches Hylo's depth bound [relation unverified].

### 3.7 Kostyukov, Mordvinov, Fedyukovich 2021: RInGen, regular invariants for CHCs over ADTs [verified]
Y. Kostyukov, D. Mordvinov, G. Fedyukovich. *Beyond the elementary representations of program invariants over
algebraic data types.* PLDI 2021, 451-465. DOI [10.1145/3453483.3454055](https://doi.org/10.1145/3453483.3454055); arXiv:2104.04463.
Local: `papers/[2021] - Beyond the Elementary Representations of Program Invariants over Algebraic Data....pdf`.
* Safe inductive invariants of CHCs over ADTs are represented as (tuple) **tree automata** ("regular invariants").
  These are strictly more expressive than first-order (elementary) invariants, and the paper proves the
  first-order ones inadequate using pumping lemmas.
* Inference reduces the CHC system (ADTs become uninterpreted sorts with EUF) to **finite model finding**
  (CVC4 finite-model mode, Vampire, …). A finite model is a deterministic tree automaton (Thm 1), and
  disequalities are handled by a transformation (Thm 5). Competitive with Spacer, Eldarica and VeriMAP-iddt.
* **Applicability to Hylo:** this is exactly "prove `Q Bool` underivable". A **certificate of failure** is a
  finite algebra (states for types) plus an interpretation of traits as state sets in which all givens hold and
  the goal is false. For intro.md the 2-element model `Int↦a, Bool↦b, P={a}, Q={a}` works. A full
  finite-model search is far too expensive for a per-goal pre-check. The engineering takeaway: **fix** a cheap
  algebra (head constructor, or depth-k as in 3.1) and compute its least model, which is polynomial, instead of
  searching for one. Keep RInGen-style search for offline explanation.

### 3.8 Haudebourg, Genet, Jensen 2020: regular language type inference [bib verified]
T. Haudebourg, T. Genet, T. Jensen. *Regular language type inference with term rewriting.* PACMPL 4(ICFP), 2020.
DOI [10.1145/3408994](https://doi.org/10.1145/3408994). Not downloaded.
* Infers regular tree-language abstractions for higher-order functional programs by completing tree automata
  against term rewriting (Timbuk 4), with counterexample-guided refinement.
* **Applicability to Hylo:** this is the most recent tree-automata line that handles **higher-order** programs.
  It is relevant to the "higher-order constraints" open question in intro.md (givens whose premises are
  themselves implications). Low priority; use it as background if Hylo's given premises become higher-order.

### 3.9 Debray, López-García, Hermenegildo 1997: non-failure analysis [verified abstract; the converted body text is garbled]
S. K. Debray, P. López-García, M. Hermenegildo. *Non-failure analysis for logic programs.* ICLP 1997, 48-62, MIT Press.
URL <https://www2.cs.arizona.edu/~debray/Publications/nonfailure.pdf>. Local: `papers/nonfailure.pdf`.
Follow-up: F. Bueno, P. López-García, M. Hermenegildo, *Multivariant non-failure analysis via standard abstract
interpretation*, FLOPS 2004, DOI [10.1007/978-3-540-24754-8_9](https://doi.org/10.1007/978-3-540-24754-8_9).
* Proves calls **cannot fail** with a *covering* test: the clause heads (with tests) cover the call's input
  type. Covering is undecidable in general but decidable for the Herbrand domain, with complexity results
  given in the paper.
* **Applicability to Hylo:** this is the **dual** of what intro.md asks for (it proves non-failure). It is useful
  in two ways. (1) As a "will succeed, skip the pre-check" filter. (2) Its covering test is the right tool for
  *exhaustiveness*-style diagnostics, e.g. "every `T` has a `P` instance". It is not a failure certificate.

### 3.10 Bol, Apt, Klop 1991: loop checking [bib verified]
R. N. Bol, K. R. Apt, J. W. Klop. *An analysis of loop checking mechanisms for logic programs.*
TCS 86(1):35-79, 1991. DOI [10.1016/0304-3975(91)90004-L](https://doi.org/10.1016/0304-3975(91)90004-L). Not downloaded.
* Classifies loop checks (equality, variant, subsumption of the goal or the resolvent) by soundness (no solution
  lost) and completeness (all infinite derivations pruned). Simple *variant* checks on the ancestor chain are sound.
* **Applicability to Hylo (high value, trivial cost):** if a subgoal G occurs as its own **descendant** on the
  current path (same closed type, or the same type up to renaming of open variables), then any derivation using
  the inner G can be shortened by grafting the inner subtree in place of the outer one. So **no minimal
  derivation repeats a goal on a path**. Pruning such threads loses no minimal result under `(steps, penalties)`,
  and ambiguity is preserved too. Implement it by carrying the ancestor goal set in
  `ResolutionThread.Environment`, pushing in `threadContinuation` (l. 3748) and checking in `summon(...where:)`
  (l. 3614). This kills the intro.md divergence (`Q Bool → P Bool → P Bool`) after 2 steps instead of 10 levels.
  Caveat: only *variant* (not subsumption) checks are safe while substitutions thread between siblings. Also
  check that a pending assumption doesn't make the "shortcut" cheaper (it can only make it cheaper, so the
  argument still holds).

---

## 4. Type-class / trait resolution engineering

### 4.1 Selsam, Ullrich, de Moura 2020: tabled typeclass resolution (Lean 4) [verified]
D. Selsam, S. Ullrich, L. de Moura. *Tabled typeclass resolution.* arXiv:2001.04301, 2020.
URL <https://arxiv.org/abs/2001.04301>. Local: `papers/[2020] - Tabled Typeclass Resolution.pdf`.
* SLD resolution re-solves the same subgoals in different branches, which gives exponential time on **diamonds**
  and divergence on **cycles**. Tabling (SLG-style) keeps a **search forest**: one generator node per distinct
  subgoal, and consumer nodes that resume on answers from the table (Fig. 2: generator stack, resume stack, table).
* Subgoal identity is up to α-equivalence. Instead of a discrimination tree they **α-normalize** (replace
  unassigned metavariables by θ₀, θ₁, … and hash). Ground subterms short-circuit using a "has-mvar" bit (§5.4).
* Instances are indexed in a discrimination tree (§5.5). Terminates under the *bounded term-size assumption*.
  Exponential speed-up on diamond benchmarks.
* Returns the **first** solution, by priority and then declaration order (most recent first), **not** the smallest one.
* **Applicability to Hylo:** this is the most directly portable engineering. Replace thread re-creation in
  `summon(...where:then:penalties:)` by a per-`summon(_:in:)` table keyed by the reified subgoal type
  (`program.types.reify(t, applying: environment.substitutions, withVariables: .kept)`, α-normalized; Hylo's
  `hasVariable` flag plays the role of the has-mvar bit). Answers are `(SubstitutionTable, WitnessExpression, cost)`.
  **Semantic caveat:** Lean's "first answer" doesn't preserve "smallest term". Order the resume stack by
  `(steps, penalties)` (Knuth, §2.1), keep all answers of minimal cost to detect ambiguity (§2.4), and handle
  sharing via pending assumptions (§0). Scope: the table is valid only for one `scopeOfUse` and one
  environment of assumed givens.

### 4.2 Rust's next-generation trait solver: search graph, provisional cache, fixpoints [verified docs]
rustc-dev-guide, *The solver: caching* and *Coinduction*:
<https://rustc-dev-guide.rust-lang.org/solve/caching.html>, <https://rustc-dev-guide.rust-lang.org/solve/coinduction.html>;
source `compiler/rustc_next_trait_solver/src/search_graph` (earlier `rustc_trait_selection/src/solve/search_graph.rs`). Not a paper.
* Goals are **canonicalized** (variables renamed) and cached globally. A repeated canonical goal on the stack is
  a cycle. **Inductive** cycles start with `Overflow` (later: error), **coinductive** ones (auto traits, `Sized`,
  WF) with `Yes`. The cycle head is re-evaluated until the provisional result reaches a **fixpoint**.
* Only the **cycle root's** result goes into the global cache. Participants' results depend on which goal was
  the root, so they live only in a provisional cache.
* Hitting the recursion limit is **not fatal**: it returns ambiguity/overflow. Cache entries record the
  remaining depth, because results computed near the limit can differ.
* **Applicability to Hylo:** two lessons. (1) Hylo's per-subgoal tables need the same "cycle-root only" rule:
  results computed while a cycle participant is on the stack must not be cached globally. Hylo already
  approximates this with `hasImplicitOnStack()` (l. 3599). (2) Under a depth limit a cached *failure* is only
  valid for the same or smaller remaining depth. A pre-check result that is depth-independent (Horn
  underivability) is valid at any depth, which is another argument for doing failure detection with a separate
  fixpoint rather than reusing search results. Hylo resolution is inductive (finite proof terms), so cycles get
  the inductive treatment and the loop check of 3.10 suffices.

### 4.3 Swift Requirement Machine (Knuth–Bendix completion) [bib verified; details from search snippets]
S. Pestov. *Compiling Swift Generics.* Swift project documentation, 2023-2025, <https://download.swift.org/docs/assets/generics.pdf>
(LaTeX sources in `swift/docs/Generics`; implementation in `lib/AST/RequirementMachine/` — `KnuthBendix.cpp`, `PropertyMap.cpp`).
Background: Pestov, "Swift type checking is undecidable" (Swift Forums, 2022).
Classic alternative: P. J. Downey, R. Sethi, R. E. Tarjan, *Variations on the common subexpression problem*,
JACM 27(4):758-771, 1980, DOI [10.1145/322217.322228](https://doi.org/10.1145/322217.322228) (congruence closure, O(n log n)).
* A generic signature (conformances, same-type requirements, associated types) is encoded as a **string rewriting
  system**, and Knuth–Bendix completion produces a confluent system. Then "does `T.A.B == U` hold?" and
  "does `T.A` conform to `P`?" are decided by normalizing both sides. Completion may fail to terminate, in which
  case Swift diagnoses after a step limit.
* Separate machines handle queries, minimization and protocol requirement signatures.
* **Applicability to Hylo:** Hylo currently *searches* for type equalities using built-in `symmetry` and
  `transitivity` givens and assumed `EqualityWitness` goals (`summon` l. 3629, `match` l. 3728). Transitivity has
  an existential middle term, which is the worst case for both search and approximation (3.3). Replacing that
  with a per-scope **congruence closure** (ground equalities, Downey–Sethi–Tarjan) or, for parametric/associated
  equalities, completed rewriting à la Requirement Machine, makes `canDeriveCoercions` exact and removes three
  always-applicable candidates from every subgoal. It also removes the main obstacle to sound head-key indexing
  (§5): coercible types end up in the same equivalence class.

### 4.4 Scala 3 implicit divergence check (SIP-31) [docs verified]
Scala 3 reference, *Changes in implicit resolution*:
<https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html>; SIP-31 "By-name implicits"
(M. Sabin). Background: M. Odersky et al., *Simplicitly: foundations and applications of implicit function types*, POPL 2018,
PACMPL 2(POPL), DOI [10.1145/3158130](https://doi.org/10.1145/3158130).
* Divergence check: an open implicit search for type T is abandoned if an enclosing search for the *same
  candidate* had a type with the same **covering set** (set of type constructors) and a smaller or equal
  **complexity** (type size). A fixed covering set and bounded size admit only finitely many types, which
  guarantees termination. Scala 3 treats divergence as an **ordinary failure** (alternatives are still tried)
  and propagates ambiguity to the caller. Siblings with the same declared type count as the same candidate.
  [Exact dominance rule: from secondary sources; SIP-31 text not read.]
* **Applicability to Hylo:** this is a cheaper but **less precise** cousin of 3.10. Pruning "dominating" (not
  identical) subgoals can discard a minimal derivation (the check is a heuristic, not a theorem), so under
  Hylo's smallest-term semantics it is **not** sound as pruning. It is fine as a *diagnostic* ("resolution
  probably diverges via given g") when the depth limit is hit.

### 4.5 GHC: instance termination (Paterson conditions) and instance lookup [docs verified]
GHC User's Guide, *Instance declarations / Instance termination rules*:
<https://ghc.gitlab.haskell.org/ghc/doc/users_guide/exts/instances.html>.
M. Sulzmann, G. J. Duck, S. Peyton Jones, P. J. Stuckey, *Understanding functional dependencies via constraint
handling rules*, JFP 17(1):83-129, 2007, DOI [10.1017/S0956796806006137](https://doi.org/10.1017/S0956796806006137).
* **Paterson conditions.** For each context constraint: (1) no type variable occurs more often than in the head;
  (2) the constraint has fewer constructors plus variables than the head; (3) no type functions. Together these
  guarantee that the size strictly decreases along every resolution path, so resolution terminates.
  `UndecidableInstances` lifts them. GHC commits to a matching head without backtracking.
* **Applicability to Hylo:** a per-given static check, linear in the size of the given's type. Givens that
  satisfy it can never cause divergence. If *every* given visible from a scope satisfies it, the BFS can't
  time out for structural reasons: the derivation height is bounded by the goal size, so fail-fast reduces to
  exhausting the finite tree. Report violating givens as the likely cause when `maxImplicitDepth` is hit.
  No soundness risk, since this is diagnostics only. The intro.md example `g: ∀T. P T ⇒ P T` violates (2).

### 4.6 Bottu, Xie, Marntirosian, Schrijvers 2019: coherence of type class resolution [verified]
G.-J. Bottu, N. Xie, K. Marntirosian, T. Schrijvers. *Coherence of type class resolution.* PACMPL 3(ICFP):91, 2019.
DOI [10.1145/3341695](https://doi.org/10.1145/3341695); arXiv:1907.00844. Local: `papers/[2019] - Coherence of Type Class Resolution.pdf`.
* Elaboration-based resolution is nondeterministic (superclasses, local givens, flexible contexts). The paper
  proves **coherence** (all elaborations are contextually equivalent) using a two-step elaboration through an
  intermediate language and logical relations.
* **Applicability to Hylo:** Hylo deliberately **doesn't** assume coherence. Distinct minimal witnesses count
  as ambiguity. The paper is relevant if Hylo ever wants to **merge** "ambiguous" candidates that are provably
  equal (e.g. the same given reached through two superclass paths). That would shrink the ambiguity set that
  §2.4 counts. No direct change to `summon`.

### 4.7 Schrijvers, Oliveira, Wadler, Marntirosian 2019: COCHIS [verified]
T. Schrijvers, B. C. d. S. Oliveira, P. Wadler, K. Marntirosian. *COCHIS: Stable and coherent implicits.*
JFP 29:e3, 2019. DOI [10.1017/S0956796818000242](https://doi.org/10.1017/S0956796818000242).
Local: `papers/[2019] - COCHIS_ Stable and coherent implicits.pdf`.
Predecessor: B. C. d. S. Oliveira, T. Schrijvers, W. Choi, W. Lee, K. Yi, *The implicit calculus*, PLDI 2012,
DOI [10.1145/2254064.2254070](https://doi.org/10.1145/2254064.2254070).
* Local scoping, overlapping, first-class and higher-order rules, plus **coherence and stability** under type
  substitution. Resolution is **deterministic**: a stack discipline picks the lexically nearest matching rule,
  related to focusing. **Committed choice**: no backtracking after a head matches (§6.2).
* **Termination** (§4.4): every rule `ρ1 ⇒ ρ2` must have ‖head(ρ1)‖ < ‖head(ρ2)‖, and no variable may occur more
  often in ρ1 than in ρ2. This is the Paterson analogue, checked syntactically and stable under substitution.
* **Applicability to Hylo:** this is the closest calculus to Hylo (lexical scopes and higher-order givens), but
  Hylo **backtracks** and minimizes globally, where COCHIS commits. The termination condition applies as is
  (see 4.5). The *stability* property is a warning: Hylo's "smallest term" selection over generic givens may
  pick a different witness after instantiation (e.g. inside vs outside a generic function). That is a semantic
  question, not a performance one [not analysed further].

### 4.8 Bottu, Karachalias, Schrijvers, Oliveira, Wadler 2017: quantified class constraints [bib verified]
G.-J. Bottu, G. Karachalias, T. Schrijvers, B. C. d. S. Oliveira, P. Wadler. *Quantified class constraints.*
Haskell Symposium 2017, 148-161. DOI [10.1145/3122955.3122967](https://doi.org/10.1145/3122955.3122967). Not downloaded.
* Allows `∀a. C a ⇒ D (f a)` in contexts (higher-order givens). Resolution with local quantified givens is
  hereditary Harrop rather than plain Horn. Gives termination conditions for this setting.
* **Applicability to Hylo:** Hylo givens with implication-typed premises are exactly this case. For the
  pre-check, treat an implication-typed premise conservatively as derivable (`⊤`), or add its hypotheses as
  temporary facts (Harrop "augment then prove"). Either way it stays sound. Exact Horn-SAT no longer applies
  to such premises.

---

## 5. Indexing candidate givens by goal head

### 5.1 McCune 1992; Graf 1995; Sekar, Ramakrishnan, Voronkov 2001 [bib verified for the first two]
W. McCune. *Experiments with discrimination-tree indexing and path indexing for term retrieval.* JAR 9(2):147-167, 1992.
DOI [10.1007/BF00245458](https://doi.org/10.1007/BF00245458).
P. Graf. *Substitution tree indexing.* RTA 1995, LNCS 914. DOI [10.1007/3-540-59200-8_52](https://doi.org/10.1007/3-540-59200-8_52).
R. Sekar, I. V. Ramakrishnan, A. Voronkov. *Term indexing.* Handbook of Automated Reasoning, ch. 26, 2001 [bib unverified].
* Discrimination trees are tries over the preorder symbol sequence of a term, with `*` for variables. Retrieval
  of generalizations, instances or unifiable terms is a trie walk that returns a **superset** (imperfect filter),
  and the result is confirmed by real unification. Substitution trees share substitutions and are better for
  large, variable-rich sets.
* **Applicability to Hylo:** a per-scope trie keyed by `[traitName, headTyCon(arg₀), …]`. Variable or alias heads
  go into `*`, and the built-in coercions and `<T> T` heads go into an "always try" bucket. Lookup replaces the
  `for g in grouping.element` loop in `summon(...where:)` (l. 3636), turning a scan of every visible given per
  subgoal into O(key length + #hits). Precompute it alongside `cache.scopeToGivens` / `moduleToGivens`.
  Soundness: it must be an over-approximation of unifiability *modulo coercions*, so it is safe once 4.3 gives
  equivalence classes of keys, or when equality-headed givens are kept in the "always try" bucket.

### 5.2 Lean 4 `DiscrTree` [verified source; behaviour partly from memory]
Lean 4 source: `src/Lean/Meta/DiscrTree/Types.lean`, `src/Lean/Meta/DiscrTree.lean`, `src/Lean/Meta/SynthInstance.lean`;
Lean reference manual §10.3 *Instance synthesis* (<https://lean-lang.org/doc/reference/latest/Type-Classes/Instance-Synthesis/>).
* `Key` = `const name arity | fvar id arity | lit | star | other | arrow | proj …` (verified). Terms are reduced
  at reducible transparency before keying, and instance-implicit or metavariable positions become `star`
  [from memory]. `getUnify` returns candidates that may unify (a superset).
* Instance candidates are ordered by priority, then by declaration order (newest first) (manual, verified).
* **Applicability to Hylo:** it shows that keying must happen *after* the normalizations Hylo's `unifiable`
  performs (Hylo: `dealiased`, `reify`). Any position that normalization could change (aliases, associated-type
  projections) must be `star`. Otherwise the index under-approximates and resolution silently loses candidates,
  which is unsound for both search and pre-check.

### 5.3 GHC `RoughMatchTc` / `RoughMap` [verified source]
GHC source: `GHC/Core/InstEnv.hs` (`is_tcs :: [RoughMatchTc]`, `instanceCantMatch`) and `GHC/Core/RoughMap.hs`
(<https://hackage.haskell.org/package/ghc-9.10.3/src/GHC/Core/RoughMap.hs>).
* Insertion key: per argument, the head after synonym expansion, either `RM_KnownTc name` (generative tycon)
  or `RM_WildCard`. Synonyms and type families are excluded because they can reduce to another head.
* Lookup key: `RML_KnownTc`, `RML_NoKnownTc` (rigid tyvar or stuck family: kept as a *unifier* candidate but not
  a *match*), or `RML_WildCard`. The structure is a trie, and `lookupRM'` returns (matches, lazy unifiers).
  Keys only use Names, so mismatching instances are rejected without loading their interfaces (#12367). The
  trie replaced an O(n) scan [commit note seen in search results].
* **Applicability to Hylo:** this is the minimal viable index, and it matches the head-constructor algebra of 3.5.
  The **same key function** gives the rough-match filter for search (5.1) and the abstract states for the
  fail-fast least model (3.5). Hylo already has the moral equivalent of `RML_NoKnownTc` vs `RML_WildCard` in the
  difference between skolems and unification variables.

---

## 6. Ranked recommendations

Notation: G = number of visible givens (all scopes), K = key length (trait + top-level args), N = number of
distinct (abstract) subgoals reached from the goal, M = number of instantiated hyperarcs among them,
d = `maxImplicitDepth` = 10.

### (a) Fail-fast pre-check (sound: "yes" ⇒ `summon` returns `[]`)

1. **Goal-directed ground Horn-SAT with depth-k wildcards** (1.1 + 1.3 + 3.1 + 3.3). Unfold from the goal,
   instantiate givens by unifying heads (this is intro.md's "propagate X = Int downward"), truncate subgoals at
   depth k to `P⟨*⟩`, and compute the least fixpoint with Dowling–Gallier counters. **Exact** for "regular"
   givens while subgoals stay subterms of the goal. Cost O(N·G·unify + M) without indexing, O(N·hits + M) with
   5.3. N ≤ #traits × #depth-k terms reached. Typically tens of nodes, versus up to (branching)^10 BFS threads.
   Caveats: model coercions (4.3, or bail out when equality or variable-headed givens exist), dealias before
   comparing, treat projections, open variables and implication-typed premises as `⊤`.
2. **Abstract minimum height > d** (2.1 with `1 + max`, 2.3). Same hypergraph, Knuth with a bucket queue,
   O(M + d). Sound despite Hylo's sharing of pending premises (argument in 2.1). It catches goals that are
   derivable in principle but need more than 10 steps, which today are the most expensive failures.
3. **Trait-level emptiness per scope** (intro.md's graph with "variables unify with anything"; 1.1). One
   Horn-SAT per scope over traits only, O(Σ|givens|), cached next to `cache.scopeToGivens`. It is the cheapest
   check and is a prerequisite for 1 (it supplies values for `P⟨*⟩` / existential premises).
4. **Head-constructor least model per scope** (3.5 Gallagher–Henriksen style, 3.4 MSL compilation).
   Precomputes `M♯ ⊆ Traits × TyCons` bottom-up in O(Σ_g |TyCons|^{vars(g)}), which is small for v ≤ 2. Lookup is
   O(1). It handles **open** goals `P⟨?x⟩` and existential premises that (1) can't instantiate, and it shares
   its key function with the index of (b)2.
5. **Regular-invariant / finite-model certificates** (3.6 Kafle–Gallagher refinement, 3.7 RInGen). Exponential
   or SMT-backed. Use it offline or as a diagnostic ("here is a 2-state model showing `Q<Bool>` can't be
   derived"), not per `summon`.

### (b) Speeding up the search itself (must preserve smallest-term and ambiguity semantics)

1. **Ancestor variant loop check** (3.10). O(1) amortized per step with a hashed ancestor set. A proof shows it
   never removes a minimal derivation. It turns the intro.md divergence and every pure cycle from "hit depth
   10" into immediate failure. Smallest change: `Environment` + `threadContinuation` + `summon(...where:)`.
2. **Head-key indexing of givens** (5.1-5.3). It replaces the scan of every visible given in `summon(...where:)`
   (l. 3636) with O(K + hits) per subgoal, and removes the thread allocations for candidates that would fail in
   `match` anyway. Keep coercion and variable-headed givens in a wildcard bucket until 4.3 is done.
3. **Tabling with Knuth ordering and capped counting** (4.1 + 2.1 + 2.2 + 2.4). One table entry per distinct
   (α-normalized) subgoal and an agenda ordered by `(steps, penalties)`. Ambiguity comes from counts capped at 2.
   Cost goes from exponential (diamonds, repeated subgoals) to O(M log N), or O(M) with a bucket queue since
   costs ≤ d+1. Caveats: answers for open subgoals are substitutions (generator/consumer as in Lean); sharing of
   pending premises must be modeled or respecified; tables are per scope and environment; cache only cycle
   roots (4.2).
4. **Admissible lower-bound pruning (A\*-style)** (2.3) using the height table from (a)2. Drop a thread when
   `steps + max h(pending) > d`. Cost is O(1) per thread after precomputation. It never changes results because
   pruned threads can't finish within the depth limit.
5. **Decide equalities instead of searching for them** (4.3). Use congruence closure, O(n log n) per scope, or
   completed rewriting for associated types, in place of the built-in symmetry/transitivity givens. This
   removes three candidates from every subgoal and the existential transitivity premise. It makes
   `canDeriveCoercions` exact and makes indexing (b)2 sound without wildcard buckets. It is the largest change.

### Things I could not verify
* The Knuth 1977 PDF wasn't retrievable. Its content is confirmed through Nederhof 2003 and F&M 2007.
* The NP-hardness of minimum distinct-hyperarc hyperpaths (1.4) and the H3 cubic bound (3.4) come from
  memory or abstracts.
* SIP-31's exact dominance rule (4.4) and Lean's DiscrTree reduction and star rules (5.2) are partly from memory.
* No paper titled "Horn clause transformation by tree automata products" was found. The closest is Kafle &
  Gallagher (3.6) and Gallagher's VPT 2016 talk.
* The 2-element model in 3.7 and the soundness arguments in 2.1 and 3.10 are my own reasoning against
  Typer.swift, not results from the literature.
