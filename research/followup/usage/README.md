# How much real code uses equality constraints

## The question

The equality machinery of the type checker (`eqsolve`, `eqmgu`, `absquotient`) never runs on the current standard library. The review could not say whether it is worth its complexity, because nobody had measured how much real code uses equality constraints. This directory measures it on comparable code bases, characterises the equalities found, and turns the most demanding real patterns into benchmarks for this compiler.

## Short answer

1. **Equality constraints are ordinary in comparable generic code.** The Swift standard library writes about 390 of them in 150,000 lines, or 2.6 per 1,000 lines (357 counted by the script, plus 32 of a form it misses). Between one generic declaration in six and one in five has one. swift-collections writes about 490 and the iterator part of the Rust core library 177, of which 96 are a single idiom (`R: Try<Output = Acc>`). The current Hylo standard library writes none, and the original Hylo standard library writes one.
2. **Most of the exposure comes from traits, not from where clauses.** 5% of the functions of the Swift standard library that have a body have an equality written in their own scope. 17% have one in scope once the equalities stated by the protocols they name are counted (`Collection` alone brings seven). In swift-algorithms it is 56%. These figures count equalities that are *available* in a scope. The census cannot tell how many bodies *use* one.
3. **A single where clause is shallow; a protocol signature is not.** A declaration with equalities has one at the median and two at the 99th percentile. Only six functions or extensions, out of about 1,000 that write an equality, write a chain of two. But the equalities of one protocol taken together form larger classes: four terms equal to `Index` in `Collection`, five in `StringProtocol`, and two recursive equalities in `Collection`. Every function over a `Collection` has these in scope.
4. **On the three benchmarks taken from Swift, the existing checker fails or is far slower, and `eqsolve` is the flag that changes this.** The existing checker (base) accepts one after 85 times the candidate matching of FIX, and wrongly rejects the other two after 1.5 million matches each. Adding only `eqsolve` to base makes all three accepted, in 5,000 to 29,000 matches. Removing only `eqsolve` from FIX makes two of them rejected again.
5. **Base also accepts false equalities.** Of the six plausible false claims added to the `Collection` benchmark, base reports two and accepts four. FIX and FULL report all six, at a cost of about 30 matches each.
6. **A false conformance with an equality condition is not decided by `eqsolve`.** The ordinary search then runs until the depth bound stops it: 45 times the matching of the valid program at the default depth of 10, and no answer within 60 s at depth 20.
7. **The fourth benchmark, from Rust's `Flatten`, is rejected by every configuration**, at the one line that uses a conformance with two equality conditions. `eqsolve` plays no part in that outcome.
8. **FULL does no better than FIX on these benchmarks**, because the candidate index is switched off in any scope that has an equality. These benchmarks give no evidence for or against `absquotient`. `absmodel` helps on one failing conformance (26 times less matching).
9. **The translation needed work-arounds.** Nine observations about associated types are listed in section 6. The patterns could only be written by restating in each where clause what a Swift protocol states once.

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

All five clones succeeded; none was refused by the network policy. `fetch_clones.sh` lists the commits. The clones were only read as text. Lines include comments and blank lines. The last code base includes 6,583 lines of unit tests (`tests.rs`).

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

The compiler tests (204 files, names resolved within each file) contain 12 equality requirements in 5 files: `positive/associated-type-equality.hylo` (4), `positive/coercion-derivability-cache.hylo` (3), `positive/equality.hylo` (3), `positive/conformance-via-equivalence.hylo` (1), `negative/associated-type-inequality.hylo` (1). Eight equate two parameters, three equate a parameter and a type, and one equates two associated types. Seven of the 60 traits have an associated type. No test has a conformance whose condition constrains an associated type. The per-file tables are `results/files-hylo-new-stdlib.csv` and `results/files-hylo-new-tests.csv`.

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
| **Equality requirements, as counted** | **0** | **12** | **1** | **357** | **527** | **22** | **177** | **15** | **72** |
| … distinct within each declaration | 0 | 12 | 1 | 357 | 491 | 22 | 177 | 15 | 72 |
| per 1,000 lines, as counted | 0 | 2.7 | 0.2 | 2.4 | 5.8 | 2.3 | 10.2 | 0.7 | 2.0 |
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

Four corrections apply to the equality counts of this table. They do not change the order of magnitude.

