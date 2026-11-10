# Equality by normalization: design and verdict

For the engineer who will implement this in `/home/user/hylo-impl/Sources/FrontEnd`. Functions are named as they are in `Typer/Typer.swift`; that file changes between sessions, so every hook is given by function name and by the existing lines it sits next to, never by line number.

## 0. Verdict

**Do not rewrite types to canonical representatives. Keep the congruence closure, and move it to where the equalities arise: inside `match`.**

- Rewriting types when they enter a scope, as Swift's requirement machine does, is neither simpler nor safe in this checker. Hylo selects a conformance by the *spelling* of the type: with `T == U`, `T is P` and `U is P` in scope, `T.X` and `U.X` are different types, and a compiler test requires it (section 3.3). A representative erases the spelling that resolution needs.
- The useful part of normalization is something else: an equality between two closed types should be *decided* at the moment two types are compared, and should never become a hypothesis that the search proves later. This needs no representative, so nothing can leak into inferred types, witnesses or diagnostics.
- This can be done in stages. The first stage is about 110 lines, uses the existing `solveEquality` unchanged, and gives the same results as the current `FULL` configuration except that valid programs rejected by the depth bound are accepted. Later stages add a closure cached per scope, which makes the test exact and complete for closed types, and class matching for types with unification variables.
- It does not deliver the reduction hoped for in the review ("200 lines replace 700"). The end state has about the same amount of code as today. What changes is behaviour: three kinds of valid programs that are rejected today are accepted, the index of givens stays enabled in scopes with equalities, and the syntactic filter `canDeriveCoercions` leaves the common path.

What each existing mechanism becomes:

| Mechanism | After stage 1 | After stages 2 and 3 |
|---|---|---|
| `fixsubst` | still needed (same rule, applied in the new path too) | needed only for pairs with unification variables on the old path |
| `eqsolve` (`solveEquality`) | unchanged, called earlier | unchanged as the source of proofs and penalties; its closure is also cached per scope as a decision oracle |
| `eqmgu` | unchanged | unchanged (it answers equality *goals* `?v ~ X`; nothing here replaces it) |
| `absquotient` | unchanged | unchanged in behaviour; can share the closure code |
| `canDeriveCoercions` | unchanged | bypassed for closed pairs; kept for pairs with variables and for scopes with non-ground equality givens |
| index special case (`coercionSources`) | removed for ground equalities (`eqindex`) | same |
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

`tests/gain-06-projection-equal-to-concrete.hylo`: rejected by both. An associated type stated equal to a concrete type does not get the conformances of that concrete type, because the pair `(Box<?t>, T.Element)` contains a unification variable and `canDeriveCoercions` compares sides up to renaming only. This is the ordinary shape of generic code (`where Element == Int`).

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
| `match` | Unifies the given's type with the goal. The handler passed to `TypeStore.unifiable` records every mismatching pair and answers "coercible", so only the *innermost* mismatches are recorded. A single mismatch at the root is a failure. Each pair must pass `canDeriveCoercions`; the pairs are then assumed (`environment.assuming(givens:)`), the witness is wrapped in a `.builtin(.coercion)` node of type `a ~ b`, and the assumptions are proved later, last first, by `threadContinuation` → `summon`. The proofs of the parts are **not** stored in the witness. | traces of `rank-01`, `gain-01` |
| `summon` (inner) | A closed equality goal goes to `solveEquality`; `?v ~ X` to `mostGeneralEqualityThread`; anything else to the search with the built-in reflexivity, symmetry and transitivity givens. | `keep-05`, `keep-13` |
| `coerced` | A value coercion first tries syntactic unification. Otherwise it starts a thread that matches the value's type against the expected type (nested equalities, as in `match`), and, if `canDeriveCoercions` allows, a second thread that assumes the equality of the two whole types. Only this root equality keeps its proof term. | `s1`–`s6`, `gain-02`, `gain-04` |
| `canDeriveCoercions` | A filter: each side of the pair must be equal *up to renaming* (`Typer.unifiable`, which is α-equivalence, not unification) to a side of some equality given or hypothesis. A side in which a unification variable occurs inside a compound type can only coincide with a side of a hypothesis, so in practice such pairs are rejected; so is a closed pair that needs a congruence step. | `gain-04`, `gain-05` |
| `applies` | Extension applicability is a `match` of the extended type against the receiver, so equalities work in nested positions (`extension Box<A>` applies to `Box<T>` when `T == A`) and not at the root (`extension A` does not apply to `T`). | `keep-24`, `experiments/m2` |
| `resolve(_:inheritedMemberOf:...)` | Trait members and associated types are found by `summon(P<T, ?...>)`, hence through equalities. | `lang-02` |
| `typeOfImplementation` | `T.X` through a coerced witness strips the coercion (`asCoercionApplication`): with `T == U` and only `U is P`, `T.X` and `U.X` are the same type `(U::w).X`. This is the one place where the checker already normalizes. | `keep-03` |
| `resolve(_:nativeMemberOf:)` | No equality is used: with `T == A`, the members of `A` are not found on a value of type `T`. | `lang-01` |
| Solver, `solve(equality:)` | Purely syntactic unification. Every flow of a value that I tried (argument, return, `inout`, initialization, inferred generic argument) is a `CoercionConstraint` and reaches `coerced`. Widening constraints simplify to syntactic equalities; I did not find a program in which that loses an equality, and did not search exhaustively. | `experiments/s1`–`s6` |
| `indexedSummon`, `givenIndex` | The index is abandoned if the scope has any coercion source, or the environment any equality hypothesis. | `cost-01` |
| `abstractModel`, `equalityOpaqueTypes` | A second congruence closure of the scope's ground equalities, to mark opaque constructors. | `keep-22` |

