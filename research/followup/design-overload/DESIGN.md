# A result-preserving speed-up of overload resolution

For the engineer who works on `/home/user/hylo-impl/Sources/FrontEnd/Typer/Solver.swift`. The behaviour of the existing solver was measured on the binary `exp/bin/eq9-723cc0e6b0f8/tc-bench`. The design was written without building anything, from an executable model of the search (`scripts/model.py`), which reproduces the binary's fork counts and diagnostic counts on 19 programs.

**Status after review (section 9).** While the review was under way, the design was implemented as first written (hylo-impl commit `9dc04d7`, binary `exp/bin/eq25-c7cbd846a05c`). The review ran that binary. Two things follow, and the document has been revised accordingly:

- `twins` returns the existing result on every program tried, and its fork counts are the model's.
- `cleanfirst` and `lookahead` are **not** result-preserving. The search they perform returns the existing solution, but they skip or reorder queries to the Typer, and the verdict of a program can depend on those queries. Eight programs in `tests/` (`a01` to `a08`) show it; four of them change verdict on the binary, in base and in FULL, in both directions (accepted to rejected and rejected to accepted). With `sigrounds` these eight programs are stable. Sections 5.5 and 9 say what this means and what to do.

Summary of the design: three changes, each behind its own flag.

| Flag | What it does | Fixes | Result-preserving? | New code |
|---|---|---|---|---:|
| `twins` | Candidates of one overload set that have the same type share one exploration. | `a + b + c + …` on `Int` (2ⁿ today) | yes | ~60 lines |
| `cleanfirst` | Look for a solution without diagnostics first; run the existing search only if there is none. | calls whose wrong candidates fail at their own arguments (`ovl-4-8`) | only if no query of a discarded fork changes the Typer's answers (5.5) | ~45 lines |
| `lookahead` | In the clean-first pass, abandon a branch as soon as a goal still on the stack is certain to fail. | candidates that differ only in their return type (`ovr-3-8`, `ovl-ret-9`) | same condition, and it also asks `coerced` earlier | ~70 lines |

## 1. The problem

A constraint system is built per statement. When the solver pops an overload constraint it forks once per candidate, and each fork solves *all* remaining goals, including the later overload constraints. Three programs show the three ways in which this becomes exponential. Counters are those of the user module; times are indicative only (shared machine).

**P1. Every combination is a solution** (`tests/s06-plus-chain-10.hylo`, `tests/s07-method-chain-6.hylo`).

```hylo
public fun main() {
  let a = 1
  let x = a + a + a + a + a + a + a        // 6 uses of +
}
```

Each `+` on `Int` has two candidates of the same type `[let Int](let Int) let -> Int`: the member of `Int`, and the requirement of `AdditiveArithmetic` seen through the conformance. Both type-check, so nothing is ever pruned: n operators visit 2ⁿ − 1 overload sets. The same happens in user code for any method that a struct declares and a trait it conforms to requires (`s07`).

| `+` operators | 6 | 10 | 14 |
|---|---:|---:|---:|
| verdict (base and FULL) | accepted | accepted | accepted |
| `solver.overloads` / `solver.forks` (base = FULL) | 63 / 126 | 1,023 / 2,046 | 16,383 / 32,766 |
| `type.user`, base / FULL | 54 / 5 ms | 136 / 131 ms | 2.8 / 2.4 s |

This is ordinary code, and the cost doubles with each operator.

**P2. A wrong candidate fails early, but is explored to the end** (`tests/s02-args-last-6.hylo`, `workloads/ovl-4-8.hylo`).

```hylo
fun f(x: A0) -> A0 { x }
fun f(x: A1) -> A1 { x }
fun f(x: A2) -> A2 { x }
fun f(x: A3) -> A3 { x }
fun g(x0: A3, x1: A3, x2: A3, x3: A3, x4: A3, x5: A3) {}
public fun main() { g(f(A3()), f(A3()), f(A3()), f(A3()), f(A3()), f(A3())) }
```

`f(x: A0)` applied to an `A3` fails at once, yet the solver continues below it: a branch is only cancelled when it has more errors than the best *complete* solution found so far, and there is none until the right candidate, declared last, has been tried at every level.

| Program | Verdict (base, FULL) | overloads / forks (base = FULL) | `type.user` base / FULL |
|---|---|---:|---:|
| right candidate declared last, 6 calls (`s02`) | accepted | 483 / 1,932 | 4.7 s / 0.21 s |
| right candidate declared first, 6 calls (`s03`) | accepted | 6 / 24 | 0.10 s / 0.01 s |
| `ovl-4-8` (`s01`) | accepted | 796 / 3,184 | 8.3 s / 0.44 s |

**P3. A wrong candidate fails only at the very end** (`workloads/ovr-3-8.hylo`, `ovl-ret-9.hylo`).

```hylo
fun h() -> A0 { A0() }
fun h() -> A1 { A1() }
fun h() -> A2 { A2() }
fun g(x0: A0, x1: A1, x2: A2, x3: A0, x4: A1, x5: A2, x6: A0, x7: A1) {}
public fun main() { g(h(), h(), h(), h(), h(), h(), h(), h()) }
```

The candidates differ only in their return type. The only goal that can reject a choice is the call to `g`, which is generated after all its arguments and therefore popped after all eight overload sets. Every one of the 3⁸ combinations reaches it.

| Program | Verdict (base, FULL) | overloads / forks (base = FULL) | `type.user` base / FULL |
|---|---|---:|---:|
| `ovr-3-8` (`s04`) | accepted | 3,280 / 9,840 | 0.59 s / 0.31 s |
| `ovl-ret-9` (`s05`) | accepted | 87,381 / 349,524 | 19 s / 14 s |

The flags of FULL do not change any solver counter: they make each goal cheaper, not the search smaller. On the standard library the solver handles 798 systems with 158 overload sets and 316 forks, so nothing in it nests deeply; the problem is in user expressions.

## 2. What the existing solver does

Each rule below was read from `Solver.swift`. The demonstrations show the rules that a small program can exhibit on the binary; the two statements about stale goals (2.1, 2.4) rest on the code alone. `scripts/model.py` implements these rules, and `results/model-vs-binary.jsonl` shows that it predicts the forks, the overload sets and the number of diagnostics of the binary on 18 programs, including the programs cited in 2.3 to 2.5 except `m01` and `m03`.

