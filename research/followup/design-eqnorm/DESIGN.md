# Equality by normalization: design and verdict

For the engineer who will implement this in `/home/user/hylo-impl/Sources/FrontEnd`. Functions are named as they are in `Typer/Typer.swift`; that file changes between sessions, so every hook is given by function name and by the existing lines it sits next to, never by line number.

**Status.** This document was written before any of it was compiled. Stage 1 (`eqindex`, `eqeager`) has since been implemented in the compiler (commits 4e7a2aa and f49136d; binary `eq15-f2809c746ab9`). An adversarial review then ran that binary and read the design against the source. It found three defects in stage 1 as first implemented, and several corrections to stages 2 and 3. The corrections are made in place below, each marked "(review)"; section 11 lists them with the evidence and gives the recommendation. **Stage 1 must not become a default before the four corrections of step 4b (section 8) are made.**

## 0. Verdict

**Do not rewrite types to canonical representatives. Keep the congruence closure, and move it to where the equalities arise: inside `match`.**

- Rewriting types when they enter a scope, as Swift's requirement machine does, is neither simpler nor safe in this checker. Hylo selects a conformance by the *spelling* of the type: with `T == U`, `T is P` and `U is P` in scope, `T.X` and `U.X` are different types, and a compiler test requires it (section 3.3). A representative erases the spelling that resolution needs.
- The useful part of normalization is something else: an equality between two closed types should be *decided* at the moment two types are compared, and should never become a hypothesis that the search proves later. This needs no representative, so nothing can leak into inferred types, witnesses or diagnostics.
- This can be done in stages. The first stage is about 140 lines and uses the existing `solveEquality` unchanged. Its intended property is: every program accepted by the current `FULL` configuration is accepted with the same witnesses, and resolutions that `FULL` abandons at the depth bound may succeed. As first implemented it does not have this property: two programs accepted by `FULL` are rejected (`tests/attack-01`, `attack-04`), and the gain is lost inside the initializer of a binding (`attack-05`). The corrections are in 5.1 and 5.2. Even corrected, a resolution that newly succeeds can change which extension or overload is selected (`attack-10`), so "only rejected programs change" is not guaranteed; no program that shows such a change was found.
- Later stages add a closure cached per scope, which makes the test exact and complete for closed types, and class matching for types with unification variables. They change which conformance is selected in programs that are accepted today, sometimes with no diagnostic (`tests/rank-06`, `attack-07`), and stage 3 meets the question of spelling again (`attack-08`). They should wait for the designers' answers to questions 1 and 4.
- It does not deliver the reduction hoped for in `REVIEW-AND-PLAN.md` ("200 lines replace 700"). The end state has more code than today (about +530 −260, section 8). What changes is behaviour: three kinds of valid programs that are rejected today are accepted, the index of givens stays enabled in scopes with equalities, and the syntactic filter `canDeriveCoercions` leaves the common path.

What each existing mechanism becomes:

| Mechanism | After stage 1 | After stages 2 and 3 |
|---|---|---|
| `fixsubst` | still needed (same rule, applied in the new path too) | needed only for pairs with unification variables on the old path |
| `eqsolve` (`solveEquality`) | unchanged, called earlier | unchanged as the source of proofs and penalties; its closure is also cached per scope as a decision oracle |
| `eqmgu` | unchanged | unchanged (it answers equality *goals* `?v ~ X`; nothing here replaces it) |
| `absquotient` | unchanged | unchanged in behaviour; can share the closure code |
| `canDeriveCoercions` | unchanged | bypassed for closed pairs; kept for pairs with variables and for scopes with non-ground equality givens |
| index special case (`coercionSources`) | removed for ground equalities (`eqindex`), unless a given in sight or the goal is an alias at its root | same |
| built-in symmetry and transitivity in the search | unchanged | reached only when `solveEquality` does not apply |

## 1. The problem

All verdicts below were obtained with `/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench`; `base` is the existing checker, `FULL` has every technique. The programs are in `tests/`, each with its current verdict recorded in a comment. Raw results: `tests/current.jsonl`.

### 1.1 Each equality between parts costs one search step

```hylo
trait P {}
struct W<X0, X1, X2, X3, X4, X5, X6, X7> {}
fun need<V where V is P>() {}
fun f<T0, ..., T7, U0, ..., U7 where T0 == U0, ..., T7 == U7, W<T0, ..., T7> is P>() {
  need<W<U0, ..., U7>>()
}
```

`tests/gain-01-wide-given.hylo`. Valid: the two types are equal argument by argument.

| | Verdict | Counters |
|---|---|---|
| base | out of memory | – |
| FULL | **rejected** | `summon.depthExhausted=1 eqsolve.proved=16 summon.matches=176` |

`match` finds eight differing arguments, assumes eight equalities, and the search proves them one per layer. With the root step and the coercion step that is 11 layers; the bound is 10. Six arguments are accepted, eight are not. The same happens for a value of type `W<T0, ..., T9>` passed where `W<U0, ..., U9>` is expected (`tests/gain-02-wide-value.hylo`). `eqsolve` made each equality cheap to prove; it did not stop each one from being a search step.

### 1.2 Only the innermost mismatch is ever considered, and a syntactic filter decides which pairs may be tried

```hylo
struct Box<T> { public memberwise init }
fun check<T>(x: T) {}
fun f<A, B, C where Box<A> == C, A == B>(x: C) { check<Box<B>>(x) }   // C == Box<A> == Box<B>
```

`tests/gain-04-congruence-then-fact.hylo`: rejected by base and by FULL (`summon.matches=1`), with "cannot pass value of type 'C' to parameter 'Box<B>'". The closure of `eqsolve` proves `C ~ Box<B>`, but it is never asked: `canDeriveCoercions` refuses the pair because `Box<B>` is not, up to renaming, a side of an equality in scope.

```hylo
fun f<A, B where Box<A> == Box<B>, Box<A> is P>() { need<Box<B>>() }
```

`tests/gain-03-compound-equality-in-given.hylo`: rejected by both. Unification descends to `(A, B)`, which is not provable (there is no injectivity), and the enclosing pair `(Box<A>, Box<B>)`, which is a stated fact, is never tried.

```hylo
trait Collection { type Element }
given <T> => Box<T> is P {}
fun f<T, A where T is Collection, T.Element == Box<A>>() { need<T.Element>() }
```

`tests/gain-06-projection-equal-to-concrete.hylo`: rejected by both. An associated type stated equal to a concrete type does not get the conformances of that concrete type, because the pair `(Box<?t>, T.Element)` contains a unification variable and `canDeriveCoercions` compares sides up to renaming only. The failure needs a *generic* conformance of the concrete type (review): with `T.Element == I` and `given I is P`, `need<T.Element>()` is accepted today, by base and by FULL (`experiments/review/r1`). So `where Element == Int` works; `where Element == Array<Int>` with a conformance of `Array<T>` for every `T` does not.

### 1.3 One equality in scope switches the index of givens off

`tests/cost-01-index-under-equality.hylo` has 40 conformances and a function `f<A, B where A == B>` that uses each once; `cost-02` is the same without the where clause.

| FULL | Verdict | `summon.matches` | `index.fallback` |
|---|---|---:|---:|
| without `where A == B` | accepted | 1640 | 0 |
| with `where A == B` | accepted | 4480 | 40 |

`indexedSummon` gives up as soon as the scope has any "coercion source". The index is the technique that gives the largest gain on real code; it is lost in exactly the scopes that use equalities.

### 1.4 What must not change

```hylo
trait P { type X }
fun check<T>(x: T) {}
fun f0<T, U where T == U, T is P, U is P>(x: U.X) { check<T.X>(x) }   // rejected: T.X is not U.X
fun f2<T, U where T == U, T is P, U is P, T.X == U.X>(x: U.X) { check<T.X>(x) }   // accepted
```

`tests/keep-01-two-witnesses.hylo` and `keep-02`, from the compiler tests `negative/associated-type-inequality` and `positive/associated-type-equality`. Both configurations give these verdicts. The trace shows why: the goal `P<U>` is answered by the given spelled `U is P` in one layer, before the given `T is P` seen through `T == U` can complete.

## 2. Where an equality is consumed today

Found by reading the code; the experiments named in the last column confirm the behaviour on the binary (programs in `experiments/` and `tests/`).

| Place | What happens | Checked by |
|---|---|---|
| `match` | Unifies the given's type with the goal. The handler passed to `TypeStore.unifiable` records every mismatching pair and answers "coercible", so only the *innermost* mismatches are recorded. A single mismatch at the root is a failure, **unless one of the two types is a type alias at its root** (review): the test is `(x == a) && (y == b)` on the types `match` started from, and unification strips aliases before it calls the handler, so the recorded pair is not recognized as the root and the equality of the two whole types is assumed like any other. Each pair must pass `canDeriveCoercions`; the pairs are then assumed (`environment.assuming(givens:)`), the witness is wrapped in a `.builtin(.coercion)` node of type `a ~ b`, and the assumptions are proved later, last first, by `threadContinuation` → `summon`. The proofs of the parts are **not** stored in the witness. | traces of `rank-01`, `gain-01`; `attack-01`, `attack-03` |
| `summon` (inner) | A closed equality goal goes to `solveEquality`; `?v ~ X` to `mostGeneralEqualityThread`; anything else to the search with the built-in reflexivity, symmetry and transitivity givens. | `keep-05`, `keep-13` |
| `coerced` | A value coercion first tries syntactic unification. Otherwise it starts a thread that matches the value's type against the expected type (nested equalities, as in `match`), and, if `canDeriveCoercions` allows, a second thread that assumes the equality of the two whole types. Only this root equality keeps its proof term. | `s1`–`s6`, `gain-02`, `gain-04` |
| `canDeriveCoercions` | A filter: each side of the pair must be equal *up to renaming* (`Typer.unifiable`, which is α-equivalence, not unification) to a side of some equality given or hypothesis. A side in which a unification variable occurs inside a compound type can only coincide with a side of a hypothesis, so in practice such pairs are rejected; so is a closed pair that needs a congruence step. | `gain-04`, `gain-05` |
| `applies` | Extension applicability is a `match` of the extended type against the receiver, so equalities work in nested positions (`extension Box<A>` applies to `Box<T>` when `T == A`) and not at the root (`extension A` does not apply to `T`). With an alias the root works too (review): given `type AA = A`, `extension AA` applies to `T`, and `extension A` applies to a receiver declared with an alias of `B` when `A == B` follows from the scope. An extension applies only if the resolution has exactly one result (`uniqueElement`); a resolution that fails, for any reason including the depth bound, silently removes the extension from the candidates. | `keep-24`, `experiments/m2`, `attack-03` |
| `resolve(_:inheritedMemberOf:...)` | Trait members and associated types are found by `summon(P<T, ?...>)`, hence through equalities. | `lang-02` |
| `typeOfImplementation` | `T.X` through a coerced witness strips the coercion (`asCoercionApplication`): with `T == U` and only `U is P`, `T.X` and `U.X` are the same type `(U::w).X`. This is the one place where the checker already normalizes. | `keep-03` |
| `resolve(_:nativeMemberOf:)` | No equality is used: with `T == A`, the members of `A` are not found on a value of type `T`. | `lang-01` |
| Solver, `solve(equality:)` | Purely syntactic unification. Every flow of a value that I tried (argument, return, `inout`, initialization, inferred generic argument) is a `CoercionConstraint` and reaches `coerced`. Widening constraints simplify to syntactic equalities; I did not find a program in which that loses an equality, and did not search exhaustively. | `experiments/s1`–`s6` |
| `indexedSummon`, `givenIndex` | The index is abandoned if the scope has any coercion source, or the environment any equality hypothesis. | `cost-01` |
| `abstractModel`, `equalityOpaqueTypes` | A second congruence closure of the scope's ground equalities, to mark opaque constructors. | `keep-22` |

