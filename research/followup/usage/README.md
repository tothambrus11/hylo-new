# How much real code uses equality constraints

## The question

The equality machinery of the type checker (`eqsolve`, `eqmgu`, `absquotient`) never runs on the current standard library. The review could not say whether it is worth its complexity, because nobody had measured how much real code uses equality constraints. This directory measures it on comparable code bases, characterises the equalities found, and turns the most demanding real patterns into benchmarks for this compiler.

## Short answer

1. **Equality constraints are ordinary in real generic code, not a corner case.** The Swift standard library writes 357 of them in 150,000 lines (2.4 per 1,000 lines). One generic declaration in five has one. swift-collections writes 527, the iterator part of the Rust core library 177. The current Hylo standard library writes none, and the original Hylo standard library writes one.
2. **Most of the exposure comes from traits, not from where clauses.** 6% of the functions of the Swift standard library have an equality written in their own scope. 18% have one in scope once the equalities stated by the protocols they name are counted (`Collection` alone brings seven). In swift-algorithms it is 56% of the functions.
3. **The reasoning needed is shallow.** A declaration with equalities has one at the median and two or three at the 99th percentile. No written where clause in any code base needs a chain of more than two equalities. No real code equates two parameters (`T == U`), which is the shape of 8 of the 12 equalities in this compiler's tests. Equalities almost always involve an associated type, and two thirds relate an associated type of one parameter to another parameter or to its associated type.
4. **The existing checker cannot handle the real patterns; the equality procedure can.** Of four benchmarks translated from real code, the existing checker (base) accepts one after 85 times more work, times out on one, wrongly rejects one after 1.5 million candidate matches, and crashes on one. With `eqsolve` three are accepted after 2,000 to 11,000 candidate matches. False claims are rejected in bounded work only with `eqsolve`.
5. **The larger obstacle is elsewhere.** Translating the patterns exposed seven missing or incomplete features around associated types (section 6). Two of them make the fourth benchmark, from Rust's `Flatten`, untypable under every configuration. Until they are addressed, a Hylo standard library cannot be written in the style that produces these equalities, whatever the equality procedure costs.

## 1. What was counted

`census.py` reads source text and counts generic declarations, where clauses, requirements and their shapes, conditional conformances and extensions, traits with associated types, and overloaded names. It is a lexical tool, not a parser; its limits are in section 8.

| Code base | Source | Files | Lines |
|---|---|---:|---:|
| hylo-new-stdlib | this repository, `StandardLibrary/Sources` | 18 | 734 |
| hylo-new-tests | this repository, `Tests/CompilerTests` | 204 | 4,481 |
| hylo-old-stdlib | hylo-lang/hylo `StandardLibrary/Sources` | 63 | 6,350 |
| swift-stdlib-core | swiftlang/swift `stdlib/public/core` | 268 | 150,232 |
| swift-collections | apple/swift-collections `Sources` | 576 | 90,637 |
| swift-algorithms | apple/swift-algorithms `Sources` | 28 | 9,464 |
| rust-core-iter | rust-lang/rust `library/core/src/iter` | 46 | 17,335 |
| rust-core-ops-slice | rust-lang/rust `library/core/src/{ops,slice}` | 37 | 22,228 |
| rust-alloc-collections | rust-lang/rust `library/alloc/src/{collections,vec}` | 54 | 36,109 |

All five clones succeeded; none was refused by the network policy. `fetch_clones.sh` lists the commits. The clones were only read as text.

Requirements are counted in the form each language writes them:

- Hylo: `T is P` and `A == B`, in a where clause or as an inline bound.
- Swift: `A: P` and `A == B` in where clauses, inline bounds, and constraints on primary associated types (`some Sequence<Int>` and `S: Sequence<Int>` state `S.Element == Int`).
- Rust: bounds in where clauses and generic parameter lists, and associated type bindings (`I: Iterator<Item = T>` states `I::Item == T`). The return type of a function bound (`F: FnMut(A) -> B`) is also a binding in Rust, but Hylo has built-in arrow types, so these are listed apart and not counted as equalities.

## 2. Local census

The current standard library has no equality requirement and almost no generic code.