### 2.1 Order of goals

`fresh` is a stack. The root constraints are pushed in reverse (`insert(fresh:)`), so they are popped in the order the Typer generated them: for a call, the callee, then the arguments from left to right, then the call itself (`inferredType(of: Call.ID)`). Subgoals scheduled by a goal are popped before older goals. A goal that lacks type information is moved to `stale` and comes back when one of its variables is assigned. When `fresh` is empty, stale coercions and widenings are turned into equalities; what is still stale at the end fails silently.

*Demonstration.* In P3 the argument coercions of `g` are popped after the last `h`: the tree is complete (3,280 = (3⁸ − 1)/2 sets). In P2 the coercion of `f`'s own argument is popped right after the choice of `f`, before the next set.

### 2.2 Forks

A fork happens exactly when an `OverloadConstraint` is popped (`solve(overload:among:)`), once per candidate, in the order of `candidates`. The fork pushes `k.type == choice.type`, records the binding, and runs the main loop to the end. Overload sets therefore nest in pop order: the first one popped is the outermost. `solver.forks` is the sum of the candidate counts of the visited sets (3,184 = 4 × 796).

Member lookups on a type that is not yet known create their overload set *during* solving (`solve(member:)`), inside each fork of the enclosing sets. That is why `a + a + a` nests: the set of the second `+` exists only once the first is resolved.

### 2.3 Cancellation

`current.errors` (E below) counts the goals whose own outcome is `.failure`. A fork returns `nil` as soon as `current > best`. `best` is `.worst` until a complete solution has been found, so cancellation does nothing before that. This is the cause of P2: `s02` and `s03` are the same problem with the candidates declared in another order, and cost 1,932 and 24 forks.

### 2.4 Scores: errors are not diagnostics

A fork's solution is scored by its number of diagnostics (D below), not by E:

```swift
let newScore = SolutionScore(
  errors: newSolution.diagnostics.elements.count, penalties: current.penalties)
if newScore < best {
  best = newScore
  viable = [(choice, newSolution)]
} else {
  viable.append((choice, newSolution))
}
```

Three consequences matter for any optimization.

- D and E differ. An "ambiguous use" diagnostic added by a nested set, and a stale coercion that cannot be simplified (`refreshCoercionAndWideningConstraints` sets a `.failure` without counting it), raise D but not E. Duplicated diagnostics lower D.
- **A solution worse than `best` is kept.** The `else` branch appends whatever was not cancelled. A fork with E = 0 and D = 1 is never cancelled, even when `best` is 0.
- **The result of a fork depends on the `best` it inherits**, not only on whether it is cancelled. Under `best ≥ 1`, a solution with one diagnostic found before a clean one is erased by the reset; under `best == 0` it stays in `viable` next to the clean one.

*Demonstrations.*
- `tests/m05`: `S.f().n()` is rejected with "ambiguous use of 'n'" although the other candidate of `S.f` gives a clean solution: the solution with a nested ambiguity stays viable and its candidate is preferred. `tests/m04`: the preferred candidate's argument error is reported although the other candidate has only a nested ambiguity.
- `tests/m06` and `tests/m07` differ in one line and show the dependence on the inherited `best`:

  ```hylo
  let s = S.a()            // m06: accepted
  two(s, f().n())

  two(S.a(), f().n())      // m07: rejected, "ambiguous use of 'f'", "ambiguous use of 'n'"
  ```

  `f -> B` (declared first) has a nested ambiguity and `f -> A` is clean. In m06 the clean solution erases the other. In m07, `S.a` has two candidates of the same type; under the first one the same thing happens, but under the second one `best` is already 0, `f -> B` stays viable, `f` becomes ambiguous, and that second candidate of `S.a` is the preferred one. This program was predicted from the model before it was run.

### 2.5 Ranking and ambiguity

After the loop, `viable.least` (`minimalElements(by:)` with `isPreferred` on the *choices of this set only*) picks the solution. If there is no unique minimal element, the solution of `viable[0]` is returned with an "ambiguous use" error added. `penalties` is never incremented.

*Demonstrations.*
- Only the outer set is ranked across combinations (`tests/m01`): in `k(S.a(), S.b())` with `k<V>(x: V, y: V)`, both (X, X) and (Y, Y) are clean, `a` prefers X and `b` prefers Y. The result is (X, X), and (Y, Y) for `k(S.b(), S.a())`.
- An ambiguous set keeps the solution of the candidate declared first (`tests/m02`, `m03`).
- In an erroneous system, ambiguities appear or not depending on the declaration order of the candidates (`tests/e01`: three diagnostics; `e02`, which only changes the type of a parameter so that the last candidate is the matching one: two). `tests/e04` has one bad argument and six diagnostics.

### 2.6 What the meaning of a program depends on

1. The pop order of goals: it decides which goal binds a variable first (`tests/e08`, `m08`) and which set is outermost (`m01`, `m10`, `m11`).
2. The order of candidates within a set: it decides `viable[0]` and, through `best`, which solutions are erased or kept (`e01`/`e02`, `m06`/`m07`).
3. The exact value of `best` each fork inherits (2.4).
4. `isPreferred`, applied to the final `viable` list in list order (`minimalElements` is order-sensitive and assumes nothing about transitivity).
5. The diagnostics of every explored solution that survives, including those of erroneous systems.

It does not depend on what a fork that returned `nil` computed, except for the side effects of that fork on the `Typer` (assumption A2 in section 5). A fork whose solution is later erased by a reset still matters through the `best` it leaves to the forks after it; Theorem 1 says when that influence vanishes.

The earlier attempt (`solver` flag) changed 1 and 2. A sound optimization must leave the pop order and the candidate order alone, and must reproduce `viable` exactly wherever it returns a result.

## 3. Options considered

Fork counts "after" are computed with the model, whose baseline matches the binary on these programs; row (c) is not modelled and is estimated by hand as one fork per candidate per set.