Three facts about the present language and checker matter for the design:

- **Every equality given that can be written today is ground.** Equalities come only from where clauses, whose types mention rigid generic parameters. `given X == Y` inside a trait is a syntax error ("expected 'is'"; `experiments/t2`). Non-ground equalities exist only as *hypotheses*: the premises of a generic given while its parameters are still unification variables. The review tried three more forms: `given <T> => T == A` at the top level and `given <where X is P> => X == Y` in a trait are syntax errors, and `given let w: X == Z` in a trait is "declaration is not allowed here". A where clause on a local given (`given <where T == U> => Box<T> is P {}` in a function body, `keep-14`) gives a hypothesis that is a *closed* equality.
- **A failed resolution is not an error by itself** (review). `applies` and overload resolution treat it as "this candidate does not apply". A resolution abandoned at the depth bound fails silently; one abandoned by `budget` reports an error. A change that makes a failing resolution succeed, or fail differently, can therefore change the verdict of a program that is accepted today.
- **Later phases do not read equality proofs.** In `IR/IREmitter.swift`, `_emit(witness:)` reaches `default: fatalError()` for a `.builtin` head, so a coerced witness cannot be lowered yet, and nothing else outside the type checker inspects a `.coercion` node (mangling handles the *type* `EqualityWitness` only). I read this; I did not run the emitter.

## 3. What "canonical form" would mean, case by case

### 3.1 Rigid generic parameters

`T == U`: a class `{T, U}`. Any choice of representative decides the equality. The choice becomes visible as soon as a representative is bound to a unification variable or used to pose a goal (3.3).

### 3.2 Type applications, tuples, arrows

Congruence without injectivity: `Box<A> == Box<B>` when `A == B`, and not the converse (`tests/keep-11`). A canonical form is computed bottom-up: canonicalize the arguments, then look the result up in the signature table. For this to be well defined the representative of a class must be a member of minimal size, otherwise canonicalizing a representative can loop through another class.

Without injectivity, matching a pattern with variables has several answers: with `Box<A> == Box<B>`, `Box<?t>` matches the class with `?t := A` and with `?t := B`, and these are not equal. A single canonical form returns one of them. Swift avoids this by making concrete type constructors injective (open question 3).

### 3.3 Associated types qualified by a witness

`T.X` is `(T::w).X`, where `w` is the witness expression of `T is P`. Two different witnesses give different types even when the conforming types are equal (`keep-01`), and a witness defined in an inner scope is not the global one (`keep-17`: with `T == A`, a local `T is P` and a global `A is P { type X = A }`, `T.X` is not `A`). In the closure such a projection is an atom; it is equal to something only through a stated fact.

This is what rules out rewriting. If `T` and `U` are rewritten to one representative `R` before resolution:

- the goal `P<R>` has two candidates, `T is P` and `U is P`, at the same layer and with the same penalty: `keep-02` becomes ambiguous and is rejected, although it is a positive compiler test;
- to repair this, resolution must prefer the given "as the user wrote the type", which is the information the rewriting removed.

Swift can normalize because it assumes coherence: one conformance per type and protocol, so `T.X` and `U.X` *are* equal when `T == U`. Whether Hylo wants that is open question 1. The comment in `negative/associated-type-inequality.hylo` says it does not.

### 3.4 The trait's own `Self.X`

`TypeStore.unifiable` lets an abstract projection `(Self::abstract).X` unify with any `(T::w).X` whose qualification types are coercible. `solveEquality` narrows this: `Self.X` equals `(T::w).X` only if `w` is the only ground conformance in scope for a type equal to `Self`, decided from the scope's givens alone. The rule is a function of the scope, so it can be cached with the scope's closure. I keep it unchanged (open question 2).

### 3.5 Hypotheses

A hypothesis is an assumed given of a `ResolutionThread.Environment`. There are three sources: the premises of a given (`formThread`), the part equalities of a coerced match (`match`), and the root equality of `coerced`. All are discharged by `threadContinuation`, in the same scope, in the environment made of the hypotheses assumed before them.

Consequence (argument in 6.2): if a derivation completes, every equality hypothesis it used is a theorem of the scope's theory. So a closed equality can be decided against the scope alone. Hypotheses matter in two cases only, and both stay on the existing path:

- a hypothesis with unification variables (`?T ~ ?U` of a generic given);
- a projection through a premise that is still pending, `(T::$k).X` (soundness problem 3). `solveEquality` resolves the premise ahead of time. This depends on the environment and cannot be cached per scope.

### 3.6 Nested scopes

An inner scope sees the equalities of the outer ones plus its own (`keep-18`), and a sibling scope must not see them (`keep-19`). The closure of the inner scope is not an extension of the outer one that could be shared by mutation, and the `Self.X` rule is not monotonic (a conformance added in the inner scope can retract a merge). So: one closure per scope that declares givens, built from all the equality givens visible from it, exactly like `givenIndex(visibleFrom:)`.

### 3.7 Generic or conditional equalities

None can be declared today (section 2). They will appear when traits can state equalities between associated types (`where Iterator.Element == Element`), as a given of type `<Self> P<Self> ==> (Self::P).A ~ (Self::P).B`. The present code reacts badly to that: such a given is visible from every scope that sees the trait, and it makes `solveEquality` answer "not applicable", `equalityOpaqueTypes` return `nil`, and the index fall back, in all of them.

In a closure-based design the natural treatment is instantiation: when a projection through a witness `w : P<T>` enters the closure, add the trait's equalities instantiated at `w`. Termination is the difficulty (`SubSequence.SubSequence == SubSequence` creates a new witness at each instantiation); it is the reason Swift moved from this scheme to Knuth–Bendix completion. This design does not solve it. It leaves a place for it (5.3, `node`), and a counter that reports when a non-ground equality given is first seen.

## 4. Options

### A. Rewrite types to representatives when they enter a scope

What the task describes. Types are hash-consed globally and declared types are memoized per declaration, so there is no place where a type "enters" a scope: the rewriting has to be applied where goals are posed (`summon`, `coerced`, `applies`, `resolve(_:inheritedMemberOf:...)`), where a given's type is read (`formThread`, `givenIndex`, `abstractClause`), where the solver compares (`solve(equality:)`), and where projections are built (`typeOfImplementation`).

- Code: about 250 to 350 lines: closure with representatives (150), canonicalization (40), call sites (60), a table from canonical to written types for diagnostics (30), ranking by written spelling (unknown).
- New invariants:
  - every type compared in a scope has been normalized for that scope; a missed site is a spurious rejection, silently;
  - the order that picks representatives is total, minimal by size, and independent of declaration order;
  - representatives are unobservable. This one is false today (3.3): they change which conformance is selected.
- Verdicts: changes `keep-02` unless spelling-based ranking is added; makes `lang-01` accepted (members of `A` on `T == A`), which may or may not be wanted.
- Rejected, unless the designers choose coherence (open question 1), in which case it becomes the right design and stages 2 to 4 below should be dropped for it.

### B. Canonicalize inside `match` only

Normalize the given's type and the goal just before unifying them. This avoids the global invariant. It keeps the other two: unifying canonical forms binds unification variables to representatives, which then appear in later goals (`Q<?t>` is posed for the representative, not for the type the user wrote) and in diagnostics. About 200 lines. Rejected for that leak.

### C. Decide, do not rewrite (chosen)

Unify the types as written. For each mismatching pair of closed types, ask whether the scope's theory makes them equal, immediately. If yes, the match succeeds with the same coerced witness as today and no hypothesis. If no, let unification try the enclosing pair. Unification variables are bound from the written types, so no representative exists anywhere.

- Stage 1 needs no new data structure: the question is asked to `solveEquality`.
- Stage 2 caches the closure per scope so that the question is cheap enough to replace `canDeriveCoercions`.
- New invariants: three for stage 1 (6.1), each checked in `selfcheck` mode.
- Cost in code: section 7.

### D. Leave everything as it is

Costs nothing. Keeps the problems of section 1, of which 1.1 and 1.3 need no language decision to fix.

## 5. The design

Five flags, declared in `Typer/TyperCounters.swift` like the existing ones:

