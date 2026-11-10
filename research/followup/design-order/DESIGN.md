# Order independence by construction: signatures computed in rounds

This document is for the engineer who will implement the change in `/home/user/hylo-impl/Sources/FrontEnd`. It states the problem with programs checked on the binary, compares three designs, specifies the chosen one down to the statements to change, gives the argument for its correctness with the assumptions it rests on, and lists tests and implementation steps.

Every verdict quoted here was obtained with `research/exp/bin/eq9-723cc0e6b0f8/tc-bench`. Section 8 says how to reproduce each number. Nothing in this document was validated by building the compiler: the design was checked on an executable model (`scripts/model.py`) that reproduces the binary's verdicts on the test programs (section 5.3), and that is weaker evidence than an implementation.

## Summary

- The verdict depends on declaration order for three reasons that act together: a lookup or resolution *computes* the signature of every candidate it meets, inside the computation that asked; a candidate whose signature is being computed is *skipped*; and whatever is computed meanwhile is *memoized*. Which edge of a dependency cycle gets skipped depends on where evaluation entered the cycle.
- The same mechanism rejects ordinary programs that have no cycle at all. Program 4 below is rejected in every order tried, 24 by the existing checker and 120 by FULL. The fuzzer cannot see such programs, because their verdict does not vary.
- Chosen design, option (c) as a fixed point over a table: the signatures of extensions and givens are computed in *rounds*. During a round, every lookup and resolution reads these signatures from the table that the previous round produced, and from nowhere else. A round starts from the untouched typing state of the module. Rounds repeat until the table is stable. The table after round `k` is a function of the program and of `k`, so nothing can depend on the order in which declarations are entered.
- It removes `givencheck` and the cycle rule of `extorder`, including `mayMatch`, and makes `memberskip` unnecessary: about 150 lines are added for the mechanism (200 with counters and assertions) and about 260 can be deleted afterwards. In code without such dependencies, which is all the code available today, one round is run and nothing is restored.
- It accepts more programs than FULL: all seven failing programs become accepted in every order, as do the programs that the conservative cycle rule rejects although they have one consistent reading. Whether that is wanted is the first question for the language designers (section 7).

## 1. The problem

### 1.1 Mechanism

The type of an alias, the extended type of an extension and the type of a given are computed on demand (`declaredType(of:)`, `extendeeType`). I call these types *signatures*. While a signature is computed, its declaration is in `declarationsOnStack`. Three things then happen.

1. **Forcing.** A member lookup calls `applies(e, to:in:)` for extensions `e`, which calls `extendeeType(e)`. An implicit resolution calls `expression(referringTo: g)` for every visible given `g`, which calls `declaredType(of: g)`. A signature that is not yet known is computed there and then, nested inside the computation that made the lookup.
2. **Skipping.** An extension or given that is on the stack is skipped: `if declarationsOnStack.contains(.init(e)) { … continue }` in the extension loop, `filter(notOnStack(_:))` in `givens(visibleFrom:)`. An alias on the stack cannot be skipped, since its value is needed, so it is an error ("refers to itself").
3. **Memoizing.** Every signature computed meanwhile is stored with `setType` and never recomputed, including those computed while something was skipped.

A dependency cycle that contains at least one lookup or resolution can be cut at that point (by skipping) or at another one (by an error, or by another skip), depending on which declaration of the cycle is entered first. `extorder` and `givencheck` check afterwards whether a skip was harmless, but only the skip that the order of evaluation happened to produce.

### 1.2 Program 1: an alias used by a given (no cycle)

```hylo
trait P { type E }
struct A {}
struct Foo<T> {}
given A is P { type E = Int }
type X = A.E                          // (1)
given Foo<X> is P { type E = Bool }   // (2)
```

| Order | base | FULL | Counters of the user module (FULL) |
|---|---|---|---|
| (1) before (2) (`problem/p1-alias-first.hylo`) | rejected: "definition of 'X' refers to itself" | rejected, same error | `summon.subgoals=1 summon.matches=72 index.unavailable=19` |
| (2) before (1) (`problem/p1-given-first.hylo`) | accepted | accepted | `summon.subgoals=1 summon.matches=71 index.unavailable=68`; no `givencheck.reported` |

With a use `fun f(x: X) {}` added (`tests/01`), base and FULL each accept 8 of the 24 orders of the last four declarations.

- Rejecting order: `X` is entered. `A.E` needs a resolution of `P<A>`. The resolution asks for the type of every given, so it computes the type of (2), which mentions `X`, which is on the stack: error. Given (2) could never match `P<A>`, but its type had to be computed to find that out.
- Accepting order: (2) is entered first and is hidden while `X` is computed. `givencheck` records the skip and finds afterwards that `P<Foo<X>>` cannot match `P<A>`.

### 1.3 Program 2: an alias and an extension of that alias

```hylo
struct A {}
struct B {}
extension A { type Me = B }
type X = A.Me                   // (1)
extension X { type Me = Int }   // (2)
```

| Order | base | FULL | Counters (FULL) |
|---|---|---|---|
| (1) before (2) (`problem/p2-alias-first.hylo`) | rejected: "definition of 'X' refers to itself" | rejected, same error | `names.appliesCalls=2` |
| (2) before (1) (`problem/p2-extension-first.hylo`) | accepted | accepted | `extorder.cycles=1 names.appliesCalls=1` |

- Rejecting order: `X` is entered. The lookup of `Me` in `A` reaches (2), which declares `Me`, and computes its extended type `X`: on the stack, error. The extension's extended type is memoized as an error.
- Accepting order: (2) is entered, computes `X`, and the lookup of `Me` in `A` skips (2). The cycle rule then finds that (2) extends `B` and cannot apply to `A`.

### 1.4 Program 3: a given and an extension

```hylo
trait P {}
struct A { struct Inner {} }
extension <T where T is P> T { type Inner = Bool }
given A.Inner.Foo is P {}              // (1)
extension A.Inner { type Foo = Int }   // (2)
```

| Order | base | FULL | Counters (FULL) |
|---|---|---|---|
| (1) before (2) (`problem/p3-given-first.hylo`) | accepted | accepted | `names.appliesCalls=3 summon.subgoals=2 index.unavailable=136` |
| (2) before (1) (`problem/p3-extension-first.hylo`) | rejected: "type 'Inner' has no static member 'Foo'" | rejected: that error and "circular extension: … lookup of 'Foo' …" | `extorder.cycles=1 names.appliesCalls=2 summon.subgoals=2 index.unavailable=87` |