Two facts about the present language matter for the design:

- **Every equality given that can be written today is ground.** Equalities come only from where clauses, whose types mention rigid generic parameters. `given X == Y` inside a trait is a syntax error ("expected 'is'"; `experiments/t2`). Non-ground equalities exist only as *hypotheses*: the premises of a generic given while its parameters are still unification variables.
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

**Why it is valid.** The index skips a given whose nominal head differs from the goal's. Such a given can match only if unification coerces the pair of the two head constructors. `match` never coerces the root pair, and a pair of constructors passes `canDeriveCoercions` only if each is, up to renaming, a side of an equality. So the index is valid when no equality has a type constructor that takes arguments as a side.

**Data.** In `GivenIndex`:

```swift
/// `true` iff every coercion source is a ground equality neither side of which is a trait or a
/// generic struct or enum without arguments.
var coercionSourcesAreRigid = true
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

**Hook 2**, in `indexedSummon`, replace the condition of

```swift
    guard let ix = givenIndex(visibleFrom: scopeOfUse), ix.coercionSources.isEmpty else {
      TyperCounters.bump("index.fallback")
      return nil
    }
```

by `ix.coercionSources.isEmpty || (TyperExperiments.eqindex && ix.coercionSourcesAreRigid)`. The test on the environment that follows (fall back if a hypothesis is an equality) stays.

**Hook 3.** The existing `selfcheck` test in `indexedSummon` (counter `selfcheck.index.confirmed`) already verifies that each skipped candidate fails to match. It must run in this new case too; nothing to add if it is placed after the guard.

About 15 lines. No verdict changes.

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
    if !TyperExperiments.eqsolve || (selfCheck == .equality) { return nil }
    if !declarationsOnStack.isEmpty || !pendingGivenChecks.isEmpty { return nil }
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

With no credit anywhere this is the existing loop: same exits, same counters. The test that bumps `summon.depthExhausted` stays as it is.

**Why `delay` and `credit` rather than nothing.** The first layer at which any thread completes decides the result (`while done.isEmpty`). Today a coerced match with `n` parts completes `n + 1` layers after its match. If the new thread completed immediately, two givens that both match through equalities, with different numbers of differing parts, would finish together; with equal penalties that is an ambiguity where today the one with fewer parts wins (`tests/rank-05`). `delay: parts.count` makes the thread resume at the layer where the last part would have been proved (checked against the 4-layer trace of `rank-05` and the 10-layer trace of `gain-01`). `credit` keeps the waiting from counting as steps; that is the whole gain.

**Hook 3, self-check.** The three callers of `takeSummonResults` on a fresh resolution (`summon(_:in:)`, `coerced`, `applies`) go through a helper that, when `selfcheck` and `eqeager` are on and `selfCheck == .none`, runs the resolution a second time with a private switch that makes `eagerlyCoerced` return `nil`, and compares the two lists of `(witness, penalties)` after erasing the names of unification variables. A difference is a `selfCheckViolation`, except when the second run ended by the depth bound (then the first is allowed to have results). About 25 lines.

About 95 lines in all.

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
    if s.isTrivial and x, y contain no abstract projection: return false
    add x and y to s.facts and s.theory
    for each abstract projection node created in s.theory by this call:
        apply the rule of 3.4 using the classes of s.facts; merge in s.theory if it gives a binding
    write s back to the cache
    return s.theory.find(node(x)) == s.theory.find(node(y))
```

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