- **Missed.** The script does not read an extension of a protocol with an argument, such as `extension RawRepresentable<Bool> where Self: Encodable`, which states `RawValue == Bool`. `Codable.swift` has 32 of them. The Swift standard library therefore writes about 389 equalities, or 2.6 per 1,000 lines.
- **Counted twice.** In swift-collections, 36 equalities are written twice on the same declaration, once as `S: Sequence<Element>` and once as `where S.Element == Element`. The distinct count is 491. The preview modules of that package (`ContainersPreview`, `BasicContainers`) contribute 213 of the 527.
- **One idiom.** In Rust's iterators, 96 of the 177 equalities are `R: Try<Output = Acc>` on `try_fold` and the methods built on it. 65 bind `Item`.
- **Share of generic declarations.** In the Swift standard library, 41 of the 309 declarations with an equality are extensions of a protocol, which the script does not count as generic declarations. With them removed from the numerator the share is 17%, not 19%.

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

"All real code" is the six Swift and Rust columns, as counted. In the task's coarser classes: parameter == parameter 0%, parameter == concrete or constructed type 5%, associated type == concrete or constructed type 25%, associated type == associated type 20%, and the remaining 50% equate an associated type with a parameter (`S.Element == Element` in an extension of `Array`).

Two remarks on this table.

- **The split between concrete and constructed is unreliable for Rust.** 29 of the 46 Rust equalities classified "associated type == concrete type" have a reference to a parameter on the right (`&'a T`, `&'a Self`) and belong with "constructed". The sum of the two rows is not affected.
- **The zero in the first row is a property of the two languages, not of their users.** Rust has no syntax for an equality between two type parameters, and Swift warns that such a requirement makes the two parameters equivalent. The row says nothing about what Hylo users would write. What the table does show is that this compiler's tests exercise mostly a shape that the model libraries do not have (8 of 12), and exercise the dominant shapes, those with an associated type, once.

## 4. Characterisation

**Requirements per declaration.** Among declarations that have at least one conformance or equality requirement:

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Requirements: median / 95th / 99th percentile / maximum | 1 / 2 / 3 / 4 | 1 / 4 / 4 / 5 | 1 / 3 / 4 / 4 | 2 / 4 / 6 / 7 | 1 / 3 / 4 / 5 | 1 / 3 / 4 / 5 |
| Distinct equalities, where there is one: median / 95th / 99th / maximum | 1 / 1 / 2 / 2 | 1 / 2 / 2 / 3 | 1 / 1 / 1 / 1 | 1 / 2 / 2 / 2 | 1 / 2 / 2 / 2 | 1 / 1 / 1 / 2 |

Three declarations of swift-collections write three distinct equalities (`RangeReplaceableContainer.replaceSubrange`); no declaration writes more.

**Chains that need transitivity, within one declaration.** For each declaration, the equalities written on it and on its enclosing declarations were merged into classes of equal terms. A class of three terms needs a chain of two equalities to relate two of them.

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Declarations with a class of two terms | 512 | 500 | 50 | 264 | 16 | 102 |
| Declarations with a class of three terms (chain of two) | 6 | 1 | 0 | 1 | 1 | 1 |
| Declarations with a larger class | 0 | 0 | 0 | 0 | 0 | 0 |

Of the ten declarations with a chain of two, six are functions or extensions: `RangeSet.init(_:within:)` (`S.Element == C.Index, C.Index == Bound`, where the body passes an `S.Element` as a `Bound`), `AnyCollection.init(_: _Either<L, R>)` (`L.Element == Element, R.Element == Element`), one in swift-collections and three in Rust. The other four are associated type declarations inside a protocol (`Collection.Indices` and the three views of `StringProtocol`). The synthetic workloads used so far (`trans-8`, `assoceq-8`) have chains of eight; nothing like them was found in a single where clause.

**Classes within one protocol are larger.** The table above merges the equalities of one associated type declaration at a time. When all the equalities written in one protocol are merged, the largest classes in the Swift standard library are:

| Protocol | Largest class of equal terms, as written in the protocol |
|---|---|
| `SIMDScalar` | 7 terms: `Self` and the `Scalar` of six storage types |
| `StringProtocol` | 5 terms: `Index`, `String.Index`, `UTF8View.Index`, `UTF16View.Index`, `UnicodeScalarView.Index` |
| `Collection` | 4 terms: `Index`, `SubSequence.Index`, `Indices.Element`, `Indices.Index` |
| `_UnicodeEncoding` | 3 terms |

`StringProtocol` refines `Collection`, so its class of `Index` has eight terms in all. No protocol of swift-collections or of the Rust code has a class of more than two terms.

**Chains through traits are unbounded in principle.** In Swift, `C: Collection` brings the seven equalities of the protocols `Collection` and `Sequence` into scope, and two of them are recursive (`SubSequence.SubSequence == SubSequence`, `Indices.SubSequence == Indices`). A fact such as `C.SubSequence.SubSequence.Element == D.Iterator.Element`, used in the first benchmark, takes one congruence step and three equalities. Swift decides these with a completion procedure, because the set of derivable equalities is infinite.