The program has one consistent reading: `A.Inner` is the struct, `Foo` is `Int`, (1) is `Int is P`, and `A` is not a `P`. The true dependencies are acyclic: (1) needs (2), and (2) needs nothing.

- Accepting order: (1) is entered. The lookup of `Foo` computes (2). Computing (2) asks whether `A is P`, which skips (1). The skip is harmless.
- Rejecting order: (2) is entered. It asks whether `A is P`, which computes (1). Computing (1) looks up `Foo` and skips (2), which it needs. The type of (1) is memoized as an error.

Both orders cut the cycle; one cuts an edge that does not matter and the other cuts the one that does. Checking the skip afterwards turns the second case into an error. It cannot turn it into the right answer.

### 1.5 Program 4: a chain that no order accepts

```hylo
trait P { type E }
trait Q { type F }
struct A {}
struct Foo<T> {}
struct Bar<T> {}
given A is P { type E = Int }
type X = A.E
given Foo<X> is Q { type F = Bool }
type Y = Foo<X>.F
given Bar<Y> is P { type E = A }
fun g(y: Y) {}
```

base rejects it in all 24 orders tried and FULL in all 120 orders tried of the last six declarations (`problem/p4-chain.hylo`, `tests/06`). In the source order FULL reports "definition of 'X' refers to itself" with `summon.subgoals=2 summon.matches=145 index.unavailable=89`.

The dependencies form a chain without any cycle. But resolving `P<A>` for `X` computes the type of `Bar<Y> is P`, which computes `Y`, which needs `X` or the given `Foo<X> is Q`, one of which is always on the stack. This is the strongest argument against repairing the current mechanism: order dependence is one symptom of forcing, and wrong rejection in every order is another.

### 1.6 The seven failing programs

Fractions are the accepting orders under FULL (`results/seven-orders.jsonl`; struct and trait declarations kept in place for the first six).

| Program | Accepted | Accepting order: what happens | Rejecting order: what happens |
|---|---|---|---|
| `al1`, `al2`, `al3` | 8 of 24 each | `extension X` is checked before `type X` and `fun f`. Its extendee `X` is computed inside it; the lookup of `Me` in `A` skips `extension X` (on the stack, declares `Me`); `X = B`. The group `{extension X}` is checked: `B` cannot match `A`. | `type X` or `fun f(x: X.Me)` comes first. `X` is on the stack; the lookup of `Me` in `A` calls `applies(extension X, A)`, whose extendee is `X`: "definition of 'X' refers to itself". The extendee is memoized as an error, so `X.Me` has no member `Me`. |
| `v01` | 16 of 24 | `extension X` or `fun h` (whose `x.g()` reaches the extension) is entered before `type X`. As above; the extension extends `Int`. | `type X` is checked first. `A.Foo` reaches `extension X` (declares `Foo`), whose extendee is `X`: error; later `Int` has no member `g`. |
| `n11`, `n12` | 27 and 29 of 60 | The cycle is entered at the given, by `check` of the given or by `fun use(x: Int.Inner)`. `A.Inner.Foo` computes `extension A.Inner`; inside it, the resolution of `P<A>` skips the given. The given is `Int is P`; `givencheck` finds it cannot match `P<A>`. | The cycle is entered at `extension A.Inner`, by its `check` or by `fun early2(i: C.Foo)`, whose lookup of `Foo` in `C` computes every extension declaring `Foo`. The resolution of `P<A>` computes the given; its lookup of `Foo` in `Inner` skips the extension. Error, then "circular extension". |
| `v6` | 16 of 24 | As `n11`: `fun use` or the given comes before the extension. | As `n11`: the extension is first among the three. |

In every case the same cycle is traversed, and the verdict depends on the member at which the traversal starts.

### 1.7 A reading that depends on order without a failing verdict

`tests/09-two-readings.hylo` and `tests/09b-two-readings-swapped.hylo` differ only in the order of two givens declared in a function body. Each given can shadow a top-level given that the other needs, so the program has two consistent readings. base and FULL accept one file and reject the other. Without the last line of the function, `let z: A.E = true`, they accept both files: that line only makes visible that `A.E` is `Bool` in one and `Int` in the other. The fuzzer permutes top-level declarations only and does not see this.

## 2. Options considered

Three properties are needed and I use them to compare the options.

- **P1, order independence**: the verdict is the same for every order of the declarations.
- **P2, consistency**: in an accepted program, no lookup or resolution would give a different answer if the declarations it skipped had been visible.
- **P3, no false cycle**: Programs 1 and 4, which have no cycle, are accepted.

### 2.1 Option (a): a language rule

**(a1) Strict rule.** *While the signature of a declaration is computed, no lookup may meet an extension that declares the name looked up and whose extended type is being computed, and no resolution may meet a given whose type is being computed, other than those hidden by the two existing scoping rules.* The checker reports the event instead of skipping.

- P1 holds by a short argument. If some order of evaluation never meets a declaration that is on the stack, every computation saw complete information, so every other order performs the same computations; a meeting in another order would be a cycle in a dependency graph that the first order showed to be acyclic.
- Cost: about 25 lines changed, and `mayMatch` and both checks can be deleted. No new invariant.
- It fails P3 completely. Programs 1 and 4, `tests/13` and every program of the form "alias defined through a conformance, used in the head of another given" are rejected in every order, because forcing remains. A given whose own where clause contains `T.Element` meets itself and would be rejected unless self-skips are exempted and checked afterwards, which brings `mayMatch` back.
- Programs of the test suite and the standard library that violate it: **none**.
  - The extension half was checked by running: no `extorder.*` counter (and no `givencheck.*` counter) appears for the user module or the standard library in any of the 192 programs of `Tests/CompilerTests` (`results/corpus-counters.jsonl`; one program, `negative/illegal-enum-case.hylo`, crashes this binary).
  - The given half has no counter in the binary, so I checked it by reading. A resolution can only run inside the computation of a given's type if its header, or an alias the header mentions, selects a member through a trait. Of the 107 given and extension headers in the test programs and the hand-written standard library, three contain a qualified name: `extension A.B` in `positive/typealiases.hylo`, `extension A.B : P` in a syntax-error test, and `given Derived.Self is Base`. None resolves a conformance. The standard library bundled with the binary, generated integer types included (19 files, 4,012 lines), has 49 givens, 4 extensions and 4 aliases, none with a qualified name in its header.
