# Improvements to the resolution engine: design

This document is for the engineer who will change `Sources/FrontEnd` of `/home/user/hylo-impl`. It covers three outstanding ideas for the engine of implicit resolution (`summon`, `formThread`, `match`, `threadContinuation`, `applyContinuation`, `takeSummonResults` in `Typer/Typer.swift`). One of them is designed completely (sections 1 to 7); the other two get a shorter treatment (sections 8 and 9).

`Typer.swift` was edited while this was written, so the document anchors every change on quoted lines and not on line numbers. Verdicts and counters marked "currently" come from the binary `research/exp/bin/eq9-723cc0e6b0f8/tc-bench`, which has none of this design. "base" is the existing checker and "FULL" the configuration of `BRIEF.md`. Scripts and raw results are listed in `README.md`.

**Status.** Steps 0 to 3 of section 6 were implemented as written, as the flag `premsubst` (commit `0bbd27e` of `/home/user/hylo-impl`, binaries `eq22` and later), with one omission: `ContextClause` did not get the `binders` field of section 3.2. The design was then reviewed against that implementation (binary `eq25-c7cbd846a05c`, configuration FULL + `premsubst`). The review confirmed every prediction of the first version and found four defects, one of them a wrong acceptance. This version of the document contains the corrections; each is marked "(review)" where it is introduced, and section 11 lists what was changed, what was observed and what is still a prediction. The corrections are not implemented: steps 5 to 8 of section 6.

## 0. Priority

| Idea | What it fixes | Evidence that it matters | Size | Recommendation |
|---|---|---|---|---|
| 1. Substituting discharged premises (`premsubst`) | A requirement on an associated type of another requirement (`where T is P, T.X is Q`) can never be satisfied by a caller. | Nine minimal programs of ordinary generic code are rejected by FULL, and rejected or not decided within 60 s by base. No workaround exists in the language. | about 330 lines, one new field in `Implication` and `ContextClause`; about 90 more for the corrections of the review | **First.** Designed in sections 1 to 7. Implemented except for the corrections. |
| 3. Height bound in place of the size bound | Valid programs with a derivation of more than 10 steps are rejected: copying a 5-tuple, calling a function with three requirements, and one program whose verdict depends on the order of its where clause. | Four minimal programs. No file of the compiler's tests reaches the bound, so the change is invisible there. | about 60 lines | Second. It needs a decision of the language designers and a work budget. Section 9. |
| 2. Tabling of subgoals | Exponential cost when several premises each have several derivations. | Nothing to gain on the code available today: 96% of the resolutions of the standard library end after one step and none has more than 5. One synthetic family of valid programs is exponential today. | 250 to 400 lines | Last, and only together with idea 3, whose cost it bounds. Section 8. |

The reason for the order is that idea 1 removes a rejection that every program of a certain ordinary shape meets, while ideas 2 and 3 concern programs near a limit. Idea 1 also takes over from the least robust part of the equality procedure, the ahead-of-time resolution of a pending premise (about 80 lines, whose correctness depends on resolving the same goal twice with the same answer). That code stops firing for requirements and can be deleted once heads are handled too (section 3.8).

## 1. The problem

### 1.1 Three programs

Each program is in `tests/`, with its current verdict in a comment.

**A requirement on an associated type, generic caller** (`tests/s1-gain-conformance-generic.hylo`):

```hylo
trait P { type X }
trait Q {}
fun f<T where T is P, T.X is Q>() {}
fun g<U where U is P, U.X is Q>() { f<U>() }
```

| | Verdict | `summon.subgoals` | `summon.matches` |
|---|---|---:|---:|
| base | rejected: no coercion from `(P<U>, Q<(U::P).X>) ==> [Void]() let -> Void` to `[Void]() let -> Void` | 9 | 652 |
| FULL | rejected, same message | 5 | 147 |

The caller has exactly the requirements of the callee. The same happens when the requirements belong to an extension (`s1-gain-extension.hylo`: "type 'Box<U>' has no member 'first'") or to a conditional given (`s1-gain-given.hylo`), with two dependent requirements (`s1-gain-conformance-two.hylo`), and with a chain `T is P, T.X is P, T.X.X is Q` (`s1-gain-chain.hylo`). All are rejected by base and by FULL.

**The same with a concrete caller** (`tests/s1-gain-conformance-concrete.hylo`):

```hylo
trait P { type X }
trait Q {}
struct A {}
struct B {}
given B is Q {}
given A is P { type X = B }
fun f<T where T is P, T.X is Q>() {}
public fun main() { f<A>() }
```

| | Verdict | `summon.subgoals` | `summon.matches` |
|---|---|---:|---:|
| base | rejected: no coercion from `(P<A>, Q<(A::P).X>) ==> …` | 6 | 441 |
| FULL | rejected, same message | 4 | 78 |

**An equality on an associated type** (`tests/s1-keep-equality-generic.hylo` and `tests/s1-gain-equality-concrete.hylo`):

```hylo
trait P { type X }
struct B { public memberwise init }
fun f<T where T is P, T.X == B>() {}
fun g<U where U is P, U.X == B>() { f<U>() }      // generic caller
// given A is P { type X = B } ... f<A>()          // concrete caller, second file
```

| | Generic caller | Concrete caller |
|---|---|---|
| base | accepted after 4,854 subgoals and 90,983 matches | timeout (60 s) |
| FULL | accepted: 5 subgoals, 288 matches, `eqsolve.proved=1`, `eqsolve.premises=1` | rejected after 379 subgoals and 10,316 matches, `summon.depthExhausted=1` |

Only the equality form with a generic caller works, and under FULL only because the equality procedure contains a special case for it (section 1.3).

### 1.2 The cause

The type of `f` is `<T> (P<T>, Q<(T::$u).X>) ==> [Void]() let -> Void`, where `$u` is the declaration that the where clause introduces for `T is P` (an implicit binding), and `(T::$u).X` is an `AssociatedType` whose `qualification` is the witness expression `.reference($u)` of type `P<T>`.

`formThread` assumes the requirements in order, `$0 : P<U>` then `$1 : Q<(U::$u).X>`, and `threadContinuation` discharges them last in, first out:

```swift
    // Are there assumptions to discharge?
    if case .assumed(let i, let assumed) = thread.environment.givens.last {
```

So `$1` is proved first. Two things are wrong at that moment.

1. **Nothing says that `$u` is `$0`.** The second requirement still names the callee's own declaration `$u`, which is not visible in the caller's scope. The implication type records the types of its usings (`Implication.usings`) but not the declarations they bind.
2. **`$0` has no witness yet.** Even if `$u` were known to be `$0`, the caller's fact is `Q<(U::$r).X>`, where `$r` is the caller's requirement `U is P`. The two projections are equal only once `$0` has been resolved to `$r`.

The trace of FULL shows the failure (`python3 scripts/run.py --trace --configs FULL tests/s1-gain-conformance-generic.hylo`):

```
[trace] resolve [Void]() let -> Void: 2 layers, 0 done, 0 minimal
[trace] resolve Q<(U::P).X>: 1 layers, 0 done, 0 minimal
```

The second line is the diagnostic code resolving the premise alone: no given matches `Q<(U::$u).X>` at the first step. Unification of two associated types requires one of the qualifications to be `.abstract` (`TypeStore.unifiable(_: AssociatedType, …)`), and the coercion `(U::$u).X ~ (U::$r).X` cannot be derived.

With a concrete caller a third thing is missing: `(A::c).X`, where `c` is the conformance `given A is P { type X = B }`, is `B` by definition. Name resolution knows this (it evaluates `A.X` with `typeOfImplementation(satisfying:in:)`), but resolution never applies it, because it never learns that the qualification is `c`.

### 1.3 The existing workaround

`solveEquality` contains this (comment quoted from the source):

```swift
    // A projection `(T::$k).X` through a premise `$k : P<T>` that has not been discharged yet is
    // equal to `(T::w).X`, where `w` is the witness that will discharge `$k`, if resolution of
    // `P<T>` has a unique result in the environment in which `$k` will be discharged (the givens
    // assumed before `$k`). Resolution is deterministic, so that is the witness eventually used.
```

It finds the pending premise by comparing types (the premise "assumed with the same type and not discharged", required to be unique), resolves it ahead of time with a nested `takeSummonResults`, and requires the result to be unique and closed. It applies to equality goals only, which is why `T.X == B` works and `T.X is Q` does not. It has no rule for a projection through a declared conformance, which is why the concrete caller fails. Among the 76 research test programs that have a requirement on a projection, it fires in 9 under FULL, of which 4 are accepted (`experiments/dependent-programs.jsonl`).

### 1.4 The order of discharge is observable today

Three facts about the engine constrain any change of order. Each was checked on the binary.

1. **A pending premise is a hypothesis for the premises discharged before it.** In `tests/s1-keep-hypothesis.hylo` the function has `where A is P, S<A> is Q`. The trace shows `S<A> is Q` proved first, its subgoal `A is P` matched against `$<assumed given 0>`, and a second derivation through the declared conformance: `4 layers, 2 done, 1 minimal`. The one through the hypothesis has the lower penalty and wins.
2. **Penalties depend on the number of pending premises.** The offset of a candidate given is its group index, and the pending premises are the first groups (`gs.append(contentsOf: environment.givens.reversed().map({ (g) in [g] }))` in `summon`). A visible given used while two premises are pending costs 2 more than the same given used while none is.
3. **Together with the bound, the order of a where clause decides the verdict.** `tests/s3-keep-where-order-a.hylo` has `where C is P, S<C> is Q` and is accepted (8 steps: `C is P`, which needs 5, is a hypothesis for the other). `tests/s3-gain-where-order-b.hylo` is the same program with the two requirements swapped and is rejected (12 steps, `summon.depthExhausted=1`), by base and by FULL.

So a change that reorders every multi-premise resolution would change penalties, sizes and verdicts in programs that have nothing to do with associated types. The design below changes the order only for premises that mention another premise, which today cannot be proved at all except through the workaround.

### 1.5 What must not change

- Every resolution in which no requirement mentions another one: same derivations, penalties, layers and witnesses. This covers the 192 files of the compiler's tests (section 4.4).
- Programs that the workaround accepts today stay accepted; their equality proofs become shorter (the witnesses differ in equality proof terms, as already allowed by the oracle).
- Programs rejected for a good reason stay rejected: `s1-reject-missing-requirement.hylo`, `s1-reject-concrete-mismatch.hylo`, and (review) `s1-attack-capture-recursion.hylo`, which the first version of this design accepted with an ill-typed witness (section 3.4, "Capture").
- `s1-reject-other-conformance.hylo` (the analogue of `Tests/CompilerTests/negative/associated-type-inequality.hylo`) stays rejected only under the commit rule of section 3.10. (review) The first version kept it rejected by accident: see section 3.7.

## 2. Options

### A. Generalize the workaround: resolve the pending premise ahead of time

Move the code of section 1.3 from `solveEquality` to `threadContinuation`, so that it applies to every premise.

- Code: about 70 lines moved and adapted.
- Invariants: (1) resolution of the same goal in the same environment is deterministic, so that the witness found ahead of time is the one found later; (2) the premise and the hypotheses before it are closed; (3) the result is unique; (4) the premise can be identified by its type. Each is a restriction: an open premise, an ambiguous one or two premises of the same type leave the projection opaque. The premise is resolved twice. The nested resolution runs inside a step of the outer one, with its own bound.
- Rejected: it keeps the invariant that the review singled out ("the discharge order of premises; determinism of resolution") and extends its reach.

### B. Discharge every clause in declaration order

First requirement first, for all implications.

- Code: about 10 lines for the order, plus the substitution of option C.
- Invariants: none new. A requirement can only mention earlier ones, so declaration order is a dependency order.
- Rejected as a first step because it is not result-preserving: it changes which premises are hypotheses and every penalty offset in every resolution with two or more premises. It flips the two programs of section 1.4, item 3. It may be what the language designers want (question 1 of section 7); option C does not prevent it.

### C. Keep the order, except that a premise waits until its type is known (chosen)

A premise whose type mentions another premise is not put on the stack of hypotheses. It waits until the premises it mentions have witnesses, which are substituted into its type; then it enters the stack at the top. Everything else stays last in, first out.

- Code: about 330 lines in five steps (section 6): 55 for the binders, 170 for the engine and its helpers, 40 for projections through declared conformances, 40 for self-checks, 25 of preparatory refactoring.
- New invariants: I1 to I4 of section 4, each with an assertion.
- Result-preserving by construction on every resolution without dependent requirements.

### D. Witness variables

Represent the unknown witness of a premise as a variable inside types, extend unification and substitution tables to witnesses, and delay goals that contain unsolved witness variables.