**Hook 2**, in `coerced`, at `if canDeriveCoercions(root.type, goal, in: scopeOfUse, where: .empty) {`: the condition becomes `decide(root.type, goal, in: scopeOfUse) ?? canDeriveCoercions(...)`. The body is unchanged: the root equality is still assumed and proved by `solveEquality`, so it keeps its proof term.

**Hook 3**, self-check: whenever `decide` returns a non-`nil` answer and `solveEquality` applied to the same pair in the same environment is not `.notApplicable`, the two must agree.

**Sharing the code (optional, after the stage is validated).** `solveEquality` and `equalityOpaqueTypes` each contain their own copy of the graph construction and of the closure. Both can build an `EqualityClosure` instead. `equalityOpaqueTypes` cannot reuse the cached *instance*: it merges abstract and concrete projections freely, on purpose, because the abstract model must over-approximate the search, which uses the liberal rule of `TypeStore.unifiable` whenever `solveEquality` does not apply. It needs a closure built with that rule (a parameter of `node`).

About 190 lines added, about 110 removed if the sharing is done.

### 5.4 Stage 3, `eqclass`: pairs with unification variables

For a recorded pair `(x, y)` in which `x` has unification variables and `y` is closed (or the converse), with the scope's closure available:

```
candidates = the members m of the class of y in `theory` that have the shape of x
             (same constructor, labels and arity), one per distinct tuple of argument classes
for each candidate m:
    unify x with m, extending a copy of the substitutions made before this pair,
        with the same handling of nested pairs (closed: decide; with variables: recursively)
    on success: one thread, as in stage 1, with the penalty of the proof of m ~ y added
no candidate: the match fails
```

This is E-matching against a ground closure, and it is complete up to the scope's equalities for pairs with one closed side. Several candidates give several threads; if they differ in an observable way the result is an ambiguity, which is the honest answer when constructors are not injective. It replaces `canDeriveCoercions` for these pairs. It needs the substitutions as they were before the failed sub-unification, so the round loop of stage 2 must record them (or `unifiable` must restore them when a sub-unification fails; one line at each of its two `return result || areCoercible(a, b)`).

Pairs with variables on both sides stay on the existing path. About 60 lines. Changes verdicts: `gain-05`, `gain-06`.

### 5.5 Stage 4, `eqrank`: remove the emulation (needs a decision)

Stages 1 to 3 reproduce two accidents of the search because the results must not change without a decision: the penalty of an equality proof (it depends on the side on which a where clause states the equality: `rank-01` is accepted, `rank-02` rejected, and they differ in `A == C` against `C == A`) and the number of layers it takes. If the designers accept the rule

> a given that matches the goal as written is preferred to one that matches through equalities; among the latter, only the lexical distance of the given counts,

then a coerced match adds a constant to the penalties, `delay` and `credit` go away (the thread continues at the next layer), `eagerlyCoerced` stops calling `solveEquality` for costs, and the proof of an explicit equality goal can be the opaque form that `equalityStep` already uses for congruences. `EqualityEdge`, the Dijkstra search, `equalityStep`, `symmetryWitness` and `transitivityWitness` are deleted: about 150 lines removed, 10 added. `rank-01`, `rank-03` and `rank-05` become ambiguous.

### 5.6 Diagnostics

No type is rewritten at any stage. A diagnostic prints the types the constraint was created with, as today. The only new types that can reach a message are bindings made by stage 3, and they are members of a class as written in a where clause.

### 5.7 Laziness and cost

