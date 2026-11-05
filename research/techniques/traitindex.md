# `traitindex`: index the visible traits by member identifier

## How it works

`lookup(_:memberOfTraitVisibleFrom:)` (Typer.swift) resolves qualified member names through traits, for example `T.m` where `T is P`.

**Baseline.** It iterates over every trait visible from the scope. For each trait it runs `lookup(name, lexicallyIn: trait)` and `.filter(resolvableWithQualification)`. Building that closure copies the `Typer` value, which showed up as 2.6% of stdlib typing.

**With the flag.** A per-scope map `[identifier: [TraitDeclaration.ID]]` is built incrementally, the same way `traits(visibleFrom:)` builds its list:
- a nested scope takes its parent's map and appends the traits it declares locally;
- a top-level scope gets the module's traits followed by the imported ones.

Only the traits that declare the identifier are visited, and the original loop body runs on them.

## Why it is sound

- A trait that declares no member with identifier `n` has no entry `declarations(lexicallyIn: trait)[n]`. The baseline's `lookup` returns `[]` for it, and the trait is skipped by `if !ms.isEmpty`.
- `lookup(_:lexicallyIn:)` and the filter of an empty array have no side effects (lookup tables are purely syntactic).
- The per-identifier lists keep the order of `traits(visibleFrom:)`: each list is a subsequence built by the same concatenation.
- So the result array is identical. Label and introducer refinement (`refineLookupResults`) still runs on the hits.

Oracle: identical on all 216 corpus files.

## What it speeds up

Qualified member lookups (`T.X`, `x.m` through a conformance) in programs with many visible traits. On the stdlib the effect is small (a few percent at most), because the lookup loop was already cheap per trait. It mostly removes the `Typer` closure copy.

Measured alone (`../round3/bench.md`, ms, baseline → flag): stdlib 1007 → 947. No workload in the benchmark changes beyond noise, so this flag is a cleanliness and scaling measure (O(hits) trait lookup) rather than a measured win.

## Costs

- One map per scope that performs a trait member lookup. It shares storage with its parent (copy-on-write) until local traits are added.
- Building a map costs O(Σ members of the visible traits) once per scope.