- So (a1) changes no verdict in the test suite, and that is all that can be said for it: the test suite does not contain the programs it forbids, and ordinary library code will.

**(a2) The same rule with a static filter.** To satisfy P3, the checker must decide that `Foo<X> is P` cannot match `P<A>` *without* computing `X`. That needs an approximate evaluator of type expressions that never computes another signature (a "skeleton": `Foo<?> is P`), a matcher on skeletons that over-approximates the real matching including coercions, and a resolution loop that consults skeletons before types.

- Cost: about 200 new lines and one new invariant: matching on skeletons over-approximates real matching, coercions included. `mayMatch` and the abstract model already rest on invariants of this kind, and this would be a third statement of it to keep in step with the other two.
- It rejects Programs 2 and 3 and `tests/05` in every order, since a skeleton such as `extension ?` or `? is P` matches everything.

### 2.2 Option (b): one record-and-check mechanism for all kinds

Every skip of any hidden declaration is recorded; cycles are identified as groups; the recorded queries of a group are re-validated when the group is final. I worked out what this needs in order to hold *by construction*, and each simplification I tried has a counter-example.

1. **Checking the skips of the current traversal is not enough.** Program 3 shows it: both orders skip, one skip is exact and the other is not. The verdict must be a property of the final state, so the check must cover every candidate edge inside a group, including edges that this traversal did not cut. The rule becomes: *build the graph whose edges are the hard references and, for every lookup or resolution made by a signature, an edge to every candidate; inside each strongly connected component, every candidate must be irrelevant to every query of a member.* Under that rule one can prove that if one order accepts, every order computes the same signatures and accepts.
2. **Forcing must become a trial that can be abandoned.** In Program 1 the alias-first order hits a hard error inside the forced given. To accept Program 1 in both orders, the forced computation must be abandoned when it reaches something on the stack: no memoization, no diagnostics, and the types it assigned to syntax nodes undone (`setType` asserts that a node is not assigned twice with different types, and in release builds silently keeps the first).
3. **Abandoning needs taint tracking.** A result is final only if nothing in its computation touched a declaration lower on the stack; otherwise it is provisional and must be recomputed. This is the low-link bookkeeping of Tarjan's algorithm applied to the evaluation stack.
4. **`mayMatch` stays**, with its invariant that it over-approximates matching under coercions.

- Cost: taint tracking (about 80 lines), abandonable trials with undo (about 100), the query log, components and validation (about 120), `mayMatch` kept (30): about 330 lines and four invariants (taint is complete; undo is complete; the candidate relation is static; `mayMatch` over-approximates).
- It satisfies P1 and P2, and P3 for Programs 1 and 4.
- It rejects Program 3, `tests/05` and every program in which a needed candidate lies on a potential cycle. The graph is dense, since every given is a candidate of every resolution, so any two givens whose signatures each make a resolution form a group, and a blanket given `given <T where …> => T is P` used by one of them is then an error. That is a new class of false rejections.

### 2.3 Option (c): a fixed point

"Provisional results are not memoized and are recomputed." There are two ways to do it.

**(c1) Fine-grained**: keep on-demand evaluation, tag what was computed under a skip, and recompute it. It needs items 2 and 3 of option (b), and its result depends on which results were provisional, which depends on the order. It satisfies P1 only if the recomputation is driven to a fixed point by a rule that does not mention the stack. Once such a rule exists, the on-demand part contributes nothing.

**(c2) Rounds over a table (chosen).** No candidate is ever forced or skipped by the stack. The signatures of all extensions and givens of the module are computed in a round; lookups and resolutions read them from the table of the previous round; a round starts from the untouched typing state. Iterate until the table is stable.

- P1 holds because the table after each round is a function of the program and the round number (section 4.1). The argument needs no approximation of matching.
- P2 holds at a stable table by definition: every signature was computed with every other signature visible at its final value.
- P3 holds: Program 1 takes 3 rounds and Program 4 takes 4.
- Programs 2 and 3 and `tests/05` are accepted in every order; the contradictions (`tests/07`, `08`, `09`) are rejected in every order because the table never becomes stable.
- Cost: about 150 lines added. `givencheck`, the cycle rule of `extorder` and `mayMatch` become dead (about 170 lines), and so does `memberskip` (about 90), because skipping an extension by name no longer changes what is computed.
- New invariants: section 4.2 lists five, each with an assertion. The essential one is that restoring the typing state of the module is complete.
- Run-time cost: one extra pass over the signatures of extensions and givens for each level of dependency between them, and none when there is no such dependency (section 3.8).

### 2.4 Comparison

| | (a1) strict rule | (a2) rule with skeletons | (b) groups and validation | (c2) rounds |
|---|---|---|---|---|
| P1 by construction | yes | yes, given the skeleton invariant | yes, with the component rule | yes |
| Program 1 (alias used by a given) | rejected | accepted | accepted | accepted |
| Program 4 (chain) | rejected | accepted | accepted | accepted |
| Programs 2, 3; `tests/05` | rejected | rejected | 2 accepted; 3 and 05 rejected | accepted |
| Contradictions (`tests/07`, `08`, `09`) | rejected | rejected | rejected | rejected |
| Lines added / removable | 25 / 60 | 225 / 60 | 330 / 0 | 150 / 260 |
| New invariants | none | skeletons over-approximate matching | four | restore is complete; four smaller ones |
| Needs `mayMatch` | no | a variant of it | yes | no |

I choose (c2). On soundness, (a1), (b) and (c2) all give P1 and P2, and (c2) has the shortest argument with the fewest assumptions about matching. (a1) is simpler still, but it rejects ordinary programs, and it leaves forcing in place, which is the cause of the wrong rejections of section 1.5. If the language designers decide that programs such as Program 3 must be rejected, a rejection rule can be added on top of (c2) as a check on the stable table (section 7, question 1); the reverse is not possible.

## 3. The design

The existing lines quoted as anchors are from `Typer/Typer.swift` at commit `4e7a2aa` of `/home/user/hylo-impl`. Line numbers are not given, because the file is being changed by other work.

### 3.1 Terms

