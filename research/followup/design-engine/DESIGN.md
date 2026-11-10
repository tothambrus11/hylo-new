# Improvements to the resolution engine: design

This document is for the engineer who will change `Sources/FrontEnd` of `/home/user/hylo-impl`. It covers three outstanding ideas for the engine of implicit resolution (`summon`, `formThread`, `match`, `threadContinuation`, `applyContinuation`, `takeSummonResults` in `Typer/Typer.swift`). One of them is designed completely (sections 1 to 7); the other two get a shorter treatment (sections 8 and 9).

`Typer.swift` was edited while this was written, so the document anchors every change on quoted lines and not on line numbers. All verdicts and counters come from the binary `research/exp/bin/eq9-723cc0e6b0f8/tc-bench`. "base" is the existing checker and "FULL" the configuration of `BRIEF.md`. Scripts and raw results are listed in `README.md`.

## 0. Priority

| Idea | What it fixes | Evidence that it matters | Size | Recommendation |
|---|---|---|---|---|
| 1. Substituting discharged premises (`premsubst`) | A requirement on an associated type of another requirement (`where T is P, T.X is Q`) can never be satisfied by a caller. | Six minimal programs of ordinary generic code are rejected by base and by FULL. No workaround exists in the language. | about 320 lines, one new field in `Implication` | **First.** Designed in sections 1 to 7. |
| 3. Height bound in place of the size bound | Valid programs with a derivation of more than 10 steps are rejected: copying a 5-tuple, calling a function with three requirements, and one program whose verdict depends on the order of its where clause. | Four minimal programs. No file of the compiler's tests reaches the bound, so the change is invisible there. | about 60 lines | Second. It needs a decision of the language designers and a work budget. Section 9. |
| 2. Tabling of subgoals | Exponential cost when several premises each have several derivations. | Nothing to gain on the code available today: 96% of the resolutions of the standard library end after one step and none has more than 5. One synthetic family of valid programs is exponential today. | 250 to 400 lines | Last, and only together with idea 3, whose cost it bounds. Section 8. |

The reason for the order is that idea 1 removes a rejection that every program of a certain ordinary shape meets, while ideas 2 and 3 concern programs near a limit. Idea 1 also removes the least robust part of the equality procedure (the ahead-of-time resolution of a pending premise, about 80 lines, whose correctness depends on resolving the same goal twice with the same answer).

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
- Programs rejected for a good reason stay rejected: `s1-reject-missing-requirement.hylo`, `s1-reject-other-conformance.hylo` (the analogue of `Tests/CompilerTests/negative/associated-type-inequality.hylo`), `s1-reject-concrete-mismatch.hylo`.

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

- Code: about 320 lines in five steps (section 6): 45 for the binders, 170 for the engine, 40 for projections through declared conformances, 40 for self-checks, 25 of preparatory refactoring.
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
| (a) `Implication` records, for each using, the declaration through which later usings refer to it (chosen) | about 45 lines in `Implication.swift`, `TypeStore.swift`, `Typer.introduce` | Exact. One corner (assumption A7). |
| (b) Recover it from the syntax: a reference to a declaration that is the *k*-th using of some context clause is bound by the *k*-th using of the implication being opened if the types agree | about 30 lines in `Typer.swift`, no change of representation | Same corner, plus confusion between two clauses whose *k*-th usings have the same type. |
| (c) By type alone, as the workaround does | 0 new lines | Fails with two usings of the same type; cannot tell a callee's using from a visible one of the same type. |

(a) is chosen because the information is known where the implication is built and lost one line later; (b) reconstructs it. With (a) the field is empty unless the flag is on *and* a later using refers to an earlier one, so type identities are those of today in every other case.

## 3. The design

Flag: `premsubst`, declared in `TyperCounters.swift` like the others:

```swift
  /// SEMANTIC FIX: a requirement that mentions another requirement of the same clause is proved
  /// after it, with the witness found for it substituted into its type.
  nonisolated(unsafe) public static var premsubst: Bool = enabled.contains("premsubst")
```

