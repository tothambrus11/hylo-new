# `typevec`: contiguous storage for type-store projections

## How it works

Every type is hash-consed in `TypeStore.types: StableSet<AnyTypeTree>`. Each projection `store[id]` (the most frequent operation in the type checker: unification, substitution, reification, `contextAndHead`, casts, …) read `types[id.offset]`. That goes through `StableSet`'s subscript. `StableSet` lives in the `StableCollections` module, which is neither inlinable nor specialized, so every read runs unspecialized generic code. Profiles showed:
- `StableSet.subscript.getter` at 12–37% inclusive;
- `__swift_instantiateGenericMetadata` at up to 26%.

With the flag, the store keeps a parallel `ContiguousArray<AnyTypeTree>` that receives each newly inserted tree. Projections read the array. Insertion (hash-consing) still goes through the `StableSet`.

This is part (A) of the judged `typevec` idea (`ideas/RESULTS-round2.md`). Parts (B) and (C), a dense tag array and cast-free interning, are not implemented yet.

## Why it is sound

- `TypeStore` never removes types, and `StableSet.insert` appends a new member at position `count`.
- So the array element at offset `i` is the same tree value as `types[i]`; a debug assertion checks `position == trees.count` on every insertion.
- Identities, insertion order and hash-consing are untouched.
- Every projection therefore returns an equal value, and nothing downstream can observe the change.

## What it speeds up

Everything, as a constant factor. It is especially effective on workloads dominated by type manipulation:

| Workload | Baseline | `typevec` |
|---|---:|---:|
| stdlib typing | 1039 ms | 827 ms (−20%) |
| assoceq-5 (equality reasoning) | 2678 ms | 2283 ms (−15%) |
| trans-8 (transitive equalities) | 1823 ms | 1477 ms (−19%) |
| breadth40 (wide resolution) | 8960 ms | 8219 ms (−8%) |

Measured with `--repeat 3`, best time, pinned.

## Costs

- One extra reference per type (8 bytes), plus a retain per inserted tree.
- When a `Program` is copied (solver forks), a second buffer is shared copy-on-write, and the first insertion after a fork copies it. The `StableSet` already behaves this way.