| Option | Result-preserving? | `ovl-4-8` (3,184) | `ovr-3-8` (9,840) | `ovl-ret-9` (349,524) | `+` chain, 14 (32,766) |
|---|---|---:|---:|---:|---:|
| (a) discard candidates by a test on the candidate alone, before forking | only relative to `best == 0` | 3,184 | 9,840 | 349,524 | 32,766 |
| (b) probe to the next overload set, prune against the best complete solution | yes; it is what the solver already does | 3,184 | 9,840 | 349,524 | 32,766 |
| (b′) the same with the bound "no error" from the start, exact fallback (`cleanfirst`) | yes | 32 | 9,840 | 349,524 | 32,766 |
| (c) solve connected components separately | only when every component's result is clean | 32 | 24 | 36 | 32,766 |
| (d) memoize identical sub-systems, restricted to same-type candidates (`twins`) | yes | 3,184 | 9,840 | 349,524 | 119, or 14 with `cleanfirst` |
| chosen: `twins` + `cleanfirst` + `lookahead` | yes | 32 | 24 | 36 | 14 |

**(a) Pre-fork filter.** When the set is popped, nothing is known about the expected type: the Typer deliberately gives the callee a fresh variable ("We cannot use the expected type to constrain the result of the callee"), and labels were already filtered in `filterInPlace`. A test on the candidate alone finds nothing on the three workloads. Moreover, "cannot succeed" is not a licence to discard: when no candidate succeeds, the discarded one may be the one whose diagnostics the solver reports (`tests/e05`). A discard is only sound as "this fork returns `nil` under `best == 0`". The useful form of (a) is a test on the goals still pending *after* the choice has propagated; that is `lookahead`.

**(b) Probing, branch and bound.** The existing solver already is a branch and bound in the existing order: a fork stops when its errors exceed `best`. A separate probe "up to the next overload set" computes nothing the fork itself does not compute. What is missing is a bound before the first complete solution. The reviewers' rule (prune a candidate whose probe has errors if another candidate's probe finishes clean) only applies at the innermost set. Their "tentative commit, re-run everything if the result has diagnostics" is close to the chosen design, but one of its supporting claims ("the decisions made inside each fork do not depend on the inherited `best`") is false (2.4, `m07`).

The obvious shortcut, "start the existing search with `best == 0` and keep its result if it is clean", is not safe either. It keeps in `viable` the solutions that the existing search would have erased; they cannot be picked (the result would not be clean), but they take part in `minimalElements` and can eliminate a rival of the winner. `scripts/mutants.py` contains a system with three candidates on which the shortcut accepts a program that the existing search calls ambiguous. It needs a preference that is not transitive, which `compareLexicalDistances` followed by `elaborationCost` does not exclude by construction. The chosen design adds an erase rule (4.2) that makes `viable` identical to the existing one, element by element, so that no property of `isPreferred` is needed. Cost: about 45 lines, three new invariants (A1, A5, A6).

**(c) Components.** Take the goals pending when a set is popped, and suppose they split into the component K₁ of that set and a rest K₂ that shares no open type variable with it. The union of the two separately computed results is the result of the nested search when the result of K₂ is clean and does not depend on `best` (the property of Theorem 1c below): K₂ then contributes the same diagnostic-free solution under every candidate of the set, so each fork's score and cancellation are those of K₁ alone and `viable` is what it would be for K₁ alone. This was reasoned, not modelled. When a component has a diagnostic (an error or an ambiguity), scores and cancellation thresholds mix across components, and the nested result is not the union: in `e01`, solving the two arguments separately gives two diagnostics, the nested search three. So (c) needs the same clean-or-fall-back structure as `cleanfirst`, plus: a constraint graph kept up to date while goals spawn subgoals and overload sets appear dynamically; a virtual decomposition of pending calls (otherwise `g(h(), h(), …)` is one component); and a merge of `elaborations` in baseline pop order, because synthetic nodes are numbered in that order. Estimate: 300 lines and four invariants. It adds nothing on the measured workloads beyond the chosen design, and nothing on the `+` chain, which is a single component. It is the only option that would fix `tests/s09-independent-clean-6.hylo` (independent sets, several clean candidates of *different* types each: 126 forks, would be 12). Not chosen; reconsider if the census finds that shape in real code.

**(d) Memoization.** Keying on the whole solver state is expensive and rarely hits: two forks of one set differ at least in the type assigned to the callee. The exception is exact and free to detect: two candidates with the same `type` produce forks that differ only in `bindings[k.name]`, which the solver never reads. This is P1, the only exponential found in ordinary code. Cost: about 45 lines, one invariant (A3).

**Why the chosen combination.** Each of the three changes is small, leaves the pop order and the candidate order untouched, and has a correctness argument that does not depend on properties of unification or of `isPreferred`. `twins` alone is correct by a two-line argument and fixes the realistic case. `cleanfirst` supplies the missing bound without changing any result, and gives `twins` and `lookahead` a setting (`best == 0`) in which they are most effective. `lookahead` is the most specialized: it only matters for return-type overloading consumed by a call whose parameter types are known.

**What is not fixed.** Systems with no clean solution run the existing search after a failed attempt: same result, up to twice the forks with `cleanfirst` alone (`e04`: 6,558 against 3,279; 3,300 with `lookahead`). `s09` is unchanged.

## 4. The design

### 4.0 Flags and state

`TyperCounters.swift`, next to the existing flags:

```swift
/// Overload resolution: candidates of one overload set that have the same type share one
/// exploration (result-preserving).
nonisolated(unsafe) public static var twins: Bool = enabled.contains("twins")

/// Overload resolution: look for a solution without diagnostics first; run the existing search
/// only if there is none (result-preserving).
nonisolated(unsafe) public static var cleanfirst: Bool = enabled.contains("cleanfirst")

/// With `cleanfirst`: abandon a branch in which a pending goal is certain to fail
/// (result-preserving).
nonisolated(unsafe) public static var lookahead: Bool = enabled.contains("lookahead")
```

New fields of `Solver` (forks copy them, as they copy everything):