- This is option C in general form. It would also cover the *head* of a callee's type (section 3.8), which needs the constraint solver to carry such variables.
- Code: a new case in `WitnessExpression.Value`, a second kind of binding in `SubstitutionTable`, changes to `unifiable`, `reify` and the solver. Several hundred lines across modules.
- Not chosen now. Option C is its restriction to one resolution thread: `.assumed(i)` inside a type *is* a witness variable whose scope is the thread. Nothing in C has to be undone to move to D.

### How `formThread` learns which declaration a using binds

| Option | Code | Exactness |
|---|---|---|
| (a) `Implication` records, for each using, the declaration through which later usings refer to it (chosen) | about 55 lines in `Implication.swift`, `ContextClause.swift`, `TypeStore.swift`, `Typer.introduce` | Exact. One corner (assumption A7). |
| (b) Recover it from the syntax: a reference to a declaration that is the *k*-th using of some context clause is bound by the *k*-th using of the implication being opened if the types agree | about 30 lines in `Typer.swift`, no change of representation | Same corner, plus confusion between two clauses whose *k*-th usings have the same type. |
| (c) By type alone, as the workaround does | 0 new lines | Fails with two usings of the same type; cannot tell a callee's using from a visible one of the same type. |

(a) is chosen because the information is known where the implication is built and lost one line later; (b) reconstructs it. With (a) the field is empty unless the flag is on *and* a later using refers to an earlier one, so type identities are those of today in every other case.

(review) None of the three distinguishes a *bound* occurrence (a reference that the clause itself makes to its using) from a *free* one (the same declaration named by the caller in a type argument). The two are the same witness expression, and substituting type arguments into the clause mixes them. This happens when a clause is instantiated at itself, as in a recursive call with explicit type arguments, and it made the first version unsound (`tests/s1-attack-capture-recursion.hylo`). The chosen option needs the capture rule of section 3.4. A representation that cannot confuse them replaces, where the implication is built, each reference in a later using by a placeholder that no caller can write (a new case of `WitnessExpression.Value`, or `.assumed` with a negative identifier counted from the using in which it occurs). It was not chosen because every consumer of `Implication.usings` would see the placeholders (`contextAndHead`, which is called in about 25 places, the diagnostic code of the solver, the abstract model), and because `headsubst` already reads `binders`. It is the representation to move to with option D.

## 3. The design

Flag: `premsubst`, declared in `TyperCounters.swift` like the others:

```swift
  /// SEMANTIC FIX: a requirement that mentions another requirement of the same clause is proved
  /// after it, with the witness found for it substituted into its type.
  nonisolated(unsafe) public static var premsubst: Bool = enabled.contains("premsubst")
```

Counters: `premsubst.binders` (usings recorded as referred to), `premsubst.bound` (implications in which `formThread` bound a later using), `premsubst.deferred`, `premsubst.released`, `premsubst.normalized`, `premsubst.stuck` (must stay 0). (review) Added: `premsubst.captureCut` (section 3.4) and the counters of `premcommit` (section 3.10).

### 3.1 Overview

For `f<U>()` in the first program of section 1.1:

| Step | Today | With `premsubst` |
|---|---|---|
| `formThread` | assumes `$0 : P<U>`, `$1 : Q<(U::$u).X>`; hypotheses `[$0, $1]` | assumes `$0 : P<U>`; rewrites the second using to `Q<(U::$0).X>`; it mentions `$0`, so it is *deferred*; hypotheses `[$0]`, deferred `[$1]` |
| after the head matches | discharges `$1`: no given matches; the thread dies | `$1` is not ready; discharges `$0`: the caller's `$r : P<U>` matches |
| next | | `$1` becomes `Q<(U::$r).X>`, enters the stack, is discharged: the caller's second requirement matches syntactically |
| result | none | `f<U>($r)($s)` in 3 layers |

Four pieces: the binders (3.2), two helper functions on types (3.3), the environment and `formThread` (3.4), `threadContinuation` (3.5). Then the cleaning of the result (3.6) and projections through declared conformances (3.7).

### 3.2 Binders

`Types/Implication.swift`: one stored property.

```swift
  /// For each using, the declaration through which the usings after it refer to its witness, or
  /// `nil` if none does. Empty if no using is referred to (always, unless `premsubst` is on).
  public let binders: [DeclarationIdentity?]

  public init(
    context: [AnyTypeIdentity], binders: [DeclarationIdentity?] = [], head: AnyTypeIdentity
  ) {
    assert(!context.isEmpty)
    assert(binders.isEmpty || (binders.count == context.count))
    self.usings = context
    self.binders = binders.contains(where: { (b) in b != nil }) ? binders : []
    self.head = head
  }
```

The normalization to `[]` keeps the identity of every implication without a recorded binder equal to what it is today. `modified(in:by:)` passes `binders` through unchanged (substitution, reification and dealiasing therefore preserve them). Unification of two implications ignores them.

`Types/TypeStore.swift`: `dropFirstRequirement` keeps the rest. The existing line

```swift
      return demand(Implication(context: .init(i.usings.dropFirst()), head: i.head)).erased
```

becomes

```swift
      return demand(Implication(
        context: .init(i.usings.dropFirst()), binders: .init(i.binders.dropFirst()),
        head: i.head)).erased
```

`lifted(_: Implication.ID)` passes `self[a].binders`. `introduce(usings:into:)` gains a parameter `binders: [DeclarationIdentity?] = []`.

Several types are rebuilt from a `ContextClause`: `declaredType(of: FunctionBundleDeclaration.ID)` and the one for variants call `contextAndHead` and then `program.types.introduce(context, into: …)`. So `ContextClause` gets the same field, with a default so that existing initializers compile:

```swift
  /// For each using, the declaration through which later usings refer to it, if any (see `Implication`).
  public let binders: [DeclarationIdentity?]       // init(parameters:usings:binders: = [])
```

`contextAndHead` collects it next to the usings (for an implication whose `binders` is empty it appends one `nil` per using, so that positions stay aligned when nested implications are flattened), and `introduce(_: ContextClause, into:)` passes it on. A type rebuilt through a path that drops the field has dependent usings that stay opaque, as they are today: a loss of coverage, not of correctness.

(review) This part is not optional, and the implementation left it out. The paths that rebuild a type from a `ContextClause` are, besides the two for bundles: `TypeStore.asBoundMemberFunction` (every call of a method on a value), `TypeStore.asConstructor` (every use of an initializer as a constructor), `Typer.typeOfInterface(for:)` (function requirements of traits), and `resolve(_:nativeMemberOf:statically:)` with the metatype case of name resolution (members selected on an unapplied type constructor). Without the field, a method, an initializer or a trait requirement with a dependent where clause is rejected exactly as today while the same clause on a free or static function is accepted: observed on `tests/s1-attack-method.hylo`, `s1-attack-initializer.hylo`, `s1-attack-trait-requirement.hylo` (`premsubst.binders=2`, `premsubst.bound=0`) against `s1-gain-static-method.hylo`. The function that compares two declared types (the one that ends with `return x == program.types.substitute(a, in: y)`) calls `introduce(usings:into:)` on both sides and may keep dropping the binders, since it drops them on both.

`Typer.introduce(types:usings:into:)` is where the declarations are known. The existing lines

```swift
    let ps = declaredTypes(of: types)
    let us = usings.map({ (p) in declaredType(of: p) })
    return program.types.introduce(.init(parameters: ps, usings: us), into: t)
```

become

```swift
    let ps = declaredTypes(of: types)
    let us = usings.map({ (p) in declaredType(of: p) })
    if TyperExperiments.premsubst && (us.count > 1) {
      var bs: [DeclarationIdentity?] = []
      for (k, p) in usings.enumerated() {
        // The name by which resolution refers to the witness of `p` (see `expression(referringTo:)`).
        guard case .reference(let r) = expression(referringTo: p) else { bs.append(nil); continue }
        let target = WitnessExpression(value: .reference(r), type: us[k])
        let used = us[(k + 1)...].contains(where: { (u) in mentions(target, in: u) })
        if used { TyperCounters.bump("premsubst.binders") }
        bs.append(used ? r : nil)
      }
      let i = program.types.introduce(usings: us, binders: bs, into: t)
      return program.types.introduce(parameters: ps, into: i)
    }
    return program.types.introduce(.init(parameters: ps, usings: us), into: t)
```

(`TypeStore.introduce(_: ContextClause, into:)` is exactly "usings, then parameters".) Only the usings after `p` are inspected, not the head `t`: the first steps do not bind the head (section 3.8).

### 3.3 Two helpers

Both are private methods of `Typer`. The first rewrites witnesses inside types; the others are one-line uses of it.

```swift
  /// Returns `t` with each witness `w` occurring in the qualification of an associated type
  /// replaced by `replacement(w)` where that is not `nil`. A witness is visited after its parts
  /// and after the types it contains, so `replacement` sees them already rewritten.
  private mutating func rewritingWitnesses(
    in t: AnyTypeIdentity, _ replacement: (WitnessExpression) -> WitnessExpression?
  ) -> AnyTypeIdentity {
    func onType(_ s: inout TypeStore, _ n: AnyTypeIdentity) -> TypeTransformAction {
      guard let a = s[n] as? AssociatedType else { return .stepInto(n) }
      let q = onWitness(&s, a.qualification)
      return .stepOver(s.demand(AssociatedType(declaration: a.declaration, qualification: q)).erased)
    }
    func onWitness(_ s: inout TypeStore, _ w: WitnessExpression) -> WitnessExpression {
      let u = s.map(w.type, onType)
      let v: WitnessExpression.Value
      switch w.value {
      case .termApplication(let a, let b):
        v = .termApplication(onWitness(&s, a), onWitness(&s, b))
      case .typeApplication(let a, let ts):
        v = .typeApplication(onWitness(&s, a), ts.mapValues({ (x) in s.map(x, onType) }))
      case .nested(let a):
        v = .nested(onWitness(&s, a))
      default:
        v = w.value
      }
      let r = WitnessExpression(value: v, type: u)
      return replacement(r) ?? r
    }
    return program.types.map(t, onType)
  }
```

An overload with the same body takes and returns a `WitnessExpression` (it calls `onWitness` on its argument); it is used to clean results (3.6). The closures must not touch `self` other than through the `TypeStore` they receive, because `program.types` is being mutated; if the compiler rejects the capture of the non-escaping `replacement` by the local functions, wrap the call in `withoutActuallyEscaping`.

```swift
  /// Returns `true` iff `target` occurs as a witness in `t`.
  private mutating func mentions(_ target: WitnessExpression, in t: AnyTypeIdentity) -> Bool {
    var found = false
    _ = rewritingWitnesses(in: t, { (w) in if w == target { found = true }; return nil })
    return found
  }

  /// Returns `true` iff a witness in `t` is an assumed given.
  private mutating func mentionsAssumed(_ t: AnyTypeIdentity) -> Bool {
    var found = false
    _ = rewritingWitnesses(in: t, { (w) in if case .assumed = w.value { found = true }; return nil })
    return found
  }
```

These traverse the whole type. They are called only in threads that have bound a using (3.4), so their cost is not paid elsewhere. If a profile shows them, a bit in `TypeProperties` (four are free) set by `AssociatedType.properties` makes `mentionsAssumed` constant-time.

### 3.4 The environment and `formThread`

`ResolutionThread.Environment` gets two fields:

```swift
      /// The premises that are not hypotheses yet: the type of each mentions an assumed given
      /// that has no witness (`premsubst`). In the order in which they were assumed.
      var deferred: [Given] = []

      /// `true` iff a using of this thread was bound to an earlier one (`premsubst`).
      var dependent = false
```

Today six places build an `Environment` by hand and copy `ancestry`, `log` and `credit` one by one (`assuming(givens:)`, `assuming(given:)`, the `fixsubst` block of `match`, `eagerlyCoerced`, `threadContinuation`, and the premise code of `solveEquality`). A forgotten copy of `deferred` would lose a premise silently. Step 0 of section 6 therefore replaces them by one method, without change of behaviour:

```swift
      /// Returns a copy of `self` with the given substitutions and hypotheses.
      func with(
        substitutions s: SubstitutionTable, givens gs: [Given], nextGivenIdentifier n: Int? = nil
      ) -> Environment
```

and adds, next to `assuming(given:)`:

```swift
      /// Returns `(e, w)` where `e` is a copy of `self` in which `t` is a premise that is not a
      /// hypothesis yet and `w` is a placeholder for a term of type `t`.
      func deferring(given t: AnyTypeIdentity) -> (Environment, WitnessExpression)
```

which is `assuming(given:)` with the given appended to `deferred` instead of `givens` (the identifier is taken from `nextGivenIdentifier` in the same way).

In `formThread`, the existing block