- A **node** is a declaration of the module being typed that is an `ExtensionDeclaration`, a `ConformanceDeclaration`, or a `BindingDeclaration` with `role == .given`. These are the declarations that a member lookup or an implicit resolution can pick as candidates and whose signature is computed on demand. Bindings with `role == .using` (the requirements of a where clause) are not nodes: they are typed by the declaration that owns them, in order, and the two deliberate hiding rules for them are unchanged.
- The **signature** of a node is what `extendeeType` or `declaredType(of:)` returns for it.
- A **soft read** of a node is a read of its signature made to decide whether it applies to a type or matches a goal: in `applies`, in the extension loop of `resolve(_:declaredIn:applyingTo:in:statically:)`, in `givens(visibleFrom:)`, and in `declaredType(of: Given)`. Every other read is a **hard read**: `typeOfSelf(in:)` from the members of the node, `check`, and the round driver.
- The **table** maps each node to its signature in the previous round, and has no entry for a node whose signature contained an error.

Aliases, functions, parameters and usings are not in the table. Their types are still computed on demand and memoized in the module, so they are recomputed in every round, because a round starts from the untouched state.

### 3.2 Algorithm

```
settleSignatures():
  nodes    := all nodes of the module                       (from the syntax, before typing)
  pristine := (typing state of the module, memo cache)      (copy-on-write, O(1))
  table    := {}                                            (every node hidden)
  for round in 1 ... count(nodes) + 2:
      hiddenCandidateSeen := false
      next := {}
      for n in nodes:
          t := signature of n, computed as today            (hard; memoized in the module)
          if t has no error: next[n] := t
      if next == table or (round == 1 and not hiddenCandidateSeen):
          table := next; return                             (stable: keep the state of this round)
      if next was the table of an earlier round, or round == count(nodes) + 2:
          report the nodes whose entries differ between table and next; return
      table := next
      (typing state of the module, memo cache) := pristine  (discard the round)
```

During `settleSignatures`, a soft read of node `n` returns `table[n]`, and the node is ignored if it has no entry; `hiddenCandidateSeen` is set whenever a node is ignored for that reason. Being on `declarationsOnStack` no longer hides a node. After `settleSignatures`, every node has a memoized signature and the existing code runs unchanged: `check` of each top-level declaration, with soft reads answered by the memoized signatures.

The test `round == 1 and not hiddenCandidateSeen` is an exact shortcut: if no lookup or resolution of round 1 had a node among its candidates, the round did not read the table, so round 2 would compute the same thing. I expect this to be the case for all code available today, because no header there selects a member through a trait (section 2.1); step 0 of section 6 measures it.

### 3.3 The flag and the state

In `Typer/TyperCounters.swift`, next to `givencheck`:

```swift
/// SEMANTIC FIX: the signatures of extensions and givens are computed in rounds before anything
/// else; lookups and resolutions read them from the previous round only (replaces `givencheck`
/// and the cycle rule of `extorder`).
nonisolated(unsafe) public static var sigrounds: Bool = enabled.contains("sigrounds")
```

In `Typer`, next to `pendingGivenChecks`:

```swift
/// `true` while `settleSignatures` is running (`sigrounds`).
private var settlingSignatures = false

/// The signatures that the previous round computed for the extensions and givens of `module`;
/// a declaration without an entry is ignored by lookups and resolutions (`sigrounds`).
private var signatureTable: [DeclarationIdentity: AnyTypeIdentity] = [:]

/// `true` iff a lookup or resolution of the current round ignored a declaration because it has
/// no entry in `signatureTable`.
private var hiddenCandidateSeen = false
```

Two helpers:

```swift
/// Returns `true` iff `d` is an extension, a conformance or a given binding of the module being
/// typed, i.e., a declaration that lookups and resolutions select by its signature.
private func isSignatureNode(_ d: DeclarationIdentity) -> Bool {
  if d.module != module { return false }
  switch program.tag(of: d) {
  case ExtensionDeclaration.self, ConformanceDeclaration.self:
    return true
  case BindingDeclaration.self:
    return program[castUnchecked(d, to: BindingDeclaration.self)].role == .given
  default:
    return false
  }
}

/// Returns the signature of `d` computed now, memoized in the module.
private mutating func computedSignature(of d: DeclarationIdentity) -> AnyTypeIdentity {
  if let e = program.cast(d, to: ExtensionDeclaration.self) { return extendeeType(e) }
  return declaredType(of: d)
}
```

### 3.4 The driver

In `apply()`, the existing lines are

```swift
    for d in program[module].topLevelDeclarations { check(d) }
    if TyperExperiments.givencheck { checkPendingGivens() }
```

Insert `if TyperExperiments.sigrounds { settleSignatures() }` before the loop.

```swift
private mutating func settleSignatures() {
  let nodes = program[module].syntax
    .compactMap({ (n) in program.castToDeclaration(n) }).filter(isSignatureNode(_:))
  if nodes.isEmpty { return }

  let pristine = (program[module], cache)
  settlingSignatures = true
  defer { settlingSignatures = false }
  signatureTable = [:]
  var earlier: [[DeclarationIdentity: AnyTypeIdentity]] = []

  for round in 1 ... (nodes.count + 2) {
    hiddenCandidateSeen = false
    var next: [DeclarationIdentity: AnyTypeIdentity] = [:]
    for n in nodes {
      let t = computedSignature(of: n)
      if !t[.hasError] { next[n] = t }
    }
    TyperCounters.bump("sigrounds.rounds")

    if (next == signatureTable) || ((round == 1) && !hiddenCandidateSeen) {
      signatureTable = next
      return
    }
    if earlier.contains(next) || (round == nodes.count + 2) {
      reportUnstableSignatures(nodes, signatureTable, next)
      signatureTable = next
      return
    }
    earlier.append(signatureTable)
    signatureTable = next
    (program[module], cache) = pristine
    reportedBudgetScopes = []
  }
}
```

Notes for the implementer.

- `program[module]` is the whole `Module` value: syntax, types of nodes, name bindings, witness tables and diagnostics of every source file (`Module.SourceContainer`). Assigning it back discards everything the round wrote, including syntax replaced by elaboration and diagnostics. `Program.subscript(m: Module.ID)` has `get` and `_modify`, so both the copy and the assignment compile.
- `program.types` (the type store) is deliberately *not* restored: the table holds type identities that must stay valid. The store only grows; types created by a discarded round are unreachable garbage.
- `cache` must be restored: `scopeToSummoned`, `scopeToExtensionApplies`, `scopeToTypeOfSelf`, `witnessToAliases` and the coercion caches hold answers computed from the previous table.
- Typer fields that record what was reported must be reset with the state: `reportedBudgetScopes` today. If `sigrounds` is ever run together with `extorder` or `givencheck` during the transition, also `reportedCircularExtensions`, `reportedCircularGivens`, `extensionFrames`, `cycleGroups` and `pendingGivenChecks`; step 2 of section 6 switches those mechanisms off instead (section 3.7).
- `pristine` goes out of scope when the function returns, so the copy-on-write cost is paid for buffers mutated during this function only.
- `earlier` detects a table that repeats with a period longer than one, which cannot converge. It holds at most `nodes.count + 2` tables.
- `reportUnstableSignatures` reports, at each node whose entries differ in the two tables, one error: "the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found". The set of nodes reported is a function of the two tables.

