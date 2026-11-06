# `eqsolve`: a decision procedure for closed equality goals

**Status:** semantic fix, part of the final configuration. Requires `occurs` and `fixsubst`.

## How it works

At the start of `summon`, a goal that is a closed equality `A ~ B` (no open type variables after substitution) is decided directly; it is not searched.

1. **Facts.** Collect the equality givens: the assumed ones in the environment, then the visible ones, in summon's group order.
   - If any given could derive other equalities, return `notApplicable` and let search run. That covers a quantified or conditional equality, and a bare-variable head.
   - Each fact records its *cost*: the penalty search gives that given, i.e. the offset of its group.
2. **Reflexive fast path.** If the dealiased sides are identical, return `refl` with the cost of the built-in group.
3. **Term graph.** Every subterm of the goal and of the facts becomes a node, deduplicated by dealiased type identity.
   - Compound nodes have a *shape* (constructor plus non-child attributes: arity, arrow style/effect/labels/access, remote access) and children.
   - A concrete associated-type projection `(T::w).X` is an atom.
   - An abstract projection `(Self::P).X` is handled by step 5.
4. **Congruence closure** (Nelson–Oppen / Downey–Sethi–Tarjan). It uses a signature table `(shape, find(children)) → node` and use lists. Unioning two classes re-signs only the parents of the smaller class. This is `O(n log n)`.
5. **Abstract projections.**
   - `(Self::P).X` is merged with the concrete projections `(T::w).X` whose qualification types are in its class, but only if they all fall in **one** class. Otherwise it would equate projections through two distinct witnesses, which `negative/associated-type-inequality.hylo` forbids.
   - A projection that acquires a second concrete class is *banned*, and the closure is recomputed without it. Bans only grow, so the loop terminates, and the result does not depend on any order.
6. **Premise projections.** A projection through a premise that is not discharged yet is resolved ahead of time: either through `$k` directly, or through a callee's `using` whose premise is assumed with the same type.
   - The premise's type is resolved in the environment in which the premise will be discharged (the givens assumed before it).
   - If that resolution has a unique result `w`, the projection is merged with `(T::w).X`.
   - Resolution is deterministic, so `w` is the witness that will discharge the premise.
   - This removes bug #3's incompleteness for conditional extensions such as `extension <T where T is Collection, T.Element == Flag> Box<T>`.
7. **Verdict.** If the goal's two nodes fall in different classes, the goal is **refuted** (`return []`). Otherwise a proof is rebuilt from the cheapest path, found by Dijkstra over edge costs. The edge costs mirror search penalties:
   - a fact costs its group offset;
   - reversing an edge adds the built-in group's offset (symmetry);
   - each composition adds it again (transitivity).

   The proof is built from `symmetry`, `transitivity`, the facts, and `coercion(refl)` for congruence edges, which is proof-irrelevant, exactly as `match` assumes part equalities. The thread gets `penalties + cost`, so derivations rank as they do under search.

## Why it is sound

- **The theory.** The decided theory is the one search implements: reflexivity, symmetry, transitivity, the ground facts, and congruence (`match` assumes equalities between mismatching parts of two types of the same shape). Injectivity is *not* used, and search does not use it either.
- **Refutation is exact for this theory.** Two terms are equal in the congruence closure of ground equations iff they fall in one class (Nelson–Oppen). Goals with open variables or non-ground facts are left to search.
- **The abstract-projection rule** is the one sound reading that agrees with both `v-abs-7.hylo` (valid) and `associated-type-inequality.hylo` (negative). Admitting the unification rule transitively derived `T.X == U.X` from `T == Self, U == Self` (review2 `abs-trans-2/3/5`).
- **Proof terms.** Every symmetry step is now instantiated with the arguments in the right order. Review2 `e1-sym-proof.hylo` showed `symmetry<B,A>` applied to an `A~B` proof.
- **Costs.** With the costs, the selection of witnesses matches the baseline's ranking on review2 `e04`/`e05`/`e06`. Without them (`eqsolvefree`), equally cheap alternatives made valid programs ambiguous.
- **Oracle.** 216/216 identical on the corpus (192 tests and 24 workloads), with the whole final configuration.

## What it speeds up

Any program whose equality goals search would explore by symmetry/transitivity, which is exponential in the length of the chains:

| workload | baseline | FIX |
|---|---|---|
| trans-8 | 1247 ms | 8.7 ms |
| assoceq-8 | 3635 ms | 143 ms |
| orig-coerc-cache | 2696 ms | 12 ms |
| p02-cc-big (31 equalities) | out of memory | 82 ms |
| perf-alias-7 (aliases expanding to 320-deep terms) | wrong rejection | 10 ms |

It also turns wrong acceptances into fast rejections: `assocneg-8` is rejected in 109 ms, where the baseline accepted it in 3064 ms.

## Costs

- The graph is rebuilt for every closed equality goal. It is linear-logarithmic in the number of subterms of the visible equalities, so it is negligible on the corpus. A cache per (scope, assumed givens) would remove it entirely.
- A premise projection costs one nested resolution, with a recursion guard of depth 2.
- Equality goals with open variables are still searched; `eqmgu` handles the common bare-variable case.