**Congruence.** In no declaration does congruence identify two written terms that the written equalities do not already identify. What does occur is a projection of a term that an equality mentions: 112 declarations in the Swift standard library, 55 in Rust's iterators. The typical case is `extension Collection where SubSequence == Self`, whose body then uses `SubSequence.Index`. Whether congruence is needed is decided in function bodies, which this census does not analyse.

**Depth of projections.** In the Swift standard library, 263 equalities involve a projection of depth one (`S.Element`), 49 of depth two (`S.Iterator.Element`), one of depth three, and 44 none. Over all type expressions in the code, signatures and bodies, 1,207 projections have depth one, 163 depth two and one depth three.

**Different parameters.** 205 of the 1,170 equalities (18%) relate associated types of two different parameters. Another 584 (50%) relate an associated type to a parameter, as in `init<S: Sequence>(_ s: S) where S.Element == Element`. How many of these relate a parameter of the function to a parameter of the enclosing type was not counted.

**What is visible in a typical scope.** The first figure of each pair counts every function declaration; the second counts only those with a body, which leaves out the requirements declared inside protocols.

| | Swift stdlib core | swift-collections | swift-algorithms | Rust core iter | Rust core ops, slice | Rust alloc collections |
|---|---:|---:|---:|---:|---:|---:|
| Local givens of a function (own and enclosing requirements): median / 95th / 99th / maximum | 0 / 2 / 3 / 7 | 0 / 2 / 4 / 5 | 0 / 2 / 3 / 4 | 2 / 6 / 10 / 14 | 0 / 2 / 4 / 5 | 1 / 3 / 4 / 6 |
| Functions with a written equality in scope, all | 438 (6%) | 479 (12%) | 32 (8%) | 223 (24%) | 10 (1%) | 73 (4%) |
| … with a body | 319 (5%) | 463 (12%) | 32 (8%) | 210 (24%) | 10 (1%) | 73 (4%) |
| Functions with an equality in scope, counting those of the traits named, all | 1,250 (18%) | 634 (16%) | 235 (56%) | 263 (28%) | 19 (2%) | 75 (4%) |
| … with a body | 1,045 (17%) | 582 (15%) | 235 (56%) | 248 (29%) | 16 (2%) | 74 (4%) |
| Equalities in scope, counting those of the traits named: median / 95th / 99th / maximum, all | 0 / 7 / 15 / 44 | 0 / 3 / 9 / 18 | 1 / 14 / 16 / 22 | 0 / 3 / 4 / 5 | 0 / 0 / 2 / 2 | 0 / 0 / 2 / 4 |
| … with a body | 0 / 7 / 9 / 36 | 0 / 3 / 9 / 18 | 1 / 14 / 16 / 22 | 0 / 3 / 4 / 5 | 0 / 0 / 1 / 2 | 0 / 0 / 2 / 4 |
| Global givens (conformances declared in the module) | 1,193 | 596 | 163 | 355 | 326 | 539 |

"The traits named" means: for each requirement `T: P` in scope, and for `Self` in an extension of a protocol, the equalities written in `P` and in the protocols it refines, counted once per constrained type, without descending into the associated types. Of the 6,138 functions with a body in the Swift standard library, 607 have one to three equalities in scope, 291 have four to seven, 116 have eight to fifteen, and 31 have sixteen or more. The last group is the members of extensions of `StringProtocol` (18 each), functions over two or more collections (7 for each), and accessors declared inside protocols whose associated types are themselves constrained. One equality of `ExpressibleByStringInterpolation` is counted twice in these figures, because it is written in both branches of an `#if`. The most common values after zero are one, three and seven; seven is the signature of `Collection`.

A resolution in a module of this size therefore sees about a thousand global givens, a handful of local ones, and in about one function out of six between one and fifteen equalities.

## 5. Benchmarks from real patterns

The four files of `benchmarks/` each name their source in a comment. They state the equalities of the original declarations in where clauses, and check facts that the original bodies rely on, written as `need<A, B>()` with `fun need<A, B where A == B>() {}`.

