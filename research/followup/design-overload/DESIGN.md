# Speeding up overload resolution: the design, and how much of it preserves results

For the engineer who works on `/home/user/hylo-impl/Sources/FrontEnd/Typer/Solver.swift`. The behaviour of the existing solver was measured on the binary `exp/bin/eq9-723cc0e6b0f8/tc-bench`. The design was written without building anything, from an executable model of the search (`scripts/model.py`), which reproduces the binary's fork counts and diagnostic counts on 19 programs.

**Status after review (section 9).** While the review was under way, the design was implemented as first written (hylo-impl commit `9dc04d7`, binary `exp/bin/eq25-c7cbd846a05c`). The review ran that binary. Two things follow, and the document has been revised accordingly:

- `twins` returns the existing result on every program tried, and its fork counts are the model's.
- `cleanfirst` and `lookahead` are **not** result-preserving. The search they perform returns the existing solution, but they skip or reorder queries to the Typer, and the verdict of a program can depend on those queries. Nine programs in `tests/` (`a01` to `a08`, `a12`) show it; four of them change verdict on the binary, in base and in FULL, in both directions (accepted to rejected and rejected to accepted). With `sigrounds` the verdicts of the nine are stable, and one diagnostic of an ill-formed program still changes (`a12`). Sections 5.5 and 9 say what this means and what to do.

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

Each rule below was read from `Solver.swift`. The demonstrations show the rules that a small program can exhibit on the binary; the two statements about stale goals (2.1, 2.4) rest on the code alone. `scripts/model.py` implements these rules, and `results/model-vs-binary.jsonl` shows that it predicts the forks, the overload sets and the number of diagnostics of the binary on 18 programs, including the programs cited in 2.3 to 2.5 except `m01` and `m03`. The review added a nineteenth (`tests/a11`: 136 forks, 51 sets).

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

6. The queries that every fork makes to the `Typer`, including the forks that return `nil` and those whose solution is erased. A query can compute the type of a declaration for the first time, and which declaration is computed first can decide whether a program is accepted (section 5.5). `tests/a01` is accepted and `tests/a02`, the same program with two overloads declared in the other order, is rejected with "definition of 'X' refers to itself": in `a01` the fork of the wrong candidate runs to the end and makes a member lookup that `a02` never makes.

Within the solver, the result does not depend on what a fork that returned `nil` computed. A fork whose solution is later erased by a reset still matters through the `best` it leaves to the forks after it; Theorem 1 says when that influence vanishes.

The earlier attempt (`solver` flag) changed 1 and 2. A sound optimization must leave the pop order and the candidate order alone, and must reproduce `viable` exactly wherever it returns a result. To preserve point 6 as well it may only skip a fork that would repeat, query for query, a fork that has just run. `twins` does that; `cleanfirst` and `lookahead` do not.

## 3. Options considered

Fork counts "after" are computed with the model, whose baseline matches the binary on these programs; row (c) is not modelled and is estimated by hand as one fork per candidate per set.

| Option | Result-preserving? | `ovl-4-8` (3,184) | `ovr-3-8` (9,840) | `ovl-ret-9` (349,524) | `+` chain, 14 (32,766) |
|---|---|---:|---:|---:|---:|
| (a) discard candidates by a test on the candidate alone, before forking | only relative to `best == 0` | 3,184 | 9,840 | 349,524 | 32,766 |
| (b) probe to the next overload set, prune against the best complete solution | yes; it is what the solver already does | 3,184 | 9,840 | 349,524 | 32,766 |
| (b′) the same with the bound "no error" from the start, exact fallback (`cleanfirst`) | yes | 32 | 9,840 | 349,524 | 32,766 |
| (c) solve connected components separately | only when every component's result is clean | 32 | 24 | 36 | 32,766 |
| (d) memoize identical sub-systems, restricted to same-type candidates (`twins`) | yes | 3,184 | 9,840 | 349,524 | 14 (119 without rule T4) |
| chosen: `twins` + `cleanfirst` + `lookahead` | `twins`: yes; the other two: see 5.5 | 32 | 24 | 36 | 14 |

In the rows (b′) and (c) and in the last one, "yes" is about the solution that the search returns. Whether the program's verdict is preserved also depends on the Typer queries that are skipped (5.5).

**(a) Pre-fork filter.** When the set is popped, nothing is known about the expected type: the overloaded name has a fresh variable as its type (`assume(_:boundTo:for:at:in:)`), the result of a call is a fresh variable too, which the Typer deliberately does not relate to the expected type ("We cannot use the expected type to constrain the result of the callee"), and labels were already filtered in `filterInPlace`. A test on the candidate alone finds nothing on the three workloads. Moreover, "cannot succeed" is not a licence to discard: when no candidate succeeds, the discarded one may be the one whose diagnostics the solver reports (`tests/e05`). A discard is only sound as "this fork returns `nil` under `best == 0`". The useful form of (a) is a test on the goals still pending *after* the choice has propagated; that is `lookahead`.

**(b) Probing, branch and bound.** The existing solver already is a branch and bound in the existing order: a fork stops when its errors exceed `best`. A separate probe "up to the next overload set" computes nothing the fork itself does not compute. What is missing is a bound before the first complete solution. The reviewers' rule (prune a candidate whose probe has errors if another candidate's probe finishes clean) only applies at the innermost set. Their "tentative commit, re-run everything if the result has diagnostics" is close to the chosen design, but one of its supporting claims ("the decisions made inside each fork do not depend on the inherited `best`") is false (2.4, `m07`).

The obvious shortcut, "start the existing search with `best == 0` and keep its result if it is clean", is not safe either. It keeps in `viable` the solutions that the existing search would have erased; they cannot be picked (the result would not be clean), but they take part in `minimalElements` and can eliminate a rival of the winner. `scripts/mutants.py` contains a system with three candidates on which the shortcut accepts a program that the existing search calls ambiguous. It needs a preference that is not transitive, which `compareLexicalDistances` followed by `elaborationCost` does not exclude by construction. The chosen design adds an erase rule (4.2) that makes `viable` identical to the existing one, element by element, so that no property of `isPreferred` is needed. Cost: about 45 lines, three new invariants (A1, A5, A6).