### 3.5 Soft reads

**Extension loop.** In `resolve(_:declaredIn:applyingTo:in:statically:)` the loop begins

```swift
      let declaresName = declarations(lexicallyIn: .init(node: e))[n.identifier] != nil
      if TyperExperiments.extorder && !declaresName { continue }
      if declarationsOnStack.contains(.init(e)) {
```

Change the second line to `if (TyperExperiments.extorder || TyperExperiments.sigrounds) && !declaresName { continue }` and insert after it:

```swift
      if settlingSignatures && (e.module == module) && (signatureTable[.init(e)] == nil) {
        hiddenCandidateSeen = true
        continue
      }
```

The existing `if declarationsOnStack.contains(.init(e))` must not fire for an extension of this module while `settlingSignatures` is true: guard it with `!(settlingSignatures && e.module == module) &&`. In the same loop, guard the `memberskip` test with `!settlingSignatures`, since its helpers read the signature memoized in the current round.

**`applies`.** The line

```swift
    let u = extendeeType(d)
```

becomes

```swift
    let u = (settlingSignatures && (d.module == module))
      ? (signatureTable[.init(d)] ?? .error) : extendeeType(d)
```

**Visibility of givens.** `givens(visibleFrom:)` filters with `notOnStack(_:)` in three places, for example

```swift
      let ls = givens(lexicallyIn: s).filter(notOnStack(_:))
```

Replace `notOnStack` in these three places by a mutating `isVisible`, written as a loop where `filter` is used today:

```swift
/// Returns `true` iff implicit resolution may use `g` now.
private mutating func isVisible(_ g: Given) -> Bool {
  switch g {
  case .user(let d):
    if settlingSignatures && isSignatureNode(d) {
      if signatureTable[d] != nil { return true }
      hiddenCandidateSeen = true
      return false
    }
    return !declarationsOnStack.contains(d)
  case .nested(_, let h):
    return isVisible(h)
  default:
    return true
  }
}
```

A using is not a node, so the deliberate hiding of the requirements of a where clause still goes through `declarationsOnStack`. The other deliberate rule, "a conformance cannot use itself to satisfy the traits it refines", inserts the conformance in `declarationsOnStack` inside `check`, which runs after `settleSignatures`, where the last `return` applies.

**Type of a given.** In `declaredType(of g: Given)`:

```swift
    case .user(let d):
      …
      return declaredType(of: d)

    case .nested(let p, let d):
      let c = contextOfSelf(in: p)
      let t = declaredType(of: d)
```

Insert at the start of the `.user` case

```swift
      if settlingSignatures && isSignatureNode(d) { return signatureTable[d] ?? .error }
```

and compute `t` in the `.nested` case as

```swift
      let t = (settlingSignatures && isSignatureNode(d))
        ? (signatureTable[d] ?? .error) : declaredType(of: d)
```

`?? .error` is reached only by callers that enumerate givens without the visibility filter; an error type matches nothing.

**Nothing else is a soft read.** The complete list of uses of `declarationsOnStack`, `notOnStack` and `extendeeType` in `Typer.swift` is short enough to audit: the three filters above and the one in `abstractModel`; the extension loop; `applies`; `check`; `typeOfSelf(in: ExtensionDeclaration)`; the insertions in the five `declaredType`/`extendeeType` bodies, in `initializeContext`, in `ignoring` and in `anonymousImplementation`; and the guards `!declarationsOnStack.isEmpty` of `givenIndex` and `abstractModel`. Every place that reads the type of a given for resolution obtains the given from `givens(visibleFrom:)`; the other enumerations (`givens(lexicallyIn:)` in the emptiness tests, in `abstractModel`, in `allGivensSettled` and in `recordSkippedGivens`) either read no type or belong to mechanisms that are off during `settleSignatures`. The index and the abstract model stay unavailable during `settleSignatures`, because the driver's node is on the stack. That is required: they would otherwise be cached from signatures of the current round.

### 3.6 Hard reads, and one new hook

Hard reads are unchanged. The bodies of `declaredType(of: ConformanceDeclaration.ID)`, `declaredType(of: BindingDeclaration.ID)` and `extendeeType` still push the declaration on `declarationsOnStack` and still report "declaration refers to itself" when re-entered; now this can only happen through a chain of hard reads, which is a cycle in every order.

One hook is new. Today, a member of an extension or conformance `c` is only reached after `c` was forced, so the requirements of `c`'s where clause are typed before any resolution inside `c` reads them. With the table, a lookup can select `c` from the previous round and evaluate one of its members before `c`'s signature was computed in the current round. The resolution inside the member then asks for the type of a using that `initializeContext` has not typed yet, and the generic path of `declaredType(of: BindingDeclaration.ID)` would type it out of order (and `initializeContextParameter` would later fail its assertion `"declaration already initialized"`). The same happens for a given declared in a function body, which `settleSignatures` evaluates before the function is checked (`tests/15`).

In `declaredType(of d: BindingDeclaration.ID)`, after the two existing lines

```swift
    if let memoized = program[d.module].type(assignedTo: d) { return memoized }
    assert(d.module == module, "dependency is not typed")
```

insert

```swift
    // A requirement of a where clause is typed by the declaration that introduces it, in order.
    if TyperExperiments.sigrounds, program[d].role == .using,
      !declarationsOnStack.contains(.init(d)),
      let o = program.parent(containing: d).node.flatMap({ (n) in program.castToDeclaration(n) })
    {
      _ = computedSignature(of: o)
      return program[d.module].type(assignedTo: d) ?? .error
    }
```