```swift
/// `true` iff no overload constraint has been popped on the path leading to `self`.
private var atFirstOverload = true

/// `true` iff `self` is looking for the first candidate whose solution has no diagnostic.
/// - Invariant: `optimistic` implies `best == .zero`.
private var optimistic = false

/// `true` iff the clean-first pass discarded a solution in the search rooted at `self`. If it
/// is `false`, that search returns what the existing algorithm returns for any value of `best`.
private var dropped = false

/// `true` iff `self` runs the existing algorithm only (`selfcheck`).
private var plain = false
```

New counters: `solver.twinsReused`, `solver.cleanfirstAttempts`, `solver.cleanfirstFallbacks`, `solver.lookaheadScans`, `solver.lookaheadCuts`.

The three flags have no effect while the old `solver` flag is on. Step 0 of section 7 deletes that experiment.

### 4.1 `twins`

In `Solution.swift`:

```swift
/// Returns a copy of `self` in which `n`, which is bound in `self`, is bound to `r`.
internal func rebinding(_ n: NameExpression.ID, to r: DeclarationReference) -> Solution {
  assert(bindings[n] != nil)
  var b = bindings
  b[n] = r  // an existing key keeps its position in the ordered dictionary
  return .init(
    substitutions: substitutions, bindings: b, elaborations: elaborations,
    argumentElaborations: argumentElaborations, diagnostics: diagnostics)
}
```

In `Solver.swift`, file scope:

```swift
/// The outcome of exploring one candidate of an overload set.
private struct Explored {
  /// The type of the candidate.
  let type: AnyTypeIdentity
  /// The value of `best` when the exploration started, or `nil` if it was optimistic.
  let bound: SolutionScore?
  /// `true` iff nothing was dropped during the exploration.
  let pure: Bool
  /// The result of the exploration.
  let solution: Solution?
}
```

and a method:

```swift
/// Returns the outcome of exploring a candidate of the same type as `choice`, if exploring
/// `choice` now would give the same outcome up to the declaration bound to the name.
private func twin(of choice: NameResolutionCandidate, in explored: [Explored]) -> Explored? {
  guard TyperExperiments.twins && !plain,
    let e = explored.last(where: { (x) in x.type == choice.type })
  else { return nil }
  if optimistic { return e }                           // rule T2 (needs `cleanfirst`)
  if let b = e.bound { return (b == best) ? e : nil }  // rule T1
  return (e.pure && best == .zero) ? e : nil           // rule T3 (needs `cleanfirst`)
}
```

The loop of `solve(overload:among:)` is the anchor for both `twins` and `cleanfirst`. Today:

```swift
    var viable: [(choice: NameResolutionCandidate, solution: Solution)] = []
    for choice in candidates {

      let equality = EqualityConstraint(lhs: k.type, rhs: choice.type, site: k.site)
      TyperCounters.bump("solver.forks")
      log("- pick: \(program.show(equality))")

      let s = indenting { (me) in
        var fork = Self(forking: me)
        let subgoal = fork.insert(fresh: equality)
        fork.outcomes[g] = fork.delegate([subgoal])
        fork.bindings[k.name] = choice.reference
        return fork.solution(betterThanOrEqualTo: me.best, using: &me.typer)
      }

      if let newSolution = s {
        let newScore = SolutionScore(
          errors: newSolution.diagnostics.elements.count, penalties: current.penalties)

        if newScore < best {
          best = newScore
          viable = [(choice, newSolution)]
        } else {
          viable.append((choice, newSolution))
        }
      }
    }
```

After all three steps (lines marked `[T]` come with `twins`, `[C]` with `cleanfirst`; the rest is unchanged, as is everything after the loop):

```swift
    assert(!optimistic || best == .zero)                                           // [C] A6
    var viable: [(choice: NameResolutionCandidate, solution: Solution)] = []
    var explored: [Explored] = []                                                  // [T]
    for choice in candidates {
      let s: Solution?
      if let e = twin(of: choice, in: explored) {                                  // [T]
        TyperCounters.bump("solver.twinsReused")                                   // [T]
        log("- reuse: \(program.show(choice.type))")                               // [T]
        s = e.solution.map({ (x) in x.rebinding(k.name, to: choice.reference) })   // [T]
      } else {
        let equality = EqualityConstraint(lhs: k.type, rhs: choice.type, site: k.site)
        TyperCounters.bump("solver.forks")
        log("- pick: \(program.show(equality))")

        var droppedInFork = false                                                  // [C]
        s = indenting { (me) in
          var fork = Self(forking: me)
          fork.dropped = false                                                     // [C]
          let subgoal = fork.insert(fresh: equality)
          fork.outcomes[g] = fork.delegate([subgoal])
          fork.bindings[k.name] = choice.reference
          let r = fork.solution(betterThanOrEqualTo: me.best, using: &me.typer)
          droppedInFork = fork.dropped                                             // [C]
          return r
        }
        dropped = dropped || droppedInFork                                         // [C]
        explored.append(                                                           // [T]
          .init(
            type: choice.type, bound: optimistic ? nil : best,
            pure: !droppedInFork, solution: s))
      }

      if let newSolution = s {
        let newScore = SolutionScore(
          errors: newSolution.diagnostics.elements.count, penalties: current.penalties)

        if optimistic {                                                            // [C]
          // The existing algorithm has `best.errors >= 1` here. A clean solution resets
          // `viable`; any other one would be erased by that reset, if it ever happens.
          if newScore == .zero {
            viable = [(choice, newSolution)]
            optimistic = false
          } else {
            dropped = true
          }
        } else if newScore < best {
          best = newScore
          viable = [(choice, newSolution)]
        } else {
          viable.append((choice, newSolution))
        }
      }
    }
```

`optimistic` and `best` are read for `Explored.bound` before the result of the fork changes them. In optimistic mode `viable` stays empty until a clean solution is found, so the existing `if viable.isEmpty { return nil }` after the loop also covers "no clean candidate".

With `twins` alone (step 1), `optimistic` is always `false`, `pure` is always `true`, and only rule T1 can fire.

### 4.2 `cleanfirst`

Anchor: the overload arm of the main loop in `solution(betterThanOrEqualTo:using:)`.

```swift
        case is OverloadConstraint:
          if deferring {
            me.parked.append(g)
            return .running
          }
          return me.solve(overload: g).map(SolverStatus.terminated(_:)) ?? .canceled
```