| File (`StandardLibrary/Sources/`) | Lines | Declarations | Generic | Where clauses | `T is P` | `A == B` | Conditional conformances | Extensions | Conformance declarations | Traits | Functions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Core/Assert.hylo | 12 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| Core/Bool.hylo | 60 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 6 |
| Core/Comparable.hylo | 36 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 4 |
| Core/Copyable.hylo | 16 | 4 | 1 | 0 | 2 | 0 | 1 | 0 | 2 | 1 | 1 |
| Core/Deinitializable.hylo | 16 | 4 | 1 | 0 | 2 | 0 | 1 | 0 | 2 | 1 | 1 |
| Core/Equatable.hylo | 24 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 |
| Core/MemoryLayout.hylo | 27 | 4 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 3 |
| Core/Movable.hylo | 28 | 6 | 1 | 0 | 2 | 0 | 1 | 1 | 2 | 1 | 2 |
| Core/Numbers/AdditiveArithmetic.hylo | 28 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 5 |
| Core/Numbers/ExpressibleByFloatingPointLiteral.hylo | 9 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Core/Numbers/ExpressibleByIntegerLiteral.hylo | 9 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Core/Numbers/Float32.hylo | 119 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 14 |
| Core/Numbers/Float64.hylo | 119 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 14 |
| Core/Numbers/Numeric.hylo | 15 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 |
| Core/Optional.hylo | 14 | 2 | 2 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| Core/Pointer.hylo | 17 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| Core/Prelude.hylo | 13 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| Core/Runtime/OffsetOfMember.hylo | 172 | 15 | 1 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 8 |
| **Total** | **734** | **115** | **9** | **1** | **7** | **0** | **4** | **4** | **28** | **9** | **68** |

No trait of the standard library has an associated type, no extension is conditional, and no function name is declared twice in one type.

The compiler tests (204 files, names resolved within each file) contain 12 equality requirements in 5 files: `positive/associated-type-equality.hylo` (4), `positive/coercion-derivability-cache.hylo` (3), `positive/equality.hylo` (3), `positive/conformance-via-equivalence.hylo` (1), `negative/associated-type-inequality.hylo` (1). Eight equate two parameters, three equate a parameter and a type, and one equates two associated types. Seven of the 60 traits have an associated type. The per-file tables are `results/files-hylo-new-stdlib.csv` and `results/files-hylo-new-tests.csv`.

## 3. Comparable code

The full table is `results/tables.md`; the numbers behind it are in `results/summary.json`, and every declaration with its classified requirements is in `results/decls-*.jsonl`.

### 3.1 Volume