The implementer must confirm that the parent scope of a using is its owner (the code reads usings through `givens(lexicallyIn:)` of the owner's scope, which implies it), for instance with `assert` that the owner's `contextParameters.usings` contains `d`.

### 3.7 What is switched off and later deleted

With `sigrounds`, guard with `&& !TyperExperiments.sigrounds`:

- the three uses of `extensionFrames` (the push and `popExtensionFrame()` in `extendeeType`, the append in the extension loop) and the call `noteExtensionCycle(through:)`;
- the two lines under `if TyperExperiments.givencheck {` in `summon(_:in:where:then:penalties:ancestors:)` and the call in `apply()`.

After step 4 of section 6: `noteExtensionCycle`, `popExtensionFrame`, `recordSkippedGivens`, `checkPendingGivens`, `mayMatch`, `reportCircularExtension`, `ExtensionFrame`, `extensionFrames`, `cycleGroups`, `nextCycleGroup`, `pendingGivenChecks`, `checkingPendingGivens`, the two `reportedCircular…` sets and `contextUsingsOnStack` can be deleted (about 170 lines), and so can `memberskip` with `appliesHasNoEffect`, `allGivensSettled`, `isSettled`, `appliesTriviallyFails`, `memoizedExtendeeShape` and two cache fields (about 90 lines). The review noted that the name filter of `extorder` "changes the meaning of some cyclic programs" because skipping an applicability test changes which signature is computed first. With `sigrounds` no signature is computed by an applicability test, so the filter cannot change a result, and `memberskip`, its result-preserving substitute, has nothing left to do.

### 3.8 Cost

- Code without dependencies between signatures: one round, no restore. The only overhead is listing the nodes and one copy-on-write of the buffers that the round mutates. The standard library bundled with the binary has 49 givens, 14 conformances declared with their struct and 4 extensions in 4,012 lines, and none of their headers makes a lookup through a trait or an extension.
- A signature that depends on a given or an extension of the same module (Program 1): three rounds, each evaluating every node signature once. A chain of `d` such dependencies takes `d + 2` rounds.
- Worst case: `count(nodes) + 2` rounds. A module with 1,000 nodes in which each depends on the previous one would evaluate a million signatures. If the census (plan item 2.1) finds deep chains in real code, the remedy is to recompute in a round only the nodes that read a changed entry; that needs a per-node restore and is not part of this design.
- Counters are inflated by discarded rounds. Benchmarks must report `sigrounds.rounds`.

## 4. Why it is correct

### 4.1 The argument

Write `T_k` for the table after round `k`, with `T_0` empty.

**Claim 1 (order independence).** For every `k`, `T_k` does not depend on the order of the declarations. Proof by induction. Round `k` starts from the pristine state (A2). Within it, the signature of a node is computed from: hard reads, whose values are determined by the program and `T_{k-1}` whichever computation asks first (A3); and soft reads, which return entries of `T_{k-1}` (A1). The order of declarations only changes the order in which nodes are evaluated and in which candidates are listed; neither changes a value (A3, A5). Whether an entry is absent is decided by `hasError`, which does not depend on which member of a cycle of hard reads was entered first (A4). Hence `T_k` is a function of the program and `T_{k-1}`. The stopping test, the reported nodes and the state handed to the rest of the checker are functions of the sequence `T_0, T_1, …`.

**Claim 2 (consistency).** If `settleSignatures` returns on `next == signatureTable`, the state it leaves was computed by a round in which every soft read returned the final signature of the node read. After it, every node is memoized, so no lookup or resolution in the rest of the checker computes a signature or skips a node; the only hidden declarations are those of the two deliberate rules. So no answer would change if a hidden declaration were visible: none is hidden.

**Claim 3 (programs that the existing checker handles without hiding anything).** Suppose that on-demand evaluation, in some order, never skips a declaration that is on the stack and never reports a self-reference. Then the rounds stabilize on the signatures that this evaluation computes. Proof. Let `G` have an edge from `n` to `m` when the computation of `n`'s signature reads `m` hard or makes a lookup or resolution for which `m` is a candidate. The evaluation is a depth-first traversal of `G` without a back edge, so `G` is acyclic. A node whose candidates and hard dependencies all have their final signature in the table gets its final signature. So nodes at depth 0 are final from round 1 on and nodes at depth `i` from round `i + 1` on; a wrong entry of an earlier round belongs to a node that is deeper than every node it could mislead. Step 0 of section 6 checks that the compiler's tests and the standard library are such programs.

**Claim 4 (programs without a true cycle).** Let `σ` be a stable table. Call `m` a *true dependency* of `n` if `m` is read hard by `n`'s signature or is relevant, with its signature in `σ`, to a lookup or resolution that `n`'s signature makes. Suppose the true dependencies are acyclic, and suppose that a signature computed while one of its true dependencies is missing from the table is erroneous (the lookup fails) rather than different. Then every table of the iteration is a subset of `σ`, a node at depth `i` is present from round `i + 1` on, and the iteration stops at `σ` after at most `depth + 2` rounds. Programs 1 and 4 are such programs, with depths 1 and 2. The second hypothesis is what makes this weaker than "no true cycle implies acceptance": `tests/09` shows a lookup that succeeds differently when a candidate is missing, because of shadowing.

**Claim 5 (termination).** At most `count(nodes) + 2` rounds. Under the hypotheses of claim 3 or 4 the bound is never reached, since the depth is at most `count(nodes) - 1`.

What is *not* claimed: that a program with a cycle between signatures is accepted whenever it has exactly one consistent reading, nor that the reading found is the only one. The iteration can fail to reach a reading, and a second reading that is not reachable from the empty table is never seen. Both would need monotonicity, and lookup is not monotone: a new candidate can turn an answer into an ambiguity, or shadow another.

### 4.2 Assumptions, with the assertion that checks each

| | Assumption | Check |
|---|---|---|
| A1 | During `settleSignatures`, every soft read of a node goes through `signatureTable`. | A property of the code: the audit list of section 3.5. To keep it true, give the three signature bodies (`extendeeType`, `declaredType(of: ConformanceDeclaration.ID)`, `declaredType(of: BindingDeclaration.ID)` for a given) a debug check: when one starts computing while `settlingSignatures` and another node is on the stack, the caller must be `typeOfSelf(in:)` or the hook of section 3.6. Record the caller in a Typer field set by these two and trap under `selfcheck` otherwise. |
| A2 | Restoring `program[module]` and `cache` restores everything a round wrote that a later round can read. | Under `selfcheck`: after a stable round, restore and run the round once more with the same table; the new table and the diagnostics of the module must be equal. A leak (state kept in a Typer field, in another module, or in a cache of the type store that is not a pure function of types) makes them differ. |
| A3 | Within a round, the value memoized for a declaration that is not a node (alias, function, parameter, using) does not depend on which computation demanded it first. | Under `selfcheck`: run the verification round of A2 with `nodes.reversed()`. Two known ways to violate it, neither reachable from the test programs: (i) a declaration lexically inside an owner is demanded while the owner's where clause is half typed, and sees fewer usings; assert in `initializeContext` that no declaration other than the usings is typed inside the owner's scope until it returns; (ii) function signatures have no re-entrancy guard. |
| A4 | A type that depends on an erroneous type has `hasError`, and such a signature is never a candidate. | The table omits them by construction. Assert in `declaredType(of: Given)` and `applies` that a signature read softly has no error while `settlingSignatures`. |
| A5 | The result of a lookup or resolution does not depend on the order in which candidates are listed (two candidates give an ambiguity, not the first). | The declaration-order fuzzer: no verdict change on the 575 programs without signature dependencies (review, section 2.4). |
| A6 | After `settleSignatures`, no node signature is computed for the first time. | Counter `sigrounds.lateNodes`, incremented in the computing branch of the three bodies when `!settlingSignatures`; must be 0. If a node can be created during typing, it must be added to the driver. |

A1 to A4 and A6 are local to the mechanism. A5 is a property of the existing checker that the present mechanisms also need.

## 5. Test plan

### 5.1 The programs

`tests/` contains 23 programs. Each starts with three comment lines: the expected verdict after the change, the reason, and the current verdicts. `tests/MANIFEST.tsv` gives, for each, the number of leading declarations to keep in place when permuting and the expected verdict. Current verdicts are over permutations of the remaining declarations: all of them when there are at most 120 (24 for base), otherwise the source order, its reverse and a seeded sample (`results/tests-orders.jsonl`).

| Program | After the change | base now | FULL now | Rounds (model) |
|---|---|---|---|---|
| `01-alias-used-by-given` | accepted | 8 of 24 | 8 of 24 | 3 |
| `02-alias-and-extension-of-alias` | accepted | 8 of 24 | 8 of 24 | 3 |
| `03-given-and-extension` | accepted | 13 of 24 | 16 of 24 | 3 |
| `04-extension-of-alias-declares-looked-up-name` | accepted | 4 of 6 | 4 of 6 | 2 |
| `05-mutually-dependent-extensions` | accepted | 3 of 6 | 0 of 6 | 3 |
| `06-chain-of-aliases-and-givens` | accepted | 0 of 24 | 0 of 120 | 4 |
| `07-contradiction` | rejected | 5 of 24 | 0 of 120 | 3 |
| `08-extension-applies-to-its-own-lookup` | rejected | 3 of 6 | 0 of 6 | 3 |
| `09-two-readings`, `09b-…-swapped` | rejected, both | rejected, accepted | rejected, accepted | 4 |
| `10-alias-cycle` | rejected, same diagnostic | 0 of 6 | 0 of 6 | 1 |
| `11-requirement-order-in-where-clause` | rejected | rejected | rejected | – |
| `12-requirement-order-in-where-clause-ok` | accepted | accepted | accepted | – |
| `13-given-whose-subject-needs-a-resolution` | accepted | 24 of 24 | 120 of 120 | 3 |
| `14-given-needs-itself` | rejected | rejected | rejected | 1 |
| `15-local-given-uses-context-of-function` | accepted | 6 of 6 | 6 of 6 | 1 |
| `16` to `19` (copies of four positive compiler tests) | accepted | all orders | all orders | 1 |
| `20-corpus-trait-refinement` | rejected, same two diagnostics | all orders | all orders | – |
| `21-local-shadowing-given` | accepted | 6 of 6 | 6 of 6 | 1 |
| `22-ambiguous-member-through-alias` | rejected | 0 of 24 | 0 of 24 | 1 |

Programs 11 to 22 are the ones the change must not break. "Rounds" is what the model needs; the counter `sigrounds.rounds` of the implementation should agree, and a difference is a reason to look, not a failure.

The seven programs of the review are expected to be accepted in every order.

### 5.2 Acceptance

1. `scripts/run-tests.sh` and `scripts/run-seven.sh` with the new configuration: one outcome per program, equal to the expected verdict.
2. The review's fuzzer over `research/report/test-programs` and `Tests/CompilerTests`: no program with more than one verdict. Use `scripts/orders.py` rather than `permute.py`: its splitter keeps a multi-line declaration together and refuses a file it cannot split (1 of the 730 files, an intentionally unterminated one), where `permute.py` reported eleven artefacts; and its sample is reproducible, whereas `permute.py` seeds with `hash()` of a string, which Python randomizes per process.
3. `Tests/CompilerTests`: the semantic dump (types, bindings, witness tables, diagnostics, witnesses) identical with and without `sigrounds`, and `sigrounds.rounds` equal to 0 or 1 for every file including the standard library.
4. Under `selfcheck`: the checks of A2 and A3 pass and `sigrounds.lateNodes` is 0, on all of the above.

The verdicts recorded in `research/report/test-programs/declaration-order/INDEX.md` will change for the programs that FULL rejects with "circular extension" or "circular given" and that have a stable table. `results/predicted-verdicts.txt` gives the model's prediction for the 77 of the 129 programs that it can express: 53 keep their verdict, the 7 order-dependent ones become accepted, and 14 that FULL rejects in every order become accepted (for example `names-t09_cycle_extendee`, `v2_noearly`, `n04-order-a`). For 3 more the model differs from FULL for a reason unrelated to this design (it ignores calls in function bodies and resolves an extendee expression outside the extension's scope). None goes from accepted in every order to rejected. These are predictions; the 14 need to be confirmed on the implementation and reviewed with question 1 of section 7.