becomes (the `deferring` lines disappear with step 0):

```swift
        case is OverloadConstraint:
          if me.atFirstOverload {
            me.atFirstOverload = false
            if TyperExperiments.cleanfirst && !me.plain && (me.current.errors == 0),
              let s = me.cleanFirstSolution(overload: g)
            {
              return .terminated(s)
            }
          }
          if TyperExperiments.lookahead && !me.plain && (me.best == .zero)        // 4.3
            && me.hasCertainFailure()
          {
            TyperCounters.bump("solver.lookaheadCuts")
            return .canceled
          }
          return me.solve(overload: g).map(SolverStatus.terminated(_:)) ?? .canceled
```

and a new method:

```swift
/// Returns the solution that the existing algorithm computes for the rest of the system, `g`
/// being its first overload constraint, if the system has a candidate of `g` with a solution
/// free of diagnostics; returns `nil` otherwise, leaving `self` unchanged.
private mutating func cleanFirstSolution(overload g: GoalIdentity) -> Solution? {
  assert(best == .worst)                              // A5
  assert(current == .zero)                            // A7: no errors, penalties are unused
  TyperCounters.bump("solver.cleanfirstAttempts")

  var attempt = Self(forking: self)
  attempt.optimistic = true
  attempt.best = .zero
  attempt.typer = self.typer.sink()
  defer { self.typer = attempt.typer.sink() }

  if TyperExperiments.lookahead && attempt.hasCertainFailure() { return nil }
  let s = attempt.solve(overload: g)
  if s == nil { TyperCounters.bump("solver.cleanfirstFallbacks") }
  return s
}
```

How it behaves. The attempt is the existing search with two differences: every fork is cancelled at its first error (`best == .zero`), and each overload set, as long as it is `optimistic`, discards every solution that has a diagnostic instead of recording it. The first clean solution of a set ends the optimistic phase *of that set*: from then on the set runs the unchanged code with `best == .zero`, which is the state the existing algorithm is in after its reset. Forks inherit the mode of their set at the time they are created, so the candidates before and including the first clean one are explored optimistically, the later ones exactly.

If the attempt returns a solution, it is the existing algorithm's solution, clean or not (it can carry an "ambiguous use" when two clean candidates tie). If it returns `nil`, the system has no clean candidate at the first set and the unchanged code runs from the state before the attempt. The attempt is made once per system, at the first overload constraint; repeating it deeper in the fallback would redo work that already failed.

In `formSolution`, after the diagnostics are built:

```swift
    assert((current.errors == 0) || !ds.elements.isEmpty)   // A1
```

### 4.3 `lookahead`

Called from the two places shown in 4.2, only when `best == .zero`, that is, in the attempt and in the exact phase that follows a clean solution.

```swift
/// Returns `true` iff some goal in `fresh` fails, and is counted in `current.errors`, in every
/// run of the solver that starts from `self` and is not cancelled before it pops that goal.
private mutating func hasCertainFailure() -> Bool {
  TyperCounters.bump("solver.lookaheadScans")
  for g in fresh {
    let k = goals[g].updated { (t) in
      self.typer.program.types.reify(t, applying: substitutions, withVariables: .kept)
    }
    if certainlyFails(k) { return true }
  }
  return false
}

/// Returns `true` iff `k`, which has been reified, fails whatever is assigned to the variables
/// that are still open.
private mutating func certainlyFails(_ k: any Constraint) -> Bool {
  switch k {
  case let k as EqualityConstraint:
    return isClosed(k.lhs, k.rhs) && (program.types.unifiable(k.lhs, k.rhs) == nil)

  case let k as WideningConstraint:
    // `solve(widening:)` turns `k` into the equality of its operands.
    return isClosed(k.lhs, k.rhs) && (program.types.unifiable(k.lhs, k.rhs) == nil)

  case let k as CoercionConstraint:
    // The tests of `solve(coercion:)` on closed operands, in the same order.
    if !isClosed(k.lhs, k.rhs) || k.isTrivial { return false }
    return typer.coerced(k.origin, withType: k.lhs, toMatch: k.rhs).uniqueElement == nil

  case let k as CallConstraint:
    // Only callees that `solve(call:)` decomposes without opening a context clause.
    let (context, head) = program.types.contextAndHead(k.callee)
    guard context.isEmpty, program.types.tag(of: head) == Arrow.self else { return false }
    if !program.types.isCallable(head, program[k.origin].style) { return true }
    let w = program.types.seenAsTermAbstraction(head)!
    guard let (_, ss, _) = matches(k, w) else { return true }
    return ss.contains(where: { (s) in certainlyFails(s) })

  default:
    return false
  }
}

private func isClosed(_ a: AnyTypeIdentity, _ b: AnyTypeIdentity) -> Bool {
  !a[.hasVariable] && !b[.hasVariable]
}
```

The look-ahead changes no solver state. It answers one question about each pending goal: with what is already assigned, is its failure decided? For P3, once `h` is bound to `() -> A1` and the call `h()` has assigned its result, the pending call to `g` has an argument coercion `A1 → A0` with closed operands, and `coerced` returns nothing. The branch is abandoned when the next `h` is popped, before forking.

Cost: one pass over `fresh` per overload set popped under `best == .zero`; a call to `coerced` only for closed, non-identical operands, which the existing search would make in every leaf below. If a profile shows repeated `coerced` calls on the same successful coercion at successive levels, add to `Solver` a set of the `(origin, lhs, rhs)` triples already found coercible; forks inherit it. Not needed for the workloads here.

### 4.4 Self-check

`TyperExperiments.selfcheck` exists. Two additions:

- In `Typer.discharge`, after `let s = solver.solution(using: &self)`: if `selfcheck` is on, one of the three flags is on and the system contained an overload constraint, solve the same obligations again with a solver whose `plain` is `true` and `atFirstOverload` is `false`, and compare: `diagnostics` (equal as ordered sets), `bindings` (equal), for every `(n, t)` in `o.syntaxToType` the type `reify(t, applying: substitutions, withVariables: .substitutedByError)`, and the elaborations pairwise after the same reification. Bump `selfcheck.overload.confirmed` or print the system and bump `selfcheck.overload.violated`. About 40 lines.
- For the look-ahead: under `selfcheck`, do not cancel when `hasCertainFailure()` holds; set a field `expectsError = true` instead (forks inherit it) and, in `formSolution`, bump `selfcheck.lookahead.violated` if `expectsError && current.errors == 0`. About 10 lines.