| Benchmark | Source | Pattern | Equalities in the largest scope |
|---|---|---|---:|
| `swift-collection-signature.hylo` | Swift `Collection.swift:401-471`, `Sequence.swift:331` | the requirement signature of `Collection` for one and for two collections; recursive equalities; chains of up to three steps with congruence | 15 |
| `swift-string-protocol.hylo` | Swift `StringProtocol.swift:14-53` | the protocol with the most equalities in the library; associated types equated to concrete types | 16 |
| `swift-transitive-parameters.hylo` | Swift `RangeSet.swift:182`, `EitherSequence.swift:187`; swift-algorithms `Chain.swift:13` | the declarations with the longest written chains; a conditional conformance whose condition is an equality | 2 |
| `rust-flatten.hylo` | Rust `iter/adapters/flatten.rs` (the where clause of 11 impls), `iter/traits/collect.rs:291` | bindings nested two deep; a parameter that only an equality determines | 2 |

`run_benchmarks.py` runs each file under base, FIX and FULL with `--count`, one process at a time with a 60 s limit, and also three generated copies: the `// NEG:` lines enabled (plausible false claims that must be reported), a control in which every claimed equality is replaced by two equalities with a fresh type (all must be reported, and no message may contain the error type `#!`, which shows that every type of a claim resolves), and each function alone. The complete table is `bench-results.md`; the raw records are `bench-results.jsonl`.

`recheck/rerun.py` runs chosen files under other flag sets, depth bounds and time limits; its records are `recheck/recheck.jsonl` and its extra programs are in `recheck/p/`. The counters of the user module are deterministic: 26 points of `bench-results.jsonl` run a second time gave the same verdicts and the same counters. Times are from a shared machine and only indicative. A 60 s limit on that machine is not a property of the program: two base runs that were cut off at 60 s finished when given more time, and they are reported below with their real outcome.

### 5.1 The benchmarks as written (expected: accepted)

| Benchmark | Configuration | Verdict | `summon.calls` | `summon.matches` | `summon.layers` | `eqsolve.proved` | `eqsolve.refuted` | `eqmgu.solved` | Time, ms (indicative) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| swift-collection-signature | base | accepted | 147 | 811,287 | 879 | – | – | – | 46,011 |
| | FIX | accepted | 147 | 9,501 | 144 | 14 | 8 | 0 | 849 |
| | FULL | accepted | 147 | 9,501 | 144 | 14 | 8 | 0 | 1,010 |
| swift-string-protocol | base | **rejected** (12 messages on 5 lines) | 166 | 1,575,190 | 706 | – | – | – | 47,015 |
| | FIX | accepted | 161 | 10,824 | 155 | 10 | 3 | 0 | 917 |
| | FULL | accepted | 161 | 10,749 | 154 | 10 | 3 | 0 | 1,268 |
| swift-transitive-parameters | base | **rejected** (1 error) | 40 | 1,549,133 | 190 | – | – | – | 45,341 |
| | FIX | accepted | 39 | 2,461 | 49 | 8 | 0 | 0 | 103 |
| | FULL | accepted | 39 | 2,236 | 46 | 8 | 0 | 0 | 92 |
| rust-flatten | base | crash (stack overflow) | | | | | | | |
| | FIX | **rejected** (1 error) | 45 | 13,841 | 56 | 3 | 0 | 142 | 588 |
| | FULL | **rejected** (1 error) | 45 | 13,841 | 56 | 3 | 0 | 142 | 418 |

- **`eqsolve` decides every claim of the three Swift benchmarks.** It proves between 8 and 14 equalities per file, and `eqsolve.untrusted` is 0, which means it never handed a goal back to the ordinary search.
- **Base wrongly rejects `swift-string-protocol`.** Five of its eight claims are reported (lines 80 to 84), with the messages "expression does not denote a type" and "ambiguous use of 'Index'": under base the type expressions `S.SubSequence.Index`, `S.Indices.Element` and three others do not resolve. Under FIX and FULL the same expressions resolve, as the control shows. In the 60 s run of `bench-results.jsonl` this point was cut off; the row above is from a run with a 600 s limit.
- **Base wrongly rejects `swift-transitive-parameters`.** The error is on `needSequence<Chain2<A, B>>()`: the conformance of `Chain2` requires `A.Element == B.Element`, which follows from `A.Element == X` and `B.Element == X`. Base stops after two searches reach the depth bound (`summon.depthExhausted` = 2) and 1.5 million candidate matches (`generated/swift-transitive-parameters.fn-chainUse.hylo`). With the bound lowered to 6 it gives the same error after 9,502 matches, so the 1.5 million are the price of the default bound, not of the answer. This is the Chain2Sequence pattern of swift-algorithms.
- **`rust-flatten` is rejected by FIX and FULL at one line**, `needIterator<Flatten<I>>()`. Section 6 gives two possible causes. The three equalities of the body are proved. Without that line and the conformance, base accepts the file too, in 3,931 matches against 1,265 for FIX (`recheck/p/flatten-no-conformance-use.hylo`).
- **Most of what FIX does on these files is resolving the where clauses, not checking the claims.** With every statement of the bodies removed (`recheck/p/*.empty-bodies.hylo`), FIX still does 7,272 of the 9,501 matches of the first benchmark, 8,548 of the 10,824 of the second and 1,839 of the 2,461 of the third. The ten claims of the first benchmark cost FIX 2,229 matches. They cost base 791,885 (811,287 less the 19,402 of its signatures), which is 355 times more.
- **The first benchmark gives two points for the number of equalities in scope, and no growth law.** The function with 7 equalities takes base 29,870 matches and FIX 3,104; the function with 15 takes base 781,417 and FIX 6,397. The two functions check different claims (six and four), and most of the FIX figures is signature resolution.