- Stage 1a: nothing at run time; one test per coercion source when an index is built.
- Stage 1b: no more calls to `solveEquality` than today (each call replaces one that the search would make, unless the thread dies first; then it is extra, bounded by the number of parts that passed `canDeriveCoercions`).
- Stage 2: a closure is built the first time a closed pair must be decided in a scope with an equality in sight; never for a scope without one (`isTrivial` is known from `ix.coercionSources`). Building is `O(F log F)` for `F` facts. A decision hashes the two types and their subterms once, then is two lookups. Memory per scope: the subterms of the facts, plus the closed types that were compared there. Nothing is cached while a declaration is being typed, as for the index.
- The standard library has no equality: every scope is trivial, and the only cost is the flag tests.

## 6. Why it is correct

### 6.1 Stage 1

**`eqindex`.** Argument in 5.1. Assumptions:
- A1. `match` fails on a single mismatch at the root. Assert: in `match`, if `eqindex` and the two types have different nominal heads, the result is `.next([])` (this is the existing `selfcheck.index` test).
- A2. `canDeriveCoercions(k, k')` is false for two distinct constructors when no equality side is a constructor. Same assertion.

**`eqeager`.** Claim: with `eqeager`, every resolution returns what it returns without, except that it may return results where the other run stopped at the depth bound.

Take a match with closed parts `p0 … pn-1` that all pass `canDeriveCoercions`, in environment `E`. Without `eqeager`:
1. the thread continues with `E + [p0 … pn-1]` and the coerced witness `w`;
2. one layer later, `threadContinuation` discharges `pn-1` in `E + [p0 … pn-2]` by calling `summon`, which calls `solveEquality(pn-1)` first;
3. if the answer is `.proved(_, c)`, one thread is created, with penalties increased by `c`; it matches at the next layer and the continuation discharges `pn-2`; and so on down to `p0`;
4. if an answer is `.refuted`, the thread dies;
5. the proofs are substituted for assumptions that `w` does not mention, so the final witness is `w` and the final penalties are the initial ones plus the sum of the `c`.

`eagerlyCoerced` makes the same `n` calls with the same goals and environments (the parts before `pi` assumed, same identifiers, same substitutions since closed proofs bind nothing). So it gets the same answers, provided:
- A3. `solveEquality` is a function of its arguments and of the scope's givens. It reads `premiseResolutionDepth`, which has the same value at both moments (both are inside the same `takeSummonResults`). Assert: the comparison of Hook 3.
- A4. `summon` does nothing observable before `solveEquality` when no declaration is on the stack and no given check is pending. This is why `eagerlyCoerced` gives up in those cases. Assert: Hook 3.
- A5. The coerced witness does not mention the assumptions of its parts. Assert in `match`: `w` has no `.assumed(i)` for the identifiers given to `gs`.

Then: all proved gives the same witness and penalties, at the same layer by `delay`; one refuted gives a dead thread in both; one inapplicable gives the existing path itself. The only difference is that `n` layers are not counted as steps.

### 6.2 Stage 2

Claim: for a closed pair of scope terms, in a plain environment, `decide` answers what `solveEquality` would eventually answer on every thread that survives.

- **Same theory.** `theory` is the closure that `solveEquality` builds when the environment has no equality hypothesis and no premise projection: same nodes, same shapes, same rule for abstract projections, computed from `facts` as `solveEquality` computes it from `p0`. Assert: Hook 3 of 5.3.
- **Hypotheses add nothing on surviving threads.** Let `h0 … hk` be the assumed givens of a thread, in order. `hi` is discharged in the environment `h0 … hi-1`. By induction on `i`, a closed equality `hi` that is discharged successfully is a theorem of the scope: `h0` is proved from the scope alone, and if `h0 … hi-1` are theorems, a proof from the scope and them is a proof from the scope. So on a thread that completes, the equalities provable with the hypotheses are those provable without. On a thread that does not complete, refuting earlier changes nothing. Assumption:
  - A6. every assumed given is discharged by `threadContinuation` in the scope where it was assumed, in the environment of the givens assumed before it. This is how `threadContinuation` is written (`thread.environment.givens.dropLast()`); assert there that the given popped is the last one.