The second run performs Typer queries the first did not, so `selfcheck` validates the search logic, not assumption A2. A2 is validated by comparing dumps between two processes (section 6).

## 5. Why it is correct

### 5.1 Facts about the existing code

Each is read off `Solver.swift`; the column says how it is checked at run time.

| | Fact | Check |
|---|---|---|
| F1 | A run that pops no overload constraint returns `nil` iff its final E exceeds `best`, and otherwise a solution that does not depend on `best`. E never decreases. | reading of the loop; `selfcheck` |
| F2 | `best` is read only by the cancellation test, by `formSolution`, and by `solve(overload:among:)`. A fork starts with the `best` of its parent at that time. | reading; `selfcheck` |
| F3 | The solution `solve(overload:among:)` returns is the solution of one of its forks, possibly with one more diagnostic. | reading |
| A1 | A solution built with E ≥ 1 has D ≥ 1: every counted failure has a root whose diagnostic builder inserts at least one diagnostic. | assertion in `formSolution` (4.2) |
| A3 | The solver never reads `bindings` to make a decision; diagnostic builders do not receive them. Hence two forks of one set whose candidates have the same `type` run identically, and their solutions differ only in `bindings[k.name]`. | `selfcheck`; code review of any new read of `bindings` |
| A4 | A type variable that is assigned is never reassigned. | existing assertion in `SubstitutionTable.assign` |
| A5 | The first overload constraint of a system is popped with `best == .worst`. | assertion in `cleanFirstSolution` |
| A6 | `optimistic` implies `best == .zero`. | assertion at the top of the loop (4.1) |
| A7 | `penalties` is always 0, so `.zero` is the score of exactly the clean solutions. | assertion in `cleanFirstSolution`; if penalties are ever used, replace the tests against `.zero` by tests on `.errors` |
| A2 | The answers of the `Typer` to the solver (`coerced`, `resolve`, `assume`, `summon`, the type store) do not depend on which other queries were made before in the same or an earlier system. | not assertable locally; two-process dump comparison (section 6). See 5.5. |

### 5.2 `twins`, rule T1

Let c and c′ be candidates of one set with the same type, S the solver state when the set is popped. By A3 the forks for c and c′ run the same computation from the same state. If both start with the same `best`, they return the same solution up to the binding of the name (F2: `best` is the only other input). Rule T1 reuses a result exactly in that case. No property of the search is used. With the flag alone this turns the `+` chain from 2ⁿ into n(n + 3)/2 forks: the first candidate of each set is explored under `.worst` and the second under `.zero`, so the outermost second candidates are re-explored, but everything below them hits T1.

### 5.3 `cleanfirst`

Write B(S, β) for what the existing `solution(betterThanOrEqualTo:)` returns from state S with `best == β`; C(S) for what the new code returns from S in optimistic mode; d(S) for the value of `dropped` afterwards. "Clean" means D = 0. A score "is at least 1" if its `errors` is.

**Theorem 1.** For every state S and every β at least 1:

- (a) if C(S) is not `nil`, then B(S, β) = C(S);
- (b) if C(S) is `nil`, then B(S, β) is `nil` or not clean;
- (c) if d(S) is `false`, then B(S, .zero) = C(S), `nil` included.

*Proof*, by induction on the number of forks the existing search makes below S.

*No overload constraint is popped.* C runs the loop with `best == .zero`. If E stays 0, C(S) is the solution, equal to B(S, β) and B(S, .zero) by F1. If E reaches 1, C(S) is `nil`, B(S, .zero) is `nil`, and B(S, β) is `nil` or has D ≥ 1 by A1. Nothing is dropped.

*An overload constraint is popped* after a prefix. If the prefix has an error, C(S) is `nil` and B(S, .zero) is `nil`; every solution below has E ≥ 1, hence D ≥ 1 (A1), and by F3 so does anything B(S, β) returns. Otherwise let S₁, …, Sₙ be the fork states, in candidate order, and let j be the first index for which C(Sⱼ) is clean, if any.

Existing search from β: by induction on i < j, the fork i starts with a `best` at least 1 (it starts at β, and is only lowered to the D of a solution that, by (a) and (b) for Sᵢ, is not clean), and returns `nil` or a solution that is not clean.

- If there is no j, every entry of the existing `viable` is not clean, so by F3 B(S, β) is `nil` or not clean; C(S) is `nil`. This is (b).
- If there is a j: B(Sⱼ, ·) = C(Sⱼ) by (a), its score 0 is below the current `best`, so the existing code sets `best = .zero` and `viable = [j]`. The new code sets `viable = [j]`, leaves `best == .zero`, and clears `optimistic`. From here both run the same code from the same state on the candidates after j, where forks compute B(Sᵢ, .zero) and `best` cannot change. The two `viable` lists are equal, element by element and in order, so the same solution is picked, whatever `isPreferred` is. This is (a).

For (c), suppose nothing was dropped in the search below S. Then, for i < j (or all i if there is no j), C(Sᵢ) is `nil` (a solution with diagnostics would have been dropped at this set) and d(Sᵢ) is `false`, so B(Sᵢ, .zero) is `nil` by (c) for Sᵢ. The existing search from `.zero` thus has an empty `viable` before j; at j it gets B(Sⱼ, .zero) = C(Sⱼ) by (c), which it appends; after j it computes the same B(Sᵢ, .zero) as the new code. Same `viable`, same result; with no j both are `nil`. ∎

**Theorem 2 (the whole system).** By A5 the first overload constraint is popped with `best == .worst`, which is at least 1. If the attempt returns a solution, it is the existing result by 1(a). Otherwise the unchanged code runs from the unchanged state. If the prefix already has an error the attempt is skipped: by A1 no clean solution exists.