### 5.2 Which flag makes the difference

FIX is eight flags. The table gives the verdict and `summon.matches` when `eqsolve` alone is added to base, and when `eqsolve` or `eqmgu` alone is removed from FIX.

| Benchmark | base | base + `eqsolve` | FIX − `eqsolve` | FIX − `eqmgu` | FIX |
|---|---|---|---|---|---|
| swift-collection-signature | accepted, 811,287 | accepted, 29,201 | accepted, 344,958 | accepted, 9,501 | accepted, 9,501 |
| swift-string-protocol | rejected (12), 1,575,190 | accepted, 24,648 | rejected (1), 216,316 | accepted, 10,824 | accepted, 10,824 |
| swift-transitive-parameters | rejected (1), 1,549,133 | accepted, 5,343 | rejected (2), 34,790 | accepted, 2,461 | accepted, 2,461 |
| rust-flatten | crash | crash | rejected (1), 14,146 | rejected (2), 177,492 | rejected (1), 13,841 |

- **`eqsolve` is sufficient and necessary for the three Swift benchmarks.** Added alone to base, it turns the two wrong rejections into acceptances and divides the matching of the first benchmark by 28. Removed alone from FIX, it brings back two wrong rejections (one by the candidate budget, "implicit resolution is too complex"; one by the depth bound) and multiplies the matching of the first benchmark by 36. The other flags of FIX account for the remaining factor of two to three between base + `eqsolve` and FIX.
- **`eqmgu` changes nothing on the three Swift benchmarks.**
- **`eqsolve` plays no part in the outcome of `rust-flatten`.** Base + `eqsolve` still overflows the stack. Base + `occurs` does not crash but does not finish in 60 s. Base + `eqmgu` gives the same single error as FIX after 17,526 matches. Without `eqmgu`, FIX gives up through the candidate budget instead of the depth bound, after 13 times more matching.

### 5.3 False claims (expected: one error per claim)

| Benchmark with `// NEG:` lines enabled | Claims | base | FIX | FULL | `summon.matches` FIX / FULL | `eqsolve.refuted` | `eqsolve.untrusted` | `eqmgu.solved` |
|---|---:|---|---|---|---:|---:|---:|---:|
| swift-collection-signature | 6 | **2 errors** (2,752,954 matches, 300 s limit) | 6 errors | 6 errors | 9,693 / 9,693 | 20 | 0 | 0 |
| swift-string-protocol | 5 | out of memory (300 s limit) | 5 errors | 5 errors | 11,108 / 11,033 | 13 | 0 | 0 |
| swift-transitive-parameters | 6 | out of memory (300 s limit) | 6 errors | 6 errors | 112,196 / 111,821 | 8 | 462 | 284 |
| rust-flatten | 3 | crash | 3 errors (+1) | 3 errors (+1) | 13,844 / 13,844 | 6 | 0 | 142 |

- **Base accepts false equalities.** Given 300 s, base finishes the first file and reports two of the six false claims. Each of the three false claims of the function `one` was then checked alone (`recheck/p/one-false-*.hylo`):

  | False claim | base | FIX |
  |---|---|---|
  | `C.SubSequence == C.Indices` | **accepted**, 133,628 matches | rejected, 2,277 matches |
  | `C.Indices.Element == C.SubSequence.Element` | **accepted**, 34,899 matches | rejected, 2,601 matches |
  | `C.Element == C.Index` | rejected, 294,738 matches | rejected, 2,358 matches |

  Which of the known soundness problems of base is responsible was not determined; adding `occurs` alone does not change the two acceptances.