| | hylo-new stdlib | hylo-new tests | hylo-old stdlib | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Functions | 68 | 563 | 861 | 6,820 | 3,946 | 419 | 928 | 827 | 1,706 |
| Generic declarations | 9 | 150 | 61 | 1,601 | 752 | 72 | 751 | 524 | 1,080 |
| Where clauses | 1 | 38 | 16 | 942 | 712 | 118 | 492 | 195 | 231 |
| Conformance requirements (`T is P`), where clauses | 0 | 36 | 18 | 608 | 213 | 127 | 895 | 249 | 377 |
| Conformance requirements, inline bounds | 7 | 25 | 37 | 952 | 355 | 59 | 257 | 194 | 902 |
| **Equality requirements** | **0** | **12** | **1** | **357** | **527** | **22** | **177** | **15** | **72** |
| per 1,000 lines | 0 | 2.7 | 0.2 | 2.4 | 5.8 | 2.3 | 10.2 | 0.7 | 2.0 |
| of which written in a trait | 0 | 0 | 0 | 39 | 5 | 0 | 1 | 4 | 0 |
| Declarations with an equality, share of generic declarations | 0% | 6% | 2% | 19% | 59% | 31% | 22% | 2% | 7% |
| Return types of `Fn` bounds (not counted) | – | – | – | – | – | – | 376 | 172 | 67 |
| Traits | 9 | 60 | 22 | 148 | 21 | 0 | 40 | 65 | 19 |
| Traits with associated types | 0 | 7 | 5 | 47 | 11 | 0 | 9 | 23 | 2 |
| Associated types | 0 | 7 | 6 | 82 | 16 | 0 | 10 | 26 | 2 |
| Extensions (Rust: inherent impls) | 4 | 32 | 17 | 1,997 | 1,602 | 197 | 38 | 54 | 183 |
| Extensions of a trait | 0 | 5 | 8 | 280 | 83 | 71 | 0 | 0 | 0 |
| Conformances declared | 28 | 110 | 176 | 1,193 | 596 | 163 | 355 | 326 | 539 |
| Conditional conformances | 4 | 10 | 7 | 207 | 98 | 74 | 285 | 125 | 358 |
| … whose condition involves an associated type or an equality | 0 | 1 | 1 | 44 | 1 | 16 | 46 | 2 | 22 |
| … whose condition is an equality | 0 | 1 | 0 | 0 | 0 | 1 | 31 | 2 | 19 |
| Conditional extensions | 0 | 6 | 9 | 183 | 71 | 24 | 18 | 18 | 66 |
| … whose condition involves an associated type or an equality | 0 | 0 | 3 | 88 | 28 | 19 | 4 | 0 | 1 |
| … whose condition is an equality | 0 | 0 | 1 | 41 | 11 | 2 | 2 | 0 | 1 |
| Extensions and conformances per type: median / 95th percentile / maximum | 1 / 7 / 7 | 2 / 20 / 21 | 4 / 16 / 16 | 3 / 21 / 77 | 4 / 37 / 65 | 3 / 7 / 24 | 3 / 12 / 19 | 2 / 10 / 25 | 2 / 38 / 60 |
| Function names declared more than once in one type, of all names | 0 of 68 | 15 of 547 | 32 of 791 | 984 of 4,259 | 675 of 2,310 | 67 of 308 | 84 of 798 | 29 of 788 | 224 of 1,349 |

In Swift, 312 of the 357 equalities of the standard library are written in where clauses and 45 through primary associated types. In swift-collections the proportion is reversed (113 and 414): recent Swift code writes `some Sequence<Element>` where older code wrote `where S.Element == Element`. The requirement is the same.

The largest overload sets are initialisers and encoders: `String.init` (62 declarations), `UnkeyedEncodingContainer.encode` (54). The most extended type is `String` (77 extensions and conformance declarations).

### 3.2 Shapes of the equalities

A term is a *parameter* if an enclosing declaration or the extended type declares it, an *associated type* if it is a projection (`S.Element`, or `Element` inside a protocol), *concrete* if it mentions no parameter (`Int`, `[UInt8]`), and *constructed* if it applies a type constructor to parameters (`Slice<Self>`, `Element?`).

| Shape | hylo-new tests | hylo-old stdlib | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections | All real code |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parameter == parameter | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |
| parameter == concrete type | 1 | 1 | 13 | 5 | 0 | 0 | 0 | 0 | 18 |
| parameter == constructed type | 2 | 0 | 31 | 10 | 0 | 0 | 0 | 2 | 43 |
| associated type == concrete type | 0 | 0 | 94 | 80 | 6 | 29 | 0 | 17 | 226 |
| associated type == constructed type | 0 | 0 | 24 | 21 | 4 | 10 | 0 | 7 | 66 |
| associated type == parameter | 0 | 0 | 91 | 313 | 2 | 120 | 13 | 45 | **584** |
| associated type == associated type, same parameter | 0 | 0 | 22 | 2 | 0 | 1 | 2 | 0 | 27 |
| associated type == associated type, different parameters | 1 | 0 | 82 | 96 | 10 | 17 | 0 | 0 | **205** |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Total | 12 | 1 | 357 | 527 | 22 | 177 | 15 | 72 | 1,170 |

"All real code" is the six Swift and Rust columns. In the task's coarser classes: parameter == parameter 0%, parameter == concrete or constructed type 5%, associated type == concrete or constructed type 25%, associated type == associated type 20%, and the remaining 50% equate an associated type with a parameter (`S.Element == Element` in an extension of `Array`).

## 4. Characterisation