```swift
      // The witness is an implication?
      if let i = program.types[witness.type] as? Implication {
        // Assume that the implication has a non-empty context.
        let h = i.usings.first!
        var (e, v) = environment.assuming(given: h)
        if TyperExperiments.loopcheck {
          e.ancestry[environment.nextGivenIdentifier] = ancestors.appending(queried)
        }
        witness = WitnessExpression(
          value: .termApplication(witness, v),
          type: program.types.dropFirstRequirement(.init(uncheckedFrom: witness.type)))
        environment = e
        continue
      }
```

becomes

```swift
      if let i = program.types[witness.type] as? Implication {
        let h = i.usings.first!
        // A using that mentions an earlier one of this thread waits for its witness.
        let waits = TyperExperiments.premsubst && environment.dependent && mentionsAssumed(h)
        var (e, v) = waits ? environment.deferring(given: h) : environment.assuming(given: h)
        if waits { TyperCounters.bump("premsubst.deferred") }
        if TyperExperiments.loopcheck { /* unchanged */ }
        var rest = program.types.dropFirstRequirement(.init(uncheckedFrom: witness.type))

        // Bind the usings after `h` that refer to it to the premise just assumed.
        if TyperExperiments.premsubst, i.usings.count > 1, let b = i.binders.first ?? nil {
          let j = program.types[rest] as! Implication
          let target = WitnessExpression(value: .reference(b), type: h)
          let us = j.usings.map({ (u) in
            rewritingWitnesses(in: u, { (w) in (w == target) ? v : nil })
          })
          if us != j.usings {
            rest = demand(Implication(context: us, binders: j.binders, head: j.head)).erased
            e.dependent = true
            TyperCounters.bump("premsubst.bound")
          }
        }

        witness = WitnessExpression(value: .termApplication(witness, v), type: rest)
        environment = e
        continue
      }
```

Notes.

- `target` compares the declaration *and* the type. `h` and the later usings were instantiated by the same type arguments (the universal quantifier is opened before the loop reaches the implication), so a reference to this using has exactly the type `h`. Earlier iterations have already rewritten the types inside later witnesses (`rewritingWitnesses` rewrites the type of a witness before the witness), which keeps the comparison exact for chains such as `T.X.X`.
- The head `j.head` is not rewritten.
- `environment.dependent` is false until the first binding, so `mentionsAssumed` is not called in other threads.
- A deferred using still gets its placeholder `.assumed(n)` in the witness, like any other.

**Capture (review).** The rewriting above replaces *every* occurrence of `target` in the later usings. That is right only if all of them are the clause's own references. An occurrence can also come from the caller: explicit type arguments are substituted into the callee's type by name resolution, before `formThread` sees it (the witness type is then an implication, not a universal type), and a type argument may mention the same declaration with the same type when the clause is instantiated at its own parameters. That is the case of a recursive call, and of any call made where the callee's using is itself a visible given:

```hylo
fun f<V where A is P, A.X is Q, V is R>() { f<W<A.X>>() }     // tests/s1-attack-capture-recursion.hylo
```

The usings of the call are `P<A>`, `Q<(A::$u).X>`, `R<W<(A::$u).X>>`, and the last `$u` is the caller's: `W<A.X>` was written in the body of `f`, where `A.X` is the associated type of `f`'s own requirement. The first version rewrote it too. The thread that discharges `P<A>` with the module's `given A is P { type X = B }` then proves `R<W<B>>` where the callee was promised `R<W<A.X>>`, and the call is accepted with the witness `f<W<A.X>>(c)(…)(W<B> is R)`, which is ill-typed. FULL rejects the program; FULL + `premsubst` as first written accepts it, and the self-check mode reports nothing. The same happens with a requirement that mentions a parameter (`f<T, V where T is P, T.X is Q, V is R>() { f<T, W<T.X>>() }`, `tests/s1-attack-capture-recursion-generic.hylo`, visible with `assocsubst`).

Inferred type arguments are not affected: `formThread` opens the universal type with fresh variables, the rewriting happens before they are assigned, and assignments are applied lazily.

The rule: *if the caller can name the witness that the binder refers to, the premise must be discharged by that very witness.* Rewriting a free occurrence to the premise and then substituting the same witness back gives the type the caller wrote, so both kinds of occurrence are then read correctly. `Environment` gets a third field,

```swift
      /// For each premise that later usings were bound to, the witness they referred to (`premsubst`).
      var bound: [Int: WitnessExpression] = [:]
```

copied by `with(…)`. `formThread` fills it where it sets `e.dependent = true`:

```swift
            e.bound[environment.nextGivenIdentifier] = target      // the identifier of the premise `v`
```

and `threadContinuation` starts with the test (it runs once per premise, in the continuation of the match that proved it, which is the only call in which that premise is the last item of the tail):

```swift
    // New (capture rule). `operand` is the witness just matched to the premise `last.assumed`.
    if let last = thread.tail.last, let target = thread.environment.bound[last.assumed],
      operand.witness.value != target.value, isVisibleGiven(target, from: scopeOfUse)
    {
      TyperCounters.bump("premsubst.captureCut")
      return .next([])
    }
```

`isVisibleGiven(_:from:)` is `givens(visibleFrom: scopeOfUse).joined().contains(where: { (g) in expression(referringTo: g) == target })`; it compares the value and the type, so it holds exactly when the clause is instantiated at the declared type of its using in a scope that sees that using. It is evaluated only when the witness differs, in threads that bound a using.