- **Rejecting a false equality is cheap when `eqsolve` decides it.** Six false claims add 192 matches to the first benchmark, about 30 each, which is 2% of the file.
- **Rejecting a false conformance that has an equality condition is expensive under FIX and FULL alike, and its cost is set by the depth bound.** The two false claims `needSequence<Chain2<A, X>>()` and `needSequence<Chain2<B.Iterator, A>>()` raise the matching of the third benchmark from 2,461 to 112,196. `eqsolve` reports `untrusted` 462 times, which hands the goals to the ordinary search; `eqmgu` runs 284 times and four searches reach the depth bound. The rejection is therefore a search that was cut off, not a refutation. With the bound raised from 10 to 20, FIX does not finish the file in 60 s. `absmodel` refutes five goals here and the total barely changes.
- **The controls** report the expected number of errors (20, 18, 4, and 2 plus the known failure) with no `#!` in any message. They cover the types of the `need` claims; the arguments of the `check`, `insert` and `needSequence` calls are not covered by a control.

### 5.4 The candidate index and the abstract model

- **The index is switched off in any scope that has an equality.** `recheck/p/index-under-equality.hylo` and `index-under-equality-2.hylo` check the same conformance goal, `Box<Box<A>> is Q`, in a function without an equality and in a function with one equality that the goal does not need. Without the equality, FIX does 220 matches and FULL 7 (`index.skipped` = 204). With it, FIX and FULL both do 296 (`index.unavailable` = 70). In a file with both functions, the index is lost only in the second (`index-mixed-scopes.hylo`).
- **This is why FULL equals FIX on the benchmarks.** FULL does the same matching as FIX on the first and the fourth, and 1% and 9% less on the second and the third, where `absmodel` refutes one and three goals. The gain that `index` gives on today's standard library does not carry over to scopes with equalities.
- **`absmodel` helps on one failing conformance; `absquotient` does not contribute to it.** `gaps/unsatisfiable-conformance.hylo` takes 11,322 matches under FIX and 441 under FULL, and overflows the stack under base. FIX + `absmodel` alone gives 441, FULL − `absmodel` gives 11,180, and FULL − `absquotient` gives 441.

## 6. Features that the translation needed and the compiler lacks

Each item has a minimal program in `benchmarks/gaps/` with the expected and the observed behaviour in its header. The verdicts are the same under base, FIX and FULL unless stated. "Expected" is what the source language does; whether each difference is a defect or an intended restriction of this compiler was not established from its code.

| File | What real code does | What happens here |
|---|---|---|
| `trait-equality.hylo` | A protocol states equalities between its associated types (`where Iterator.Element == Element`). 39 equalities are written this way in the Swift standard library. | The form tried, a trait member `given A == B`, is a syntax error ("expected 'is'"). No other way to state it was found in the compiler's tests. The benchmarks restate the equalities in each where clause. |
| `trait-given-not-used-for-lookup.hylo` | `S.Iterator.Element` for `S: Sequence`. | The `given Iterator is IteratorProtocol` of the trait is not used to look up `Element`; the type is `#!` unless the function restates `S.Iterator is IteratorProtocol`. |
| `inherited-associated-type.hylo` | `C.Element` for `C: Collection`, where `Element` is declared by `Sequence`. | The type is `#!`. |
| `error-type-accepted.hylo` | – | A type expression that does not resolve is not reported, and two unresolved types are compatible, so the program is accepted without a diagnostic. "Accepted" therefore does not show that a program's types were resolved; this is why the benchmarks have a control. |
| `where-clause-order.hylo` | Rust writes `Item = U::Item` before `U: Iterator`. | A where clause is resolved left to right: "type 'U' has no static member 'X'". |
| `generic-projection.hylo` | `<IntoIter<A> as Iterator>::Item` is `A`. | An associated type defined by a generic conformance is not reduced, and `VecIter<A>.Item` is not accepted as a type expression. |
| `associated-type-premise.hylo` | `extension Range: Sequence where Bound: Strideable, Bound.Stride: SignedInteger`. 44 of the 207 conditional conformances of the Swift standard library and 46 of the 285 of Rust's iterators have a condition on an associated type or an equality. | In this program the conformance is not found, with an abstract or a concrete argument. The search stops after two layers without reaching a bound. |
| `two-equality-conditions.hylo` | `impl<I, U> Iterator for FlattenCompat<I, U> where I: Iterator<Item: IntoIterator<IntoIter = U, Item = U::Item>>, U: Iterator`. | Under FIX and FULL a conformance with the two conditions `I.InnerIter == U` and `I.InnerItem == U.Item` is not found although its conditions are exactly the givens in scope; with either condition alone it is found. The search does not conclude: it reaches the depth bound (14,020 matches), and with the bound raised to 20 it reaches the candidate budget (419,045 matches). Without `eqmgu` it reaches the budget at the default bound (162,459 matches). The failure is therefore not specific to `eqmgu`. Base does not finish in 60 s. |
| `restated-conformance.hylo` | Swift derives `C.SubSequence.SubSequence: Collection` from `SubSequence.SubSequence == SubSequence`. | If the program states that conformance, FIX and FULL reject `C.SubSequence.SubSequence.Index == C.Index` (`eqsolve.refuted` = 2), because the stated conformance is a second witness and the projections through the two witnesses are different types; base accepts. Without the restated conformance all three accept. It is a trap for anyone porting Swift code. |