```swift
/// Keep the index of givens in scopes whose coercion sources are ground equalities.
nonisolated(unsafe) public static var eqindex: Bool = enabled.contains("eqindex")

/// Decide the equalities between closed mismatching parts inside `match` instead of assuming
/// them (requires `eqsolve` and `fixsubst`).
nonisolated(unsafe) public static var eqeager: Bool = enabled.contains("eqeager")

/// SEMANTIC CHANGE: decide closed pairs with a congruence closure cached per scope, in place of
/// `canDeriveCoercions`, trying enclosing pairs when a nested one is refuted (requires `eqeager`).
nonisolated(unsafe) public static var eqclosure: Bool = enabled.contains("eqclosure")

/// SEMANTIC CHANGE: match a type with unification variables against the members of the
/// equality class of a closed type (requires `eqclosure`).
nonisolated(unsafe) public static var eqclass: Bool = enabled.contains("eqclass")

/// SEMANTIC CHANGE: a match through equalities costs a constant; equality proofs are opaque.
nonisolated(unsafe) public static var eqrank: Bool = enabled.contains("eqrank")
```

### 5.1 Stage 1a, `eqindex`: keep the index under ground equalities

**Why it is valid.** The index skips a given whose nominal head differs from the goal's. Such a given can match only if unification coerces the pair of the two head constructors, or the pair of the two whole types. A pair of constructors passes `canDeriveCoercions` only if each is, up to renaming, a side of an equality. `match` does not coerce the pair of the whole types when neither is an alias at its root (section 2). So the index is valid when no equality has a type constructor that takes arguments as a side, **and neither the given's type nor the goal is a type alias at its root** (review).

The second condition was missing in the first implementation, and `nominalHead` looks through aliases. `tests/attack-01`: a given of type `AA` (`type AA = A`) is filed under `A` and skipped for the goal `B`, although it matches `B` through `T == A, T == B`. `FULL` accepts the program; `FULL` + `eqindex` on binary eq15 rejects it, and `selfcheck` reports "the index skipped a for B, which matches". Conformance givens have a type of the form `P<...>` and are not affected; a given binding declared with an alias type is.

**Data.** In `GivenIndex`:

```swift
/// `true` iff every coercion source is a ground equality neither side of which is a trait or a
/// generic struct or enum without arguments.
var coercionSourcesAreRigid = true

/// `true` iff the head of some given is a type alias (review). `match` may then coerce the whole
/// type of that given to a goal with another head.
var hasAliasHead = false
```

**Hook 1**, in `givenIndex(visibleFrom:)`, at

```swift
        if context.parameters.contains(where: { (p) in p.erased == head })
          || program.types.isEquality(head)
        {
          ix.coercionSources.append(g)
        }
```

add inside the `if`:

```swift
          if !isGroundEquality(gt) || hasConstructorSide(head) { ix.coercionSourcesAreRigid = false }
```

where `hasConstructorSide` dealiases both sides of the `EqualityWitness` and returns `true` if one is a `Trait`, or a `Struct` or `Enum` whose declaration has a non-empty `parameters` list.

**Hook 1b (review)**, in the same loop, after `let (context, head) = program.types.contextAndHead(gt)`:

```swift
        if program.types[head] is TypeAlias { ix.hasAliasHead = true }
```

**Hook 2**, in `indexedSummon`, replace the condition of

```swift
    guard let ix = givenIndex(visibleFrom: scopeOfUse), ix.coercionSources.isEmpty else {
      TyperCounters.bump("index.fallback")
      return nil
    }
```

by

```swift
    ix.coercionSources.isEmpty
      || (TyperExperiments.eqindex && ix.coercionSourcesAreRigid
          && !ix.hasAliasHead && !(program.types[u] is TypeAlias))       // last two: review
```

The test on the environment that follows (fall back if a hypothesis is an equality) stays. The flag `hasAliasHead` is coarse (one such given anywhere in sight turns `eqindex` off for the scope), which is acceptable because givens with an alias type are rare; the finer alternative is to add the alias-headed entries to the candidates of every head. With no coercion source the index keeps looking through aliases, as today: then no pair is coerced at all.

**Hook 3.** The existing `selfcheck` test in `indexedSummon` (counter `selfcheck.index.confirmed`) already verifies that each skipped candidate fails to match. It must run in this new case too; nothing to add if it is placed after the guard. It is this check that exposes `attack-01`.

About 20 lines. No verdict changes, once Hook 1b and the two added conditions of Hook 2 are in.

### 5.2 Stage 1b, `eqeager`: decide closed parts inside `match`

**Idea.** When every mismatching pair is closed, ask `solveEquality` now the question that the search would ask it later, with the environment it would have then. If all are proved, continue with the same coerced witness, the summed penalties and no new hypothesis. If one is refuted, the match fails. If `solveEquality` does not apply to one, do exactly what is done today.

**Data.** Two fields, so that the thread completes at the same layer as today without the waiting layers counting against the depth bound.

```swift
// In ResolutionThread:
/// The number of layers the thread waits before its next step (`eqeager`).
let delay: Int            // new parameter of `init`, default 0; `copy` passes 0

// In ResolutionThread.Environment:
/// The number of layers that this thread and its ancestors spent waiting (`eqeager`).
var credit = 0
```

`credit` must be copied wherever an `Environment` is built from another one, next to the existing copies of `ancestry` and `log`: `assuming(givens:)`, `assuming(given:)`, the `fixsubst` block of `match`, and `threadContinuation`. The environments built in `solveEquality` (premise resolution) and `.empty` start a new resolution and keep 0.

**Hook 1**, in `match`, between the loop that fills `gs` and the comment `// If yes, assume non-syntactic equalities between pairwise nested parts.`:

```swift
    if TyperExperiments.eqeager,
      let r = eagerlyCoerced(thread, to: b, assuming: gs, keeping: substitutions, in: scopeOfUse)
    {
      return r
    }
```

**New function.**

```swift
  /// Returns the step following a match of `thread` to `b` up to the equalities `parts`, having
  /// decided them now, or `nil` if they must be assumed and proved by search.
  ///
  /// - Requires: `parts` are the equalities recorded by `match`, in order.
  private mutating func eagerlyCoerced(
    _ thread: ResolutionThread, to b: AnyTypeIdentity, assuming parts: [AnyTypeIdentity],
    keeping substitutions: SubstitutionTable, in scopeOfUse: ScopeIdentity
  ) -> ResolutionThread.Advanced? {
    // The conditions under which `summon` would have reached `solveEquality` for each part
    // without doing anything else that is observable.
    if !TyperExperiments.eqsolve || !TyperExperiments.fixsubst || (selfCheck == .equality) {
      return nil
    }
    if hasImplicitOnStack() || !pendingGivenChecks.isEmpty { return nil }      // review, see below
    if parts.contains(where: { (p) in p[.hasVariable] }) { return nil }

    var e = ResolutionThread.Environment(
      substitutions: thread.environment.substitutions.union(substitutions),
      givens: thread.environment.givens,
      nextGivenIdentifier: thread.environment.nextGivenIdentifier)
    e.ancestry = thread.environment.ancestry
    e.log = thread.environment.log
    e.credit = thread.environment.credit + parts.count

    // Search discharges `parts[i]` while `parts[..<i]` are still assumed.
    var cost = 0
    var refuted = false
    for i in parts.indices {
      switch solveEquality(parts[i], in: scopeOfUse, where: e.assuming(givens: Array(parts[..<i]))) {
      case .notApplicable: return nil
      case .refuted: refuted = true
      case .proved(_, let c): cost += TyperExperiments.eqsolveCost ? c : 0
      }
    }
    if refuted { return .next([]) }
    TyperCounters.bump("eqeager.matches")
    TyperCounters.bump("eqeager.parts", by: parts.count)

    let t = demand(EqualityWitness(lhs: thread.witness.type, rhs: b)).erased
    let w = WitnessExpression(
      value: .termApplication(.init(value: .builtin(.coercion), type: t), thread.witness),
      type: b)
    return .next([
      ResolutionThread(
        matching: w, to: b, in: e, then: thread.tail,
        penalties: thread.penalties + cost, delay: parts.count)
    ])
  }
```

Notes on the code:
- The parts are tested with `hasVariable` on the types as recorded, not after reification. This is what makes the call identical to the later one: a hypothesis whose recorded type has a variable makes `solveEquality` inapplicable today.
- The loop does not stop at the first refutation, because an inapplicable part must send the whole match to the existing path.
- The witness and its type are the ones `match` builds today at `let t = demand(EqualityWitness(lhs: a, rhs: b)).erased`.
- `e` keeps the bindings of the match. That is the `fixsubst` rule; `eqeager` assumes `fixsubst` is on (the new path has no unsound variant to preserve).
- **The stack condition (review).** The first implementation gives up when `declarationsOnStack` is not empty. The declaration of a local binding is on the stack while its initializer is typed, so `let r = need<W<U0, ..., U7>>()` gets nothing from `eqeager` while `return need<W<U0, ..., U7>>()` does: `tests/attack-05` is rejected and `attack-06` accepted on binary eq15. The only thing `summon` does before `solveEquality` that depends on the stack is `recordSkippedGivens`, and it records only givens that are on the stack: its `skipped` function returns a declaration only for a `.user(d)` given with `d` in `declarationsOnStack`, and every such `d` is a conformance declaration or a `given`/`using` binding, which is what `hasImplicitOnStack()` tests. So the condition is `hasImplicitOnStack()`, as written above. Assert in `selfcheck` mode: when `eagerlyCoerced` proceeds, `recordSkippedGivens` called for each part appends nothing to `pendingGivenChecks`.
- The self-check counter `eagerDecisions` of the implementation is incremented after the loop, for refuted matches too; that is right, since a refutation is also a decision to verify.

**Hook 2**, in `takeSummonResults`, at

```swift
    while done.isEmpty && !work.isEmpty && (depth < maxImplicitDepth) {
      var next: [ResolutionThread] = []
      for item in work {
        switch match(item, in: scopeOfUse) {
```

the loop becomes

```swift
    func bound(_ ts: [ResolutionThread]) -> Int {
      TyperExperiments.eqeager
        ? maxImplicitDepth + (ts.lazy.map(\.environment.credit).max() ?? 0) : maxImplicitDepth
    }
    while done.isEmpty && !work.isEmpty && (depth < bound(work)) {
      var next: [ResolutionThread] = []
      for item in work {
        if item.delay > 0 { next.append(item.waiting()); continue }       // same thread, delay - 1
        if depth - item.environment.credit >= maxImplicitDepth { continue } // out of steps
        switch match(item, in: scopeOfUse) {
```