Counters: `premsubst.binders` (usings recorded as referred to), `premsubst.bound` (implications in which `formThread` bound a later using), `premsubst.deferred`, `premsubst.released`, `premsubst.normalized`, `premsubst.stuck` (must stay 0).

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

`lifted(_: Implication.ID)` passes `self[a].binders`. `introduce(usings:into:)` gains a parameter `binders: [DeclarationIdentity?] = []`. `ContextClause` is not changed in the first steps: an implication rebuilt from a `ContextClause` (`contextAndHead` followed by `introduce`, for instance for the members of a generic type) loses its binders, and its dependent usings stay opaque as they are today. That is a loss of coverage, not of correctness.

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

### 3.5 `threadContinuation`

The function gains a prologue that *releases* deferred premises; the rest is the existing code operating on the environment after release.

```swift
  private mutating func threadContinuation(
    appending operand: SummonResult, to thread: ResolutionThread, in scopeOfUse: ScopeIdentity
  ) -> ResolutionThread.Advanced {
    var environment = thread.environment

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
- **Ambiguity.** If the premise that others wait for has several results, each continues as its own thread, as today, and the waiting premises are checked for each.

The cost is one pass over the tail per step of a thread that has waiting premises: quadratic in the size of a derivation, which the bound limits to 10. If it shows in a profile, carry `solved` in the environment.

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

### 3.7 Projections through a declared conformance (step 3)

After substitution a projection can have the form `(A::c).X` with `c` a conformance declaration. Name resolution never builds that type: it returns the declared type of the implementation (`typeOfImplementation(satisfying:in:)`, the branch "The witness refers to a given declaration?"). `normalizingProjections(in:)` applies the same rule so that both spellings agree:

```
normalizingProjections(in t):
  repeat at most 8 times:
    collect the nodes n of t (found with program.types.map, a closure that only records) such
      that n is an AssociatedType whose qualification w, after removing coercion applications
      (asCoercionApplication), has w.value == .reference(d)
    keep those where d is a ConformanceDeclaration with empty contextParameters
    if none: return t
    for each: m = typeOfImplementation(satisfying: n.declaration, in: n.qualification)
              replacement[n] = inhabitant of the metatype m, or .error
              bump "premsubst.normalized"
    t = program.types.map(t) { n in replacement[n] → .stepOver, else .stepInto }
  return .error