Two further files are controls. `equality-determined-parameter.hylo` has a conformance with a parameter that only an equality determines. Every configuration accepts it: base in 807 matches, FIX without `eqmgu` in 586, FIX in 291 (`eqmgu.solved` = 1). `eqmgu` halves the work there and is not needed for the answer. `unsatisfiable-conformance.hylo` is described in section 5.4.

## 7. What the numbers imply

**How often will a Hylo type checker meet equalities once its standard library reaches the size of Swift's?** If Hylo's library is written in the style of Swift's or Rust's, then:

- about 2 to 6 equality requirements are written per 1,000 lines, which is 300 to 500 in a library of that size;
- between one generic declaration in six and one in five carries one;
- an equality is in scope in 5% to 12% of the functions of the three Swift libraries if only written requirements count (24% in Rust's iterators), and in 15% to 56% if the equalities of traits count. For Hylo they will count: an equality that a trait states has to become a given wherever the trait is assumed, whether the language lets the trait state it or forces each function to restate it.

So roughly one function in six of such a standard library, and most functions of a generic algorithms library, would be checked with equalities in scope. Two consequences follow with different strength.

- *Measured:* in those scopes the present candidate index is switched off (section 5.4), so the cost of every resolution there is that of FIX, not of FULL.
- *Not measured:* how many of those bodies contain a goal that needs the equality procedure. `eqsolve` runs when a goal `A ~ B` arises, not because an equality is in scope. The census counts scopes, not goals.

The statement of the review that none of these behaviours "occurs in today's code" is true only because today's code has no trait with an associated type.

**How demanding is it?** Less than the synthetic workloads suggest in one respect, and more in another.

- Less: within one where clause, chains are short (two equalities at most, in six declarations) and a declaration writes one or two equalities. The scaling workloads with eight chained equalities do not resemble any single where clause.
- More: a protocol signature brings classes of four to eight terms and recursive equalities, and the number of equalities simultaneously in scope is 7 for any function over a `Collection`, 9 at the 99th percentile of the Swift standard library and 36 at the maximum. On the benchmarks built from those signatures, base wrongly rejects two of three valid programs and accepts four of six false claims, so it cannot be the checker of such a library.

**What this says about each technique.**

- `eqsolve`: supported by these benchmarks. Added alone to base it is enough to accept the three Swift benchmarks, and FIX without it fails two of them. It also rejects the false equalities that base accepts, at about 30 matches each. It does not decide a conformance goal whose condition is an equality: there it answers `untrusted` and the ordinary search runs, bounded only by depth or budget.
- `eqmgu`: not shown to be needed. It changes nothing on the three Swift benchmarks. On the control with a conformance parameter determined by an equality it halves the matching, and the program is accepted without it. On the `Flatten` pattern (31 of the 285 conditional conformances of Rust's iterators have an equality condition; none of the 207 of the Swift standard library) the program is rejected with and without it; with it the failing search ends sooner.
- `absmodel`: one supporting point, a failing conformance that it refutes in 26 times less matching. It does not help the costly false conformance of section 5.3.
- `absquotient`: no evidence either way. No measurement here changes when it is removed.
- `index` and the other result-preserving techniques: they stop helping when an equality is in scope. If one function in six has equalities in scope, an index that works under equalities (for example on the representatives of the equality classes) becomes more valuable than it looks today.

**What to do first.** This part is a judgement, not a measurement. The benchmarks could only be written by restating in every where clause what a protocol would state once, and the pattern from Rust could not be made to type-check at all. A reasonable order is: let traits state equalities and use the conformances of associated types for lookup, reduce projections through generic conformances, support conditions on associated types, and report unresolved types. Then the benchmarks of this directory can be rewritten without restating anything, and they will measure the equality procedure on the givens that a real library produces. Two items concern the equality machinery itself and can be examined now: the search that does not conclude on a conformance with two equality conditions, and the cost of rejecting a false conformance with an equality condition.

## 8. Limits

What the experiment cannot show:

- **How often equality reasoning is used.** The census counts the equalities available in a scope. Whether a body relies on one, and whether it needs transitivity or congruence, can only be measured by a compiler. The Swift compiler could report it (requirement machine statistics); nothing was executed here.
- **The cost on real bodies.** The benchmarks reduce bodies to equality claims. No member lookup, overload resolution or inference from the original bodies is exercised, and under FIX three quarters of the measured matching is signature resolution.
- **A growth law.** There are two points for the number of equalities in scope (7 and 15), from functions that check different claims. Nothing can be fitted to them.
- **The behaviour of base beyond its limits.** Four base runs ended by a crash or by lack of memory, and their answer is unknown. The 60 s verdicts of base in `bench-results.md` depend on the load of the machine: two of them changed when the limit was raised.
- **The value of `absquotient`,** and of `absmodel` beyond one program.
- **Whether the failures of section 6 are defects.** "Expected: accepted" for the `Flatten` pattern is a judgement from the fact that the conditions of the conformance are the givens in scope. The checker's code was not traced.
- **Which soundness problem makes base accept false equalities.**
- **What Hylo users will write.** Swift and Rust are the model. The original Hylo standard library has one equality in 6,350 lines because its collections are barely generic over one another yet. A library that prefers type parameters to associated types would have fewer.
- **Other versions of the checker.** The verdicts and counters are for `tc-bench` build `eq9-723cc0e6b0f8`, with the default depth bound of 10 and budget of 100,000 unless stated. Several outcomes are set by those bounds.

Limits of the census:

- **It is lexical.** Declaration heads are found by keyword and cut with bracket matching. Independent counts agree with it to within a few percent: a separate regular expression finds 305 `==` inside the where clauses of the Swift standard library (census: 312), and 172 first bindings of the form `Trait<Name = …>` in Rust's iterators (census: 177 with second bindings and without type definitions). It has not been compared with the output of a compiler.
- **Known miscounts.** Extensions of a protocol with an argument are missed (32 in the Swift standard library). A requirement written twice on a declaration is counted twice (36 in swift-collections). Both branches of an `#if` are counted. Protocol requirements without a body are counted as functions unless stated.
- **Classification is by spelling.** Type aliases are not expanded, so a bare name that is an alias is classified by a name table and can be wrong (`Element` of a dictionary, a tuple, is taken for an associated type). Rust references to a parameter are classified as concrete. Nested types with the same simple name (`Iterator`, `IntoIter`, `Index`) are merged in the per-type counts for Rust, which inflates "extensions per type" there.
- **Templates and macros are counted once.** Swift `.gyb` files and Rust `macro_rules!` bodies are counted as written, not per expansion. Rust's numeric code is mostly macros, so the Rust numbers outside the iterator module are lower bounds.
- **Implied equalities are counted one level deep, by spelling.** The equalities of the traits named are added without following associated types, so the real number of facts in scope is larger and, for recursive protocols, unbounded. The requirements of a generic type are not carried to its extensions, which undercounts.
- **The benchmarks are translations, not ports.** The compiler cannot state equalities in traits, so each benchmark states in a where clause what Swift derives from a protocol, unrolled to the depth its body needs. The work measured is the work for that finite set of givens.

## 9. Files

| File | Contents |
|---|---|
| `census.py` | the counting script; `python3 -I census.py results` rewrites `results/` |
| `fetch_clones.sh` | fetches the five clones into `clones/` (not under version control) and lists the commits counted |
| `results/tables.md`, `results/summary.json` | all aggregated numbers, as counted |
| `results/files-*.csv` | per-file counts for each code base |
| `results/decls-*.jsonl` | one record per declaration: kind, name, whether it has a body, requirements with their shapes, classes of equal terms, longest chain, equalities in scope |
| `benchmarks/*.hylo` | the four benchmarks |
| `benchmarks/gaps/*.hylo` | minimal programs for the missing features, with expected and observed behaviour |
| `benchmarks/generated/` | the false-claim, control and single-function copies written by the runner |
| `run_benchmarks.py` | runs everything under base, FIX and FULL with a 60 s limit; restartable; `--report-only` rewrites the table |
| `bench-results.jsonl`, `bench-results.md`, `bench-run.log` | raw records for the current files, the table, and the log of all runs (including runs of earlier versions of two files) |
| `recheck/rerun.py` | runs chosen files under any flag set (`base+eqsolve`, `FIX-eqmgu`, …), depth bound and time limit; appends to `recheck/recheck.jsonl` |
| `recheck/recheck.jsonl` | raw records, with every counter and message, for sections 5.2 to 5.4, the long base runs and the depth-bound runs |
| `recheck/p/*.hylo` | the extra programs: benchmarks with empty bodies, single false claims, the index pair, reductions of `rust-flatten` |