### 5.3 Evidence from the model

`scripts/model.py` implements, for a subset of Hylo, the on-demand semantics (with and without an approximation of the two checks) and the round semantics.

- Fidelity. On the 17 programs of `tests/` that it can express, the on-demand model accepts exactly as many permutations as base, for every program (`results/model-vs-binary.txt`). With the checks it agrees with FULL on 16 of them and on 6 of the 7 failing programs, including 27 of 60 and 29 of 60 for `n11` and `n12`. The two differences are understood: `05` (FULL checks every lookup of a cycle group, the model only the skipped ones) and `v01` (the model ignores calls in function bodies).
- Random programs. 22,000 programs of three to five declarations, each in every order (`results/model-fuzz-summary.txt`):
  - the round verdict never varied with the order (expected: the model shares the construction);
  - 1,262 programs are accepted on demand in every order, with and without the checks; rounds accept all of them with the same alias types;
  - 37 are accepted on demand in every order but rejected by the checks in every order (a given or extension that is relevant to its own signature); rounds reject all 37;
  - 45 are order-dependent even with the checks, the class the review found; rounds accept all 45;
  - no program accepted by the checked semantics in every order is rejected by rounds;
  - the largest number of rounds was 6.

The model has no generic givens, no coercions and no scopes other than one function body, so it says nothing about A2, A3 or the hook of section 3.6.