**Requirements per declaration.** Among declarations that have at least one conformance or equality requirement:

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Requirements: median / 95th / 99th percentile / maximum | 1 / 2 / 3 / 4 | 1 / 4 / 4 / 5 | 1 / 3 / 4 / 4 | 2 / 4 / 6 / 7 | 1 / 3 / 4 / 5 | 1 / 3 / 4 / 5 |
| Equalities, where there is one: median / 95th / 99th / maximum | 1 / 1 / 2 / 2 | 1 / 2 / 3 / 3 | 1 / 1 / 1 / 1 | 1 / 2 / 2 / 2 | 1 / 2 / 2 / 2 | 1 / 1 / 1 / 2 |

**Chains that need transitivity.** For each declaration, the equalities written on it and on its enclosing declarations were merged into classes of equal terms. A class of three terms needs a chain of two equalities to relate two of them.

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Declarations with a class of two terms | 512 | 500 | 50 | 264 | 16 | 102 |
| Declarations with a class of three terms (chain of two) | 6 | 1 | 0 | 1 | 1 | 1 |
| Declarations with a larger class | 0 | 0 | 0 | 0 | 0 | 0 |

The ten declarations with a chain of two are known by name. Examples: `RangeSet.init(_:within:)` (`S.Element == C.Index, C.Index == Bound`, where the body passes an `S.Element` as a `Bound`); `AnyCollection.init(_: _Either<L, R>)` (`L.Element == Element, R.Element == Element`); the three views of `StringProtocol` (`UTF8View.Index == Index`, `Index == String.Index`); `Collection.Indices` (`Indices.Element == Index`, `Indices.Index == Index`). The synthetic workloads used so far (`trans-8`, `assoceq-8`) have chains of eight; nothing like them was found in a written where clause.

**Chains through traits are longer, and unbounded in principle.** The count above sees only what one declaration writes. In Swift, `C: Collection` also brings the seven equalities of the protocols `Collection` and `Sequence` into scope, and two of them are recursive (`SubSequence.SubSequence == SubSequence`, `Indices.SubSequence == Indices`). A fact such as `C.SubSequence.SubSequence.Element == D.Iterator.Element`, used in the first benchmark, takes one congruence step and three equalities. Swift decides these with a completion procedure, because the set of derivable equalities is infinite.

**Congruence.** In no declaration does congruence identify two written terms that the written equalities do not already identify. What does occur is a projection of a term that an equality mentions: 112 declarations in the Swift standard library, 55 in Rust's iterators. The typical case is `extension Collection where SubSequence == Self`, whose body then uses `SubSequence.Index`. Whether congruence is needed is decided in function bodies, which this census does not analyse.

**Depth of projections.** In the Swift standard library, 263 equalities involve a projection of depth one (`S.Element`), 49 of depth two (`S.Iterator.Element`), and one of depth three. Over all type expressions in the code, signatures and bodies, 1,207 projections have depth one, 163 depth two and one depth three.

**Different parameters.** 205 of the 1,170 equalities (18%) relate associated types of two different parameters. Another 584 (50%) relate an associated type to a parameter, and in most of them the parameter belongs to the enclosing type while the associated type belongs to a parameter of the function, as in `init<S: Sequence>(_ s: S) where S.Element == Element`.

**What is visible in a typical scope.**

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Local givens of a function (own and enclosing requirements): median / 95th / 99th / maximum | 0 / 2 / 3 / 7 | 0 / 2 / 4 / 5 | 0 / 2 / 3 / 4 | 2 / 6 / 10 / 14 | 0 / 2 / 4 / 5 | 1 / 3 / 4 / 6 |
| Functions with a written equality in scope | 438 (6%) | 479 (12%) | 32 (8%) | 223 (24%) | 10 (1%) | 73 (4%) |
| Functions with an equality in scope, counting those of the traits named | 1,250 (18%) | 634 (16%) | 235 (56%) | 263 (28%) | 19 (2%) | 75 (4%) |
| Equalities in scope, counting those of the traits named: median / 95th / 99th / maximum | 0 / 7 / 15 / 44 | 0 / 3 / 9 / 18 | 1 / 14 / 16 / 22 | 0 / 3 / 4 / 5 | 0 / 0 / 2 / 2 | 0 / 0 / 2 / 4 |
| Global givens (conformances declared in the module) | 1,193 | 596 | 163 | 355 | 326 | 539 |