- **What is excluded.** A hypothesis with variables can be instantiated by the search in ways the argument does not cover, and when one is pending `solveEquality` does not apply and the search uses the liberal rule for abstract projections; `environmentIsPlain` keeps today's path there. A projection through a pending premise is not a scope term; `decide` returns `nil`.
- A7. every equality given of a scope is ground. True of every program that can be written today; counted by `eqclosure.nonground`.
- A8. types are hash-consed and `dealiased` is idempotent, so a type has one node. Assert in `node`: `types.dealiased(nodes[i]) == nodes[i]`.

Where stage 2 differs from today, on purpose: the filter is exact, so closed pairs that `canDeriveCoercions` rejected are accepted when they are equal (`gain-03`, `gain-04`), and a given that could not match now can, which may create an ambiguity (`rank-06`).

No representative is ever computed, so there is no invariant about representatives to maintain.

### 6.3 Stage 3

Soundness: a thread continues only when `x` under the bindings is syntactically `m` up to nested closed pairs that are equal, and `m` is in the class of `y`. Completeness up to the scope's equalities, for one closed side: if `xσ` equals `y` then `xσ` is congruent to a member of the class of `y` with the same constructor, argument by argument, and the recursion finds it.

## 7. Test plan

`tests/` has 41 programs. Each starts with a comment giving the expected verdict at each stage and the reason, and a line `// currently:` with the verdict and counters under base and FULL, written by `record.py` from `tests/current.jsonl`.

| Group | Programs | Expectation |
|---|---|---|
| `keep-01` … `keep-24` | compiler tests on equalities, the three soundness problems, chains, the `Self.X` rule, open requirements, equality premises, pending premises, nested scopes, the abstract model | verdict never changes |
| `gain-01`, `gain-02` | many differing parts | rejected → accepted with `eqeager` |
| `gain-03`, `gain-04` | compound equalities | rejected → accepted with `eqclosure` |
| `gain-05`, `gain-06` | a parameter or projection equal to a concrete type | rejected → accepted with `eqclass` |
| `cost-01`, `cost-02` | index | same verdict; `index.fallback` 40 → 0 and `summon.matches` 4480 → about 1640 with `eqindex` |
| `rank-01` … `rank-06` | ranking | unchanged through stage 1; `rank-06` becomes ambiguous with `eqclosure`; `rank-01`, `-03`, `-05` with `eqrank` |
| `lang-01` … `lang-03` | open questions | unchanged by this design |

For each stage, in this order:
1. the 41 programs, against the expectations;
2. the existing oracle (types, bindings, witness tables, diagnostics, and witnesses with equality proofs erased) on the 216 corpus files and on the test programs of `research/report/test-programs`: identical for `eqindex`; identical for `eqeager` except programs whose FULL run has `summon.depthExhausted > 0`, each to be read; for `eqclosure` and later, a list of differences, each to be classified as a gain, a new ambiguity, or a defect;
3. the same with `selfcheck`: zero `selfcheck.violations`;
4. the declaration-order fuzzer (`followup/permute.py`) and a where-clause permutation of the `keep`, `gain` and `rank` programs (reorder the requirements, swap the sides of each equality): the verdict must not vary, except `rank-01` and `rank-03` before `eqrank`, which are known to.

## 8. Implementation order

| Step | Change | Lines | Builds and tests alone | Expected result |
|---|---|---:|---|---|
| 1 | `eqindex` (5.1) | +15 | yes | `cost-01` counters; oracle identical |
| 2 | `delay` and `credit`, with no producer (5.2, Hook 2) | +25 | yes | nothing changes, with or without the flag |
| 3 | `eagerlyCoerced` and its hook (5.2) | +45 | yes | `gain-01`, `gain-02` accepted |
| 4 | the double-run self-check (5.2, Hook 3) | +25 | yes | zero violations on the corpus |
| 5 | `EqualityClosure`, `ScopeEqualities`, `scopeEqualities`, `decide`, used only by a self-check against `solveEquality` | +150 | yes | zero disagreements; `eqclosure.nonground = 0` |
| 6 | `eqclosure` in `match` and `coerced` (5.3, Hooks 1 and 2) | +45 | yes | `gain-03`, `gain-04` accepted; `rank-06` ambiguous |
| 7 | `solveEquality` and `equalityOpaqueTypes` build on `EqualityClosure` | +30 −110 | yes | oracle identical to step 6 |
| 8 | `eqclass` (5.4) | +60 | yes | `gain-05`, `gain-06` accepted |
| 9 | `eqrank` (5.5), after the designers' answer | +10 −150 | yes | `rank-01`, `-03`, `-05` ambiguous |