With no credit anywhere this is the existing loop: same exits, same counters.

**Two corrections to this loop (review).**

1. *The budget past the depth bound.* A thread with credit runs past layer `maxImplicitDepth`. Up to that layer the frontier with `eqeager` is never larger than without (a waiting thread stands for the thread that proves a part; a match with a refuted part dies earlier), so `budget` fires with `eqeager` only if it fires without. Past it, the run without `eqeager` has stopped and returned nothing, silently; the run with `eqeager` goes on, and a search that does not terminate grows until it exceeds the budget, which reports an error. `tests/attack-04`: a conditional extension whose premise diverges through `A == B`. `FULL` stops after three steps of the divergent search (frontier 6561), the extension does not apply, another one does, and the program is accepted. With `eqeager` on binary eq15 the search goes one or two steps deeper (59049 subgoals of ten candidates each with the index: frontier 590490; about 600000 without the index, one step earlier) and the program is rejected with "implicit resolution is too complex". So the test that follows `depth += 1` becomes:

   ```swift
      } else if TyperExperiments.budget && done.isEmpty
        && work.count > TyperExperiments.budgetLimit
      {
        if depth > maxImplicitDepth {
          // Without `eqeager` this resolution ended at the depth bound, silently (review).
          TyperCounters.bump("eqeager.budgetPastDepth")
          exhausted = true
        } else {
          TyperCounters.bump("summon.budgetExhausted")
          reportResolutionBudgetExhausted(in: scopeOfUse)
        }
        work = []
      }
   ```

   This keeps the property "what `FULL` accepts is accepted". It does not bound the extra work below the budget: on `attack-04` with five branches instead of nine (no budget error in either run), `summon.subgoals` goes from 931 to 3906 and `eqsolve.proved` from 775 to 3900. A resolution that fails at the depth bound today can cost up to `budgetLimit` threads per layer afterwards.

2. *The counter.* `summon.depthExhausted` is bumped when `depth == maxImplicitDepth` with work left, which now happens in resolutions that go on and succeed: `gain-01` is accepted on eq15 with `summon.depthExhausted=1`. The counter (and `lastResolutionExhaustedDepth`, which the self-check reads) must mean "ended without result because of the bound". Set a local `exhausted` in the loop when a thread is dropped by `depth - credit >= maxImplicitDepth`, or when the loop condition fails on `depth` with work left, or in case 1 above; after the loop, `if done.isEmpty && exhausted { bump; lastResolutionExhaustedDepth = true }`. Without `eqeager` this bumps in the same resolutions as today.

**Why `delay` and `credit` rather than nothing.** The first layer at which any thread completes decides the result (`while done.isEmpty`). Today a coerced match with `n` parts completes `n + 1` layers after its match. If the new thread completed immediately, two givens that both match through equalities, with different numbers of differing parts, would finish together; with equal penalties that is an ambiguity where today the one with fewer parts wins (`tests/rank-05`). `delay: parts.count` makes the thread resume at the layer where the last part would have been proved (checked against the 4-layer trace of `rank-05` and the 10-layer trace of `gain-01`). `credit` keeps the waiting from counting as steps; that is the whole gain.

**Hook 3, self-check.** The three callers of `takeSummonResults` on a fresh resolution (`summon(_:in:)`, `coerced`, `applies`) go through a helper that, when `selfcheck` and `eqeager` are on and `selfCheck == .none`, runs the resolution a second time with a private switch that makes `eagerlyCoerced` return `nil`, and compares the two lists of `(witness, penalties)` after erasing the names of unification variables. A difference is a `selfCheckViolation`, except when the second run ended by the depth bound (then the first is allowed to have results). About 25 lines. (In the implementation the check is inside `takeSummonResults` itself and runs when `eagerDecisions` changed during the call.)

This check compares results only. It did not see `attack-04` (both runs return nothing; the difference is a diagnostic) and cannot see a difference in cost. Add to it (review): a flag set where `reportResolutionBudgetExhausted` is called; a violation if the first run set it and the second run, given the same budget, did not.

About 115 lines in all.

### 5.3 Stage 2, `eqclosure`: a closure cached per scope, used as the exact test for closed pairs

Stage 1 still asks `canDeriveCoercions` first, and calls `solveEquality` only for pairs that pass it. `solveEquality` cannot replace the filter as it is: each call walks every visible given to collect the facts, and `match` runs for every candidate given. Stage 2 gives the decision a cache.

**Data.**

```swift
/// A congruence closure of ground equalities between closed types (`eqclosure`).
internal struct EqualityClosure {
  private var nodes: [AnyTypeIdentity] = []          // dealiased
  private var index: [AnyTypeIdentity: Int] = [:]
  private var shapes: [String?] = []                  // nil for atoms
  private var children: [[Int]] = []
  private var parent: [Int] = []
  private var uses: [[Int]] = []
  private var table: [EqualitySignature: Int] = [:]

  /// Returns the node of `t`, adding it and its subterms if needed.
  mutating func node(_ t: AnyTypeIdentity, in types: inout TypeStore) -> Int
  /// Merges the classes of `i` and `j` and restores closure under congruence.
  mutating func merge(_ i: Int, _ j: Int)
  /// Returns the representative node of the class of `i`.
  func find(_ i: Int) -> Int
}

/// The equalities of a scope (`eqclosure`).
internal struct ScopeEqualities {
  /// The scope's facts closed under congruence (the `p0` of `solveEquality`).
  var facts = EqualityClosure()
  /// `facts` plus the bindings of abstract projections (rule of section 3.4).
  var theory = EqualityClosure()
  /// The ground conformances of the scope, for the rule of abstract projections.
  var conformances: [(head: AnyTypeIdentity, concept: AnyTypeIdentity, witness: WitnessExpression)] = []
  var ambiguousConcepts: Set<AnyTypeIdentity> = []
  /// The values of the witnesses of the scope's givens, to recognize premise projections.
  var visibleValues: Set<WitnessExpression.Value> = []
  /// `true` iff the scope has no equality fact at all.
  var isTrivial = true
}
```

`node`, `merge` and `find` are the code that is in `solveEquality` today between the comments `// Build the term graph.` and `// Close under congruence, with a signature table and use lists (Nelson-Oppen).`, moved without the edges. One change: `node` must work after merges have happened. When it creates a compound node it computes the signature from the current classes of the children; if the table has it, the new node is merged into that class, otherwise it is inserted, and it is added to the use lists of the classes of its children. Adding a node never merges two existing classes, so earlier answers stay valid.

**Building.** `scopeEqualities(visibleFrom:) -> ScopeEqualities?` follows `givenIndex(visibleFrom:)` line for line: return `nil` while `declarationsOnStack` is non-empty; forward to the parent if the scope declares no given; read `cache.scopeToEqualities`; otherwise build and store. Building:

```
for g in the visible givens (ix.coercionSources when the index is available, else all):
    if g can prove anything (<T> T), or is an equality that is not ground:
        bump "eqclosure.nonground"; return nil          // every caller then takes the existing path
    if g is a ground equality l ~ r:
        isTrivial = false
        merge node(l), node(r) in `facts` and in `theory`
collect `conformances`, `ambiguousConcepts`, `visibleValues` exactly as solveEquality does under
    "An abstract projection `(Self::P).X` is equal to ..."
```

`nil` is cached as well (a second dictionary or an optional value), so a non-ground scope pays once.

**Deciding.**

```
mutating func decide(x, y, in scope) -> Bool?       // nil: not decidable here
    guard let s = scopeEqualities(visibleFrom: scope) else return nil
    if x or y has a variable, an error, or a projection through a premise
        (qualification `.assumed`, or `.reference` not in s.visibleValues): return nil
    if dealiased(x) == dealiased(y): return true
    if s.isTrivial and x, y contain no abstract projection:
        return (x or y contains a type of a kind that `node` does not model) ? nil : false   // review
    add x and y to s.facts and s.theory
    for each abstract projection node created in s.theory by this call:
        apply the rule of 3.4 using the classes of s.facts; merge in s.theory if it gives a binding
    write s back to the cache
    if s.theory.find(node(x)) == s.theory.find(node(y)): return true
    return s.theory.hasUnmodelledNode ? nil : false                                      // review
```

**Unmodelled kinds (review).** `solveEquality` treats a type of a kind it does not model (a universal type, an implication, an opaque type, ...; the `default` case of its `node`, flag `unmodelled`) as an atom, and then does not trust its own refutations: it answers "not applicable" and search decides. `decide` must do the same, or it refutes pairs that search would accept, and the argument of 6.2 fails. `EqualityClosure.node` sets `hasUnmodelledNode` in that same `default` case; the flag covers every node of the closure, the facts included, exactly as `unmodelled` does. The self-check of Hook 3 would not have shown the omission, because it skips the pairs for which `solveEquality` is not applicable.

The place for future trait-level equalities is the same as for abstract projections: the creation of a projection node.

**Hook 1**, in `match`. The existing statements

```swift
    var substitutions = SubstitutionTable()
    var coercions: [(AnyTypeIdentity, AnyTypeIdentity)] = []
    let unified = program.types.unifiable(a, b, extending: &substitutions) { (x, y) in
      coercions.append((x, y))
      return true
    }
```