"The traits named" means: for each requirement `T: P` in scope, and for `Self` in an extension of a protocol, the equalities written in `P` and in the protocols it refines, counted once, without descending into the associated types. In the Swift standard library, 690 functions have one to three equalities in scope, 330 have four to seven, 171 have eight to fifteen, and 59 have sixteen or more. The last group is the members of `StringProtocol` and of the protocols that restate the equalities of `Collection` (`BidirectionalCollection`, `RandomAccessCollection`), where the restated equalities are counted twice. The most common values after zero are one, three and seven; seven is the signature of `Collection`.

A resolution in a module of this size therefore sees about a thousand global givens, a handful of local ones, and in one function out of five between one and fifteen equalities.

## 5. Benchmarks from real patterns

The four files of `benchmarks/` each name their source in a comment. They state the equalities of the original declarations in where clauses, and check facts that the original bodies rely on, written as `need<A, B>()` with `fun need<A, B where A == B>() {}`.

| Benchmark | Source | Pattern | Equalities in the largest scope |
|---|---|---|---:|
| `swift-collection-signature.hylo` | Swift `Collection.swift:401-471`, `Sequence.swift:331` | the requirement signature of `Collection` for one and for two collections; recursive equalities; chains of up to three steps with congruence | 15 |
| `swift-string-protocol.hylo` | Swift `StringProtocol.swift:14-53` | the protocol with the most equalities in the library; associated types equated to concrete types | 16 |
| `swift-transitive-parameters.hylo` | Swift `RangeSet.swift:182`, `EitherSequence.swift:187`; swift-algorithms `Chain.swift:13` | the declarations with the longest written chains; a conditional conformance whose condition is an equality | 2 |
| `rust-flatten.hylo` | Rust `iter/adapters/flatten.rs` (the where clause of 11 impls), `iter/traits/collect.rs:291` | bindings nested two deep; a parameter that only an equality determines | 2 |

`run_benchmarks.py` runs each file under base, FIX and FULL with `--count`, one process at a time with a 60 s limit, and also three generated copies: the `// NEG:` lines enabled (plausible false claims that must be reported), a control in which every claimed equality is replaced by two equalities with a fresh type (all must be reported, and no message may contain the error type `#!`, which shows that every type of the benchmark resolves), and each function alone. The complete table is `bench-results.md`; the raw records are `bench-results.jsonl`. Times are from a shared machine and only indicative.

### 5.1 The benchmarks as written (expected: accepted)

| Benchmark | Configuration | Verdict | `summon.calls` | `summon.matches` | `summon.layers` | `eqsolve.proved` | `eqsolve.refuted` | `eqmgu.solved` | Time, ms (indicative) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| swift-collection-signature | base | accepted | 147 | 811,287 | 879 | – | – | – | 46,011 |
| | FIX | accepted | 147 | 9,501 | 144 | 14 | 8 | 0 | 849 |
| | FULL | accepted | 147 | 9,501 | 144 | 14 | 8 | 0 | 1,010 |
| swift-string-protocol | base | timeout (60 s) | | | | | | | |
| | FIX | accepted | 161 | 10,824 | 155 | 10 | 3 | 0 | 917 |
| | FULL | accepted | 161 | 10,749 | 154 | 10 | 3 | 0 | 1,268 |
| swift-transitive-parameters | base | **rejected** (1 error) | 40 | 1,549,133 | 190 | – | – | – | 45,341 |
| | FIX | accepted | 39 | 2,461 | 49 | 8 | 0 | 0 | 103 |
| | FULL | accepted | 39 | 2,236 | 46 | 8 | 0 | 0 | 92 |
| rust-flatten | base | crash (stack overflow) | | | | | | | |
| | FIX | **rejected** (1 error) | 45 | 13,841 | 56 | 3 | 0 | 142 | 588 |
| | FULL | **rejected** (1 error) | 45 | 13,841 | 56 | 3 | 0 | 142 | 418 |