**(c) Components.** Take the goals pending when a set is popped, and suppose they split into the component K₁ of that set and a rest K₂ that shares no open type variable with it. The union of the two separately computed results is the result of the nested search when the result of K₂ is clean and does not depend on `best` (the property of Theorem 1c below): K₂ then contributes the same diagnostic-free solution under every candidate of the set, so each fork's score and cancellation are those of K₁ alone and `viable` is what it would be for K₁ alone. This was reasoned, not modelled. When a component has a diagnostic (an error or an ambiguity), scores and cancellation thresholds mix across components, and the nested result is not the union: in `e01`, solving the two arguments separately gives two diagnostics, the nested search three. So (c) needs the same clean-or-fall-back structure as `cleanfirst`, plus: a constraint graph kept up to date while goals spawn subgoals and overload sets appear dynamically; a virtual decomposition of pending calls (otherwise `g(h(), h(), …)` is one component); and a merge of `elaborations` in baseline pop order, because synthetic nodes are numbered in that order. Estimate: 300 lines and four invariants. It adds nothing on the measured workloads beyond the chosen design, and nothing on the `+` chain, which is a single component. It is the only option that would fix `tests/s09-independent-clean-6.hylo` (independent sets, several clean candidates of *different* types each: 126 forks, would be 12). Not chosen; reconsider if the census finds that shape in real code.

**(d) Memoization.** Keying on the whole solver state is expensive and rarely hits: two forks of one set differ at least in the type assigned to the callee. The exception is exact and free to detect: two candidates with the same `type` produce forks that differ only in `bindings[k.name]`, which the solver never reads. This is P1, the only exponential found in ordinary code. Cost: about 60 lines, one invariant (A3). It is also the only option that skips nothing but exact repetitions, so it is the only one that leaves the Typer's queries, and therefore point 6 of section 2.6, untouched.

**Why the chosen combination.** Each of the three changes is small, leaves the pop order and the candidate order untouched, and has a correctness argument that does not depend on properties of unification or of `isPreferred`. `twins` alone is correct by a short argument and fixes the realistic case completely (linear, with rule T4 of 4.1). `cleanfirst` supplies the missing bound; the solution it returns is the existing one, but it is exact for the whole program only where the Typer's answers do not depend on the order of queries (5.5). `lookahead` is the most specialized: it only matters for return-type overloading consumed by a call whose parameter types are known, and it has the same restriction.

**What is not fixed.** Systems with no clean solution run the existing search after a failed attempt: same result, up to twice the forks with `cleanfirst` alone (`e04`: 6,558 against 3,279; 3,300 with `lookahead`). `s09` is unchanged.

## 4. The design

### 4.0 Flags and state

`TyperCounters.swift`, next to the existing flags:

```swift
/// Overload resolution: candidates of one overload set that have the same type share one
/// exploration (result-preserving).
nonisolated(unsafe) public static var twins: Bool = enabled.contains("twins")

/// Overload resolution: look for a solution without diagnostics first; run the existing search
/// only if there is none. Returns the solution of the existing search, but skips queries to the
/// typer that the existing search makes, which can change the verdict of a program whose
/// declarations are computed in an order-dependent way.
nonisolated(unsafe) public static var cleanfirst: Bool = enabled.contains("cleanfirst")

/// With `cleanfirst`: abandon a branch in which a pending goal is certain to fail. Same caveat
/// as `cleanfirst`; it also makes some queries earlier than the existing search.
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

/// `true` iff, in the search rooted at `self`, a goal failed, or a fork returned no solution or
/// a solution with a diagnostic (`twins`, rule T4). While it is `false`, no decision of that
/// search depended on `best`.
private var blemished = false
```

New counters: `solver.twinsReused`, `solver.cleanfirstAttempts`, `solver.cleanfirstFallbacks`, `solver.lookaheadScans`, `solver.lookaheadCuts`, and the two exposure counters of 4.5, `solver.forcedAfterError` and `solver.forcedInScan`.