become, when `eqclosure` is on and `environmentIsPlain(thread.environment)` (no hypothesis that is an equality with a variable, or that can prove anything; otherwise `solveEquality` would not apply and today's path must be kept):

```swift
    var refuted = Set<Memos.TypePair>()
    var substitutions = SubstitutionTable()
    var coercions: [(AnyTypeIdentity, AnyTypeIdentity)] = []
    var unified = false
    while true {
      substitutions = .init()
      coercions = []
      let r = refuted
      unified = program.types.unifiable(a, b, extending: &substitutions) { (x, y) in
        if (x == a) && (y == b) { return false }        // root rule: the whole types are never coerced
        if r.contains(.init(x, y)) { return false }     // the enclosing pair is asked next
        coercions.append((x, y))
        return true
      }
      if !unified { return .next([]) }
      let n = refuted.count
      for (x, y) in coercions where decide(x, y, in: scopeOfUse) == false {
        refuted.insert(.init(x, y))
      }
      if refuted.count == n { break }
    }
```

followed by the existing code. Today `unifiable` can only fail on an occurs check at the root, because the handler always answers `true`; here it also fails when the root pair is reached, which is the case that the existing test `coercions.uniqueElement, (x == a), (y == b)` rejects, extended to the case where other pairs were recorded first. The handler only reads a local set, so there is no access to `self` during unification. Each round refutes at least one pair, and a refuted pair makes unification ask about a strictly larger one, so the number of rounds is bounded by the depth of the types; in the common case of a failing candidate it is two.

Then, in the loop that fills `gs`, a pair for which `decide` answered `true` skips `canDeriveCoercions`:

```swift
    for c in coercions {
      if (decided[.init(c.0, c.1)] == true)
        || canDeriveCoercions(c.0, c.1, in: scopeOfUse, where: thread.environment)
      {
        gs.append(demand(EqualityWitness(lhs: c.0, rhs: c.1)).erased)
      } else {
        return .next([])
      }
    }
```

(`decided` remembers the answers of the last round.) Stage 1 then takes over: the pairs are proved by `solveEquality` for their penalties, which now happens only for candidates that match.

Shortcut for scopes without equalities, which is every scope of the standard library: if the scope's equalities are trivial and the environment has no equality hypothesis, a refuted pair cannot be rescued by an enclosing one (equality is identity), so `match` returns `.next([])` after the first round. That is today's outcome (`canDeriveCoercions` finds no source) for one unification and no cache lookup.

A sub-unification that fails may leave bindings in `substitutions` (`unifiable` has no rollback; today its handler never answers `false`). This is sound: a pair is accepted only if it is closed and equal, or by the existing path; a stale binding can make an enclosing pair with variables fail where another binding would have succeeded. Stage 3 removes the limitation for the pairs it handles.

Three properties of this loop that the implementer must know (review):

- *The root test keeps the alias behaviour of today.* `(x == a) && (y == b)` compares with the types `match` started from, so when `a` or `b` is an alias at its root the pair of the whole types is recorded and decided like a nested one, as today (`attack-01`, `attack-03` keep their verdicts). Do not "fix" the test by stripping aliases inside this change: that would change those verdicts, and whether it should is open question 5. Assertion A1 of `eqindex` depends on the same fact.
- *Pairs recorded inside a pair that is then refuted stay in the list.* With `Pair<A, C>` against `Pair<B, D>` nested somewhere, `(A, B)` true and `(C, D)` refuted, the second round records `(A, B)` and then the enclosing `(Pair<A, C>, Pair<B, D>)`. The first is redundant. Removing it by comparing types would be unsound (the same two types can be a required pair at another position), so it stays. The consequences are a part more in the `delay` and the penalty of the match, so a ranking that differs from the one a minimal set of parts would give; and, when the redundant pair is false, one more round (it is refuted in turn, and the next round does not record it).
- *Arguments after a refuted pair are not visited.* `unifiable` stops at the first failing argument, so in `G<C, ?t>` against `G<D, A>` with `(C, D)` refuted, `?t` is not bound, while in `G<?t, C>` against `G<A, D>` it is. In both cases the enclosing pair has a variable and takes the existing path. The result of the round loop for pairs with variables therefore depends on argument order until stage 3.

**Hook 2**, in `coerced`, at `if canDeriveCoercions(root.type, goal, in: scopeOfUse, where: .empty) {`: the condition becomes `decide(root.type, goal, in: scopeOfUse) ?? canDeriveCoercions(...)`. The body is unchanged: the root equality is still assumed and proved by `solveEquality`, so it keeps its proof term.

**Hook 3**, self-check: whenever `decide` returns a non-`nil` answer and `solveEquality` applied to the same pair in the same environment is not `.notApplicable`, the two must agree.

**Sharing the code (optional, after the stage is validated).** `solveEquality` and `equalityOpaqueTypes` each contain their own copy of the graph construction and of the closure. Both can build an `EqualityClosure` instead. `equalityOpaqueTypes` cannot reuse the cached *instance*: it merges abstract and concrete projections freely, on purpose, because the abstract model must over-approximate the search, which uses the liberal rule of `TypeStore.unifiable` whenever `solveEquality` does not apply. It needs a closure built with that rule (a parameter of `node`).

About 255 lines added (steps 5 and 6 of section 8), about 110 removed if the sharing is done.

### 5.4 Stage 3, `eqclass`: pairs with unification variables

For a recorded pair `(x, y)` in which `x` has unification variables and `y` is closed (or the converse), with the scope's closure available:

```
candidates = the members m of the class of y in `theory` that are subterms of the scope's facts
             (nodes created while the closure was built, not by a later `decide`) and have the
             shape of x (same constructor, labels and arity); every such member, in the order of
             the nodes                                                                  // review
for each candidate m:
    unify x with m, extending a copy of the substitutions made before this pair,
        with the same handling of nested pairs (closed: decide; with variables: recursively)
    on success: one thread, as in stage 1, with the penalty of the proof of m ~ y added
no candidate: the match fails
```

This is E-matching against a ground closure, and it is complete up to the scope's equalities for pairs with one closed side. Several candidates give several threads; if more than one completes, with the same penalties, the result is an ambiguity, which is the honest answer when constructors are not injective. It replaces `canDeriveCoercions` for these pairs.

**The candidate set (review).** The first version took "the members of the class, one per distinct tuple of argument classes". Both halves are wrong for this checker.

- The cached closure grows with every pair that `decide` is asked about. If the candidates are "the members of the class", a type compared earlier in the scope (`Box<B>`, congruent to the stated `Box<A>`) becomes a candidate, and the bindings of a match depend on which other expressions were checked before it. The candidates must be the members written in the where clauses: `EqualityClosure` records the number of nodes at the end of building, and only nodes below it are candidates. This is also what 5.6 promises for diagnostics.
- Two members with equal arguments, `Box<A>` and `Box<B>` with `A == B`, are not interchangeable: binding `?t` to `A` or to `B` sends a later goal `?t is Q` to `A is Q` or to `B is Q`, which are different witnesses with different associated types (section 3.3). Keeping "one per tuple of argument classes" picks one by node order, that is, by the order of the where clause. `tests/attack-08` would be accepted or rejected depending on that order. So every written member is a candidate. When two of them complete, the program is ambiguous. That is strict; it is the same strictness as `keep-01`, and only coherence (question 1) removes it.

So stage 3 does not escape the question of spelling: it chooses a spelling for `?t`. It is safe to implement only with the "every written member" rule, and it then rejects as ambiguous some programs that a user would expect to be accepted (`where T.Element == Box<A>, U.Element == Box<B>, A == B, T.Element == U.Element` and a need for `P<T.Element>` from `given <X> => Box<X> is P`: two results that differ only in a type argument). It needs the substitutions as they were before the failed sub-unification, so the round loop of stage 2 must record them (or `unifiable` must restore them when a sub-unification fails; one line at each of its two `return result || areCoercible(a, b)`).

Pairs with variables on both sides stay on the existing path. About 100 lines (section 8). Changes verdicts: `gain-05`, `gain-06`.

### 5.5 Stage 4, `eqrank`: remove the emulation (needs a decision)

Stages 1 to 3 reproduce two accidents of the search because the results must not change without a decision: the penalty of an equality proof (it depends on the side on which a where clause states the equality: `rank-01` is accepted, `rank-02` rejected, and they differ in `A == C` against `C == A`) and the number of layers it takes. If the designers accept the rule

> a given that matches the goal as written is preferred to one that matches through equalities; among the latter, only the lexical distance of the given counts,

then a coerced match adds a constant to the penalties, `delay` and `credit` go away (the thread continues at the next layer), `eagerlyCoerced` stops calling `solveEquality` for costs, and the proof of an explicit equality goal can be the opaque form that `equalityStep` already uses for congruences. `EqualityEdge`, the Dijkstra search, `equalityStep`, `symmetryWitness` and `transitivityWitness` are deleted: about 150 lines removed, 10 added. `rank-01`, `rank-03` and `rank-05` become ambiguous.

### 5.6 Diagnostics

No type is rewritten at any stage. A diagnostic prints the types the constraint was created with, as today. The only new types that can reach a message are bindings made by stage 3, and they are members of a class as written in a where clause.

### 5.7 Laziness and cost

- Stage 1a: nothing at run time; one test per coercion source when an index is built.
- Stage 1b: in a resolution that completes within the depth bound, no more calls to `solveEquality` than today (each call replaces one that the search would make, unless the thread dies first; then it is extra, bounded by the number of parts that passed `canDeriveCoercions`). In a resolution that today ends at the depth bound, more (review): the search continues until every thread has taken `maxImplicitDepth` steps of its own or the budget is exceeded. Measured on the five-branch variant of `attack-04`: `eqsolve.proved` 775 → 3900, `summon.subgoals` 931 → 3906. Each call to `solveEquality` walks every visible given, so this is the expensive kind of work. In the standard library no resolution takes more than 5 layers (`followup/census.json`), so nothing changes there; how many resolutions of the corpus end at the depth bound was not counted for this review.
- Stage 2: a closure is built the first time a closed pair must be decided in a scope with an equality in sight; never for a scope without one (`isTrivial` is known from `ix.coercionSources`). Building is `O(F log F)` for `F` facts. A decision hashes the two types and their subterms once, then is two lookups. Memory per scope: the subterms of the facts, plus the closed types that were compared there. Nothing is cached while a declaration is being typed, as for the index.
- The standard library has no equality: every scope is trivial, and the only cost is the flag tests.

## 6. Why it is correct

### 6.1 Stage 1

**`eqindex`.** Argument in 5.1. Assumptions:
- A1. `match` fails on a single mismatch at the root **when neither type is an alias at its root** (review; false without the condition, `attack-01`). Assert: in `match`, if `eqindex` and the two types have different nominal heads, the result is `.next([])` (this is the existing `selfcheck.index` test).
- A2. `canDeriveCoercions(k, k')` is false for two distinct constructors when no equality side is a constructor. Same assertion. From stage 2 the same holds of `decide`: a constructor is an atom of the closure, and an atom leaves its singleton class only through a fact of which it is a side.

**`eqeager`.** Claim: with `eqeager`, every resolution returns what it returns without, except that it may return results where the other run stopped at the depth bound; and no resolution reports an error that the other run does not report (review: the second half needs the budget rule of 5.2; `attack-04`).

The claim is about one resolution. It does not extend to programs (review): a resolution that fails without `eqeager` and succeeds with it can add a candidate to a member lookup or to an overload set (section 2, third fact). In `tests/attack-10` an extension applies with `eqeager` that did not apply before, next to one that already did; the program stays accepted, and nothing says which of the two is now called. The review did not find a program that this turns from accepted to rejected (three attempts, `attack-10` and two variants with distinct return types), and has no argument that none exists.

Take a match with closed parts `p0 … pn-1` that all pass `canDeriveCoercions`, in environment `E`. Without `eqeager`:
1. the thread continues with `E + [p0 … pn-1]` and the coerced witness `w`;
2. one layer later, `threadContinuation` discharges `pn-1` in `E + [p0 … pn-2]` by calling `summon`, which calls `solveEquality(pn-1)` first;
3. if the answer is `.proved(_, c)`, one thread is created, with penalties increased by `c`; it matches at the next layer and the continuation discharges `pn-2`; and so on down to `p0`;
4. if an answer is `.refuted`, the thread dies;
5. the proofs are substituted for assumptions that `w` does not mention, so the final witness is `w` and the final penalties are the initial ones plus the sum of the `c`.

`eagerlyCoerced` makes the same `n` calls with the same goals and environments (the parts before `pi` assumed, same identifiers, same substitutions since closed proofs bind nothing). So it gets the same answers, provided:
- A3. `solveEquality` is a function of its arguments and of the scope's givens. It reads `premiseResolutionDepth`, which has the same value at both moments (both are inside the same `takeSummonResults`). Assert: the comparison of Hook 3.
- A4. `summon` does nothing observable before `solveEquality` when no given is on the stack and no given check is pending. This is why `eagerlyCoerced` gives up in those cases. Assert: Hook 3, and the assertion on `recordSkippedGivens` of 5.2. (The first version required an empty stack, which is sufficient and too strong: `attack-05`.)
- A4b (review). Up to layer `maxImplicitDepth` the frontier of the run with `eqeager` is never larger than that of the other run, so `budget` fires in it only if it fires in the other. This holds because `summon` of a part that `solveEquality` proves creates exactly one thread, which the waiting thread stands for, and a match with a refuted part dies at once instead of some layers later. Past that layer the run with `eqeager` must not report (5.2). Assert: the budget flag of Hook 3.
- A5. The coerced witness does not mention the assumptions of its parts. Assert in `match`: `w` has no `.assumed(i)` for the identifiers given to `gs`.

Then: all proved gives the same witness and penalties, at the same layer by `delay`; one refuted gives a dead thread in both; one inapplicable gives the existing path itself. The only difference is that `n` layers are not counted as steps.

### 6.2 Stage 2

Claim: for a closed pair of scope terms, in a plain environment, `decide` answers what `solveEquality` would eventually answer on every thread that survives.

- **Same theory.** `theory` is the closure that `solveEquality` builds when the environment has no equality hypothesis and no premise projection: same nodes, same shapes, same rule for abstract projections, computed from `facts` as `solveEquality` computes it from `p0`. Assert: Hook 3 of 5.3. The cached closure has more nodes than the one `solveEquality` builds for a single goal (the types of earlier questions). That changes no answer: adding a term to a closure that is closed under congruence puts the new node in an existing class or in a new one and never merges two existing classes, and the binding of an abstract projection is a function of `facts` and of the scope's conformances only. Answers of `decide` therefore do not depend on the order of the questions (review; this is not true of *enumerating* a class, see 5.4).
- **Same doubts (review).** Where `solveEquality` does not trust a refutation (a type of an unmodelled kind anywhere in its graph), search decides, by rules that are not those of the closure. `decide` answers `nil` in exactly those cases (5.3); otherwise the induction below would use "discharged successfully" for a hypothesis that search, not the closure, discharged.
- **Hypotheses add nothing on surviving threads.** Let `h0 … hk` be the assumed givens of a thread, in order. `hi` is discharged in the environment `h0 … hi-1`. By induction on `i`, a closed equality `hi` that is discharged successfully is a theorem of the scope: `h0` is proved from the scope alone, and if `h0 … hi-1` are theorems, a proof from the scope and them is a proof from the scope. So on a thread that completes, the equalities provable with the hypotheses are those provable without. On a thread that does not complete, refuting earlier changes nothing. Assumption:
  - A6. every assumed given is discharged by `threadContinuation` in the scope where it was assumed, in the environment of the givens assumed before it. This is how `threadContinuation` is written (`thread.environment.givens.dropLast()`); assert there that the given popped is the last one.
- **What is excluded.** A hypothesis with variables can be instantiated by the search in ways the argument does not cover, and when one is pending `solveEquality` does not apply and the search uses the liberal rule for abstract projections; `environmentIsPlain` keeps today's path there. A projection through a pending premise is not a scope term; `decide` returns `nil`.
- A7. every equality given of a scope is ground. True of every program that can be written today; counted by `eqclosure.nonground`.
- A8. types are hash-consed and `dealiased` is idempotent, so a type has one node. Assert in `node`: `types.dealiased(nodes[i]) == nodes[i]`.

Where stage 2 differs from today, on purpose: the filter is exact, so closed pairs that `canDeriveCoercions` rejected are accepted when they are equal (`gain-03`, `gain-04`, `attack-09`), and a given that could not match now can. That has two effects on programs accepted today. It may create an ambiguity (`rank-06`). And it may replace the selected conformance by the newcomer with no diagnostic, when the newcomer needs fewer parts and so completes at an earlier layer (review; `attack-07`: today `Pair<Box<A>, D> is P` is selected, with two parts; from stage 2 `Pair<C, B> is P`, with one). The second effect is the more dangerous one, because nothing reports it; step 6 must compare witnesses, not verdicts.

No representative is ever computed, so there is no invariant about representatives to maintain.

### 6.3 Stage 3

Soundness: a thread continues only when `x` under the bindings is syntactically `m` up to nested closed pairs that are equal, and `m` is in the class of `y`. Completeness up to the scope's equalities, for one closed side: if `xσ` equals `y` then `xσ` is congruent to a member of the class of `y` with the same constructor, argument by argument, and the recursion finds it. Restricting the candidates to the members written in the facts (5.4) keeps this: a member added by a question has a shape different from every written member of its class, or is congruent, argument by argument, to a written member of the same shape, because a node added to a closed closure joins a class only by congruence with a node already there. What the restriction gives up is a choice of spelling, not a class.

Termination (review; `tests/attack-09`): a class can contain a term built from itself (`C == Box<C>`). The recursion is on the pattern `x`, which loses a constructor at each step, not on the class, so it terminates. `decide` terminates because it only adds the subterms of the two types it is given.

Order independence: the candidates are a function of the scope's facts. Their order is the order of the where clauses, and since every candidate becomes a thread and threads are ranked by layer and penalty, the order does not affect the result, provided that the penalty of the proof of `m ~ y` does not depend on it either. Today that penalty does depend on how the where clause is written (`rank-01` against `rank-02`); stage 3 inherits this until stage 4.

## 7. Test plan

`tests/` has 51 programs: the 41 of the first version and 10 added by the review (`attack-*`). Each starts with a comment giving the expected verdict at each stage and the reason, and a line `// currently:` with the verdict and counters under base and FULL, written by `record.py` from `tests/current.jsonl`. For the `attack-*` programs the line also gives the verdict of stage 1 as first implemented (binary eq15, `FULL,eqindex,eqeager`), written by hand from `review.jsonl`.

The review ran the 41 programs again under base and FULL: every recorded verdict and counter is reproduced. Two base runs need more than the 60 s of the brief on a loaded machine (`gain-01`, out of memory, and `keep-16`, rejected after a million matches; reproduced with 240 s, `review-base-long.jsonl`). It also ran all of them on binary eq15 (`review.py`, raw results in `review.jsonl`): with `FULL` only, the results are those of the frozen binary; with `FULL,eqindex,eqeager`, `gain-01` and `gain-02` are accepted and nothing else changes; with `selfcheck` added there is no violation on the 41.

| Group | Programs | Expectation |
|---|---|---|
| `keep-01` … `keep-24` | compiler tests on equalities, the three soundness problems, chains, the `Self.X` rule, open requirements, equality premises, pending premises, nested scopes, the abstract model | verdict never changes |
| `gain-01`, `gain-02` | many differing parts | rejected → accepted with `eqeager` |
| `gain-03`, `gain-04` | compound equalities | rejected → accepted with `eqclosure` |
| `gain-05`, `gain-06` | a parameter or projection equal to a concrete type | rejected → accepted with `eqclass` |
| `cost-01`, `cost-02` | index | same verdict; `index.fallback` 40 → 0 and `summon.matches` 4480 → 1680 with `eqindex` (measured on eq15) |
| `rank-01` … `rank-06` | ranking | unchanged through stage 1; `rank-06` becomes ambiguous with `eqclosure`; `rank-01`, `-03`, `-05` with `eqrank` |
| `lang-01` … `lang-03` | open questions | unchanged by this design |
| `attack-01`, `attack-02` | a given with an alias type and the index | verdict of FULL at every stage; eq15 rejects `attack-01` with `eqindex` (defect) |
| `attack-03` | an extension of an alias applies through a root equality | accepted at every stage (documented quirk) |
| `attack-04` | divergent premise through an equality, budget | accepted at every stage; eq15 rejects it with `eqeager` (defect) |
| `attack-05`, `attack-06` | the same call in an initializer and in a return | both accepted from stage 1; eq15 rejects `attack-05` (defect) |
| `attack-07` | a given that newly matches with fewer parts | accepted at every stage; the selected conformance changes at stage 2 without a diagnostic |
| `attack-08` | two written members of a class with equal arguments | rejected at every stage (ambiguous from stage 3, whatever the order of the where clause) |
| `attack-09` | a class that contains a term built from itself | rejected in stage 1, accepted from stage 2; no loop |
| `attack-10` | an extension that applies only past the depth bound | accepted at every stage; compare the witness of the call |

For each stage, in this order:
1. the 51 programs, against the expectations;
2. the existing oracle (types, bindings, witness tables, diagnostics, and witnesses with equality proofs erased) on the 216 corpus files and on the test programs of `research/report/test-programs`: identical for `eqindex`; identical for `eqeager` except programs whose FULL run has `summon.depthExhausted > 0`, each to be read (for these, compare the witnesses of every call site, not only the verdict: `attack-10`); for `eqclosure` and later, a list of differences in verdicts *and in selected witnesses*, each to be classified as a gain, a new ambiguity, a silent change of conformance (`attack-07`), or a defect;
3. the same with `selfcheck`: zero `selfcheck.violations`;
4. the declaration-order fuzzer (`followup/permute.py`) and a where-clause permutation of the `keep`, `gain`, `rank` and `attack` programs (reorder the requirements, swap the sides of each equality): the verdict must not vary, except `rank-01` and `rank-03` before `eqrank`, which are known to. For stage 3 this is the test of the candidate rule of 5.4 (`attack-08`);
5. a statement-position variation of the `gain` programs (review): the call as a statement, in a `return`, as the initializer of a `let`, and as an argument. The verdict must not vary (`attack-05`, `attack-06`).

What the existing corpus cannot show (review): of the 216 files, the equality procedure runs in 4 (`REVIEW-AND-PLAN.md`, 2.3), and no file of the compiler tests, the workloads or the standard library declares a `given` binding at all (searched for `given let` and `given var`), so none has a given whose type is an alias. The comparison "215 of 216 identical, no self-check violation on 253 programs" that followed the implementation of stage 1 is therefore silent on the three defects found here. They were found by reading `match` for the cases its root test does not cover, and by asking what else, besides the result, a longer search can produce.

## 8. Implementation order

| Step | Change | Lines | Builds and tests alone | Expected result |
|---|---|---:|---|---|
| 1 | `eqindex` (5.1) | +15 | done (4e7a2aa) | `cost-01` counters; oracle identical |
| 2 | `delay` and `credit`, with no producer (5.2, Hook 2) | +25 | done (f49136d) | nothing changes, with or without the flag |
| 3 | `eagerlyCoerced` and its hook (5.2) | +45 | done (f49136d) | `gain-01`, `gain-02` accepted |
| 4 | the double-run self-check (5.2, Hook 3) | +25 | done (f49136d) | zero violations on the corpus |
| 4b | corrections from the review, one change each: (a) `hasAliasHead` and the goal test in `eqindex` (5.1); (b) silent end when the budget is exceeded past the depth bound, and the budget flag in the self-check (5.2); (c) `hasImplicitOnStack()` in place of the empty-stack test, with the assertion on `recordSkippedGivens` (5.2); (d) `summon.depthExhausted` counted after the loop (5.2) | +6, +12, +6, +6 | yes, each | (a) `attack-01` accepted with `eqindex`, no self-check violation; (b) `attack-04` accepted with `eqeager`; (c) `attack-05` accepted; (d) `gain-01` accepted with `summon.depthExhausted=0`. Oracle and self-check as for steps 1 to 4 |
| 5 | `EqualityClosure`, `ScopeEqualities`, `scopeEqualities`, `decide`, used only by a self-check against `solveEquality` | +200 | yes | zero disagreements; `decide` is `nil` whenever `solveEquality` is not applicable to a closed pair in a plain environment; `eqclosure.nonground = 0` |
| 6 | `eqclosure` in `match` and `coerced` (5.3, Hooks 1 and 2) | +55 | yes | `gain-03`, `gain-04`, `attack-09` accepted; `rank-06` ambiguous; `attack-07` selects the other conformance |
| 7 | `solveEquality` and `equalityOpaqueTypes` build on `EqualityClosure` | +30 −110 | yes | oracle identical to step 6 |
| 8 | `eqclass` (5.4) | +100 | yes | `gain-05`, `gain-06` accepted; `attack-08` ambiguous under every permutation of its where clause |
| 9 | `eqrank` (5.5), after the designers' answer | +10 −150 | yes | `rank-01`, `-03`, `-05` ambiguous |

Stage 1 is steps 1 to 4b (about 140 lines). It is useful without the rest and needs no decision from anyone, except that step 4b (b) and the cost of deeper searches follow from the answer assumed for question 6.

Two estimates were raised by the review. Step 5 was +150: the closure with incremental `node` for the nine kinds of compound type that `solveEquality` models is about 80 lines, building the scope's facts and conformances 40, `decide` with the rule for abstract projections 50, the self-check and the cache of `nil` 30. Step 8 was +60: it needs the list of members of each class (kept up to date by `merge`), unification of a pattern against a member on a copy of the substitutions, one thread per candidate out of `match`, and the penalty of `m ~ y` from `solveEquality`.

If everything is adopted the balance is about +530 −260. Once `eqclosure` and `eqclass` are the default and the language states that equality givens are ground (or adopts the instantiation scheme of 3.7), `canDeriveCoercions`, `canDeriveCoercion`, their four caches and the flags `coesrc` and `coercememo` can be deleted: about 150 more lines. That is the simplification available; it depends on answers to section 9.

**What would make us abandon.**
- Step 4 reports a difference that is not explained by the depth bound. Then the argument of 6.1 has a hole, and stage 1b is dropped until it is understood; `eqindex` stays.
- After step 4b, a program accepted by `FULL` is rejected, or selects another witness at some call site, with `eqindex,eqeager` (review). The review found two such programs before step 4b and none after it by reasoning, but `attack-10` shows the mechanism by which one could exist. If one is found in code the designers consider reasonable, `eqeager` must give up `credit` (the depth bound counts the equality layers again, and `gain-01` is rejected again) and keeps only its saving of search steps.
- The deeper searches of 5.7 cost measurable time on real code (a resolution that fails at the depth bound today is the case to measure). Then give `credit` a cap, or drop it.
- Step 5 reports a disagreement between `decide` and `solveEquality` that is not a defect of the new code. Then the two do not implement one theory, and stage 2 must wait for the written specification (plan item 3.1).
- Step 6 produces new ambiguities, or changes the selected conformance at any call site (review, `attack-07`), in the corpus or in code that the designers consider reasonable. Then stage 2 is kept as a filter that only refutes (it would still remove `canDeriveCoercions` from failing candidates) and the completeness gains are given up.
- Step 8 makes programs ambiguous that the designers want accepted (two written members with equal arguments, 5.4). Then stage 3 waits for the answer to question 1; there is no rule for choosing a member that is both deterministic and independent of spelling.
- The designers choose coherence (question 1). Then option A becomes sound; keep stage 1, drop stages 2 to 4, and redesign around representatives.
- The census of real code (plan item 2.1) shows no scope with more than a handful of equalities and no depth failure. Then stop after stage 1.

## 9. Questions for the language designers

1. **Are conformances coherent across equal types?** With `T == U`, `T is P` and `U is P`, are the two witnesses the same, so that `T.X == U.X`? The test `associated-type-inequality` says no. If no, a type's spelling selects its conformance, and equal types cannot be replaced by one another before resolution. If yes, normalization in the style of Swift is sound and simpler than what is proposed here.
2. **`Self.X` and `T.X` when `T == Self` and `T is P`.** Inside the trait, are they equal? Today's rule (equal if `T is P` is the only such conformance in scope) was chosen to agree with the existing checker on one program (`keep-12`). Under a strict reading of question 1 they are different.
3. **Concrete types.** Is `Box<A> == Box<B>` allowed to hold without `A == B` (no injectivity, `keep-11`)? Is `where T == A, T == B` with two distinct structs an error at the declaration, or a way to make `A` and `B` interchangeable in the body (`lang-03`, accepted today)? Injectivity would make matching against a class deterministic.
4. **Ranking through equalities.** Should the choice between two conformances that both apply through equalities depend on the side on which an equality is written (`rank-01` against `rank-02`), on where the equality is declared (`rank-03`), or on how many arguments differ (`rank-05`)? The proposal of 5.5 is that none of these counts.
5. **Members through an equality.** With `T == A`, are the members of `A` available on a value of type `T` (`lang-01`, rejected today; trait members are available, `lang-02`)? Does `extension A` apply to `T`? If yes, member lookup needs a concrete member of the class of `T`; the closure of stage 2 provides it. Today the answer depends on an alias (review): `extension A` does not apply to `T`, but with `type AA = A`, `extension AA` does (`attack-03`), and a given of type `AA` is usable where `B` is required when `A == B` follows from the scope, while a given of type `A` is not (`attack-01` against `attack-02`). One of the two behaviours is a defect of `match`; which one?
6. **The depth bound.** Is it meant to count the steps that prove equalities? Stage 1 assumes not. Is a resolution that fails at the bound meant to fail silently, so that another extension or overload is used (`attack-04`, `attack-10`)? Stage 1 keeps that behaviour and extends it to the budget past the bound; the alternative is to report every abandoned resolution, which rejects programs that are accepted today.
7. **Equalities in traits.** How will a trait state `Iterator.Element == Element`? As a quantified conditional given it makes every scope's equalities non-ground. Is a bound on the depth of instantiation acceptable (incomplete beyond it), or must such signatures be completed as in Swift?
8. **Proof terms.** Must an equality proof be a term built from the stated equalities (for lowering, or for a checker of derivations), or is "equal by the closure of the scope" enough? Stage 4 assumes the latter; `match` already discards the proofs of the parts.

## 10. What I did not establish

- Stages 2 to 4 have not been compiled. The Swift fragments follow the code as read on the day of writing; names such as `Memos.TypePair`, `pendingGivenChecks` and `selfCheck` exist there. Stage 1 has been compiled by the coordinator, in the first version of 5.1 and 5.2; the corrections of step 4b have not.
- The claim that stage 1b preserves results was first an argument and traces of six programs. It has since been run: no difference on the corpus, no self-check violation on 253 programs. The review showed that this evidence did not cover a given with an alias type, a divergent search behind an equality, or a call in an initializer (section 11). The claim that the corrected stage 1 preserves the verdict of every program accepted by `FULL` is again an argument only, and it has a known gap: candidate selection after a resolution that newly succeeds (6.1).
- The effect of `eqclosure` on ambiguity is known from one constructed program (`rank-06`); how often it happens in real code is unknown.
- Timings were not measured (the machine was shared); all cost statements are in counters or in asymptotic terms.
- Widening constraints in the solver compare types syntactically. I did not find a program where this loses an equality, and did not look systematically.

## 11. Review

An adversarial review of this design, made after stage 1 had been implemented. The reviewer read the design against the source (`Typer.swift` as of commit f49136d plus uncommitted work, `TypeStore.swift`, `Solver.swift`), ran every program of `tests/` on the frozen binary (eq9) and on the binary that has stage 1 (eq15), and wrote programs meant to break each stage. Nothing was built. Scripts and raw results: `review.py`, `review.jsonl`, `review-base-long.jsonl`, `experiments/review/` (34 exploratory programs with `results.jsonl`).

### 11.1 The account of the existing code

Confirmed by reading and by runs: only the innermost mismatches are recorded; `canDeriveCoercions` compares with the sides of equalities up to renaming; `TypeStore.unifiable` has the liberal rule for abstract projections and `solveEquality` the narrow one; parts are discharged last first, one layer each, with the earlier parts assumed, which is what `delay: parts.count` reproduces; every equality given that can be written is ground (three more forms tried); the hooks of stages 1 and 2 exist where the design says, and the names it uses exist.

Wrong or incomplete, and corrected in place:

| # | Statement of the first version | What the code does | Evidence |
|---|---|---|---|
| 1 | "A single mismatch at the root is a failure"; "`extension A` does not apply to `T`" | Not when one of the two types is a type alias at its root: the root test compares with the types before alias stripping | `attack-01`, `attack-03`: accepted by base and FULL |
| 2 | A1: the index may skip any given whose head differs from the goal's, once equalities have no constructor side | A given with an alias type matches a goal with another head through a root equality | `attack-01`: FULL accepted, FULL + `eqindex` rejected, self-check violation |
| 3 | Stage 1 returns what FULL returns, except that programs rejected by the depth bound are accepted | A resolution that fails is not an error; one that exceeds the budget is. A search that the depth bound used to stop silently runs deeper and reports | `attack-04`: FULL accepted, FULL + `eqeager` rejected; the self-check confirms the resolution and sees nothing |
| 4 | A4: `eagerlyCoerced` must give up when a declaration is on the stack | Only givens on the stack matter; a local binding is on the stack while its initializer is typed | `attack-05` rejected, `attack-06` accepted, same call |
| 5 | "The test that bumps `summon.depthExhausted` stays as it is" | It now also fires in resolutions that succeed | `gain-01` accepted on eq15 with `summon.depthExhausted=1` |
| 6 | 5.7: stage 1b makes no more calls to `solveEquality` than today | True only when the resolution completes within the bound | five-branch variant of `attack-04`: 775 → 3900 |
| 7 | `decide` answers `false` when the two nodes are in different classes | `solveEquality` does not trust that answer when a type of an unmodelled kind is in the graph; `decide` must answer `nil` | reading of `solveEquality` (`unmodelled`); no program |
| 8 | Stage 3 candidates: "the members of the class, one per tuple of argument classes" | The cached class grows with earlier questions, and two members with equal arguments select different conformances | `attack-08` (reasoned; stage 3 does not exist) |
| 9 | 1.2: `where Element == Int` is rejected today | Accepted when the conformance of the concrete type is not generic | `experiments/review/r1` |
| 10 | Estimates of steps 5 and 8 | Raised from 150 to 200 and from 60 to 100 lines | section 8 |

### 11.2 What was changed in this document

- Status paragraph at the top; section 0 states the property stage 1 is meant to have and that the first implementation does not have it.
- Section 2: the alias exception in the rows of `match` and `applies`; a third fact (a failed resolution is not an error).
- 5.1: `hasAliasHead` (Hook 1b) and two more conditions in Hook 2.
- 5.2: `hasImplicitOnStack()` in place of the empty-stack test; the budget rule past the depth bound; the counter; one more comparison in the self-check.
- 5.3: `nil` for unmodelled kinds; three properties of the round loop (alias at the root, redundant pairs, arguments after a refuted pair).
- 5.4: the candidates are the members written in the facts, every one of them.
- 5.7, 6.1, 6.2, 6.3: the cost of deeper searches; A1 and A4 restated, A4b added, the claim limited to one resolution; order independence of `decide` argued and distinguished from enumeration; termination on a cyclic class.
- 7: ten `attack-*` programs, a test of statement positions, witnesses compared as well as verdicts, and what the corpus cannot show.
- 8: steps 1 to 4 marked done, step 4b added, two estimates raised, three more reasons to abandon.
- 9: questions 5 and 6 extended.

### 11.3 Attacks that the revised design withstands

- *Two witnesses* (`keep-01`, `keep-02`): on eq15 with stage 1, same verdicts, no self-check violation. Stage 2 keeps them: concrete projections are atoms of the closure.
- *Ranking by number of parts* (`rank-05`) and by orientation (`rank-01`, `rank-02`): same verdicts on eq15; the `delay` reproduces the layer.
- *Hypotheses*: equality premises with variables (`keep-23`), a closed equality premise of a local given (`keep-14`), projections through a pending premise (`keep-15`, `keep-16`): same verdicts on eq15, no violation. For stage 2 the induction of 6.2 holds once `decide` answers `nil` wherever search, not the closure, would decide.
- *Order of questions to the cached closure*: answers of `decide` do not depend on it (6.2).
- *Termination*: a class that contains a term built from itself (`attack-09`) loops neither `decide` nor class matching; the round loop of stage 2 refutes at least one pair per round.
- *The index under stage 2*: a constructor is an atom, so A2 holds of `decide` as of `canDeriveCoercions`.
- *Non-ground equalities*: none can be written; a scope that sees one makes every new mechanism answer `nil` and take the existing path.
- *Unsoundness*: no stage accepts a match on an equality that `solveEquality`, or the closure built from the same facts by the same rules, does not prove. The review found no program accepted wrongly, at any stage.
- `attack-01`, `attack-04` and `attack-05` are withstood by the corrections of step 4b. This rests on reading the code, since the corrections are not built: for (a) the alias is the only way the root test is defeated that the review found in `unifiable`; for (b) the frontier argument A4b; for (c) the reading of `recordSkippedGivens`.

### 11.4 Attacks that it does not withstand

1. **Stage 1, selection after a resolution that newly succeeds.** An extension or an overload that did not apply because its resolution ended at the depth bound applies with `eqeager` (`attack-10`). No program was found that this rejects or whose meaning it visibly changes, in three attempts (`attack-10`; `h-*` and `e-flip-*` in `experiments/review`); there is no argument that none exists. It follows from accepting more resolutions, and cannot be removed without removing the gain.
2. **Stage 1, cost.** A resolution that ends at the depth bound today can cost up to the budget afterwards (5.7). Not measured on real code.
3. **Stage 2, silent change of conformance.** `attack-07`: accepted before and after, another conformance selected, no diagnostic. With `rank-06` (new ambiguity) this means stage 2 changes the meaning of programs that are accepted today. The design has no remedy; it is the price of matching more givens while ranking by layer.
4. **Stage 2, artefacts of the round loop.** Redundant parts change the ranking; for pairs with variables the outcome depends on the order of type arguments (5.3).
5. **Stage 3, spelling.** With two written members of a class that have equal arguments, any rule either depends on the order of the where clause or reports an ambiguity that users will not expect (`attack-08`). The design chooses the ambiguity.
6. **The self-check.** It compares results, so it is blind to diagnostics (corrected for the budget only), to cost, and to anything outside the programs it is run on. It reported nothing on 253 programs while three defects were present.
7. **The alias behaviour of `match`** is kept, not explained (question 5). Every argument above that says "the root is never coerced" carries the exception.

### 11.5 Recommendation

**Implement only the first step.**

- Stage 1 is the part whose value does not depend on a language decision: the index stays on in scopes with equalities (`cost-01`: 4480 → 1680 candidate matches), and wide matches no longer fail at the depth bound. It is already in the compiler. Make the four corrections of step 4b before `eqindex` or `eqeager` is added to any configuration that is compared, measured or shipped: without (a) and (b) the flags reject programs that `FULL` accepts, and the existing comparison does not show it. Then run the test plan of section 7 including the `attack-*` programs, the statement-position test, and a comparison of witnesses on the programs whose `FULL` run reaches the depth bound.
- Step 5 (the cached closure, used only to check itself against `solveEquality`) changes no behaviour and is the cheapest way to learn whether the two implement one theory. It can be done next, as a measurement.
- Steps 6 to 9 should not be adopted now. Stage 2 changes which conformance is selected in accepted programs, in one case without any diagnostic, and stage 3 has to choose a spelling, which is the question this design set out to avoid. Both are sound, and both would make more valid programs accepted (`gain-03` to `gain-06`, `attack-09`); whether their changes of meaning are acceptable depends on questions 1 and 4, which only the designers can answer. If they are built earlier as experiments behind their flags, judge step 6 by the list of call sites whose witness changes, not by verdicts.
- For the owner's concern, equalities in real code: chains and equalities between associated types are already decided by `eqsolve` (`keep-08`, `keep-10`), and an associated type equal to a concrete type gets that type's non-generic conformances today. What stays rejected after stage 1 is the use of a *generic* conformance through such an equality (`gain-05`, `gain-06`) and compound equalities (`gain-03`, `gain-04`). The first of these is the likeliest to matter in real code and is the reason to return to stage 3 once question 1 is answered; with a single written member of the right shape in the class, which is the usual case, stage 3 accepts it without ambiguity.