- The equality procedure is used by every benchmark: `eqsolve` proves between 3 and 14 equalities, and `eqmgu` runs on the one benchmark with a conformance parameter determined by an equality.
- Base wrongly rejects `swift-transitive-parameters`. The error is on `needSequence<Chain2<A, B>>()`: the conformance of `Chain2` requires `A.Element == B.Element`, which follows from `A.Element == X` and `B.Element == X`. Base gives up after two depth-exhausted searches and 1.5 million candidate matches (`generated/swift-transitive-parameters.fn-chainUse.hylo`). This is the Chain2Sequence pattern of swift-algorithms.
- Base handles the one-collection function of the first benchmark in 29,870 matches (FIX: 3,104) and the two-collection function in 781,417 (FIX: 6,397). From 7 to 15 equalities in scope its work grows by a factor of 26, and that of FIX by a factor of 2. (The two functions check different facts, six and four, so the comparison is indicative.)
- `rust-flatten` is rejected by FIX and FULL at one line, `needIterator<Flatten<I>>()`. Section 6 gives the two causes. The equalities of the body are proved.
- FIX and FULL do the same amount of matching. With an equality in scope the candidate index reports `index.unavailable` (6,529 times in the first benchmark) and falls back to the full list of givens. The gain that `index` gives on today's standard library does not carry over to scopes with equalities.

### 5.2 False claims (expected: one error per claim)

| Benchmark with `// NEG:` lines enabled | Claims | base | FIX | FULL | `summon.matches` FIX / FULL | `eqsolve.refuted` | `eqmgu.solved` |
|---|---:|---|---|---|---:|---:|---:|
| swift-collection-signature | 6 | timeout | 6 errors | 6 errors | 9,693 / 9,693 | 20 | 0 |
| swift-string-protocol | 5 | timeout | 5 errors | 5 errors | 11,108 / 11,033 | 13 | 0 |
| swift-transitive-parameters | 6 | timeout | 6 errors | 6 errors | 112,196 / 111,821 | 8 | 284 |
| rust-flatten | 3 | crash | 3 errors (+1) | 3 errors (+1) | 13,844 / 13,844 | 6 | 142 |

- Rejecting a false equality costs the equality procedure almost nothing: six false claims add 2% to the matching of the first benchmark. Base does not finish any of the four in 60 s.
- Rejecting a false *conformance* that has an equality condition is expensive under FIX and FULL alike. The two false claims `needSequence<Chain2<A, X>>()` and `needSequence<Chain2<B.Iterator, A>>()` raise the matching of the third benchmark from 2,461 to 112,196. `eqmgu` runs 284 times and four searches exhaust the depth bound. The abstract model does not help here (`absmodel.refuted` = 5, same total).
- The abstract model does help on a failing conformance with no equality given in scope: `gaps/unsatisfiable-conformance.hylo` takes 11,322 matches under FIX and 441 under FULL, and overflows the stack under base.
- The controls report the expected number of errors (20, 18, 4, and 2 plus the known failure) with no `#!` in any message.

## 6. Features that the translation needed and the compiler lacks

Each item has a minimal program in `benchmarks/gaps/` with the expected and the observed behaviour in its header. The verdicts are the same under base, FIX and FULL unless stated.