Effects: `s1-attack-capture-recursion` and `-generic` are rejected (the thread through the function's own requirement fails on `R<W<A.X>>`, the others are cut). `s1-keep-recursion` and `s1-keep-extension-sibling` are accepted with the witness they have today, and no longer depend on the function's own requirement being the nearest given. A call made outside the scope of the callee's using is never cut. What the rule gives up: inside a function, a recursive call at the function's own parameters cannot discharge the bound requirement with any other given than the function's own. The residual assumption is A7 of section 4.3.

### 3.5 `threadContinuation`

The function gains a prologue that *releases* deferred premises; the rest is the existing code operating on the environment after release.

```swift
  private mutating func threadContinuation(
    appending operand: SummonResult, to thread: ResolutionThread, in scopeOfUse: ScopeIdentity
  ) -> ResolutionThread.Advanced {
    var environment = thread.environment

    // New (review). The capture test of section 3.4 goes here, before anything else.

    // New. A premise whose type is now known becomes a hypothesis, on top of the stack, once
    // every hypothesis assumed after it has been discharged (invariant I2).
    if !environment.deferred.isEmpty {
      let solved = solvedWitnesses(thread.tail, operand)
      var gs = environment.givens
      var waiting: [Given] = []
      for g in environment.deferred {
        guard case .assumed(let i, let a) = g else { unreachable() }
        // Identifiers grow with time: a hypothesis with a larger one was assumed after `g`.
        if case .assumed(let youngest, _) = gs.last, youngest > i { waiting.append(g); continue }
        var t = program.types.reify(a, applying: operand.substitutions, withVariables: .kept)
        t = rewritingWitnesses(in: t, { (w) in
          if case .assumed(let j) = w.value { solved[j] } else { nil }
        })
        t = normalizingProjections(in: t)                       // step 3 (section 3.7)
        if mentionsAssumed(t) {
          waiting.append(g)
        } else if t[.hasError] {
          return .next([])
        } else if !commits(g, solved, operand, environment, in: scopeOfUse) {   // (review) 3.10
          return .next([])
        } else {
          gs.append(.assumed(i, t))
          TyperCounters.bump("premsubst.released")
        }
      }
      environment = environment.with(substitutions: environment.substitutions, givens: gs)
      environment.deferred = waiting
    }

    // Are there assumptions to discharge?                      (existing, on `environment`)
    if case .assumed(let i, let assumed) = environment.givens.last {
      var e = environment.with(
        substitutions: operand.substitutions, givens: environment.givens.dropLast())
      /* ancestry, trace: unchanged */
      var t = thread.tail
      t.append(.init(i, in: operand))
      return .next(
        summon(
          assumed, in: scopeOfUse, where: e, then: t, penalties: operand.penalties,
          ancestors: ancestors))
    }

    // New. No hypothesis is left but a premise still waits: excluded by invariant I2.
    else if !environment.deferred.isEmpty {
      TyperCounters.bump("premsubst.stuck")
      if TyperExperiments.selfcheck { selfCheckViolation("a deferred premise is never released") }
      return .next([])
    }

    // We're done; apply the continuation.                      (existing)
    else {
      assert(environment.givens.isEmpty)
      let r = applyContinuation(thread.tail[...], to: operand)
      return .done(environment.dependent ? withoutAssumed(r, thread.tail, operand) : r)
    }
  }
```

The witnesses of the premises discharged so far are read from the continuation. An item `(a, E)` of the tail means "the next result fills the hole `a` of `E`", so the result that filled `a` is the elaboration of the following item, or `operand` for the last one:

```swift
  /// Returns the witnesses of the assumed givens discharged so far in a thread whose continuation
  /// is `tail` and whose latest result is `operand`. A witness may mention assumed givens that
  /// are still pending.
  private mutating func solvedWitnesses(
    _ tail: [ResolutionThread.ContinuationItem], _ operand: SummonResult
  ) -> [Int: WitnessExpression] {
    var solved: [Int: WitnessExpression] = [:]
    var w = operand.witness
    for item in tail.reversed() {
      // `w` was found for `item.assumed`. The givens it assumes were discharged after it, if at
      // all, so their witnesses are already in `solved`.
      let known = solved
      let r = program.types.reify(w, applying: operand.substitutions, withVariables: .kept)
      solved[item.assumed] = rewritingWitnesses(in: r, { (x) in
        if case .assumed(let j) = x.value { known[j] } else { nil }
      })
      w = item.elaboration.witness
    }
    return solved
  }
```

What this implements:

- **Order.** Last in, first out among the premises whose types are known. A premise that mentions another one is off the stack until the other has a witness and everything assumed after itself has been discharged; it is then pushed on top and discharged next. The second condition matters because the equalities that `match` assumes for a coerced match leave no placeholder in the witness: without it a premise could be released while the derivation of the premise it mentions is still incomplete.
- **Hypotheses.** Only `environment.givens`, as today. Every site that reads the hypotheses (`summon`, `indexedSummon`, `solveEquality`, `canDeriveCoercions`, `mostGeneralEqualityThread`, `eagerlyCoerced`) reads that array and needs no change. A waiting premise is not a hypothesis. A released premise is a hypothesis for whatever is discharged above it afterwards (nothing, in practice: it is discharged immediately, and several premises released together are hypotheses for each other in the usual direction).
- **Penalties.** Unchanged definition: offsets count `environment.givens`. Waiting premises do not count.
- **Layers.** The number of steps of a derivation is unchanged; only their order changes.
- **Ambiguity.** If the premise that others wait for has several results, each continues as its own thread, as today, and the waiting premises are checked for each. (review) This is more than a matter of ties: it lets the waiting premises choose the witness. Section 3.10 describes what was observed and the rule that prevents it.

The cost is one pass over the tail per step of a thread that has waiting premises: quadratic in the size of a derivation, which the bound limits to 10. If it shows in a profile, carry `solved` in the environment.

**Nested resolutions (review).** A resolution started from the environment of a thread must not inherit its waiting premises: it has no continuation that could give them a witness, so it would end in the branch "stuck" and fail. Two places start one. The premise code of `solveEquality` builds its environment by hand with the hypotheses only, which is right and must stay so (it is an exception to assumption A5). The self-check search `searchDerives` copies the environment and must clear `deferred`; the implementation does (`e.deferred = []`), the first version of this document did not say so. `eagerlyCoerced`, `mayCoerce` and `canDeriveCoercions` only read `environment.givens` and start nothing. Any future nested search (the commit rule of section 3.10, tabling) has to follow the same rule.

### 3.6 Cleaning the result

`applyContinuation` substitutes placeholders in the *values* of witness expressions (`substituting(assumed:with:)`), not in types. After 3.4 the types of inner nodes of the final witness mention `.assumed`: the partially applied `f<U>($0) : (Q<(U::$0).X>) ==> …` and the placeholder of the deferred premise. They must not leave the engine.

```swift
  /// Returns `r` with the assumed givens that occur in the types of its witness replaced by their
  /// witnesses.
  private mutating func withoutAssumed(
    _ r: SummonResult, _ tail: [ResolutionThread.ContinuationItem], _ operand: SummonResult
  ) -> SummonResult {
    let solved = solvedWitnesses(tail, operand)
    let w = rewritingWitnesses(in: r.witness, { (x) in
      if case .assumed(let j) = x.value { solved[j] } else { nil }
    })
    return .init(witness: w, substitutions: r.substitutions, penalties: r.penalties)
  }
```

The type of the result itself (the head) and the substitution table contain no assumed given (invariant I1), so only inner types change.

### 3.7 Projections in the form name resolution gives them (step 3)

The caller's facts are stated with the types that name resolution builds. For `T.X` it resolves `T is P`, takes the witness `w`, and calls `typeOfImplementation(satisfying:in:)`, which has three branches:

1. "The witness is the result of a coercion?": the coercion is removed and the rule applied to the witness under it;
2. "The witness refers to a given declaration?": the result is the declared type of the implementation of `X` in that conformance (with `assocsubst`, instantiated with the type arguments of the witness);
3. otherwise the result is the opaque type `(T::w).X`.

A substituted premise must be brought to the same form, or it denotes the caller's type without being the caller's type. `normalizingProjections(in:)` therefore applies branches 1 and 2 to every projection of the type:

```
normalizingProjections(in t):
  repeat at most 8 times:
    collect the nodes n of t that are an AssociatedType (program.types.map with a closure that
      only records); let w = n.qualification and w' = w without its outer coercion applications
      (asCoercionApplication)
    keep n if   (a) w' != w                                                    -- branch 1 (review)
           or   (b) w' refers to a ConformanceDeclaration, has no variable, mentions no assumed
                    given, and is a plain reference (any application of one if assocsubst is on)
    if none: return t
    for each kept n:
      if (b) holds:  m = typeOfImplementation(satisfying: n.declaration, in: w')
                     replacement[n] = inhabitant of the metatype m, or .error
      else:          replacement[n] = AssociatedType(declaration: n.declaration, qualification: w')
      bump "premsubst.normalized"
    t = program.types.map(t) { n in replacement[n] → .stepOver, else .stepInto }
    if t has an error: return .error
  return .error
```

When only (a) holds, the result is `(T'::w').X`: the same projection without the coercion, which is what the third branch of `typeOfImplementation` builds for name resolution. The definition of a conformance is read only under the guards of (b), also below a coercion, so that a generic conformance is never read without its type arguments.

(review) The first version applied branch 2 only, and stated as assumption A3 that the witness recorded for a premise is the one name resolution used. That is false whenever the witness is a coercion. In

```hylo
fun f<T where T is P, T.X is Q>() {}
fun g<U, V where U == V, V is P, V.X is Q>() { f<U>() }       // tests/s1-attack-coerced-witness.hylo
```

`U is P` is proved by coercing the requirement `$r : P<V>`, the premise becomes `Q<(U::coerce($r)).X>`, and the caller's fact is `Q<(V::$r).X>`. The call is rejected (observed), and it is still rejected when the caller states its requirement as `U.X is Q`, the very projection the callee asks for (`s1-attack-coerced-witness-own-projection.hylo`), because name resolution turns the caller's `U.X` into `(V::$r).X` as well. With case (a) both are accepted. This is a prediction: the corrected function was not built.

Case (a) has a consequence that must be decided together with it. `tests/s1-reject-other-conformance.hylo` (`g<T, U where T == U, T is P, U is P, T.X is Q>() { f<U>() }`) was rejected by the first version only because of the same mismatch: among the witnesses of `U is P` is `T`'s requirement coerced along `T == U`, whose projection is, once the coercion is removed, the `T.X` that the caller knows to be `Q`. With case (a) and nothing else, that program is accepted through `T`'s conformance. Whether it should be is the question of section 3.10, whose rule keeps it rejected.

Restrictions, on purpose:

- A generic conformance is reduced only with `assocsubst`. Without it `typeOfImplementation` returns the declared type of the implementation without substituting the conformance's type arguments, and name resolution rejects `Box<B>.X` altogether ("expression does not denote a type", `unsimplified-projections/t11-generic-conf.hylo`). Such projections stay opaque: `(Box<B>::c<B>).X`.
- A where-clause requirement is an implicit binding, not a conformance declaration, so `(U::$r).X` is left alone, as it must be.
- A projection through a refined trait (`trait Q refines P`, `U is Q`, `U.X`) is an error type in name resolution today, in the caller's own clause; nothing here changes that.

### 3.8 What this does not fix: the head

`tests/s1-open-parameter-type.hylo`:

```hylo
fun h<T where T is P>(x: T.X) {}
fun g<U where U is P>(y: U.X) { h<U>(y) }     // cannot pass value of type '(U::P).X' to parameter '(U::P).X'
```

The parameter type is in the head of the callee's type. The constraint solver opens the callee's type before resolution runs (`Solver.swift`, call constraints):

```swift
      (_, callee) = program.types.open(k.callee)
      coercion = schedule(
        CoercionConstraint(on: f, from: k.callee, to: callee, at: program[f].site))
```

and checks the arguments against `callee`, whose parameter type still names the callee's own requirement. The result of the coercion (the witness for `U is P`) is never fed back into that type. Fixing it needs the solver to know which witness a parameter type depends on, which is option D. If the head were bound in `formThread` alone, the root match of every call to such a function would fail against the solver's unbound copy, and programs that are accepted today would be rejected: `tests/s1-keep-result-type.hylo` calls a function whose result type is `W<T.X>` without constraining the result, and is accepted by base and FULL. So the first steps leave heads alone, for all threads.

A later, separate step can bind heads for the two kinds of thread where the solver is not involved: candidates of `summon` (givens such as `given <T where T is P> => Box<T.X> is Q`) and extension applicability (`applies`). The obstacle is known: the mismatching parts that `match` assumes would then mention assumed givens, `canDeriveCoercions` would have to let them through, and they would have to be deferred like usings. Invariant I1 no longer holds in that form. It should get its own flag, after the solver question is settled. Only then can the workaround of section 1.3 be deleted; until then it still serves projections that come from heads.

A requirement of a member that mentions a requirement of the enclosing extension or type also stays opaque: binders are computed per clause (section 3.2), and the reference crosses two clauses. (`review/attacks/d4-ext-member-clause.hylo`: rejected before and after.)

(review) Since this was written, heads of *calls* have been handled in the constraint solver by the flag `headsubst` (see `../BRIEF2.md`): `s1-open-parameter-type.hylo` is accepted under the configuration NEW. Heads of givens and of extensions are still not bound, and the premise code of `solveEquality` still fires for them (three programs of `../reference`, `eqsolve.premises=1` with `premsubst` on).

### 3.9 Two side effects to know about

- **Diagnostics.** When a callee coercion fails, `diagnoseInvalidCoercion` (in `Solver.swift`) resolves each using of the callee separately (`let ws = tp.summon(x, in: scopeOfUse)`) to say which one has no unique given. It does so on the unbound types, so for a clause with a dependent requirement it will keep blaming that requirement (`Q<(U::P).X>`) even when another one failed. This does not affect verdicts. The clean fix is to make that loop resolve the usings in order and substitute, with the functions of 3.3; it can wait until the tests pass.
- **Serialized modules.** `Implication` and `ContextClause` are `@Archivable`. A new stored property changes the archive format, and a module typed without the flag has no binders: its generic declarations with dependent requirements behave as today when used from a module typed with the flag. `tc-bench` types the standard library in the same process, so the experiments are not affected.

### 3.10 Which witness a requirement gets: the commit rule (review)

The first version says (section 3.5, "Ambiguity") that if the premise others wait for has several results, each continues as its own thread. That is how the engine treats every premise, and for independent premises it is harmless: whether `B` holds does not depend on which witness proved `A`. For a dependent premise it does, so the engine now *chooses the witness of a requirement by whether the requirements after it hold*. Not only among witnesses of equal rank (question 4 of the first version): a witness that is farther, or of a later layer, wins as soon as the nearest one fails. Observed on the implementation:

| Program (`tests/`) | Alone, the first requirement resolves to | FULL + `premsubst`, first version |
|---|---|---|
| `s1-attack-shadowed-requirement`: `fun g<where A is P>() { f<A>() }`, the module has `given A is P { type X = B }` and `B is Q` | `g`'s requirement (nearest; `need<A>()` selects it), whose `X` is abstract | accepted through the module's conformance |
| `s1-attack-shadowed-local-given`: a local `given A is P { type X = C }` shadows the module's, `C` is not `Q` | the local conformance | accepted through the module's conformance |
| `s1-attack-nonminimal-witness` (with `assocsubst`): a one-step witness with `X = C`, a two-step witness with `X = B` | the one-step witness | accepted through the two-step witness |
| `s1-open-ambiguous-dependency`: two conformances of equal rank, one with a `Q` associated type | ambiguous | accepted |
| `s1-attack-shadowed-result-type` (with `headsubst`): as the second row, `f` returns `W<T.X>` | the local conformance, so `A.X` is `C` in `main` | `let x: W<B> = f<A>()` accepted; `let x: W<A.X> = f<A>()` rejected with "no coercion from 'W<X>' to 'W<X>'" |

In each of these, the requirements of `f` written out at the call site (`A is P`, then `A.X is Q` with the call site's `A.X`) do not hold (in the fourth row `A.X` is ambiguous there), and the call is accepted. Shadowing a conformance has no effect on the call, and the type of the call is not the type its signature gives when read at the call site. Name resolution, by contrast, *commits*: `A.X` is the projection through the result of resolving `A is P` alone.

**The rule.** A premise that another premise waits for must have been discharged by the witness that resolving it alone gives, under the hypotheses it had. If resolving it alone is ambiguous, the thread fails. It is a filter on threads: it never produces a witness, so nothing can be accepted because of it.

Flag: `premcommit` (it accepts fewer programs than `premsubst` alone; whether it is the language's rule is question 4 of section 7). Counters: `premcommit.checked`, `premcommit.cut`, `premcommit.ambiguous`, `premcommit.open`.

`Environment` records, when a premise is popped in a thread that bound a using, what was asked and under which hypotheses. In the branch "Are there assumptions to discharge?" of `threadContinuation`, after `e` is built:

```swift
      if TyperExperiments.premcommit && environment.dependent { e.discharged[i] = (assumed, e.givens) }
```

(`var discharged: [Int: (goal: AnyTypeIdentity, hypotheses: [Given])] = [:]`, copied by `with(…)`.) The release loop calls, for a premise `g` about to be released:

```
commits(g, solved, operand, environment, in scopeOfUse) -> Bool:
  if !premcommit: return true
  for each j such that .assumed(j) occurs in the type of g as deferred (before substitution):
    (goal, hyps) = environment.discharged[j], both reified with operand.substitutions
    w = solved[j]                         -- free of assumed givens, or g would not be released
    if goal, a hypothesis or w has a variable: bump "premcommit.open"; continue
    rs = hyps.isEmpty
           ? summon(goal, in: scopeOfUse)                                  -- the public, cached one
           : takeSummonResults(
               from: summon(goal, in: scopeOfUse,
                            where: Environment(substitutions: .init(), givens: hyps,
                                               nextGivenIdentifier: environment.nextGivenIdentifier),
                            then: [], penalties: 0),
               in: scopeOfUse)
    bump "premcommit.checked"
    guard let r = rs.uniqueElement else: bump "premcommit.ambiguous"; return false
    v = r.witness reified with r.substitutions, its assumed givens replaced through solved
    if the value of v differs from the value of w: bump "premcommit.cut"; return false
  return true
```

Notes.

- The environment of the nested search is built by hand, without `deferred` (section 3.5, "Nested resolutions"). The premise code of `solveEquality` runs the same kind of nested search today.
- Values are compared as trees of references and applications, ignoring the types recorded on inner nodes: `w` went through `solvedWitnesses`, `v` through `applyContinuation`, and the two may annotate an inner node with types that differ in spelling.
- A premise with unification variables cannot be resolved alone in a meaningful way (the search would enumerate instances), so it keeps the joint reading; `premcommit.open` counts these (`s1-gain-open-variable-a` has one).
- Cost: one resolution per premise that others wait for, per thread; cached by `summon(_:in:)` when the premise has no hypotheses, which is the case of the first requirement of a call.
- The nested search runs inside a step of the outer one. It must save and restore `lastResolutionExhaustedDepth` (the outer loop reads it after its last layer), as any nested search should.
- The filter relies on the nested search and the thread seeing the same givens. They run at the same moment in the same typer state, so `declarationsOnStack` is the same for both. If they ever differ, the effect is a rejection.

Predicted verdicts (nothing here was built):

| Program | `premsubst` first version (observed) | + coercions removed (3.7) | + commit rule |
|---|---|---|---|
| every `s1-gain-*`, `s1-keep-*` | accepted | accepted | accepted |
| `s1-attack-coerced-witness`, `-own-projection` | rejected | accepted | accepted (the coerced witness is the only one) |
| `s1-reject-other-conformance`, `s1-attack-other-conformance-equality` | rejected | **accepted** | rejected |
| `s1-attack-shadowed-requirement`, `-local-given`, `-nonminimal-witness`, `s1-open-ambiguous-dependency`, `s1-attack-shadowed-result-type` | accepted | accepted | rejected |
| `s1-reject-ambiguous-both` | rejected (two results) | rejected | rejected |

The middle column is why sections 3.7 and 3.10 belong together: removing coercions alone turns the analogue of the compiler's negative test `associated-type-inequality.hylo` into an accepted program.

The commit rule does not replace the capture rule of section 3.4: when a nearer given shadows the function's own requirement inside a recursive call, the commit rule selects the nearer given and a captured reference would be rewritten to it.

## 4. Why it is correct

Notation: a premise is *pending* from the moment it is assumed until a candidate has matched it; it is a *hypothesis* if it is in `environment.givens` and *waiting* if it is in `environment.deferred`.

### 4.1 Invariants

**I1. The matcher never sees an assumed given.** With the flag on, the type of every goal passed to `summon`, the type of every hypothesis and every value of a substitution table contain no `.assumed` witness.

*Argument.* Assumed givens enter types in one place: the rewriting of later usings in `formThread`. A using rewritten that way satisfies `mentionsAssumed`, so it is deferred. A deferred type is not unified with anything. It leaves `deferred` only through the release of 3.5, which substitutes it and checks `!mentionsAssumed`. The head of a candidate is not rewritten. Mismatching parts recorded by `match` are subterms of a head and of a goal, both clean. Substitution tables are filled by unification of clean types.

*Assertions.* At the entry of the private `summon`: `assert(!environment.dependent || !mentionsAssumed(u))`, under `selfcheck` (it traverses the type). In the release loop the check is part of the algorithm.

**I2. A premise only mentions premises assumed before it; a waiting premise is always released.** If the substituted type of a waiting premise `p` mentions `.assumed(k)`, then `k` is pending and was assumed before `p`.

*Argument.* At creation, a using mentions earlier usings of its clause only (A8). Later, substitution can add mentions: `p` mentions `k`, `k` is discharged by a witness that uses a hypothesis `q`. Hypotheses are discharged last in, first out, so when `k` is discharged every hypothesis assumed after `k` is gone; `q` was assumed before `k`, hence before `p`. Premises assumed by the candidate that proved `k` are newer than `p`; `p` is not released while any of them is on the stack (the test on identifiers in 3.5).

*Consequence.* When no hypothesis is left, the waiting premise assumed first mentions nothing that is pending and nothing on the stack is newer, so it is released. The branch "stuck" of 3.5 is unreachable; it is kept as a counter and a self-check violation, and fails the thread (a rejection, never a wrong acceptance).

*Consequence.* A released premise was assumed after every hypothesis still on the stack, by the test on identifiers, so pushing it on top restores the order in which premises were assumed. It relies on identifiers being allocated in increasing order within a thread (`nextGivenIdentifier`); assert it in `assuming` and `deferring`.

**I3. The elaboration is well typed.** The goal posed for a released premise is the type of its using in which each reference to an earlier using is replaced by the witness that the same thread found for it. The final witness `f(w0)(w1)` therefore has `w1 : Q<(U::w0).X>`, which is the dependent reading of the clause `T is P, T.X is Q` at `T = U`.

*Assertion.* Under `selfcheck`, after `withoutAssumed`: no `.assumed` remains in the witness or its types (`mentionsAssumed` on the witness overload). `applied(_:to:)` already checks each proof step it builds; the same check can be run over the final witness.

**I4. Nothing changes without a dependent using.** If no implication opened during a resolution has a binder, `dependent` stays false, `deferred` stays empty, and every new branch is skipped: the prologue of `threadContinuation` (guarded by `!deferred.isEmpty`), the deferral test in `formThread` (guarded by `dependent`), the cleaning (guarded by `dependent`).

*Assertion.* `assert(environment.dependent || environment.deferred.isEmpty)` in `threadContinuation`.

**I5 (review). A reference that the caller wrote is read as the caller wrote it.** If a using of an instantiated clause contains an occurrence of the binder's witness that does not come from the clause, then the witness substituted for it is that same witness.

*Argument.* Such an occurrence has the value `.reference(b)` and the type `h` of the instantiated using, and it was written (or abbreviated by an alias) in a scope where name resolution could produce it, that is, where `b` is a given with declared type `h` (assumption A7). The capture test of section 3.4 cuts every thread that discharges the premise with another witness in exactly that situation, and `.reference(b)` substituted for `.assumed(i)` restores the occurrence.

*Assertion.* None is possible inside the engine, because the two kinds of occurrence are the same expression; the tests are `s1-attack-capture-recursion*.hylo`. `premsubst.captureCut` must be 0 on every program in which no call is made from inside the declaration it calls.

### 4.2 What is not assumed

The workaround assumes that resolving a premise twice gives the same witness. Here each premise is resolved once, and the witness substituted is the one in the derivation. Nothing depends on uniqueness, closedness or determinism. (review) The commit rule of section 3.10 resolves a premise a second time, but only to cut threads: if the two resolutions disagree the program is rejected, and no witness comes from the second one.

### 4.3 Assumptions about the rest of the type checker

| | Assumption | How to check it |
|---|---|---|
| A1 | In the type of a using, a reference to an earlier using of the same clause is the witness `(.reference(r), type: T)`, where `r` is what `expression(referringTo:)` returns for the earlier using and `T` its declared type; possibly inside a coercion application. | In `Typer.introduce` under `selfcheck`: every witness `.reference(r)` with `r` among the clause's usings that occurs in a later using has type `us[k]`. `premsubst.binders` must be positive on `tests/s1-gain-*.hylo`. |
| A2 | Substitution, reification and dealiasing apply the same transformation to a using and to the references to it, and keep `binders`. | In `formThread` under `selfcheck`: if `i.binders.first` is set and no later using was rewritten, report a violation. |
| A3 | After `normalizingProjections`, the type of a substituted premise is the *same type identity* as the one name resolution builds for the same projection at the call site. (review) The first version assumed this of the raw witness; it is false for a witness that is a coercion, which name resolution removes (section 3.7). It holds by construction for the three branches of `typeOfImplementation` if the witness found by the thread is the witness that `summon` returns to name resolution for the same goal in the same scope. | Observed for references to requirements and to non-generic conformances (all `s1-gain-*`), and for applications of generic conformances with `assocsubst` (`s1-gain-nested-dependent-given`). Predicted for coercions (`s1-attack-coerced-witness*`). Under `selfcheck`: when the goal of a discharged premise was closed and it had no hypotheses, compare with the witness that `summon(goal, in: scopeOfUse)` returns, and count the disagreements (`selfcheck.premsubst.otherWitness`); with `premcommit` the same comparison is part of the algorithm. |
| A4 | For a reference to a non-generic conformance declaration, `typeOfImplementation` returns the metatype of the implementation, and its only effects are memoized declared types. | `s1-gain-conformance-concrete`, `s1-gain-equality-concrete`, `s1-reject-concrete-mismatch`. `expression(referringTo:)` already computes declared types inside resolution, so re-entrancy is not new. |
| A5 | No `Environment` of a thread is built without copying the new fields, and no nested search inherits `deferred` (section 3.5, "Nested resolutions"). | After step 0, `Environment(` occurs only in `with`, `assuming`, `deferring`, `empty`, and in the two nested searches that must *not* copy them (the premise code of `solveEquality`, `commits`); `searchDerives` clears `deferred`. |
| A6 | No later phase needs the types of inner nodes of a witness to mention the callee's own using. | They are rewritten to the caller's witnesses by 3.6; the semantic dump shows the difference, only in programs with dependent usings. |
| A7 | (review) An occurrence of `(.reference(b), type: h)` in a using of an instantiated clause, where `b` is the binder of that clause for the using of type `h`, either comes from the clause or was written where `b` is a visible given of declared type `h`. The first version assumed that such an occurrence "resolves to the same requirement unless a nearer given shadows it" and left it unchecked; that is wrong, since every witness of the premise is tried and a farther one wins when the nearer fails (`s1-attack-capture-recursion`). | Enforced by the capture test where `b` is visible. Not checkable where it is not: the type would have to reach an explicit type argument without being written in the scope of `b`. The types of `b`'s scope that escape it are heads (a result type `W<T.X>`), and a caller cannot spell them. If a way is found, the fallback is to cut whenever `h` is the declared type of `b`, visible or not, which loses calls from outside to clauses whose bound requirement mentions no parameter (`where A is P, A.X is Q`). |
| A8 | The type of a using mentions only earlier usings of its clause. | `initializeContext` computes them in order, each hidden until it is done ("resolution can't 'see' `q` while it is computing the type of `p`"). A reference to a later using would simply not be bound. |

### 4.4 Why the compiler's tests are unaffected

By I4, a resolution changes only if it opens an implication with a binder, that is, the type of a declaration in which a using mentions an earlier using. A search of `Tests/CompilerTests` and of the standard library for where clauses that constrain a projection finds one declaration:

```hylo
fun f2<T, U where T == U, T is P, U is P, T.X == U.X>(x: U.X) {      // positive/associated-type-equality.hylo
```

`f2` is never called, and it is a function, not a given, so no thread is formed from its type. The standard library declares no associated type. Expected: `premsubst.bound = 0` on all 192 files and identical semantic dumps. If the dump of any file differs with the flag on, the binders have leaked into something observable; see the stop conditions of section 6.

### 4.5 What changes in programs with dependent usings

For a resolution that does bind a using, compared with today:

1. the dependent premise is discharged after the premises it mentions, with their witnesses in its type;
2. while it waits it is not a hypothesis, and does not count in penalty offsets;
3. when it is discharged, the premises it mentions are no longer hypotheses (they have been discharged);
4. witnesses of equality premises are shorter (no detour through the callee's own projection).
5. (review) the witness of a premise that others wait for is chosen among *all* its derivations by whether the waiting premises hold, unless the commit rule of section 3.10 is on.

Items 2 and 3 can change penalties and, through the bound, sizes, but only among derivations of such resolutions, which today fail unless the workaround applies.

Among the 76 research programs with a requirement on a projection (`experiments/dependent-programs.txt`, results in `experiments/dependent-programs.jsonl`), FULL accepts 32. In most of them the dependent clause belongs to a declaration that is checked but never used by another, so nothing is bound. The workaround fires in 9, which are the programs to diff first. Predicted from the design:

| Program (`research/report/test-programs/`) | FULL today | With `premsubst` |
|---|---|---|
| `unsimplified-projections/t4-generic-caller`, `v5-generic`; `equalities/x10b-ext-where-assoc`, `eq-regress-judge-x10b-ext-where-assoc` | accepted | accepted, `eqsolve.premises=0` |
| `unsimplified-projections/min`, `t1`; `equalities/assoc-eq-call-incomplete`, `x10-ext-where-assoc` | rejected | accepted from step 3 (a projection through a declared conformance) |
| `unsimplified-projections/t8-cond-call` | rejected | rejected: the conformance is generic, its projection stays opaque (3.7) |

(review) Observed on `eq25`, FULL against FULL + `premsubst`, with and without `selfcheck` (`scripts/review_run.py`, results in `review/corpus-eq25.jsonl`): the nine programs behave as the table says (`t8-cond-call` is accepted once `assocsubst` is added), no other of the 76 programs changes its verdict or its messages, no self-check violation is reported, and `premsubst.stuck` is 0 everywhere. The comparison of FULL with NEW over 997 programs (`../compare-new.jsonl`) has 30 programs in which a using is bound: 16 go from rejected to accepted, 10 stay accepted, 4 stay rejected, and none goes from accepted to rejected.

## 5. Test plan

`tests/` holds the programs. Each has a comment with the expected verdict after the change and the reason, and two recorded lines:

- `// currently:` the verdict and counters under base and FULL on `eq9`, which has none of this design (`scripts/record.py`, raw results in `tests/current.jsonl`);
- `// observed:` (the `s1-*` programs) what the implementation of the first version does on `eq25`, under FULL + `premsubst`, the same with `selfcheck`, with `assocsubst`, and under NEW (`scripts/record_observed.py`, raw results in `tests/observed.jsonl`).

The table is generated from those two files by `review/test_table.py`. "Step" is the step of section 6 that the program tests. A bold expectation differs from what the first version does. The programs named `s1-attack-*` were added by the review; the comment of each explains the attack.

| Program | Step | Expected, design as revised | Observed: first version (FULL + `premsubst` / NEW) | Currently (base / FULL) |
|---|---|---|---|---|
| `s1-gain-conformance-generic` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-conformance-two` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-chain` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-middle` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-extension` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-given` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-static-method` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-equal-parameters` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-extension-concrete` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-conformance-concrete` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-equality-concrete` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-given-concrete` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-open-variable-a` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-open-variable-b` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-nested-dependent-given` | 3 | accepted with `assocsubst`, `premsubst.stuck=0`; rejected without | rejected / accepted | rejected / rejected |
| `s1-keep-equality-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted | accepted / accepted |
| `s1-keep-extension-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted | accepted / accepted |
| `s1-keep-recursion` | 2, 5 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-extension-sibling` | 2, 5 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-result-type` | 2 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-hypothesis` | 2 | accepted, trace identical | accepted / accepted | accepted / accepted |
| `s1-reject-missing-requirement` | 2 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-concrete-mismatch` | 3 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-given-concrete` | 3 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-ambiguous-both` | 3 | rejected (two results) | rejected / rejected | rejected / rejected |
| `s1-reject-duplicate-requirement` | – | rejected where the clause is declared | rejected / rejected | rejected / rejected |
| `s1-reject-cyclic-definition` | 3 | rejected at the conformance, terminates | rejected / rejected | rejected / rejected |
| `s1-reject-capture-control` | – | rejected | rejected / rejected | rejected / rejected |
| `s1-attack-capture-recursion` | 5 | **rejected** | accepted / accepted | rejected / rejected |
| `s1-attack-capture-recursion-generic` | 5 | **rejected**, also with `assocsubst` | rejected / accepted | rejected / rejected |
| `s1-attack-method` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-initializer` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-trait-requirement` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-coerced-witness` | 7 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-coerced-witness-own-projection` | 7 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-reject-other-conformance` | 7, 8 | rejected with `premcommit`; accepted with step 7 alone | rejected / rejected | rejected / rejected |
| `s1-attack-other-conformance-equality` | 7, 8 | rejected with `premcommit`; accepted with step 7 alone | rejected / rejected | accepted / rejected |
| `s1-attack-shadowed-requirement` | 8 | rejected with `premcommit`; accepted without | accepted / accepted | rejected / rejected |
| `s1-attack-shadowed-local-given` | 8 | rejected with `premcommit`; accepted without | accepted / accepted | rejected / rejected |
| `s1-attack-nonminimal-witness` | 8 | rejected with `premcommit`; accepted without, given `assocsubst` | rejected / accepted | rejected / rejected |
| `s1-open-ambiguous-dependency` | 8 | rejected with `premcommit`; accepted without; question 4 | accepted / accepted | rejected / rejected |
| `s1-attack-shadowed-result-type` | 8 | rejected with `premcommit`; accepted without, given `headsubst` | rejected / accepted | rejected / rejected |
| `s1-attack-shadowed-result-type-own` | – | rejected | rejected / rejected | rejected / rejected |
| `s1-attack-where-order-a` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-attack-where-order-b` | 2 | rejected by the bound (`summon.depthExhausted=1`); accepted under a height bound | rejected / rejected | rejected / rejected |
| `s1-open-parameter-type` | – | rejected by `premsubst`; accepted with `headsubst` | rejected / accepted | rejected / rejected |

All 60 recorded `// currently:` lines of the first version were re-run and agree. Under the first version no program has a self-check violation and `premsubst.stuck` is 0 in all of them.

The programs `s2-*` and `s3-*` of the same directory belong to sections 8.3 and 9.1; they are recorded in the same way and keep their current verdicts and counters under `premsubst` (observed; none has a dependent requirement).

Beyond these:

1. **The oracle** (types, bindings, witness tables, diagnostics, witnesses) on the 192 compiler tests, flag on against flag off, alone and added to MIN5 and to FULL: identical. The same with `premcommit` added, which must not fire: `premcommit.checked = 0`.
2. **The research programs**: `python3 scripts/review_run.py --configs FULL,FULL+premsubst,FULL+premsubst+selfcheck` on the files of `experiments/dependent-programs.txt` before and after each step. Every change of verdict must be one of: a program of the shape of section 1.1 now accepted, or explained in writing. A program accepted today and rejected with the flag is a defect. (Done for the first version: section 4.5.)
3. **Metamorphic**: for each `s1-gain-*` program, move the dependent requirement to every position after the one it mentions (`s1-gain-middle`, `s1-gain-open-variable-a/b` are instances): same verdict, *provided the derivation stays within the bound in every order*. (review) The proviso is needed: two dependent requirements are hypotheses for each other in one direction only, like any two requirements, so `s1-attack-where-order-a` (9 steps) is accepted and `-b` (13 steps) is rejected. A metamorphic test must therefore compare runs at `HYLO_TC_MAXDEPTH=40`, or be restricted to derivations of at most 5 steps. Renaming and adding an unrelated requirement: same verdict.
4. **Self-check mode** on all of the above: `premsubst.stuck = 0`, no violation.
5. **Counters as evidence that the new path ran**: `premsubst.bound > 0` and `premsubst.released > 0` on every `s1-gain-*`; `premsubst.normalized > 0` on the concrete ones; all zero on the compiler tests. `premsubst.captureCut > 0` on the two capture programs and on no other program of this directory except, possibly, `s1-keep-recursion` and `s1-keep-extension-sibling` (only if another given of the same type is in scope). `premcommit.cut > 0` or `premcommit.ambiguous > 0` on every program whose expectation says "rejected with `premcommit`".
6. **The corrected steps are predictions.** The column "Expected" for steps 5 to 8 was derived by hand from the traces of the first version; none of it was run.

## 6. Implementation order

Each step builds and is tested on its own. Lines are added or changed lines, estimated. Steps 0 to 3 are done (commit `0bbd27e`; that commit also contains `headsubst`, and the part that belongs to this design is about 340 lines, against 330 estimated). Steps 5 to 8 come from the review and are the work that remains; each is small, and 5 should be done before the flag is used for anything.

| Step | Change | Lines | Test | Status |
|---|---|---:|---|---|
| 0 | `Environment.with(substitutions:givens:nextGivenIdentifier:)`; replace the hand-written copies. No flag. | 25 | Oracle identical on everything. Counters identical. | done |
| 1 | Flag and counters. `Implication.binders`, `ContextClause.binders`; `dropFirstRequirement`, `lifted`, `modified`, `contextAndHead`, `introduce(usings:binders:into:)`; `Typer.introduce` computes binders when the flag is on; `rewritingWitnesses`, `mentions`. Nothing reads the binders yet. | 55 + 40 | Flag on: oracle identical on the 192 tests and on the research programs. `premsubst.binders > 0` on `s1-*`, `= 2` in `associated-type-equality.hylo` (the two requirements that `T.X == U.X` mentions), `= 0` elsewhere in the tests. | done, except `ContextClause.binders` (step 6) |
| 2 | `deferred`, `dependent`, `deferring(given:)`; the `formThread` block; the prologue and the two new branches of `threadContinuation`; `solvedWitnesses`; `withoutAssumed`; the assertions of I1 and I4. | 130 | The six generic `s1-gain-*` accepted; `s1-keep-*`; `s1-reject-*`; test plan items 1 to 3 and 5. | done |
| 3 | `normalizingProjections(in:)` and its call in the release loop. | 40 | The three concrete `s1-gain-*` accepted; `s1-reject-concrete-mismatch` rejected; `s1-open-ambiguous-dependency` recorded. | done; reduces generic conformances too when `assocsubst` is on |
| 4 | Self-checks: A1, A2, A3, I3. | 40 | Test plan item 4. | partly: the checks of A2 and I3 exist; those of A1 and A3 do not |
| 5 | **Capture rule** (section 3.4): `Environment.bound`, filled in `formThread`; the test at the head of `threadContinuation`; `isVisibleGiven(_:from:)`; counter `premsubst.captureCut`. Under `premsubst`, no new flag: it removes a wrong acceptance. | 20 | `s1-attack-capture-recursion` and `-generic` rejected (the second also with `assocsubst`); `s1-keep-recursion`, `s1-keep-extension-sibling` accepted with the same witness; every other verdict of section 5 unchanged; test plan items 1 and 2. | to do, first |
| 6 | **`ContextClause.binders`** (section 3.2): the field, `contextAndHead`, `introduce(_: ContextClause, into:)`. | 20 | `s1-attack-method`, `-initializer`, `-trait-requirement` accepted with `premsubst.bound > 0`; a function bundle with a dependent clause likewise; oracle identical on the compiler tests. | to do |
| 7 | **Coercions removed in step 3** (section 3.7, case (a)). | 5 | `s1-attack-coerced-witness`, `-own-projection` accepted. With step 8 off, `s1-reject-other-conformance` and `s1-attack-other-conformance-equality` become accepted: land it together with step 8, or record the two as open. | to do |
| 8 | **Commit rule** (section 3.10), flag `premcommit`: `Environment.discharged`, `commits`, the call in the release loop, four counters. | 35 | The column "+ commit rule" of the table in 3.10; `premcommit.cut = 0` and `premcommit.ambiguous = 0` on every `s1-gain-*` and `s1-keep-*`; `premcommit.checked = 0` on the compiler tests. | to do; the default awaits question 4 |
| later | Bind heads for givens and extensions, behind its own flag; then delete the premise code of `solveEquality` (about 80 lines, `premiseResolutionDepth`, the `eqsolve.untrusted` path for premises). | – | Section 3.8. | calls are covered by `headsubst`; givens and extensions are not |

What the first estimate left out, found when the design was implemented or reviewed: the helpers of 3.3 had to be static functions over the `TypeStore` (a closure cannot capture the typer while `program.types` is being mutated), with `withoutActuallyEscaping` wrappers; `normalizingProjections` needs the guards "no variable, no assumed given" on the witness before calling `typeOfImplementation`; `searchDerives` must clear `deferred` (section 3.5); and steps 5 to 8 above, about 80 lines.

**Results that should make us stop.**

- Step 1: a semantic dump differs with the flag on in a program without dependent usings. Then recording binders changes a type identity that something compares. Fall back to option (b) of section 2 (no change of representation), which costs the exactness discussed there. (Not observed.)
- Step 2: an `s1-gain-*` program is still rejected because the substituted type is not the caller's type although they denote the same thing (A3 fails). (review) This did happen, for witnesses that are coercions; the fix is local (step 7). If a further case appears that `typeOfImplementation` does not explain, that is, a witness that the thread and name resolution spell differently for the same goal in the same scope, the approach needs a normal form for witness expressions, and option D or the normalization design of `research/followup/design-eqnorm` should take over.
- Step 2: `premsubst.stuck > 0` on any program. Then invariant I2 is wrong and the order of release must be re-derived before going on; failing the thread is only a safe way to find out. (Not observed: 0 on about 1,000 programs.)
- Step 5: a program is found in which a free occurrence of a binder reaches a using outside the scope of the binder (assumption A7). Then use the fallback of A7, and move to placeholders (section 2) before relying on the flag.
- Step 8: `premcommit.cut > 0` on a program whose every requirement has a single witness. Then the two resolutions of a premise spell one witness in two ways, and the comparison needs the normal form mentioned above; until then keep `premcommit` off and record the programs of section 3.10 as accepted.
- Any step: a program of the research set that FULL accepts today is rejected with the flag and the reason is not one of items 2 and 3 of section 4.5 combined with the bound. (Not observed.)

## 7. Open questions for the language designers

1. **Are the pending requirements of a clause meant to be assumptions for its other requirements?** Today they are, in one direction (a requirement is an assumption for those written after it), which makes the verdict depend on the order of the clause through the bound (`s3-keep-where-order-a` against `s3-gain-where-order-b`). If the answer is no, hypotheses can be removed, penalties no longer depend on the number of pending premises, and option B (declaration order) becomes result-preserving up to penalties. If yes, should a requirement that has just been proved remain available to the dependent ones proved after it (it is not, in this design)?
2. **Is `A.X` through a declared conformance equal to its definition inside resolution?** Step 3 says yes for non-generic conformances, as name resolution does. For generic conformances the compiler has no answer yet (`Box<B>.X` does not denote a type).
3. **Should a call typecheck when a parameter type mentions an associated type of a requirement** (`h<U>(y)` in 3.8)? Presumably yes; it decides whether the solver must carry witness variables (option D).
4. **Is the witness of a requirement chosen on its own, or together with the requirements that depend on it?** (review; this replaces the narrower question about witnesses of equal rank.) On its own (the commit rule, section 3.10): `T is P` gets the witness that resolving it alone gives, as name resolution does when the caller writes `T.X`, and the dependent requirements are checked against that witness; an ambiguity of `T is P` alone is an error. Together (the first version of this design, and how the engine treats independent premises): every witness of `T is P` is tried and the smallest derivation of the whole clause wins, so that a shadowed or more distant conformance is selected when the nearest one does not satisfy a dependent requirement, and the type of the call is not the type its signature has at the call site (`s1-attack-shadowed-*`, `s1-open-ambiguous-dependency`). The same choice decides whether `s1-reject-other-conformance`, the analogue of the compiler's negative test `associated-type-inequality.hylo`, is rejected. The review recommends "on its own".
5. **May a clause list the same requirement twice** (`T is P, T is P`)? Answered by the compiler as it is: a projection `T.X` in a later requirement is then an error where the clause is declared ("ambiguous use of 'X'", `tests/s1-reject-duplicate-requirement.hylo`), so the design never sees such a clause with a binder.
6. **Penalties.** The offset of a given counts the pending premises. Is that intended as part of the ranking, or an accident of representing premises and hypotheses by one array? (It is the only reason penalties of dependent programs change here.)
7. The questions about the bound are in section 9.4.

## 8. Tabling (shorter treatment)

### 8.1 Measurements

*How much repeats today.* `scripts/repeats.py` reads the trace of base and counts the goals that are premises on completed derivations (the trace does not print the subgoals of failing branches; `summon.subgoals` counts all of them).

| | Resolutions | End after 1 layer | Most layers | Premise goals on completed derivations | Distinct | Subgoals posed, base / FULL |
|---|---:|---:|---:|---:|---:|---:|
| Standard library | 5,417 | 5,214 (96%) | 5 | 160 | 25 | 699 / 291 |
| 114 positive tests (user module) | 7,025 | 6,534 (93%) | 9 | 259 | 181 (per file) | 9,099 / 668 |

- In the standard library the repeated goals are `Movable<Bool>` (17 times), `Movable<Int>` (12), and so on: the premise of a conditional extension, re-derived for each extension whose applicability is tested. 152 of the 160 are closed and posed with no pending premise. Each costs one step. Under MIN5 the whole library poses 329 subgoals and tries 4,083 candidates; resolution is about a third of type checking there (79 of 245 samples under `Typer.summon` in `research/followup/profile/min5.json`). Sharing the repeated premises would save at most a few percent of the time.
- In the tests, one file poses 7,388 of the 9,099 subgoals (`coercion-derivability-cache.hylo`, a search for an equality, 4 subgoals under FULL). The median file poses 8.
- No resolution in either set has a derivation large enough to contain the same subgoal twice in a way that matters.

*Where sharing would matter.* A given with *k* premises `A is P`, plus a given `<T where T is P> => T is P` that gives every `P` goal derivations of every size (`experiments/p2/wide-loop-ok-k.hylo`, valid programs, the derivation found has *k* + 2 steps):

| *k* | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---|
| `summon.subgoals`, FULL | 10 | 47 | 286 | 2,102 | 17,984 | rejected: "implicit resolution is too complex" (98,590) |

The engine keeps one thread for every combination of derivations of the premises, not one per premise. The same with a last premise that fails (`wide-loop-fail-k`): 7,434 and 22,065 subgoals for *k* = 2 and 3, the budget for *k* = 4; and with the bound raised from 10 to 14, the budget already for *k* = 2 (more than 122,000 subgoals). The number of distinct (goal, hypotheses) pairs in these programs is under a hundred.

So: no potential on today's code; an exponential in a synthetic family of valid programs; and a direct conflict with any larger bound.

### 8.2 Is tabling compatible with the engine?

Tabling as in Lean 4 (Selsam, Ullrich and de Moura) shares the answers of a subgoal between all its consumers and yields them in the order found. Five properties of this engine stand in the way.

| Property | Consequence |
|---|---|
| The result is the set of derivations of least size (layer), then of least penalty; ties are an ambiguity. | A table must hold, for a subgoal, *all* its minimal derivations with their size and penalty, not the first answer. |
| Pending premises are hypotheses, so the same goal has different answers in different threads. | The key must contain the hypotheses. The loop check failed for exactly this reason (`research/report/rejected/README.md`): it compared goals only. |
| The penalty of a given counts the hypotheses. | The penalties of a table entry are valid only for the same list of hypotheses, which the key already fixes. |
| A subgoal with unification variables exports bindings; a later premise can fail for the minimal answer and succeed for a larger one. | Minimal answers are not enough for open subgoals. They would need answers streamed in order of cost, which is the full Lean design plus ranking. |
| The bound counts the steps of the whole derivation. | An entry "no derivation" is valid only up to the depth it was searched to. |

Full tabling is therefore not compatible without redefining ranking. The largest restriction that is exact:

**Share the resolution of a premise whose type is closed and whose hypotheses are closed.** Key: (scope, goal, list of the types of the hypotheses in order). Value: either the minimal derivations (size *n*, and for each its penalty and witness with hypotheses numbered by position), or "none of size up to *d*".

*Why it is exact (dominance).* Let a thread pose a closed premise *G* with closed hypotheses, and let *D* and *D′* be derivations of *G* with (size, penalty)(*D*) < (size, penalty)(*D′*) lexicographically. Whatever the thread does afterwards does not depend on which was chosen: *G* exports no binding, and its derivation is not a hypothesis of anything. So every completion through *D′* is strictly worse than the same completion through *D* and is never among the results. Derivations that tie are all kept, so the number of results (ambiguity) is preserved: it is the product of the numbers of minimal derivations. The same argument shows that a subgoal whose key equals the key of one of its ancestors can be cut.

(review) The argument has a premise that idea 1 removes. "Whatever the thread does afterwards does not depend on which was chosen" is true while the derivation of *G* is used for nothing but filling its hole. With `premsubst`, the *witness* of *G* is substituted into the types of the premises that wait for it, so a completion can succeed through *D′* and fail through *D*: this is exactly what `tests/s1-attack-shadowed-requirement.hylo` and `s1-attack-nonminimal-witness.hylo` show, where the smaller derivation of the first requirement is not the one in the result. The restriction must therefore add a condition: **no waiting premise of the thread mentions the premise being shared** (in the terms of section 3.4, the popped premise is not a key of `Environment.bound`). Two ways to keep the sharing for such premises: under the commit rule of section 3.10 only the witness of the minimal derivation survives, so dominance holds again and the table entry is the very resolution that `commits` performs; without it, the table must hand out all derivations, not the minimal ones, which is full tabling. This is one more reason to settle question 4 before tabling.

*Use.* In `threadContinuation`, when the premise popped is closed and the remaining hypotheses are closed:

- entry with derivations of size *n*: if the current layer plus *n* exceeds the bound, the thread dies; otherwise it is replaced by one thread per minimal derivation that waits *n* − 1 layers (the `delay` field that `eqeager` added to `ResolutionThread`, here counted against the bound) and adds the entry's penalty;
- entry "none up to *d*": the thread dies if the remaining depth is at most *d*;
- no entry: solve the premise as its own resolution.

*The obstacle is the last case.* Solving the premise eagerly, to the remaining depth, can cost more than today: breadth-first search would have stopped as soon as another alternative of the root completed. The exact fix is a table of *suspended* searches (frontier and depth) that advance one layer per layer of their consumers, which is the generator and consumer machinery of the paper, synchronized by layer. That is where the 250 to 400 lines go, with new invariants on the bound, the budget, `declarationsOnStack` (an entry computed while a declaration is hidden is not reusable, as for `cache.scopeToSummoned`), and the renaming of hypothesis identifiers.

A cheap special case exists: when the premise is the *last* pending one and has no hypotheses, its minimal derivations are what the public `summon(_:in:)` returns and caches. It covers 152 of the 160 repeated premises of the standard library, for about 40 lines, but still needs the delay and the eagerness argument, and saves a few percent at best. Not recommended on its own.

### 8.3 What would be needed, and when

1. Idea 1 first: it turns premises that are open today (they mention an unknown witness) into closed ones. (review) It also makes the result depend on the witness of a shared premise; see the condition added in 8.2.
2. A decision on question 1 of section 7. Without hypotheses the key is (scope, goal), the penalties are context-free, and the design is half the size.
3. Then the table of suspended searches, validated by the self-check mode: with the table on, every resolution is replayed without it and must give the same results (`takeSummonResults` already has such a replay for `eqeager`).

Tests: `tests/s2-keep-shared-premise.hylo` (same witness), `tests/s2-keep-wide-loop-ok.hylo` (same witness and penalty although every premise but one is proved from a hypothesis), `tests/s3-cost-wide-loop-fail.hylo` (`summon.subgoals` should fall from 22,065 to under 100), and the two where-order programs.

Do it only if idea 3 is adopted, or if the census of real code starts to show resolutions with several multi-derivation premises.

## 9. The depth bound (shorter treatment)

### 9.1 The problem

The loop of `takeSummonResultsUnchecked` runs `while done.isEmpty && !work.isEmpty && (depth < bound(work))`, and every thread takes one step per layer. A thread is a whole derivation built depth-first, so the bound of 10 limits the *number of givens used* in a derivation, summed over all the requirements of a call, plus one for the call.

| Program (`tests/`) | Steps | Height | base and FULL at bound 10 | Smallest tested bound that accepts |
|---|---:|---:|---|---:|
| `s3-keep-tuple4`: a 4-tuple is `Copyable` | 10 | 5 | accepted | 10 |
| `s3-gain-tuple5`: a 5-tuple is `Copyable` | 12 | 6 | rejected | 12 |
| `s3-gain-three-requirements`: a function with three requirements, each a pair that is `Copyable` (5 steps each, accepted one at a time) | 16 | 3 | rejected | 16 |
| `s3-gain-three-requirements-nostd` | 13 | 4 | rejected | 14 |
| `s3-gain-where-order-b`: `where S<C> is Q, C is P` | 12 | 3 | rejected (accepted with the two requirements swapped) | 12 |
| `s3-reject-chain9`: `S<…<Z>…> is P`, 9 levels | 11 | 10 | rejected | 12 |

(`experiments/p3.jsonl`; bounds 10, 12, 14, 16 and 20 were tested; all rejections have `summon.depthExhausted > 0`. The height is the level of the deepest premise, as defined in 9.2.) Meanwhile the equality procedure proves equalities of any size.

### 9.2 A principled bound

Two separate limits, for two separate purposes.

1. **A bound on the height of a derivation**, per branch: a premise at level *ℓ* > *H* is not discharged. The premises of the root are at level 1; the premises of a candidate that matched a goal of level *ℓ*, and the equalities that `match` assumes for it, are at level *ℓ* + 1. This is what makes the search finite, and it is a property of the derivation (it does not depend on the order of requirements or on how many requirements a call has).
2. **A work budget** per resolution, whose exhaustion is an *error* ("implicit resolution is too complex"), not a silent failure, as the `budget` flag already does for the size of the frontier. It protects against searches that are finite but huge. (review) The reason it must be an error: a silent failure that depends on a count of work makes a verdict depend on every optimization that changes the count (`index`, `absmodel`, `eqeager`), and a failed resolution can silently steer overload or extension selection. An implementation of this section that was in progress in the working tree during the review declares its budget as "past it the resolution fails, silently"; that should be changed before the flag is evaluated.

Implementation, behind a flag `heightbound`: the engine already threads the needed information for the abandoned loop check (`Environment.ancestry` maps an assumed given to the list of its ancestor goals; the level is its length plus one). Replace it by `levels: [Int: Int]`, give `formThread` the level of the goal being matched, set the level of the equalities assumed in `match`, and in `threadContinuation` kill the thread when the level of the popped premise exceeds *H*. In the loop, replace `depth < bound(work)` by the budget test: the function already counts the candidates tried by the resolution (`matchCount - matchesAtEntry`), and no file of the compiler's tests tries more than 128,802 in total under base and 1,406 under FULL, so a limit of 1,000,000 (read from the environment like `HYLO_TC_BUDGET`) is far from anything observed. About 60 lines.

*H = 9 preserves every result of today.* A premise at level *ℓ* exists only after *ℓ* steps and needs one more, so a derivation that completes within 10 steps has no premise above level 9. The frontier of the new search is therefore identical to today's through layer 10. Any resolution that today completes or runs out of threads within 10 layers gives the same results; only resolutions that today hit the bound (`summon.depthExhausted`) continue. (review) With `eqeager` the layers that a thread spends waiting for equalities decided in `match` do not count against today's bound (`Environment.credit`), so "layer 10" reads "the layer at which today's bound stops the thread"; levels are not affected by waiting, and the argument is unchanged.

### 9.3 What it changes

- **Compiler tests: nothing.** `scripts/corpus_scan.py` ran the 192 files under base and FULL with the bound at 10 and at 40 (`experiments/corpus-scan.jsonl`): `summon.depthExhausted = 0` in all 768 runs, and verdicts, diagnostics and `summon.matches` are identical at 10 and 40.
- **The programs of 9.1**: the four rejected ones with height at most 9 are accepted; `chain9` stays rejected with *H* = 9.
- **Research test programs.** Under FULL, 6 of 538 reach the bound and 2 the frontier budget (`experiments/programs-scan.jsonl`). With the bound at 40 none becomes accepted (`experiments/reach-bound.jsonl`). Four of the six are the failing equality searches of section 1 (`min`, `t1`, `t8-cond-call`, `assoc-eq-call-incomplete`): at 40 they try 185,000 candidates instead of 10,300 and end in the budget error. Three of those four are valid programs that idea 1 accepts in a few steps, which is one more reason to do idea 1 first. The other two are `performance/div-trunc-b1` and `-b2`, divergent searches that the abstract model cannot refute.
- **Cost of failing searches.** Where every given has one premise, size and height coincide and nothing changes (`s3-cost-div-branch`: 110,449 matches under base either way; 1 under FULL, refuted by the abstract model). Where givens have several premises with several derivations, the search no longer stops at 10 steps. The binary cannot bound the height, so the only measurement is with the size bound raised: `wide-loop-fail-2` goes from 7,434 subgoals at bound 10 to the budget at bound 14. Such programs end in the budget error unless subgoals are shared (section 8). This is the reason the two ideas belong together.
- **A failed resolution is not always an error** (overload and extension selection use failures), so a resolution that fails today by reaching the bound and succeeds tomorrow can change which candidate is selected. None exists in the compiler's tests.

### 9.4 Interactions and questions

- With idea 1: premise substitution removes steps (no detour through equality coercions), so fewer derivations are near the bound; the level of a premise does not depend on the order of discharge, so the two changes commute. (review) Idea 1 also creates new verdicts that depend on the order of a where clause through the size bound (`tests/s1-attack-where-order-a` is accepted in 9 steps, `-b` is rejected at 13); both have height 6, so a height bound of 9 should accept both. The commit rule of section 3.10 starts a nested resolution, which has its own bound and budget, like the premise code of `solveEquality` today.
- With idea 2: see 9.3. With a table keyed by (goal, hypotheses), the work is bounded by the number of distinct keys times the candidates per key, and the height bound alone suffices for termination.
- Questions for the language designers: (a) is the bound part of the language (a program is ill-typed beyond it) or a safeguard (then its exhaustion should always be reported as such, never as "no given")? (b) which *H*? With *H* = 9 a chain of 9 conditional givens is still rejected; (c) may acceptance depend on a work budget, which optimizations change? (d) should derivations of equalities be exempt, as they are in the equality procedure, with the bound applying to uses of declared givens only?

*Result that should make us abandon it:* a resolution in real code that hits the work budget under the height bound while failing quickly today. The mutation benchmark of the follow-up plan (5.2) is the place to look; none of the 192 tests can show it.

## 10. What was not established

- The first version of sections 1 to 7 was implemented and run (steps 0 to 3). Its predictions for the tests of section 5 and for the research programs of section 4.5 were all confirmed on `eq25`. The corrections of the review (the capture rule, `ContextClause.binders`, the removal of coercions, the commit rule) are **not built**: their Swift and pseudo-code are written against the source as read, and the verdicts expected from them are derived by hand from traces.
- Assumption A7 (a free occurrence of a binder only exists where the binder is a visible given) is an argument about what a caller can write. No program was found against it, and no proof was attempted.
- The commit rule compares a witness found in a thread with the witness of a second resolution of the same goal. That the two are spelled alike was observed for the witnesses printed by the trace in the programs of section 3.10, not checked by a build; a mismatch rejects programs (stop condition of step 8).
- Penalties of resolutions that bind a using differ from today's by the number of waiting premises (section 4.5, items 2 and 3). No program was found whose verdict changes for that reason; a tie created or resolved by it is possible in a clause with three or more requirements that today is accepted through the workaround, and was not constructed.
- A projection through a refined trait (`trait Q refines P`) is an error type in the existing checker, so nothing could be tested there.
- The numbers of section 8.1 for failing branches are totals (`summon.subgoals`); the binary cannot list the subgoals of failing branches, so the count of *distinct* keys in the synthetic family is an estimate from the shape of the programs.
- The effect of a height bound is known only through the proxy "size bound raised to 40", which explores a superset of what a height bound of 9 explores up to 40 steps and nothing beyond.
- The working tree of `/home/user/hylo-impl` was being edited during the review (uncommitted: binding of the heads of givens and extensions, a height bound). The review refers to commit `0bbd27e` for the code and to `eq25-c7cbd846a05c` for the behaviour, and did not examine the uncommitted changes beyond two remarks in sections 9.2 and 11.

## 11. Review

The design was reviewed by a second engineer after steps 0 to 3 had been implemented. The review read the functions the design hooks into, ran the implementation (`eq25-c7cbd846a05c`, FULL + `premsubst`, with and without `selfcheck`, and the configuration NEW), wrote programs to break it, and corrected this document. Scripts: `scripts/review_run.py` (any binary, any flags), `scripts/record_observed.py`, `review/test_table.py`. Raw results: `review/*.jsonl`, `tests/observed.jsonl`. Candidate programs that did not become tests are in `review/attacks/`.

### 11.1 What was checked and holds

- **The account of the code.** `summon` (hypotheses first, one group each, offsets as penalties, also in `indexedSummon`), `formThread`, `match`, `threadContinuation`, `applyContinuation`, the loop of `takeSummonResultsUnchecked`, the unification of associated types, the premise code of `solveEquality`, `initializeContext`, the opening of the callee in the solver, and `applies` are described correctly, with two exceptions listed in 11.2 (what `typeOfImplementation` does with a coercion; what follows from trying every witness).
- **The recorded verdicts.** All 30 programs of the first version were run again under base and FULL on `eq9`: the 60 recorded lines agree, counters included.
- **The predictions.** On `eq25`: the nine `s1-gain-*` programs are accepted, the `s1-keep-*` stay accepted with `eqsolve.premises=0` where predicted, the `s1-reject-*` stay rejected, `s1-open-parameter-type` stays rejected, the `s2-*` and `s3-*` programs are unchanged. Of the 76 research programs with a requirement on a projection, exactly the four predicted become accepted, the four predicted stay accepted without the workaround, `t8-cond-call` stays rejected, and nothing else changes. No self-check violation; `premsubst.stuck = 0`.
- **The estimate.** About 340 lines for the part implemented, against 330.
- **Attacks that the design withstands** (programs in `tests/` unless noted):
  - *Invariant I2 ("stuck").* Two levels of waiting premises pending at once, a conditional conformance with a dependent premise proving the first requirement of a dependent clause (`s1-gain-nested-dependent-given`): released in the right order, accepted with `assocsubst`.
  - *Open variables.* A dependent equality that relates the associated type to a parameter the head does not determine, in both orders of the clause (`s1-gain-open-variable-a/b`): accepted in both; the enumeration of candidates is the one the engine does today.
  - *The abstract model.* It does not refute a goal on an unbound dependent premise (`s1-gain-given-concrete`, `s1-reject-given-concrete`).
  - *Termination of step 3.* An associated type defined by itself, and one defined through a conditional extension that needs it (`s1-reject-cyclic-definition`, `review/attacks/h2-self-def.hylo`): rejected at the declaration as today, no loop.
  - *Ambiguity.* Two conformances of equal rank that both satisfy the dependent requirement: two results, rejected (`s1-reject-ambiguous-both`).
  - *Sibling members and recursion.* `s1-keep-extension-sibling`, `s1-keep-recursion`: accepted with the witness of today.
  - *Cost of failing calls.* A call that fails on its dependent requirement now explores the derivations of the first requirement before failing, where today it fails at once. Measured on three programs with divergent or wide givens (`review/attacks/f1`, `f3`, `tests/s1-reject-missing-requirement`): the number of subgoals goes from 8 to 18 and from 21 to 30 under base, and rises by at most 2 under FULL. The size bound keeps it small; it will grow with a height bound.
  - *Duplicate requirements* (question 5 of the first version): rejected where the clause is declared.

### 11.2 What was wrong, and what was changed

1. **A wrong acceptance (capture).** Binding by declaration and type also rewrites references that the caller wrote, when a clause is instantiated at itself with explicit type arguments. `tests/s1-attack-capture-recursion.hylo` is accepted by the implementation with the witness `f<W<A.X>>(A is P)(B is Q)(W<B> is R)`, whose last argument proves another requirement than the one of the call; FULL rejects it and the self-check is silent. Assumption A7 had named the situation, described it wrongly (it does not need a requirement without parameters, and a shadowing given is not needed either, because every witness is tried), and left it unchecked. *Changed:* the capture rule in section 3.4, invariant I5, assumption A7 rewritten, step 5, a paragraph in section 2 on the representation that would avoid the problem.
2. **A wrong reading of name resolution (assumption A3).** Name resolution removes a coercion from a witness before it selects an associated type; the design substituted the witness as found. Valid programs in which the first requirement is proved through an equality are rejected (`s1-attack-coerced-witness`, `-own-projection`). *Changed:* section 3.7 now applies all the branches of `typeOfImplementation`; A3 restated; step 7.
3. **An unstated choice of semantics.** Trying every witness of a requirement and letting the dependent requirements select among them makes a shadowed or more distant conformance win (five programs, section 3.10), and, once defect 2 is fixed, turns the design's own negative test `s1-reject-other-conformance` into an accepted program. The first version had seen only the case of two witnesses of equal rank. *Changed:* section 3.10 (the commit rule, flag `premcommit`), question 4 rewritten, step 8, item 5 of section 4.5, the note in 1.5.
4. **A part of the design that the implementation skipped.** Without `ContextClause.binders`, methods, initializers and trait requirements with a dependent clause are rejected as before while free and static functions are accepted (`s1-attack-method`, `-initializer`, `-trait-requirement`). The design had the field but presented it as serving bundles only and its absence as harmless. *Changed:* section 3.2 lists the paths and says it is required; step 6.
5. **A claim of the test plan.** "Move the dependent requirement to any later position: same verdict" is false near the bound (`s1-attack-where-order-a/b`). *Changed:* item 3 of section 5.
6. **The argument for tabling.** Dominance ("a larger derivation of a closed premise is never in a result") does not hold for a premise whose witness is substituted into waiting premises. *Changed:* a condition added in section 8.2.
7. **Smaller corrections.** Nested searches must not inherit waiting premises (section 3.5; A5 restated); the status of heads after `headsubst` (3.8); `eqeager` credit in the argument for *H* = 9, and the budget of the height bound must fail loudly (9.2); question 5 answered; sections 4.5, 5, 6 and 10 now say what was observed and what is predicted.

### 11.3 What the revised design still does not withstand

- **It is revised on paper.** Steps 5 to 8 were not built. The expected verdicts of the bold rows of section 5 and of the table in section 3.10 are derived by hand.
- **The capture rule rests on assumption A7**, which is an argument and not a check, because inside the engine a bound and a free occurrence are the same expression. The representation that removes the assumption (placeholders, section 2) is a larger change.
- **Question 4 is open.** With `premcommit` off the five programs of section 3.10 are accepted through a conformance that the call site does not select, and with step 7 two more. With it on, a resolution is performed twice and compared, which is the kind of dependence on determinism that option A was rejected for, here confined to cutting threads.
- **Order of a where clause.** Requirements remain hypotheses for one another in one direction, so verdicts near the size bound depend on the order (`s1-attack-where-order-a/b`, like the existing pair of section 1.4). Only a decision on question 1 or the height bound of section 9 changes that.
- **Not covered, as before:** requirements of a member that mention a requirement of the enclosing clause; heads of givens and extensions; projections through generic conformances without `assocsubst`.
- **A remark outside this design.** The working tree, in `instantiated(_:declaredIn:through:)`, substitutes the type arguments of a witness into a definition and into the requirements, and then rewrites binders by declaration and type. That is the order that causes defect 1. There the order can simply be exchanged (rewrite in the declared types, then substitute the type arguments). This was read, not tested.

### 11.4 Recommendation

**Keep the implementation, and implement step 5 before `premsubst` is used in any configuration that is evaluated or reported; then steps 6, 7 and 8 as designed.**

The mechanism (deferral, release, substitution, cleaning) is sound in its bookkeeping: every prediction held, about 1,000 programs ran under the configuration NEW with the self-check on without a stuck premise and without a violation that concerns this mechanism (`../compare-new.jsonl`; the one violation in it is about the index of givens), and no program in which a using is bound goes from accepted to rejected. The defects are at its two interfaces: how the clause's own references are told apart from the caller's (step 5, a wrong acceptance, 20 lines), and how a substituted type is made identical to the caller's (steps 6 and 7, valid programs still rejected, 25 lines). Step 8 depends on an answer from the language designers; until they answer, the review recommends running with `premcommit` on, because it is the reading under which a call means what its signature says at the call site, it accepts fewer programs, and it keeps the analogue of the compiler's negative test rejected.