```

Restrictions, on purpose:

- Only non-generic conformance declarations. For a generic one, `typeOfImplementation` returns the declared type of the implementation without substituting the conformance's type arguments, and name resolution rejects `Box<B>.X` altogether today ("expression does not denote a type", `unsimplified-projections/t11-generic-conf.hylo`). Such projections stay opaque: `(Box<B>::c<B>).X`.
- A where-clause requirement is an implicit binding, not a conformance declaration, so `(U::$r).X` is left alone, as it must be.

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

and checks the arguments against `callee`, whose parameter type still names the callee's own requirement. The result of the coercion (the witness for `U is P`) is never fed back into that type. Fixing it needs the solver to know which witness a parameter type depends on, which is option D. If the head were bound in `formThread` alone, the root match of every call to such a function would fail against the solver's unbound copy, and programs that are accepted today (a dependent parameter that is never constrained) would be rejected. So the first steps leave heads alone, for all threads.

A later, separate step can bind heads for the two kinds of thread where the solver is not involved: candidates of `summon` (givens such as `given <T where T is P> => Box<T.X> is Q`) and extension applicability (`applies`). The obstacle is known: the mismatching parts that `match` assumes would then mention assumed givens, `canDeriveCoercions` would have to let them through, and they would have to be deferred like usings. Invariant I1 no longer holds in that form. It should get its own flag, after the solver question is settled. Only then can the workaround of section 1.3 be deleted; until then it still serves projections that come from heads.

Members of a generic type whose own where clause mentions a requirement of the enclosing type also stay opaque (the binders are lost through `ContextClause`, section 3.2).

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

### 4.2 What is not assumed

The workaround assumes that resolving a premise twice gives the same witness. Here each premise is resolved once, and the witness substituted is the one in the derivation. Nothing depends on uniqueness, closedness or determinism.

### 4.3 Assumptions about the rest of the type checker

| | Assumption | How to check it |
|---|---|---|
| A1 | In the type of a using, a reference to an earlier using of the same clause is the witness `(.reference(r), type: T)`, where `r` is what `expression(referringTo:)` returns for the earlier using and `T` its declared type; possibly inside a coercion application. | In `Typer.introduce` under `selfcheck`: every witness `.reference(r)` with `r` among the clause's usings that occurs in a later using has type `us[k]`. `premsubst.binders` must be positive on `tests/s1-gain-*.hylo`. |
| A2 | Substitution, reification and dealiasing apply the same transformation to a using and to the references to it, and keep `binders`. | In `formThread` under `selfcheck`: if `i.binders.first` is set and no later using was rewritten, report a violation. |
| A3 | The witness recorded for a premise is syntactically the witness that name resolution used when the caller wrote the same projection, so that the substituted type is the *same type identity* as the caller's. | The `s1-gain-*` tests are accepted only if this holds. Under `selfcheck`: when the goal of a discharged premise was closed and it had no hypotheses, `summon(goal, in: scopeOfUse)` returns that witness. This is a check, not something the algorithm uses. |
| A4 | For a reference to a non-generic conformance declaration, `typeOfImplementation` returns the metatype of the implementation, and its only effects are memoized declared types. | `s1-gain-conformance-concrete`, `s1-gain-equality-concrete`, `s1-reject-concrete-mismatch`. `expression(referringTo:)` already computes declared types inside resolution, so re-entrancy is not new. |
| A5 | No `Environment` is built without copying the new fields. | After step 0, `Environment(` occurs only in `with`, `assuming`, `deferring` and `empty`. |
| A6 | No later phase needs the types of inner nodes of a witness to mention the callee's own using. | They are rewritten to the caller's witnesses by 3.6; the semantic dump shows the difference, only in programs with dependent usings. |
| A7 | A type argument substituted into an implication does not contain a reference to that implication's own binder with the type of the instantiated using. | It can only happen in a function that calls itself with an argument that is a projection through one of its own requirements, when that requirement does not mention the function's parameters (`where Int is P`). The projection is then bound to the callee's premise, which resolves to the same requirement unless a nearer given of the same type shadows it. Documented, not checked. |
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

Items 2 and 3 can change penalties and, through the bound, sizes, but only among derivations of such resolutions, which today fail unless the workaround applies.

Among the 76 research programs with a requirement on a projection (`experiments/dependent-programs.txt`, results in `experiments/dependent-programs.jsonl`), FULL accepts 32. In most of them the dependent clause belongs to a declaration that is checked but never used by another, so nothing is bound. The workaround fires in 9, which are the programs to diff first. Predicted from the design:

| Program (`research/report/test-programs/`) | FULL today | With `premsubst` |
|---|---|---|
| `unsimplified-projections/t4-generic-caller`, `v5-generic`; `equalities/x10b-ext-where-assoc`, `eq-regress-judge-x10b-ext-where-assoc` | accepted | accepted, `eqsolve.premises=0` |
| `unsimplified-projections/min`, `t1`; `equalities/assoc-eq-call-incomplete`, `x10-ext-where-assoc` | rejected | accepted from step 3 (a projection through a declared conformance) |
| `unsimplified-projections/t8-cond-call` | rejected | rejected: the conformance is generic, its projection stays opaque (3.7) |

## 5. Test plan

`tests/` holds the programs; each has a comment with the expected verdict after the change, the reason, and a line `// currently:` with the verdict and counters under base and FULL, written by `scripts/record.py` (raw results in `tests/current.jsonl`).

| Program | Step | Expected | Currently (base / FULL) |
|---|---|---|---|
| `s1-gain-conformance-generic` | 2 | accepted | rejected / rejected |
| `s1-gain-conformance-two` | 2 | accepted | rejected / rejected |
| `s1-gain-chain` | 2 | accepted | rejected / rejected |
| `s1-gain-middle` (the dependent requirement is neither first nor last) | 2 | accepted | rejected / rejected |
| `s1-gain-extension` | 2 | accepted | rejected / rejected |
| `s1-gain-given` | 2 | accepted | rejected / rejected |
| `s1-gain-extension-concrete` (`Box<Bag>().first()`) | 3 | accepted | timeout / rejected |
| `s1-gain-conformance-concrete` | 3 | accepted | rejected / rejected |
| `s1-gain-equality-concrete` | 3 | accepted | timeout / rejected |
| `s1-keep-equality-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted (`eqsolve.premises=1`) |
| `s1-keep-extension-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted (`eqsolve.premises=1`) |
| `s1-keep-recursion` | 2 | accepted, same witness | accepted / accepted |
| `s1-keep-hypothesis` | 2 | accepted, trace identical | accepted / accepted |
| `s1-reject-missing-requirement` | 2 | rejected | rejected / rejected |
| `s1-reject-other-conformance` | 2 | rejected | rejected / rejected |
| `s1-reject-concrete-mismatch` | 3 | rejected | rejected / rejected |
| `s1-open-parameter-type` | – | rejected (not fixed, section 3.8) | rejected / rejected |
| `s1-open-ambiguous-dependency` | 3 | accepted as designed; question 4 | rejected / rejected |

Beyond these:

1. **The oracle** (types, bindings, witness tables, diagnostics, witnesses) on the 192 compiler tests, flag on against flag off, alone and added to MIN5 and to FULL: identical.
2. **The research programs**: `python3 scripts/run.py --configs FULL` on the files of `experiments/dependent-programs.txt` before and after. Every change of verdict must be one of: a program of the shape of section 1.1 now accepted, or explained in writing. A program accepted today and rejected with the flag is a defect.
3. **Metamorphic**: for each `s1-gain-*` program, move the dependent requirement to every position after the one it mentions (`s1-gain-middle` is one instance): same verdict. Renaming and adding an unrelated requirement: same verdict.
4. **Self-check mode** (step 4) on all of the above: `premsubst.stuck = 0`, no violation.
5. **Counters as evidence that the new path ran**: `premsubst.bound > 0` and `premsubst.released > 0` on every `s1-gain-*`; `premsubst.normalized > 0` on the three concrete ones; all zero on the compiler tests.

## 6. Implementation order

Each step builds and is tested on its own. Lines are added or changed lines, estimated.

| Step | Change | Lines | Test |
|---|---|---:|---|
| 0 | `Environment.with(substitutions:givens:nextGivenIdentifier:)`; replace the hand-written copies. No flag. | 25 | Oracle identical on everything. Counters identical. |
| 1 | Flag and counters. `Implication.binders`; `dropFirstRequirement`, `lifted`, `modified`, `introduce(usings:binders:into:)`; `Typer.introduce` computes binders when the flag is on; `rewritingWitnesses`, `mentions`. Nothing reads the binders yet. | 45 + 40 | Flag on: oracle identical on the 192 tests and on the research programs. `premsubst.binders > 0` on `s1-*`, `= 2` in `associated-type-equality.hylo` (the two requirements that `T.X == U.X` mentions), `= 0` elsewhere in the tests. |
| 2 | `deferred`, `dependent`, `deferring(given:)`; the `formThread` block; the prologue and the two new branches of `threadContinuation`; `solvedWitnesses`; `withoutAssumed`; the assertions of I1 and I4. | 130 | The six generic `s1-gain-*` accepted; `s1-keep-*`; `s1-reject-*`; test plan items 1 to 3 and 5. |
| 3 | `normalizingProjections(in:)` and its call in the release loop. | 40 | The three concrete `s1-gain-*` accepted; `s1-reject-concrete-mismatch` rejected; `s1-open-ambiguous-dependency` recorded. |
| 4 | Self-checks: A1, A2, A3, I3. | 40 | Test plan item 4. |
| later | Bind heads for givens and extensions, behind its own flag; then delete the premise code of `solveEquality` (about 80 lines, `premiseResolutionDepth`, the `eqsolve.untrusted` path for premises). | – | Section 3.8. |

**Results that should make us stop.**

- Step 1: a semantic dump differs with the flag on in a program without dependent usings. Then recording binders changes a type identity that something compares. Fall back to option (b) of section 2 (no change of representation), which costs the exactness discussed there.
- Step 2: an `s1-gain-*` program is still rejected because the substituted type is not the caller's type although they denote the same thing (A3 fails: for instance the two witnesses differ in a type annotation or in an alias). If making the two spellings agree needs more than a local fix (say 30 lines), the approach needs a normal form for witness expressions, and option D or the normalization design of `research/followup/design-eqnorm` should take over.
- Step 2: `premsubst.stuck > 0` on any program. Invariant I2 is wrong; do not ship the fallback.
- Any step: a program of the research set that FULL accepts today is rejected with the flag and the reason is not one of items 2 and 3 of section 4.5 combined with the bound.

## 7. Open questions for the language designers

1. **Are the pending requirements of a clause meant to be assumptions for its other requirements?** Today they are, in one direction (a requirement is an assumption for those written after it), which makes the verdict depend on the order of the clause through the bound (`s3-keep-where-order-a` against `s3-gain-where-order-b`). If the answer is no, hypotheses can be removed, penalties no longer depend on the number of pending premises, and option B (declaration order) becomes result-preserving up to penalties. If yes, should a requirement that has just been proved remain available to the dependent ones proved after it (it is not, in this design)?
2. **Is `A.X` through a declared conformance equal to its definition inside resolution?** Step 3 says yes for non-generic conformances, as name resolution does. For generic conformances the compiler has no answer yet (`Box<B>.X` does not denote a type).
3. **Should a call typecheck when a parameter type mentions an associated type of a requirement** (`h<U>(y)` in 3.8)? Presumably yes; it decides whether the solver must carry witness variables (option D).
4. **When a requirement has two witnesses of equal rank and only one makes a dependent requirement hold, is the call ambiguous?** In this design the requirements are solved together and the call is accepted (`s1-open-ambiguous-dependency.hylo`). The alternative, "each requirement must have a unique witness on its own", is what the workaround implements and needs one extra check.
5. **May a clause list the same requirement twice** (`T is P, T is P`), and which one does `T.X` denote then? The design binds a projection to the declaration that name resolution chose.
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

Tabling as in Lean 4 (Selsam, Ullrich and de Moura) shares the answers of a subgoal between all its consumers and yields them in the order found. Four properties of this engine stand in the way.

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

*Use.* In `threadContinuation`, when the premise popped is closed and the remaining hypotheses are closed:

- entry with derivations of size *n*: if the current layer plus *n* exceeds the bound, the thread dies; otherwise it is replaced by one thread per minimal derivation that waits *n* − 1 layers (the `delay` field that `eqeager` added to `ResolutionThread`, here counted against the bound) and adds the entry's penalty;
- entry "none up to *d*": the thread dies if the remaining depth is at most *d*;
- no entry: solve the premise as its own resolution.

*The obstacle is the last case.* Solving the premise eagerly, to the remaining depth, can cost more than today: breadth-first search would have stopped as soon as another alternative of the root completed. The exact fix is a table of *suspended* searches (frontier and depth) that advance one layer per layer of their consumers, which is the generator and consumer machinery of the paper, synchronized by layer. That is where the 250 to 400 lines go, with new invariants on the bound, the budget, `declarationsOnStack` (an entry computed while a declaration is hidden is not reusable, as for `cache.scopeToSummoned`), and the renaming of hypothesis identifiers.

A cheap special case exists: when the premise is the *last* pending one and has no hypotheses, its minimal derivations are what the public `summon(_:in:)` returns and caches. It covers 152 of the 160 repeated premises of the standard library, for about 40 lines, but still needs the delay and the eagerness argument, and saves a few percent at best. Not recommended on its own.

### 8.3 What would be needed, and when

1. Idea 1 first: it turns premises that are open today (they mention an unknown witness) into closed ones.
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
2. **A work budget** per resolution, whose exhaustion is an *error* ("implicit resolution is too complex"), not a silent failure, as the `budget` flag already does for the size of the frontier. It protects against searches that are finite but huge.

Implementation, behind a flag `heightbound`: the engine already threads the needed information for the abandoned loop check (`Environment.ancestry` maps an assumed given to the list of its ancestor goals; the level is its length plus one). Replace it by `levels: [Int: Int]`, give `formThread` the level of the goal being matched, set the level of the equalities assumed in `match`, and in `threadContinuation` kill the thread when the level of the popped premise exceeds *H*. In the loop, replace `depth < bound(work)` by the budget test. About 60 lines.

*H = 9 preserves every result of today.* A premise at level *ℓ* exists only after *ℓ* steps and needs one more, so a derivation that completes within 10 steps has no premise above level 9. The frontier of the new search is therefore identical to today's through layer 10. Any resolution that today completes or runs out of threads within 10 layers gives the same results; only resolutions that today hit the bound (`summon.depthExhausted`) continue.

### 9.3 What it changes

- **Compiler tests: nothing.** `scripts/corpus_scan.py` ran the 192 files under base and FULL with the bound at 10 and at 40 (`experiments/corpus-scan.jsonl`): `summon.depthExhausted = 0` in all 768 runs, and verdicts, diagnostics and `summon.matches` are identical at 10 and 40.
- **The programs of 9.1**: the five with height at most 9 are accepted; `chain9` stays rejected with *H* = 9.
- **Cost of failing searches.** Where every given has one premise, size and height coincide and nothing changes (`s3-cost-div-branch`: 110,449 matches under base either way; 1 under FULL, refuted by the abstract model). Where givens have several premises with several derivations, the search no longer stops at 10 steps: `wide-loop-fail-2` goes from 7,434 subgoals at bound 10 to the budget at bound 14. Such programs end in the budget error unless subgoals are shared (section 8). This is the reason the two ideas belong together.
- **A failed resolution is not always an error** (overload and extension selection use failures), so a resolution that fails today by reaching the bound and succeeds tomorrow can change which candidate is selected. None exists in the compiler's tests.

### 9.4 Interactions and questions

- With idea 1: premise substitution removes steps (no detour through equality coercions), so fewer derivations are near the bound; the level of a premise does not depend on the order of discharge, so the two changes commute.
- With idea 2: see 9.3. With a table keyed by (goal, hypotheses), the work is bounded by the number of distinct keys times the candidates per key, and the height bound alone suffices for termination.
- Questions for the language designers: (a) is the bound part of the language (a program is ill-typed beyond it) or a safeguard (then its exhaustion should always be reported as such, never as "no given")? (b) which *H*? With *H* = 9 a chain of 9 conditional givens is still rejected; (c) may acceptance depend on a work budget, which optimizations change? (d) should derivations of equalities be exempt, as they are in the equality procedure, with the bound applying to uses of declared givens only?

*Result that should make us abandon it:* a resolution in real code that hits the work budget under the height bound while failing quickly today. The mutation benchmark of the follow-up plan (5.2) is the place to look; none of the 192 tests can show it.

## 10. What was not established

- No line of this design has been compiled. The Swift in section 3 is written against the source as read; names and signatures are quoted from it, but details such as the capture of non-escaping closures may need adjusting.
- A3 (the substituted type is identical to the caller's) is argued from the traces, which print `(U::P).X through $r`, and from reading `typeOfImplementation` and `resolve(_:inheritedMemberOf:…)`. It is the assumption most likely to need a fix.
- The numbers of section 8.1 for failing branches are totals (`summon.subgoals`); the binary cannot list the subgoals of failing branches, so the count of *distinct* keys in the synthetic family is an estimate from the shape of the programs.
- The effect of a height bound on the research programs that reach the bound today is known only through the proxy "bound raised to 40" (`experiments/programs-scan.jsonl`, see README).
