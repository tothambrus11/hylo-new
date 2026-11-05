# `symindex`: one-pass standard-library symbol table

## How it works

Before typing the standard library, `Program.initializeStandardLibraryCaches()` (Program.swift) finds the declaration of each `StandardLibraryEntity`, about 24 of them. These are the entities the compiler needs to know by name: `Bool`, `Int`, `Movable`, `Deinitializable` and so on. Each one is located through its `@_symbol("…")` annotation.

**Baseline.** One `select(from: stdlib, .symbol(name))` call per entity. Each call is a full scan over every syntax node of the standard library, and each node gets an `as? any Annotatable` existential cast. That is 24 full scans.

**With the flag.** One scan builds `[symbol string: [node]]`. Then each entity is looked up in that dictionary and passes through the same `uniqueElement` and `castToDeclaration` checks and the same precondition.

## Why it is sound

- `select` is `filter` over `modules.values[m].syntax`, which preserves order. The predicate is the same `symbol(annotating:) == name`.
- So `table[name]` holds exactly the nodes that `select` returns, in the same order.
- `uniqueElement` therefore gives the same answer, including `nil` for a missing or duplicated symbol, and the precondition fires in the same cases.
- The function has no other effect.

Oracle: identical on all 216 corpus files.

## What it speeds up

Every compilation that types the standard library, or loads it from an archive (the same function runs there). The saving is a fixed amount per compilation, independent of the user program.

Measured alone (`../round3/bench.md`): stdlib typing 1007 → 885 ms (−12%). The profile estimated 13.7%, and the measurement agrees. User-typing workloads are unaffected (±noise).

## Costs

- One dictionary of about 30 entries, kept only during initialization.
- No asymptotic cost: one pass instead of 24.