| File | What real code does | What happens here |
|---|---|---|
| `trait-equality.hylo` | A protocol states equalities between its associated types (`where Iterator.Element == Element`). 39 equalities are written this way in the Swift standard library, and they are in scope in 18% of its functions. | Syntax error: a trait member `given A == B` is not accepted. The benchmarks restate the equalities in each where clause. |
| `trait-given-not-used-for-lookup.hylo` | `S.Iterator.Element` for `S: Sequence`. | The `given Iterator is IteratorProtocol` of the trait is not used to look up `Element`; the type is `#!` unless the function restates `S.Iterator is IteratorProtocol`. |
| `inherited-associated-type.hylo` | `C.Element` for `C: Collection`, where `Element` is declared by `Sequence`. | The type is `#!`. |
| `error-type-accepted.hylo` | – | A type expression that does not resolve is not reported, and two unresolved types are compatible, so the program is accepted without a diagnostic. "Accepted" therefore does not show that a program's types were resolved; this is why the benchmarks have a control. |
| `where-clause-order.hylo` | Rust writes `Item = U::Item` before `U: Iterator`. | A where clause is resolved left to right: "type 'U' has no static member 'X'". |
| `generic-projection.hylo` | `<IntoIter<A> as Iterator>::Item` is `A`. | An associated type defined by a generic conformance is not reduced, and `VecIter<A>.Item` is not accepted as a type expression. |
| `associated-type-premise.hylo` | `extension Range: Sequence where Bound: Strideable, Bound.Stride: SignedInteger`. 44 of the 207 conditional conformances of the Swift standard library and 46 of the 285 of Rust's iterators have a condition on an associated type. | Such a conformance is never found, with abstract or concrete arguments. |
| `two-equality-conditions.hylo` | `impl<I, U> Iterator for FlattenCompat<I, U> where I: Iterator<Item: IntoIterator<IntoIter = U, Item = U::Item>>, U: Iterator`. | Under FIX and FULL a conformance with the two conditions `I.InnerIter == U` and `I.InnerItem == U.Item` is not found although its conditions are exactly the givens in scope; with either condition alone it is found. Base does not finish. This one is in the equality machinery itself (`eqmgu.solved` = 142 before the failure). |
| `restated-conformance.hylo` | Swift derives `C.SubSequence.SubSequence: Collection` from `SubSequence.SubSequence == SubSequence`. | If the program states that conformance, FIX and FULL reject `C.SubSequence.SubSequence.Index == C.Index`, because the two conformances are different witnesses; base accepts. Without the restated conformance all three accept. This follows from the decision that conformances are not unique, but it is a trap for anyone porting Swift code. |

Two further files are controls that behave as expected: `equality-determined-parameter.hylo` (a conformance parameter that only an equality determines is found, with `eqmgu.solved` = 1) and `unsatisfiable-conformance.hylo` (above).

## 7. What the numbers imply

**How often will a Hylo type checker meet equality reasoning once its standard library reaches the size of Swift's?** If Hylo's library is written in the style of Swift's or Rust's, then:

- about 2 to 6 equality requirements are written per 1,000 lines, which is 300 to 500 in a library of that size;
- about one generic declaration in five carries one;
- an equality is in scope in 6% to 12% of all functions of the three Swift libraries if only written requirements count (24% in Rust's iterators), and in 16% to 56% if the equalities of traits count. For Hylo they will count: an equality that a trait states has to become a given wherever the trait is assumed, whether the language lets the trait state it or forces each function to restate it.

So the equality procedure would run in roughly one function in five of the standard library and in most functions of a generic algorithms library. It is not an adversarial case. The statement of the review that none of these behaviours "occurs in today's code" is true only because today's code has no trait with an associated type.

**How demanding is it?** Less than the synthetic workloads suggest in one respect, and more in another.

- Less: chains are short (two written equalities at most), classes are small (three terms at most), a declaration writes one or two equalities, and projections are one or two deep. The scaling workloads with eight chained equalities overstate the written depth by a factor of four.
- More: the number of equalities simultaneously in scope is 7 for any function over a `Collection`, 15 at the 99th percentile, and 44 at the maximum. Several are recursive. The existing checker's cost grows by a factor of 26 from 7 to 15 equalities on the first benchmark, and it fails three of the four benchmarks (a timeout, a wrong rejection and a crash), so it cannot be the checker of such a library.

**What this says about each technique.**

- `eqsolve`: needed. It is what turns a timeout, a crash or a wrong rejection into an answer on every realistic benchmark, and it rejects false equalities at almost no cost. A procedure of this kind, complete for transitivity and congruence over a set of ground equalities, is a requirement for a library in this style, not an optimisation.
- `eqmgu`: needed by the pattern of Rust's `Flatten` (a conformance parameter determined by an equality; 31 of the 285 conditional conformances of Rust's iterators have an equality condition, and none of the 207 of the Swift standard library). Its current form fails on the realistic case with two equality conditions (`gaps/two-equality-conditions.hylo`), and a failing search through it is the most expensive thing measured here (112,196 matches).
- `absquotient` and `absmodel`: these benchmarks neither support nor contradict them. FULL and FIX do the same work on all four and on their false-claim variants. The abstract model shows a benefit only on a failing conformance without equalities in scope (26 times less matching).
- `index` and the other result-preserving techniques: they stop helping when an equality is in scope, because the index is unavailable there. If one function in five has equalities in scope, an index that works under equalities (for example on the representatives of the equality classes) becomes more valuable than it looks today.