## 6. Implementation order

Each step builds and can be tested alone. Line counts are estimates.

| Step | Change | Lines | Test | Abandon or rethink if |
|---|---|---|---|---|
| 0 | Counters only, no flag: number of nodes per module; times a signature body is entered with a non-empty stack; times the extension loop or `givens(visibleFrom:)` skips a declaration on the stack that is not a using. | 25 | Run on the standard library and both test directories. | – . Expected: the last two counters are 0 for the standard library and `Tests/CompilerTests`. If not, list the files: they are the real code this design affects, and step 2 must be watched on them. |
| 1 | Flag `sigeager`: `settleSignatures` reduced to one loop that computes every node signature before the checks, with the existing on-demand code. Add the hook of section 3.6 and counter `sigrounds.lateNodes`. | 45 | Semantic dump identical on `Tests/CompilerTests`; `lateNodes` is 0 on every test program. | The dump differs on a compiler test. Computing all signatures first would then change real code, and the reason must be understood before going on. A non-zero `lateNodes` means nodes are created during typing; find where. |
| 2 | Flag `sigrounds`: table, soft reads (section 3.5), rounds with restore, shortcut, bound, `reportUnstableSignatures`. `extorder` cycle rule and `givencheck` guarded off (section 3.7). | 90 | Section 5.2, items 1 to 3. | A compiler test changes verdict or needs more than one round; or a program of `tests/` has two verdicts and the cause is not a missed soft read. |
| 3 | `selfcheck` assertions for A1 to A4 and A6. | 40 | Section 5.2, item 4. | The A2 check fails and the leaking state cannot be put in `program[module]` or `cache`; or the A3 check fails on a program that is not a pure cycle of hard reads. Either means the "by construction" argument does not hold in this code base. |
| 4 | Make `sigrounds` imply the name filter and switch `memberskip` off; verify identical results; then delete the code listed in section 3.7 and the flags `givencheck`, `memberskip`. | −260 | Everything again; timing with the method of plan item 0.3. | Type checking of the standard library is more than 2% slower with `sigrounds` than without. Expected: not measurable, one round and no restore. |
| 5 | Documentation: replace `soundness/5-declaration-order.md`; regenerate the INDEX of the declaration-order programs after the designers answer question 1. | – | – | – |

Step 1 is separated from step 2 on purpose. It tests the two things that the model cannot: that every node can be listed before typing, and that computing a signature early, before the declaration that contains it, is harmless.

## 7. Open questions for the language designers

1. **Are cyclic dependencies between signatures legal when the iteration finds a stable reading?** Program 3 and `tests/05` are accepted by this design and rejected by the current cycle rule. If the answer is no, the rule must be stated on the stable table, for example the component rule of section 2.2 evaluated on it. It cannot be "the table must be stable after two rounds", which would reject Program 1, nor "no declaration may be skipped" in the sense of the current mechanism, which rejects Program 4. If the answer is yes, is "the reading reached from the state where no extension or given of the module is visible" the intended meaning? `tests/09` shows that a program can have two consistent readings; this design rejects it because the table oscillates, but a program with two readings of which only one is reachable would be accepted with that one.
2. **Is the bound part of the language?** A program whose table needs more than `count(nodes) + 2` rounds is rejected. The bound is generous and I know no natural program that reaches it, but it is observable.
3. **May a given see itself?** Today a given is invisible while its own type is computed. In this design it sees its signature of the previous round, like every other given. `tests/14` is rejected either way. A given that is relevant to a resolution in its own header is rejected by `givencheck` today, and here it is rejected only if the table does not stabilize.
4. **Are erroneous givens and extensions invisible?** The table omits a node whose signature contains an error. After `settleSignatures` the existing code still tries such a declaration and fails to match it. The program is rejected in both cases; only the secondary diagnostics differ.
5. **Givens in a function body.** They are visible in the whole body, before their declaration, and the order of two of them is not supposed to matter (`tests/09`). The design treats them like top-level givens. Is that the intent, or should a local given be visible only after its declaration, like a local binding?
6. **The order of requirements in a where clause stays significant** (`tests/11`, `tests/12`), by the existing deliberate rule. Confirm that this is intended; it is a place where textual order still changes a verdict, by design.
7. **Which declaration is blamed in a cycle of aliases** depends on the order (`tests/10`: "definition of 'X' refers to itself" names the alias entered first). The verdict does not. Should the diagnostic name every member?

## 8. Reproduction

All commands run from this directory, one `tc-bench` process at a time. The claim of section 1.7 about `tests/09` without its last statement was checked by removing the line `let z: A.E = true` from both files and running `./run.sh base` and `./run.sh FULL` on them: four runs, no diagnostics. `negative/illegal-enum-case.hylo` crashes this binary (exit code -4) and is counted as rejected in `results/corpus-counters.jsonl`.

| Result | Command | Raw data |
|---|---|---|
| Tables of sections 1.2 to 1.5 | `scripts/run-problem.sh` | `results/problem.txt` |
| Orders accepted, `tests/` | `scripts/run-tests.sh FULL 120 OUT.jsonl`, `scripts/run-tests.sh base 24 OUT.jsonl`; `scripts/show.py OUT.jsonl -v` | `results/tests-orders.jsonl` |
| Orders accepted, the seven programs | `scripts/run-seven.sh FULL 60 OUT.jsonl` | `results/seven-orders.jsonl` |
| `extorder.cycles` in the compiler tests | `scripts/corpus_counters.py OUT.jsonl` | `results/corpus-counters.jsonl` |
| Model against the binary | `scripts/compare_model.py results/tests-orders.jsonl`, then the same for `results/seven-orders.jsonl` | `results/model-vs-binary.txt` |
| Random programs on the model | `scripts/fuzz_model.py 6000 SEED OUT.jsonl` (4000 for seed 1) | `results/model-fuzz-seed*.jsonl`, `results/model-fuzz-summary.txt` |
| Predicted verdicts of the declaration-order programs | `scripts/predict.py` | `results/predicted-verdicts.txt` |