Stage 1 is steps 1 to 4 (about 110 lines). It is useful without the rest and needs no decision from anyone.

If everything is adopted the balance is about +405 −260. Once `eqclosure` and `eqclass` are the default and the language states that equality givens are ground (or adopts the instantiation scheme of 3.7), `canDeriveCoercions`, `canDeriveCoercion`, their four caches and the flags `coesrc` and `coercememo` can be deleted: about 150 more lines. That is the simplification available; it depends on answers to section 9.

**What would make us abandon.**
- Step 4 reports a difference that is not explained by the depth bound. Then the argument of 6.1 has a hole, and stage 1b is dropped until it is understood; `eqindex` stays.
- Step 5 reports a disagreement between `decide` and `solveEquality` that is not a defect of the new code. Then the two do not implement one theory, and stage 2 must wait for the written specification (plan item 3.1).
- Step 6 produces new ambiguities in the corpus or in code that the designers consider reasonable. Then stage 2 is kept as a filter that only refutes (it would still remove `canDeriveCoercions` from failing candidates) and the completeness gains are given up.
- The designers choose coherence (question 1). Then option A becomes sound; keep stage 1, drop stages 2 to 4, and redesign around representatives.
- The census of real code (plan item 2.1) shows no scope with more than a handful of equalities and no depth failure. Then stop after stage 1.

## 9. Questions for the language designers

1. **Are conformances coherent across equal types?** With `T == U`, `T is P` and `U is P`, are the two witnesses the same, so that `T.X == U.X`? The test `associated-type-inequality` says no. If no, a type's spelling selects its conformance, and equal types cannot be replaced by one another before resolution. If yes, normalization in the style of Swift is sound and simpler than what is proposed here.
2. **`Self.X` and `T.X` when `T == Self` and `T is P`.** Inside the trait, are they equal? Today's rule (equal if `T is P` is the only such conformance in scope) was chosen to agree with the existing checker on one program (`keep-12`). Under a strict reading of question 1 they are different.
3. **Concrete types.** Is `Box<A> == Box<B>` allowed to hold without `A == B` (no injectivity, `keep-11`)? Is `where T == A, T == B` with two distinct structs an error at the declaration, or a way to make `A` and `B` interchangeable in the body (`lang-03`, accepted today)? Injectivity would make matching against a class deterministic.
4. **Ranking through equalities.** Should the choice between two conformances that both apply through equalities depend on the side on which an equality is written (`rank-01` against `rank-02`), on where the equality is declared (`rank-03`), or on how many arguments differ (`rank-05`)? The proposal of 5.5 is that none of these counts.
5. **Members through an equality.** With `T == A`, are the members of `A` available on a value of type `T` (`lang-01`, rejected today; trait members are available, `lang-02`)? Does `extension A` apply to `T`? If yes, member lookup needs a concrete member of the class of `T`; the closure of stage 2 provides it.
6. **The depth bound.** Is it meant to count the steps that prove equalities? Stage 1 assumes not.
7. **Equalities in traits.** How will a trait state `Iterator.Element == Element`? As a quantified conditional given it makes every scope's equalities non-ground. Is a bound on the depth of instantiation acceptable (incomplete beyond it), or must such signatures be completed as in Swift?
8. **Proof terms.** Must an equality proof be a term built from the stated equalities (for lowering, or for a checker of derivations), or is "equal by the closure of the scope" enough? Stage 4 assumes the latter; `match` already discards the proofs of the parts.

## 10. What I did not establish

- No line of this design has been compiled. The Swift fragments follow the code as read on the day of writing; names such as `Memos.TypePair`, `pendingGivenChecks` and `selfCheck` exist there.
- The claim that stage 1b preserves results rests on the argument of 6.1 and on traces of six programs, not on a run. The double-run self-check of step 4 is what tests it.
- The effect of `eqclosure` on ambiguity is known from one constructed program (`rank-06`); how often it happens in real code is unknown.
- Timings were not measured (the machine was shared); all cost statements are in counters or in asymptotic terms.
- Widening constraints in the solver compare types syntactically. I did not find a program where this loses an equality, and did not look systematically.