**What to do first.** The equality procedure is not the bottleneck for adopting this style of library; the features of section 6 are. A reasonable order is: let traits state equalities and use the conformances of associated types for lookup, reduce projections through generic conformances, support conditions on associated types, and report unresolved types. Then the benchmarks of this directory can be rewritten without restating anything, and they will measure the equality procedure on the givens that a real library produces.

## 8. Limits of the method

- **The census is lexical.** Declaration heads are found by keyword and cut with bracket matching. Two independent checks agree with it: a line-based search finds 302 where-clause lines with `==` in the Swift standard library (census: 312 equalities in where clauses), and 169 bindings in Rust's iterators (census: 177). Every `where` token of the Swift standard library is attributed to a declaration except the 75 inside `@_specialize` attributes, which are not requirements.
- **Classification is by spelling.** Type aliases are not expanded, so a bare name that is an alias for an associated type inside a concrete type is classified by a name table and can be wrong. Nested types with the same simple name (`Iterator`, `IntoIter`, `Index`) are merged in the per-type counts for Rust, which inflates "extensions per type" there.
- **Templates and macros are counted once.** Swift `.gyb` files and Rust `macro_rules!` bodies are counted as written, not per expansion. Rust's numeric code is mostly macros, so the Rust numbers outside the iterator module are lower bounds.
- **Implied equalities are counted one level deep, by spelling.** The equalities of the traits named are added without following associated types, so the real number of facts in scope is larger and, for recursive protocols, unbounded. In the other direction, a protocol that restates an equality of the protocol it refines is counted twice.
- **Bodies are not analysed.** The census shows which equalities are available, not which ones a body uses. How often transitivity or congruence is actually exercised can only be measured by a compiler; the Swift compiler could report it (requirement machine statistics) but nothing was executed here.
- **Style is a choice.** Swift and Rust are the model. The original Hylo standard library has one equality in 6,350 lines because its collections are barely generic over one another yet, not because Hylo code avoids equalities. A library that prefers type parameters to associated types would have fewer.
- **The benchmarks are translations, not ports.** The compiler cannot state equalities in traits, so each benchmark states in a where clause what Swift derives from a protocol, unrolled to the depth its body needs. The work measured is therefore the work for that finite set of givens. Bodies are reduced to equality checks; no member lookup, overload resolution or inference from the original bodies is exercised.
- **Four patterns, one binary.** The verdicts and counters are for `tc-bench` build `eq9-723cc0e6b0f8`. Times were taken on a shared machine and are indicative; the counters are exact and reproducible.

## 9. Files

| File | Contents |
|---|---|
| `census.py` | the counting script; `python3 -I census.py results` rewrites `results/` |
| `fetch_clones.sh` | fetches the five clones into `clones/` (not under version control) and lists the commits counted |
| `results/tables.md`, `results/summary.json` | all aggregated numbers |
| `results/files-*.csv` | per-file counts for each code base |
| `results/decls-*.jsonl` | one record per declaration: kind, name, requirements with their shapes, classes of equal terms, longest chain, equalities in scope |
| `benchmarks/*.hylo` | the four benchmarks |
| `benchmarks/gaps/*.hylo` | minimal programs for the missing features, with expected and observed behaviour |
| `benchmarks/generated/` | the false-claim, control and single-function copies written by the runner |
| `run_benchmarks.py` | runs everything under base, FIX and FULL; restartable; `--report-only` rewrites the table |
| `bench-results.jsonl`, `bench-results.md`, `bench-run.log` | raw records for the current files, the table, and the log of all runs (including runs of earlier versions of two files) |