The three flags have no effect while the old `solver` flag is on. Step R7 of section 7 deletes that experiment.

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
  /// `true` iff the set was popped without error, no goal failed during the exploration, and the
  /// fork and every fork below it returned a solution without diagnostics (rule T4).
  let spotless: Bool
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
  if e.spotless { return e }                           // rule T4: valid under any bound
  if optimistic { return e }                           // rule T2 (needs `cleanfirst`)
  if let b = e.bound { return (b == best) ? e : nil }  // rule T1
  return (e.pure && best == .zero) ? e : nil           // rule T3 (needs `cleanfirst`)
}
```

Rule T4 was added in review. It needs one more line in the main loop of `solution(betterThanOrEqualTo:using:)`, where errors are counted:

```swift
        if me.outcomes.failed(g) {
          me.current.errors += 1
          me.blemished = true                                                      // [T]
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
        var blemishedInFork = false                                                // [T]
        s = indenting { (me) in
          var fork = Self(forking: me)
          fork.dropped = false                                                     // [C]
          fork.blemished = false                                                   // [T]
          let subgoal = fork.insert(fresh: equality)
          fork.outcomes[g] = fork.delegate([subgoal])
          fork.bindings[k.name] = choice.reference
          let r = fork.solution(betterThanOrEqualTo: me.best, using: &me.typer)
          droppedInFork = fork.dropped                                             // [C]
          blemishedInFork = fork.blemished                                         // [T]
          return r
        }
        dropped = dropped || droppedInFork                                         // [C]
        let spotless =                                                             // [T]
          (current.errors == 0) && !blemishedInFork
          && (s.map({ (x) in x.diagnostics.elements.isEmpty }) ?? false)
        blemished = blemished || !spotless                                         // [T]
        explored.append(                                                           // [T]
          .init(
            type: choice.type, bound: optimistic ? nil : best,
            pure: !droppedInFork, spotless: spotless, solution: s))
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

With `twins` alone, `optimistic` is always `false`, `pure` is always `true`, and only rules T1 and T4 can fire. T1 alone leaves the `+` chain quadratic, because the first candidate of the outermost set is explored under `.worst` and the second under `.zero` (65 forks for ten operators, measured on the implementation). T4 makes it linear without `cleanfirst` (10 forks in the model): the exploration of the first candidate meets no failure, so its result does not depend on the bound.

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

becomes (the `deferring` lines disappear with step R7; commit `9dc04d7` also tests `me.best == .worst` here instead of asserting A5, and sets a flag `sawOverload` for the self-check):

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

This assertion is not in commit `9dc04d7` and must be added. A1 holds for every goal that is a subgoal of a root goal. It does not hold by construction under `headsubst`: `resolve(_:elaboratedBy:at:)` schedules its equalities with `_ = schedule(EqualityConstraint(lhs: x.erased, rhs: v, site: site))` and attaches them to no goal, so if one fails it is counted in `current.errors` and no diagnostic builder reaches it. The existing search then scores that solution as clean, and the attempt cancels it. Either make `solve(coercion:)` return these equalities as subgoals (`.forward`, with a diagnostic), or skip the attempt when `TyperExperiments.headsubst` is on, until the assertion has been run on the `headsubst` tests. No program on which such an equality fails was found; the variable is fresh in the cases tried.

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

"Closed" means exactly `!t[.hasVariable]`, and must stay so: it is the condition under which `TypeStore.reify` returns its argument unchanged (`if !n[.hasVariable] { return n }`), which is what makes the goal that a leaf pops identical to the goal scanned here. Without `arrowenv`, the type of an arrow whose environment contains a variable has `hasVariable == false`; it is still "closed" in this sense, because `reify` does not look into it either.

The look-ahead changes no solver state. It answers one question about each pending goal: with what is already assigned, is its failure decided? It does make queries to the Typer (`coerced`) earlier than the existing search makes them, and makes some that the existing search makes only in other forks; section 5.5 shows a program whose verdict this changes (`tests/a07`). For P3, once `h` is bound to `() -> A1` and the call `h()` has assigned its result, the pending call to `g` has an argument coercion `A1 → A0` with closed operands, and `coerced` returns nothing. The branch is abandoned when the next `h` is popped, before forking.

Cost: one pass over `fresh` per overload set popped under `best == .zero`; a call to `coerced` only for closed, non-identical operands, which the existing search would make in every leaf below. If a profile shows repeated `coerced` calls on the same successful coercion at successive levels, add to `Solver` a set of the `(origin, lhs, rhs)` triples already found coercible; forks inherit it. Not needed for the workloads here.

### 4.4 Self-check

`TyperExperiments.selfcheck` exists. Two additions:

- In `Typer.discharge`, after `let s = solver.solution(using: &self)`: if `selfcheck` is on, one of the three flags is on and the system contained an overload constraint, solve the same obligations again with a solver whose `plain` is `true` and `atFirstOverload` is `false`, and compare: `diagnostics` (equal as ordered sets), `bindings` (equal), for every `(n, t)` in `o.syntaxToType` the type `reify(t, applying: substitutions, withVariables: .substitutedByError)`, and the elaborations pairwise after the same reification. Bump `selfcheck.overload.confirmed` or print the system and bump `selfcheck.overload.violated`. About 40 lines.
- For the look-ahead: under `selfcheck`, do not cancel when `hasCertainFailure()` holds; set a field `expectsError = true` instead (forks inherit it) and, in `formSolution`, bump `selfcheck.lookahead.violated` if `expectsError && current.errors == 0`. About 10 lines.

The second run performs Typer queries the first did not, so `selfcheck` validates the search logic, not assumption A2. On `tests/a01`, `a03` and `a07`, whose verdict changes, the self-check of commit `9dc04d7` reports no violation. A2 can only be tested by comparing two processes (section 6).

Two remarks on the self-check as implemented in `9dc04d7`. It compares the diagnostics and the bindings only, not the types and elaborations; that is enough for the search logic, since the solution is one object. It compares `DeclarationReference` values with `==`; a reference `.inherited(w, m, _)` contains a witness, and a witness can contain variables created during solving, which differ between the two runs. No false violation was seen on the tests, but if one appears, compare the references after reification.

### 4.5 Measuring the exposure to A2

Whether `cleanfirst` changes a result depends on what the forks it cancels would have asked the Typer. This can be measured in the existing search, without the flags, with a counter of the *first computations of a signature* (and of the diagnostics reported by the Typer) that happen in a solver state that the attempt never reaches, that is, a state with `current.errors >= 1`.

In `Typer`:

```swift
/// The number of solver forks in progress that have counted an error (instrumentation).
internal var doomedDepth = 0

/// `true` while the solver scans pending goals (`lookahead`; instrumentation).
internal var scanning = false

/// Records that the type of a declaration is computed for the first time, or that a diagnostic
/// is reported, while the solver is in a state that `cleanfirst` does not visit.
private func noteForcing() {
  if doomedDepth > 0 { TyperCounters.bump("solver.forcedAfterError") }
  if scanning { TyperCounters.bump("solver.forcedInScan") }
}
```

`noteForcing()` is called at each place where a declaration enters `declarationsOnStack` for the first time (the four tests `if declarationsOnStack.insert(.init(d)).inserted {` in `Typer.swift`, which include `extendeeType`) and in `report(_:)`. In `Solver`, the main loop of a solver below the first overload constraint (`!atFirstOverload`) increments `typer.doomedDepth` when `current.errors` goes from 0 to 1, and that solver decrements it when it returns (a local flag remembers that it did; the forks made meanwhile run inside that interval); `hasCertainFailure()` sets `typer.scanning` around its loop. About 25 lines.

Reading: if `solver.forcedAfterError` is 0 for a program under the existing search, the attempt and the existing search drive the Typer through the same first computations in the same order, and `cleanfirst` gives the same result for that program. If `solver.forcedInScan` is 0 as well (measured with the flag on), so does `lookahead`. The counters are not a guard: the tails that the attempt skips are not run, so the solver cannot know at run time what they would have forced. They tell, on a corpus, how many programs are exposed. On `tests/a01`, `a03`, `a05` and `a12` the first counter must be positive, on `a07` the second.

## 5. Why it is correct

### 5.1 Facts about the existing code

Each is read off `Solver.swift`; the column says how it is checked at run time.

| | Fact | Check |
|---|---|---|
| F1 | A run that pops no overload constraint returns `nil` iff its final E exceeds `best`, and otherwise a solution that does not depend on `best`. E never decreases. | reading of the loop; `selfcheck` |
| F2 | `best` is read only by the cancellation test, by `formSolution`, and by `solve(overload:among:)`. A fork starts with the `best` of its parent at that time. | reading; `selfcheck` |
| F3 | The solution `solve(overload:among:)` returns is the solution of one of its forks, possibly with one more diagnostic. | reading |
| A1 | A solution built with E ≥ 1 has D ≥ 1: every counted failure has a root whose diagnostic builder inserts at least one diagnostic. Read off the code for every goal that is a subgoal of a root; not guaranteed under `headsubst` (4.2). Rule T4 does not use it. | assertion in `formSolution` (4.2) |
| A3 | The solver never reads `bindings` to make a decision; diagnostic builders do not receive them. Hence two forks of one set whose candidates have the same `type` run identically, and their solutions differ only in `bindings[k.name]`. | `selfcheck`; code review of any new read of `bindings` |
| A4 | A type variable that is assigned is never reassigned. | existing assertion in `SubstitutionTable.assign` |
| A5 | The first overload constraint of a system is popped with `best == .worst`. | assertion in `cleanFirstSolution` |
| A6 | `optimistic` implies `best == .zero`. | assertion at the top of the loop (4.1) |
| A7 | `penalties` is always 0, so `.zero` is the score of exactly the clean solutions. | assertion in `cleanFirstSolution`; if penalties are ever used, replace the tests against `.zero` by tests on `.errors` |
| A2 | The answers of the `Typer` to the solver (`coerced`, `resolve`, `assume`, `summon`, the type store) do not depend on which other queries were made before in the same or an earlier system. **False in base and in FULL** (`tests/a01` to `a08`), and for the text of one diagnostic also with `sigrounds` (`a12`); needed by `cleanfirst` and `lookahead` only. | not assertable locally; two-process dump comparison (section 6); exposure counters (4.5). See 5.5. |
| A2′ | A fork that repeats, query for query, a fork that has just run from the same solver state leaves the `Typer` in a state that no later query can tell from the state before it. This is all that `twins` needs. | two-process dump comparison with `twins` alone (section 6) |

### 5.2 `twins`, rules T1 and T4

Let c and c′ be candidates of one set with the same type, S the solver state when the set is popped. By A3 the forks for c and c′ run the same computation from the same state. If both start with the same `best`, they return the same solution up to the binding of the name (F2: `best` is the only other input). Rule T1 reuses a result exactly in that case. No property of the search is used. With T1 alone the `+` chain goes from 2ⁿ to n(n + 3)/2 forks: the first candidate of each set is explored under `.worst` and the second under `.zero`, so the outermost second candidates are re-explored, but everything below them hits T1.

**Theorem 0 (rule T4).** Call the exploration of a fork *spotless* if its set was popped with E = 0, no goal failed in the fork or anywhere below it, and the fork and every fork below it returned a solution without diagnostics. If the exploration of S + c under some bound β is spotless, the existing algorithm returns the same solution from S + c under every bound β′, and performs the same goal steps in the same order.

*Proof*, by induction on the number of forks below. `best` is read in three places (F2). The cancellation test and `formSolution` compare `current` with `best`; E is 0 throughout, so neither fires under any bound. In `solve(overload:among:)`, take a set below, popped with bound b in one run and b′ in the other. Its first fork returns, by induction, the same clean solution in both runs. Its score 0 either is below the bound, and the code sets `best = .zero` and `viable = [1]`, or the bound is already 0 and the solution is appended to the empty list: `viable = [1]` and `best == .zero` in both runs. Every later fork therefore starts from the same state with `best == .zero` in both runs and returns the same solution, which is clean and is appended (`0 < 0` is false). The two `viable` lists are equal, so the same solution is picked. ∎

An exploration made in optimistic mode that is spotless drops nothing and is, step for step, the exploration under `.zero`; the theorem then applies to it.

The flag `blemished` of 4.1 is the negation of "spotless": it is set where an error is counted, and at each set for a fork that returned `nil` or a solution with a diagnostic, and it propagates from a fork to the solver that made it. T4 does not use A1: a failure that produced no diagnostic still sets the flag.

Rules T1 and T4, and T2 and T3 below, have one thing in common: the fork that is skipped would have repeated, goal step for goal step, a fork that has just run from the same state. The queries to the Typer that are skipped are repetitions, which is why `twins` needs A2′ and not A2.

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

Theorems 1 and 2 are statements about B and C as functions of the solver state, with the Typer's answers held fixed. They say that the *search* returns the same solution. The existing search also runs the forks that the attempt cancels, to the end, and what those forks ask the Typer can change later answers. That part is A2, and it fails (5.5).

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

### 5.5 Assumption A2 is false: what `cleanfirst` and `lookahead` change

Every pruning skips Typer queries that the existing solver makes in branches whose result is discarded, and the look-ahead makes some queries earlier. The first version of this section argued that this was unlikely to matter and reported that no program had been found on which it did. The review found such programs, and the implementation confirms them.

**Mechanism.** The type of a declaration (an alias, the extended type of an extension, the type of a given, the signature of a function) is computed the first time something asks for it, and memoized. While it is computed the declaration is in `declarationsOnStack`; a lookup that meets an extension or a given on the stack skips it, and an alias on the stack is an error ("definition of 'X' refers to itself"), reported at once into the module's diagnostics. So which declaration of a group is *entered first* can decide the verdict (`research/report/soundness/5-declaration-order.md`, `research/followup/design-order/DESIGN.md`). A solver fork enters declarations: `solve(member:)` calls `typer.resolve`, which computes the signature of every member it finds (`typeOfName(referringTo:)`) and the extended type of extensions; `solve(coercion:)` calls `typer.coerced`, whose slow path enumerates the givens in scope. Nothing of this is undone when the fork's solution is discarded.

**The programs.** Each pair differs by one thing that the solver itself does today. Verdicts on binary `eq25-c7cbd846a05c`; "all three" is `twins,cleanfirst,lookahead`.

| Program | What the discarded fork does | base | base + `cleanfirst` | FULL | FULL + `cleanfirst` |
|---|---|---|---|---|---|
| `a01` | looks `m` up in `C`; that enters `extension X` before the alias `X` | accepted | **rejected** | accepted | **rejected** |
| `a02` = `a01`, the two `f` swapped | is cancelled by the existing solver before the lookup | rejected | rejected | rejected | rejected |
| `a03` | looks `m` up in `C`; `C.m` mentions `X`, the alias is entered first | rejected | **accepted** | rejected | **accepted** |
| `a04` = `a03`, the two `f` swapped | is cancelled before the lookup | accepted | accepted | accepted | accepted |
| `a05` (`extension X` does not declare `m`) | as `a01` | accepted | **rejected** | rejected | rejected |
| `a06` = `a05`, the two `f` swapped | is cancelled before the lookup | rejected | rejected | rejected | rejected |

| Program | Order of two queries in the fork of `h -> C` | base, FULL | + `cleanfirst` | + all three |
|---|---|---|---|---|
| `a07`: `two(h(), k().m())` | lookup of `m` in `K` (enters the alias `X`), then the argument that cannot be coerced | rejected | rejected | **accepted** |
| `a08`: `pair(two1(h()), k().m())` | the argument that cannot be coerced (its `coerced` enumerates the givens, which enters `given Foo<X> is P`), then the lookup | accepted | accepted | accepted |

| Program | What the discarded fork does | base, FULL, and `NEW` without the three flags | + `cleanfirst` |
|---|---|---|---|
| `a12`: `type X = Y`, `type Y = X` | looks `m` up in `C`; `C.m` mentions `Y`, which is entered first | rejected, "definition of 'Y' refers to itself" | rejected, "definition of '**X**' refers to itself" |

`a01`, `a03` and `a05` are the alias-and-extension shape (Program 2 of `design-order/DESIGN.md`); they have one consistent reading (`X` is `B`). `a07` is the alias-and-given shape (Program 1); it has no circular definition at all (`X` is `Int`). `a12` is ill-formed in every reading; only the alias that is blamed changes. With `twins` alone every one of the nine has its existing verdict and dump. The in-process self-check reports no violation on any of them, as 4.4 says it cannot.

**What the first version got wrong.** It said that "the first member lookup of a system evaluates the applicability of every visible extension, and the first coercion that needs resolution enumerates every visible given, whatever the types involved", so that skipped queries would be "later queries of the same kinds". Two things are missing. A member lookup also computes the signatures of the members it finds, and those depend on the type looked into, which depends on the candidate (`C.m` in `a01` and `a03`). And with `extorder`, which is in FIX and FULL, a lookup only evaluates the extensions that declare the name (`if (TyperExperiments.extorder || TyperExperiments.sigrounds) && !declaresName { continue }`), so what is entered depends on the name as well.

**Which programs are exposed.** A program can change only if, under the existing search, a fork that has already counted an error computes a signature for the first time or makes the Typer report a diagnostic (for `lookahead`: or if a scan does), *and* the verdict depends on which declaration of some group is entered first. The second condition is the known dependence on declaration order: 52 of 129 programs written for it under base, 7 under FULL. Nothing is known about how often the first condition holds; the counters of 4.5 measure it. Code without such groups of declarations is not exposed: the compiler tests and the workloads show no difference (section 9.2).

**`twins` is not exposed.** It skips a fork only when that fork would repeat a fork that has just run from the same state, goal step for goal step (5.2). Every signature that the repetition would enter has been entered by the original, in the same order.

**With `sigrounds`.** The signatures of extensions and givens are then computed before any statement is checked, in rounds, from a table, so a lookup no longer enters them. In the configuration `NEW` of `BRIEF2.md` without the three flags, `a01` to `a08` are all accepted, and they are accepted with the same dump when the three flags are added (binary `eq25`). The 129 programs written for declaration order and the 42 of `design-order/tests` show no difference either, under FULL or under that configuration; few of them contain an overloaded call, so this says little. What `sigrounds` does not settle is aliases: in `a12` the diagnostic still depends on which alias a discarded fork enters. No program was found whose *verdict* changes with `sigrounds` on; none is excluded by an argument.

**No cheap guard.** An exact guard would have to know what the cancelled tails would have asked, which is the work that is being saved. Running the tails for their side effects only is the existing search. Entering every declaration of the module before the first statement is checked would make the solver's queries harmless, but it changes the order in which declarations are entered for every program, and with it the verdict of programs like `a01` to `a08`: that is the subject of `design-order`, not of this design.

**Consequences.**

- `cleanfirst` and `lookahead` must not be described as result-preserving relative to base or FULL, and must not be in a configuration that is.
- Where the verdict does not depend on the order in which declarations are entered, they are exact. That is a property of the configuration (`sigrounds`), to be established there (R5 and R6 of section 7), or a decision of the language designers (question 8).
- Fresh type variables are numbered differently when forks are skipped, and fewer types are interned. Stored types replace leftover variables by errors, and diagnostics print reified types, so this is invisible in types and messages. It is visible in the dump only in the raw identities that references to builtin functions print (section 6).

### 5.6 Evidence from the model

`scripts/model.py` implements section 2 and section 4 over abstract goals (overload sets, and checks whose outcome is a function of the types chosen, with counted and uncounted failures, shared diagnostics, twins, sets created dynamically, and an arbitrary, possibly intransitive preference).

- On 200,000 random systems (4 seeds), six combinations of the flags return exactly the baseline's solution: 0 differences in 1,200,000 comparisons (`results/model-fuzz.jsonl`). Of these systems 47% are clean and 53% are not; 40% take the fallback.
- Six deliberately wrong variants, each removing one clause of the argument above, are all detected (`results/model-mutants.jsonl`): no erase rule (825 of 30,000 systems differ), trusting an attempt without a clean candidate (2,442), look-ahead counting uncounted failures (51), look-ahead under `best > 0` (1,944), T3 without the purity test (32), T1 without the bound test (154).
- The random systems are not exhaustive: they did not find the flaw of the "start with `best == 0`" shortcut of section 3 in 30,000 systems; a hand-made system shows it. The argument for the design is the proof of 5.3; the fuzzer only failed to refute it.
- The model's baseline agrees with the binary on forks, overload sets and number of diagnostics for 18 of the test programs, the delicate ones included (`results/model-vs-binary.jsonl`).

- Added in review: rule T4 is in the model (`spotless=True`, the default with `twins`). On 270,000 further random systems, seven combinations of the flags return the baseline's solution, 0 differences (`results/review-model-fuzz.jsonl`). A variant of T4 that ignores solutions with diagnostics when it decides that an exploration is spotless is detected, though rarely: 3 systems of 30,000 (`results/review-model-mutants.jsonl`).

The model does not contain unification, so it says nothing about F1 to A4 themselves or about the Lemma's reading of `solve(call:)` and `solve(coercion:)`. Those are covered by the assertions and by `selfcheck`. The model does not contain the Typer either: it cannot show the failure of A2.

### 5.7 Evidence from the implementation

Commit `9dc04d7` implements sections 4.0 to 4.4 as first written (rules T1 to T3, without T4, without the assertion A1, and without the removal of the old experiment and the change to the dump). The review compared it with the existing search on binary `exp/bin/eq25-c7cbd846a05c` (`scripts/review_impl.py`; raw results in `results/review-impl-*.jsonl`). The numbers are in section 9.2.

## 6. Test plan

`tests/` holds 46 programs. Each starts with the expected outcome after the change, the reason, and the current outcome on the binary under base and FULL. `scripts/make_tests.py` wrote the first 34 (`--check` re-runs the binary and compares); `scripts/review_tests.py` wrote the twelve of the review (`a01` to `a12`). `scripts/review_check.py` runs every file of `tests/` as it is on disk and compares with its comments: all 92 recorded outcomes are those of binary `eq9-723cc0e6b0f8`.

| Group | Programs | Expectation |
|---|---|---|
| `s01`–`s08` | the three workloads, their variants, `+` chain, method chain, mixed operators | same dump as today; `solver.forks` at most the bound in the comment (from the model) |
| `s09` | independent clean sets | unchanged, 126 forks; documents what is not fixed |
| `e01`–`e08` | erroneous systems | same diagnostics, character for character, including the ambiguities that depend on search order; fork bounds in the comments |
| `m01`–`m17` | programs whose meaning depends on pop order, candidate order, the inherited `best`, or ranking; the counterexamples to the earlier attempt; `overload-priority.hylo` | same dump as today |
| `a01`–`a08`, `a12` | programs whose verdict, or whose diagnostic (`a12`), depends on a Typer query made in a fork whose result is discarded (`a01` to `a08` are pairs: the program, and the same program with the query removed or moved by a change that the solver itself makes today) | same dump as today with `twins`; **`a01`, `a03`, `a05` (base) change verdict with `cleanfirst`, `a07` with `lookahead`, and `a12` changes one diagnostic with `cleanfirst`**: these are the known differences of section 5.5, not regressions to hunt |
| `a09`–`a11` | twins separated by another candidate, a spotless twin, twins around overloaded calls with failing candidates | same dump as today; fork bounds in the comments |

Tests aimed at one clause each: `m06` (erase rule), `m07` (purity test of T3, and the "every solution is clean" clause of T4), `a09` (T1 needs the same bound, T4 an exploration without failure), `a10` (T4 fires; the binding must be the existing one), `m04`/`m05` (solutions worse than `best` stay viable), `e01`/`e02` (no result is taken from an attempt without a clean candidate), `m14` (the look-ahead asks `coerced` rather than comparing identities), `s03` (no extra forks when the existing search is already linear), `e08`/`m08`/`m13` (pop order untouched).

Procedure for each flag, alone and with the flags before it in the order `twins`, `cleanfirst`, `lookahead`:

1. Dump comparison against base (`tc-bench --dump`) on: `tests/`, `research/review/solver/*.hylo` and its `verify-S*` directories, the 216 corpus files, the test programs under `research/report/test-programs/` (declaration-order and cycles included, because of A2), and the declaration-order fuzzer of `research/followup/permute.py` on `tests/`. Zero differences with `twins`; with `cleanfirst` and `lookahead`, no difference other than those of `a01`, `a03`, `a05`, `a07` and `a12`, and every other difference must be explained by 5.5 before it is accepted. Compare the dumps after masking two things that are not part of the result. A reference to a builtin function prints the raw identity of a machine type (`erased: 8800`), which shifts when fewer types are interned: under base, the dump of the standard library differs in 330 such lines with `twins` and in nothing else. And in an ill-typed program a type variable that was never assigned is printed with its number (`apply<A, %2v4>` against `apply<A, %2v3>` in `research/review/solver/t04_closure.hylo`), which shifts when forks are skipped. `scripts/review_impl.py` masks both. **Before trusting `twins`**, make the dump print which declaration a name is bound to: today it prints only the name (`0:8 -> infix+`), so it cannot tell the two candidates of `+` apart, and a wrong `rebinding` would pass unnoticed.
2. Counters: the bounds in the test comments; on the standard library, `solver.goalSteps` not above today's 9,484. On every program that base accepts, `solver.cleanfirstFallbacks` must be 0: by Theorem 1b a fallback means that the existing result has a diagnostic.
3. `selfcheck` on all of the above: no `[selfcheck] VIOLATION` line (commit `9dc04d7` prints one per violation and counts the confirmed systems in `selfcheck.overload.confirmed`).
4. Debug build: none of the assertions A1, A5, A6, A7 fires.
5. Timing with the interleaved method of the plan (0.3) on the standard library (expected: no measurable change) and on `s01`, `s04`, `s06`.

If the algorithm of section 4 is changed during implementation, change `scripts/model.py` in the same way and re-run `model.py fuzz` and `mutants.py` before building: the model is where a mistake in the bookkeeping of `viable` and `best` shows first.

## 7. Implementation order

### 7.1 What exists

Commit `9dc04d7` of hylo-impl contains the three flags in one change: `twins` with rules T1 to T3, `cleanfirst`, `lookahead`, and a self-check that compares diagnostics and bindings. It does not contain step 0 (the old `solver` experiment is still there and the dump is unchanged), the assertion A1, or rule T4. Measured on binary `eq25-c7cbd846a05c` (section 9.2): the fork counts are those the model predicted, and the dumps are those of the existing search on every test except the five programs of 5.5 (`a01`, `a03`, `a05`, `a07`, `a12`).

### 7.2 Remaining steps

Each step builds and is testable alone. Line counts are estimates of added lines.

| Step | Change | Lines | Expected result | Stop if |
|---|---|---:|---|---|
| R1 | Remove `cleanfirst` and `lookahead` from the configuration `NEW` in `research/followup/tcrun.py`; keep `twins`. A configuration that is described as result-preserving must not contain a flag that changes `a01`. Replace "(result-preserving)" in the comments of these two flags in `TyperCounters.swift` and in the message of commit `9dc04d7`'s successor by the wording of 4.0. | 5 | `NEW` gives the verdicts of `NEW` without the three flags on `tests/a*` | – |
| R2 | Rule T4: field `blemished`, `Explored.spotless`, the first line of `twin(of:in:)`, the line where errors are counted (4.1). | 15 | with `twins` alone: `s06` 65 → 10 forks, `s07` 27 → 6, `s08` 44 → 8, `a10` 3 → 2, `a09` and `a11` unchanged (3 and 84); every dump identical to base | a dump difference with `twins` alone. That would refute A2′, and `twins` would have to go too. |
| R3 | Assertion A1 in `formSolution` (4.2); run a debug build on `tests/` and on `research/followup/headsubst/tests` with `headsubst`. | 3 | no assertion fires | it fires: attach the equalities of `resolve(_:elaboratedBy:at:)` to the coercion goal, or skip the attempt under `headsubst`. |
| R4 | `semanticDump` prints, for each binding, the kind of reference and the site of the declaration. Re-run the dump comparison of section 6 with `twins`. | 10 | identical dumps; in `a10`, `s06`, `s07` the declaration bound is the existing one | a binding differs: `rebinding` or the order of `viable` is wrong. |
| R5 | Exposure counters of 4.5. Run the standard library, the 192 compiler tests, the workloads and the test programs under base, FULL and `NEW` without the three flags. | 25 | `solver.forcedAfterError` is 0 everywhere except `a01`, `a03`, `a05`, `a12` and programs already known to depend on declaration order | it is positive in ordinary code: `cleanfirst` changes ordinary programs and cannot be on by default in that configuration. |
| R6 | Decide where `cleanfirst` and `lookahead` may be on (5.5, question 8 of section 8). The review's proposal: only together with `sigrounds`, after R5 has been run under that configuration, and never as part of a configuration called result-preserving relative to base or FULL. | – | – | – |
| R7 | Delete the old `solver` experiment (`parked`, `probing`, `probeFinished`, `resolveParked`, `probe`, the `deferring` branches). | −95 | counters unchanged | – |
| R8 (optional) | In the exact search with `0 < best < .worst`, cancel at an overload constraint when `current.errors` plus the *number* of certain failures exceeds `best.errors`. Sound by the same Lemma, for any `best`; same exposure to A2 as `lookahead`. | 20 | `e03`: 308 → 56 in the model; `e04`: no gain | no erroneous workload of interest improves; the model says this is likely. |

Measured effect on the three workloads with all three flags (binary `eq25`, section 9.2): `ovl-4-8` 3,184 → 32 forks; `ovr-3-8` 9,840 → 24 forks and 22 scans; `ovl-ret-9` 349,524 → 36 forks. With `twins` alone these three are unchanged; the `+` chain of ten operators goes from 2,046 forks to 65, and to 10 once T4 is in.

Order rationale: `twins` fixes the only exponential seen in ordinary code, and it is the only one of the three whose result does not depend on the Typer's order of evaluation. R2 to R4 complete it. `cleanfirst` and `lookahead` fix workloads that were written to be hard (several overloaded calls with distinct types in one statement); they wait for R5 and R6.

## 8. Open questions for the language designers

1. **Is the nested ranking intended?** Only the outermost overload set is ranked across combinations; inner sets are ranked inside each outer choice (`m01`, `m10`, `m11`: swapping two arguments changes the selected overloads, or turns an accepted program into an ambiguity). A symmetric rule would make component-wise solving possible and would change these programs.
2. **Is a solution with more diagnostics than the best one meant to stay viable?** The `else { viable.append(…) }` branch lets a preferred candidate with a nested ambiguity or an error win over a clean one (`m04`, `m05`), makes acceptance depend on the order of the search (`m06` accepted, `m07` rejected), and produces ambiguity errors in erroneous systems that depend on declaration order (`e01` against `e02`; `e04`: six diagnostics for one bad argument). If the intended rule is "among the solutions with the fewest diagnostics, the preferred one", the solver becomes simpler, erroneous systems no longer need the exact fallback, and these programs change.
3. **Should a member and the trait requirement it implements be two candidates?** For a concrete receiver they denote the same function. If name resolution kept one, the exponential of P1 would disappear at its source and `twins` would be unnecessary for it. Which one is bound affects the elaboration (direct call or call through the witness).
4. **Should errors be counted the way diagnostics are?** Failures that are not counted in `current.errors` (stale constraints, a coercion that cannot be simplified) are the other source of the behaviours in question 2.
5. **Are the diagnostics of an erroneous system part of the contract?** If an implementation may report a different, smaller set of errors for an ill-typed statement, the erroneous case can be made fast as well. Today it must reproduce diagnostics such as those of `e04`.
6. **For an ambiguous use, is "continue with the candidate declared first" the intended recovery** (`m02`, `m03`)?
7. **Are declarations whose types depend on each other through extensions and givens legal?** If not, assumption A2 holds by construction, and with it the last unprovable step of this design.
8. **Which verdict is right for `tests/a01` and `tests/a07`?** Today `a01` is accepted and `a02`, which differs in the order of two overloads of an unrelated function, is rejected; `a07`, which has no circular definition, is rejected, and `a08`, which states the same call in another way, is accepted. `cleanfirst` and `lookahead` move `a01`, `a03` and `a07` to the verdict of their twin. If the intended semantics is the order-independent one (`sigrounds` accepts all eight), these changes are harmless and the two flags can be used with it, up to the diagnostic of `a12`. If the verdicts of base are to be kept exactly, the two flags cannot be used.

## 9. Review

An adversarial review of the first version of this document, made after it was written and, as it turned out, while it was being implemented. The reviewer could not build; from the middle of the review on, a binary containing the implementation (`exp/bin/eq25-c7cbd846a05c`, hylo-impl commit `9dc04d7`) was available and was used. Scripts: `scripts/review_check.py`, `scripts/review_tests.py`, `scripts/review_impl.py`; raw results: `results/review-*.jsonl`.

### 9.1 The account of the existing code

Checked against `Solver.swift`, `Typer.swift`, `Solution.swift`, `Constraint.swift`, `TypeStore.swift` and `Sequence+Extensions.swift`. Sections 2.1 to 2.5 are right: the pop order, the forks, the two different counts E and D, the reset-or-append rule, `minimalElements`, the unused `penalties`. The anchors quoted in section 4 are the code. The 68 verdicts and counters recorded in the 34 tests are those of the binary, and so are the standard library's solver counters (798 systems, 158 sets, 316 forks, 9,484 goal steps).

Errors and omissions found:

1. **Section 5.5 (first version)** rested on a wrong reading of member lookup: it computes the signature of the members it finds, not only the applicability of extensions, and with `extorder` it evaluates only the extensions that declare the name. The conclusion drawn from it, that pruning could only skip "later queries of the same kinds", is false. This is the main finding (9.3).
2. **A1 under `headsubst`.** `resolve(_:elaboratedBy:at:)` schedules equalities that belong to no goal (`_ = schedule(...)`), so a failure there is counted without a diagnostic. Not exercised by any program found; the assertion that would detect it is missing from the implementation.
3. **Option (a), wording.** The Typer's comment is about the result of a call, not about the callee; corrected.
4. **The Lemma's "closed".** Correct, but for a reason the text did not give: `reify` returns a type without `hasVariable` unchanged. Without `arrowenv` an arrow with a variable in its environment counts as closed for both, so the look-ahead and the leaf still see the same goal. Stated in 4.3 so that nobody "improves" the test.
5. **The dump** is not free of raw identities: references to builtin functions print `erased: <number>` (under base, the dump of the standard library differs in 330 lines with `twins`, all of this kind), and leftover type variables print their number. Both must be masked before dumps are compared (section 6).
6. **The risk "the two candidates of `+` may not have the same type identity"** is settled: with `twins`, `solver.twinsReused` is 45 on the chain of ten operators.

### 9.2 The implementation against the existing search

`scripts/review_impl.py` compares, for each program, the run under a reference configuration with the run under the same configuration plus flags: exit code, messages in order, and the dump after the masking of section 6.

| Programs | Reference | `twins` | `twins,cleanfirst` | all three | all three + `selfcheck` |
|---|---|---|---|---|---|
| `tests/` (46) | base | 46 same | 42 same; `a01`, `a03`, `a05`, `a12` differ | 41 same; these and `a07` differ | 0 violations; every system with an overload confirmed |
| `tests/` (46) | FULL | 46 same | 43 same; `a01`, `a03`, `a12` differ | 42 same; these and `a07` differ | 0 violations |
| `tests/` (46) | `NEW` without the three flags | 46 same | – | 45 same; `a12` differs (one diagnostic) | – |
| `research/review/solver` (54), the compiler's tests and packages (204), `design-order/tests` (42), `report/test-programs/declaration-order` (129) | FULL | 429 same | – | 429 same | – |
| `headsubst/tests` (13), `design-order/tests` (42), `declaration-order` (129) | `NEW` without the three flags | 184 same | – | 184 same | – |

Fork counts of the implementation (base; FULL is identical), next to the model's:

| Program | Today | `twins` | `twins,cleanfirst` | all three | Model |
|---|---:|---:|---:|---:|---|
| `s01` (`ovl-4-8`) | 3,184 | 3,184 | 32 | 32 | same |
| `s02` | 1,932 | 1,932 | 24 | 24 | same |
| `s04` (`ovr-3-8`) | 9,840 | 9,840 | 9,840 | 24 | same |
| `s05` (`ovl-ret-9`) | 349,524 | 349,524 | 349,524 | 36 | same |
| `s06` (`+` × 10) | 2,046 | 65 | 10 | 10 | same; 10 with `twins` alone once T4 is in |
| `s07`, `s08` | 126, 510 | 27, 44 | 6, 8 | 6, 8 | same; 6, 8 with T4 |
| `a11` | 136 | 84 | 12 | 12 | same |
| `e03` | 280 | 280 | 308 | 308 | same |
| `e04` | 3,279 | 3,279 | 6,558 | 3,300 | same |
| `m07` | 10 | 9 | 8 | 8 | same |
| `e01`, `e02` | 6 | 6 | 12 | 10 | 6 with all three: the model's encoding of these two makes the bad argument visible to the first scan, the program does not |

The standard library, under base: today 158 visited sets, 316 forks, 9,484 goal steps; with `twins` 155 sets, 288 forks, 22 reuses, 9,211 goal steps; with `twins,cleanfirst` 133 sets, 133 forks, 133 reuses, 7,644 goal steps (114 attempts, no fallback). So every overload set of the standard library is a pair of candidates of the same type, and T1 alone reuses few of them, because a set that is not nested explores its first candidate under `.worst` and its second under `.zero`. This is the case T4 is for; with it `twins` alone should reach the 133 forks.

The search logic of the design is confirmed: wherever the Typer's answers are the same, the implementation returns the existing solution, on the programs built to break it (`m04` to `m07`, `e01` to `e08`) as on the others.

### 9.3 Attacks

| Attack | Programs | Outcome |
|---|---|---|
| A query made in a fork that `cleanfirst` cancels decides which declaration is entered first | `a01`/`a02`, `a03`/`a04` (base and FULL), `a05`/`a06` (base) | **Not withstood by `cleanfirst`.** Predicted from the pairs on the old binary, then observed on the implementation: `a01` accepted → rejected, `a03` rejected → accepted. Withstood by `twins`. Withstood with `sigrounds`. |
| The look-ahead asks `coerced` before a lookup that the existing search makes first | `a07`/`a08` (base and FULL) | **Not withstood by `lookahead`**: `a07` rejected → accepted; it has no circular definition. Withstood by `twins` and by `cleanfirst` alone. Withstood with `sigrounds`. |
| The same with a true cycle of aliases, to see what `sigrounds` leaves | `a12` (base, FULL, and with `sigrounds`) | **Not withstood by `cleanfirst`, in any configuration**: the program stays rejected, the alias named in the diagnostic changes from `Y` to `X`. Withstood by `twins`. |
| In-process self-check as evidence of result preservation | `a01`, `a03`, `a07` | The self-check confirms these systems although the verdict changes: it validates the search, not the program. As the design said; now shown. |
| Twins separated by a clean candidate, so that the bound changes between them | `a09` | Withstood: 3 forks, no reuse with `twins` alone. |
| A twin reused although something below it depended on the bound | `m07` (two ambiguities must remain), model mutants `twins-any-bound`, `twins-no-purity`, `spotless-errors-only` | Withstood by T1 to T3 on the implementation and by T4 in the model. |
| Reuse binds the name to the wrong declaration | `a10`, `s06`, `s07` | Not observable in the dump, which prints only the name. The self-check compares bindings and reports no violation. Step R4 makes it observable. |
| "Closed" operands that are not closed (arrow environments without `arrowenv`) | – | Withstood, by the reading in 9.1 (4); no program. |
| A counted failure without diagnostic (A1) | – | Not exercised. `headsubst` can produce one in principle (9.1 (2)); the tests pass in the configuration with `headsubst`. Assertion required (R3). |
| Ill-typed statements: cost of the failed attempt | `e03`, `e04`, `e05` to `e08` | As designed: same diagnostics, up to twice the forks with `cleanfirst` alone. |
| Loops, unbounded work | – | None: the attempt visits only states that the existing search visits, once; the fallback is the existing search. |

### 9.4 What the review changed in this document

- The header, the summary table, sections 2.6, 3 and 5.1 no longer claim that `cleanfirst` and `lookahead` preserve results. Section 5.5 is rewritten around the counterexamples.
- Rule T4 is added to `twins` (4.0, 4.1, Theorem 0 in 5.2, model, mutant, fuzz). With it, `twins` alone makes operator chains linear, so the realistic case no longer needs `cleanfirst`. T4 is not in the implementation; it has been run in the model only.
- Section 4.5 adds two counters that measure, in the existing search, how many programs are exposed to the failure of A2.
- Sections 4.2 to 4.4: the missing assertion A1 and the `headsubst` case, the definition of "closed", two remarks on the self-check as implemented.
- Section 6: twelve programs added (`a01` to `a12`), the masking of raw identities in dumps, the known differences.
- Section 7 is rewritten as the steps that remain after commit `9dc04d7`.
- Section 8: question 8.
- `scripts/model.py` and `scripts/mutants.py` contain T4 and its mutant; the earlier fuzz results are unchanged by it (the six earlier combinations are still run, with T4 on wherever `twins` is; 0 differences).

### 9.5 Recommendation

**Implement only the first step: keep `twins`, complete it with rule T4, and take `cleanfirst` and `lookahead` out of every configuration that is meant to preserve results.**

Reasons:

- `twins` is the part that matters for code as it is written today. Every overload set of the standard library is a pair of twins (9.2), and the only exponential found in ordinary code is the operator chain. `twins` removes it, it is exact by an argument that needs nothing from the Typer beyond the harmlessness of an immediate repetition, and the implementation agrees with the existing search on every program compared. With T4 the chain is linear without the other two flags.
- `cleanfirst` and `lookahead` change the verdict of programs under base and FULL, in both directions, and one of the programs has no circular definition. The programs were constructed for the purpose; none of the 429 existing programs compared changes. The task was a speed-up that provably returns the same diagnostics; these two do not, and no local fix exists (5.5). What they speed up are the three workloads written to be hard, not a shape seen in existing code.
- They are not wrong as search algorithms, and with `sigrounds` every verdict compared is stable (the 46 tests and 184 other programs); what remains there is the wording of the diagnostic for a true cycle of aliases (`a12`). If the project adopts the order-independent configuration, enabling them there is reasonable after R5 has been run under it and if a diagnostic that names another member of the same cycle is acceptable (question 5). That is a second decision, to be taken with the exposure counters in hand and with the answers to questions 5 and 8, not as part of this change.