**Rules T2 and T3.** T2: in optimistic mode, c′ would be explored by the same procedure from the same state as c (A3), so C and d are the same; the reused solution is `nil` or not clean, otherwise the optimistic phase would have ended at c. T3: the result needed is B(S + c′, .zero), which by A3 is B(S + c, .zero) rebound, which by 1(c) is C(S + c) when nothing was dropped below c. `tests/m07` is a program where something *was* dropped and the two differ.

The work of the attempt is bounded by the existing search: it only visits states with E = 0, and the existing search never cancels such a state. Hence at most twice the work when the attempt fails.

### 5.4 `lookahead`

**Lemma.** Let F be a solver state and G a goal in `F.fresh`. Every run from F either is cancelled first or pops G, in every leaf below F, reified with a substitution that extends F's (A4, and forks copy `fresh`). If G reified with F's substitution has closed operands, it is the same goal in every leaf, and:

- a closed equality fails iff `unifiable` returns `nil`;
- a closed widening is simplified to that equality, which is then popped and fails;
- a closed, non-trivial coercion reaches `typer.coerced` with the same arguments and fails iff the result has no unique element (the `postpone` branches of `solve(coercion:)` need a variable);
- a call whose callee has an empty context and an `Arrow` head is decomposed by `solve(call:)` according to the arrow's labels, arity and style only, which substitution does not change; it fails directly if it is not callable or `matches` returns `nil`, and otherwise schedules the coercions that `matches` returns, to which the previous case applies.

Each such failure is a `.failure` outcome of a popped goal, so it is counted in E. ∎

So when `hasCertainFailure()` holds at F, every leaf below F has E ≥ 1 or is cancelled. With `best == .zero` every fork below returns `nil` (F1), and so does every set (empty `viable`): cancelling at F is what B(F, .zero) returns. In optimistic mode, returning `nil` without dropping anything satisfies 1(b) (A1 and F3) and 1(c).

The look-ahead must only count failures that E counts. A stale coercion that cannot be simplified is a diagnostic but not an error; treating it as one changes results (model variant `count-quirks`). The cases above involve no stale goal: a goal with closed operands is never postponed.

### 5.5 The assumption that cannot be asserted: A2

Every pruning skips Typer queries that the existing solver makes in branches whose result is discarded, and the look-ahead makes some queries earlier. If the answer to a later query depended on that, results could change. This is the mechanism behind the known dependence on declaration order: a query can force the lazy computation of a declaration's type, and the value computed depends on what is on `declarationsOnStack` at that moment. The unconditional extension skip was rejected for this reason.

What limits the risk here: the first member lookup of a system evaluates the applicability of every visible extension, and the first coercion that needs resolution enumerates every visible given, whatever the types involved; the skipped queries are later queries of the same kinds, and T1 to T3 skip exact repetitions. A program on which this design changes a result is therefore a program whose result already depends on the order in which declarations are first evaluated. No such program was found, and none could be tested, since the design is not built. The test plan treats this as the main thing to check.

Fresh type variables are numbered differently when forks are skipped. Stored types replace leftover variables by errors, and diagnostics print reified types, so this should be invisible in types and messages. The witness dump has shown such renamings before (one file, section 2.5 of the review) and must be compared up to the names of leftover variables.

### 5.6 Evidence from the model

`scripts/model.py` implements section 2 and section 4 over abstract goals (overload sets, and checks whose outcome is a function of the types chosen, with counted and uncounted failures, shared diagnostics, twins, sets created dynamically, and an arbitrary, possibly intransitive preference).

- On 200,000 random systems (4 seeds), six combinations of the flags, including each step of section 7, return exactly the baseline's solution: 0 differences in 1,200,000 comparisons (`results/model-fuzz.jsonl`). Of these systems 47% are clean and 53% are not; 40% take the fallback.
- Six deliberately wrong variants, each removing one clause of the argument above, are all detected (`results/model-mutants.jsonl`): no erase rule (825 of 30,000 systems differ), trusting an attempt without a clean candidate (2,442), look-ahead counting uncounted failures (51), look-ahead under `best > 0` (1,944), T3 without the purity test (32), T1 without the bound test (154).
- The random systems are not exhaustive: they did not find the flaw of the "start with `best == 0`" shortcut of section 3 in 30,000 systems; a hand-made system shows it. The argument for the design is the proof of 5.3; the fuzzer only failed to refute it.
- The model's baseline agrees with the binary on forks, overload sets and number of diagnostics for 18 of the test programs, the delicate ones included (`results/model-vs-binary.jsonl`).

The model does not contain unification, so it says nothing about F1 to A4 themselves or about the Lemma's reading of `solve(call:)` and `solve(coercion:)`. Those are covered by the assertions and by `selfcheck`.

## 6. Test plan

`tests/` holds 34 programs. Each starts with the expected outcome after the change, the reason, and the current outcome on the binary under base and FULL (`scripts/make_tests.py` wrote them; `--check` re-runs the binary and compares).

| Group | Programs | Expectation |
|---|---|---|
| `s01`–`s08` | the three workloads, their variants, `+` chain, method chain, mixed operators | same dump as today; `solver.forks` at most the bound in the comment (from the model) |
| `s09` | independent clean sets | unchanged, 126 forks; documents what is not fixed |
| `e01`–`e08` | erroneous systems | same diagnostics, character for character, including the ambiguities that depend on search order; fork bounds in the comments |
| `m01`–`m17` | programs whose meaning depends on pop order, candidate order, the inherited `best`, or ranking; the counterexamples to the earlier attempt; `overload-priority.hylo` | same dump as today |

Tests aimed at one clause each: `m06` (erase rule), `m07` (purity test of T3), `m04`/`m05` (solutions worse than `best` stay viable), `e01`/`e02` (no result is taken from an attempt without a clean candidate), `m14` (the look-ahead asks `coerced` rather than comparing identities), `s03` (no extra forks when the existing search is already linear), `e08`/`m08`/`m13` (pop order untouched).

Procedure for each step of section 7, with the flag alone and with all earlier flags:

1. Dump comparison against base (`tc-bench --dump`) on: `tests/`, `research/review/solver/*.hylo` and its `verify-S*` directories, the 216 corpus files, the test programs under `research/report/test-programs/` (declaration-order and cycles included, because of A2), and the declaration-order fuzzer of `research/followup/permute.py` on `tests/`. Zero differences. **Before step 1**, make the dump print which declaration a name is bound to (step 0): today it prints only the name, so it cannot tell the two candidates of `+` apart, and a wrong `rebinding` would pass unnoticed.
2. Counters: the bounds in the test comments; on the standard library, `solver.goalSteps` not above today's 9,484. On every program that base accepts, `solver.cleanfirstFallbacks` must be 0: by Theorem 1b a fallback means that the existing result has a diagnostic.
3. `selfcheck` on all of the above: `selfcheck.overload.violated` and `selfcheck.lookahead.violated` equal to 0.
4. Debug build: none of the assertions A1, A5, A6, A7 fires.
5. Timing with the interleaved method of the plan (0.3) on the standard library (expected: no measurable change) and on `s01`, `s04`, `s06`.

If the algorithm of section 4 is changed during implementation, change `scripts/model.py` in the same way and re-run `model.py fuzz` and `mutants.py` before building: the model is where a mistake in the bookkeeping of `viable` and `best` shows first.

## 7. Implementation order

Each step builds and is testable alone. Line counts are estimates of added lines.

| Step | Change | Lines | Expected result | Abandon if |
|---|---|---:|---|---|
| 0 | Delete the `solver` experiment from `Solver.swift` (`parked`, `probing`, `probeFinished`, `resolveParked`, `probe`, the `deferring` branches). Make `semanticDump` print, for each binding, the kind of reference and the site of the declaration. | −95, +10 | dumps identical to base except the new binding column; counters unchanged | – |
| 1 | `twins` with rule T1 only: `Explored`, `twin(of:in:)`, the `[T]` lines, `Solution.rebinding`. | 45 | `s06`: 2,046 → 65 forks; `s07`: 126 → 27; `s08`: 510 → 44; everything else unchanged | `solver.twinsReused` is 0 on `s06` and `s07`. Then the two candidates do not have the same type identity, and the premise of A3 is not met; do not weaken the test to "equal after dealiasing" (the fork's stored types would differ). Ask question 3 of section 8 instead. |
| 2 | Self-check of 4.4 (first bullet) and assertion A1. | 45 | 0 violations with `twins` | A1 fires: find the failure without a diagnostic; `cleanfirst` cannot be added before it is understood. |
| 3 | `cleanfirst`: the three fields, the overload arm, `cleanFirstSolution`, the `[C]` lines, rules T2 and T3. | 45 | `s01`: 3,184 → 32; `s02`: 1,932 → 24; `s06`: 10; `s07`: 6; `s08`: 8; `e03` ≤ 308; `e04` ≤ 6,558 | any dump difference on a program without cyclic declarations; or a fallback in a program that base accepts (Theorem 1b excludes it, so it would show that a fact of 5.1 is wrong). |
| 4 | `lookahead`: `hasCertainFailure`, `certainlyFails`, the two call sites, the second self-check. | 80 | `s04`: 9,840 → 24; `s05`: 349,524 → 36; `e04` ≤ 3,300 | `selfcheck.lookahead.violated` > 0 (the Lemma's reading of `solve(call:)` or `solve(coercion:)` is wrong for some shape: restrict `certainlyFails` to that shape or drop the flag); or a dump difference traced to `coerced` being asked earlier (A2). |
| 5 (optional) | In the exact search with `0 < best < .worst`, cancel at an overload constraint when `current.errors` plus the *number* of certain failures exceeds `best.errors`. Sound by the same Lemma, for any `best`. | 20 | `e03`: 308 → 56 in the model; `e04`: no gain | no erroneous workload of interest improves; the model says this is likely. |

Estimated effect on the three workloads after step 4, from the fork counts and today's ratio of goal steps to forks (indicative): `ovl-4-8` 3,184 → 32 forks, about 350 goal steps instead of 35,119; `ovr-3-8` 9,840 → 24 forks plus 22 scans; `ovl-ret-9` 349,524 → 36 forks plus 33 scans. At today's cost per fork that is about 0.1 s under base and a few milliseconds under FULL for `ovl-4-8`, and a few milliseconds for the other two.

Order rationale: step 1 fixes the only exponential seen in ordinary code and has the simplest argument. Step 3 is the foundation for step 4. If step 3 has to be abandoned, step 1 stands alone; step 4 does not.

## 8. Open questions for the language designers

1. **Is the nested ranking intended?** Only the outermost overload set is ranked across combinations; inner sets are ranked inside each outer choice (`m01`, `m10`, `m11`: swapping two arguments changes the selected overloads, or turns an accepted program into an ambiguity). A symmetric rule would make component-wise solving possible and would change these programs.
2. **Is a solution with more diagnostics than the best one meant to stay viable?** The `else { viable.append(…) }` branch lets a preferred candidate with a nested ambiguity or an error win over a clean one (`m04`, `m05`), makes acceptance depend on the order of the search (`m06` accepted, `m07` rejected), and produces ambiguity errors in erroneous systems that depend on declaration order (`e01` against `e02`; `e04`: six diagnostics for one bad argument). If the intended rule is "among the solutions with the fewest diagnostics, the preferred one", the solver becomes simpler, erroneous systems no longer need the exact fallback, and these programs change.
3. **Should a member and the trait requirement it implements be two candidates?** For a concrete receiver they denote the same function. If name resolution kept one, the exponential of P1 would disappear at its source and `twins` would be unnecessary for it. Which one is bound affects the elaboration (direct call or call through the witness).
4. **Should errors be counted the way diagnostics are?** Failures that are not counted in `current.errors` (stale constraints, a coercion that cannot be simplified) are the other source of the behaviours in question 2.
5. **Are the diagnostics of an erroneous system part of the contract?** If an implementation may report a different, smaller set of errors for an ill-typed statement, the erroneous case can be made fast as well. Today it must reproduce diagnostics such as those of `e04`.
6. **For an ambiguous use, is "continue with the candidate declared first" the intended recovery** (`m02`, `m03`)?
7. **Are declarations whose types depend on each other through extensions and givens legal?** If not, assumption A2 holds by construction, and with it the last unprovable step of this design.
