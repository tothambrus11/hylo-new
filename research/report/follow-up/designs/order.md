# Order independence by construction: signatures computed in rounds

This document is for the engineer who will implement the change in `/home/user/hylo-impl/Sources/FrontEnd`. It states the problem with programs checked on the binary, compares three designs, specifies the chosen one down to the statements to change, gives the argument for its correctness with the assumptions it rests on, and lists tests and implementation steps.

Every verdict of the existing checker quoted here ("base", "FULL") was obtained with `research/exp/bin/eq9-723cc0e6b0f8/tc-bench`. Section 8 says how to reproduce each number.

**Status.** This is the second version of the document. The first version was written without an implementation, on the evidence of an executable model (`scripts/model.py`, section 5.3). It was then implemented as written, behind the flag `sigrounds` (commit `cdb3415` of `/home/user/hylo-impl`; binary `research/exp/bin/eq17-4c2982653305/tc-bench`). An adversarial review ran that binary and found three defects, each shown by a program in `tests/`. This version corrects them. The corrections are marked **[R1]**, **[R2]** and **[R3]** where they change the design; they are *not* implemented, so what this document says about them is reasoning, not measurement. Section 9 lists what the review changed, what the design withstands and what it does not. Wherever a verdict is given "with the first design", it was observed on the `eq17` binary with `FULL,sigrounds` (and `selfcheck` where stated).

## Summary

- The verdict depends on declaration order for three reasons that act together: a lookup or resolution *computes* the signature of every candidate it meets, inside the computation that asked; a candidate whose signature is being computed is *skipped*; and whatever is computed meanwhile is *memoized*. Which edge of a dependency cycle gets skipped depends on where evaluation entered the cycle.
- The same mechanism rejects ordinary programs that have no cycle at all. Program 4 below is rejected in every order tried (60) by the existing checker and by FULL. The fuzzer cannot see such programs, because their verdict does not vary.
- Chosen design, option (c) as a fixed point over a table: the signatures of extensions and givens are computed in *rounds*. During a round, every lookup and resolution reads these signatures from the table that the previous round produced, and from nowhere else. A round starts from the untouched typing state of the module. Rounds repeat until the table is stable. The table after round `k` is meant to be a function of the program and of `k`, so that nothing depends on the order in which declarations are entered.
- That property holds only if everything else a round computes is independent of who asks first. The first design broke this in three ways, all found on the implementation: it computed, before the checks, the type of a given that can only be inferred while the enclosing expression is typed (a legal program was rejected, another crashed); it treated the named requirements of a where clause as givens of the table (a program that the requirement-order rule rejects was accepted); and its hook for where clauses could type a where clause from inside a declaration that the where clause needs (the verdict of `tests/28` depended on the order of two top-level declarations, which it does not today). The corrections restrict the table to declarations whose signature is a type expression **[R1]**, compute the signature of an enclosing function, extension or conformance before anything declared inside it **[R2]**, and make the self-check compare both evaluation orders in every round **[R3]**.
- It removes `givencheck` and the cycle rule of `extorder`, including `mayMatch`, and makes `memberskip` unnecessary: the implementation of the first design added about 175 lines, the corrections are about 45 more (85 with the self-check of every round and the assertions still missing), and about 260 can be deleted afterwards.
- Cost, measured in rounds on the implementation: the standard library needs one round (72 nodes, nothing restored). A module in which a where clause selects a member through an earlier requirement (`C.Element`), the ordinary shape of generic library code, needs two rounds, which about doubles the resolution work of the signature phase (section 3.8). A chain of `n` dependent givens needs `n + 1` rounds.
- It accepts more programs than FULL: all seven failing programs become accepted in every order (measured), as do the programs that the conservative cycle rule rejects although they have one consistent reading. Whether that is wanted is the first question for the language designers (section 7).

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
type FX = Foo<X>
given FX is Q { type F = Bool }
type Y = FX.F
given Bar<Y> is P { type E = A }
type Z = Bar<Y>
type W = Z.E
fun g(y: Y, w: W) {}
```

base and FULL reject it in all 60 orders tried of the last nine declarations (`problem/p4-chain.hylo`, `tests/06b`). In the source order FULL reports "definition of 'X' refers to itself" (`results/problem.txt` has the counters). With the first design implemented it is accepted in all 60 orders, in 4 rounds.

The dependencies form a chain without any cycle. But resolving `P<A>` for `X` computes the type of `Bar<Y> is P`, which computes `Y`, which needs `X` or the given `FX is Q`, one of which is always on the stack. This is the strongest argument against repairing the current mechanism: order dependence is one symptom of forcing, and wrong rejection in every order is another.

The first version of this document wrote the program with `type Y = Foo<X>.F` (`tests/06`). That program is rejected in every order for an unrelated reason, which the review found when the implementation rejected it too: the existing checker does not accept a member selected on a type application as a type expression ("expression does not denote a type", also for `type Y = Foo<Int>.F` alone). The members are therefore selected on aliases here.

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

- P1 holds if the table after each round is a function of the program and the round number (section 4.1). The argument needs no approximation of matching, but it does need every value that a round memoizes to be independent of who asked for it first (assumption A3). The first design violated A3; section 3.6 says how and what replaces it.
- P2 holds at a stable table by definition: every signature was computed with every other signature visible at its final value.
- P3 holds: Program 1 takes 3 rounds and Program 4 takes 4 (measured).
- Programs 2 and 3 and `tests/05` are accepted in every order; the contradictions (`tests/07`, `08`, `09`) are rejected in every order because the table never becomes stable (all measured on the implementation of the first design).
- Cost: about 175 lines added by the implementation of the first design, about 45 more for the corrections. `givencheck`, the cycle rule of `extorder` and `mayMatch` become dead (about 170 lines), and so does `memberskip` (about 90), because skipping an extension by name no longer changes what is computed.
- New invariants: section 4.2 lists seven, each with an assertion. The essential ones are that restoring the typing state of the module is complete (A2) and that hard reads are confluent (A3).
- Run-time cost: one extra pass over the signatures of extensions and givens for each level of dependency between them, one extra pass as soon as any signature makes a resolution or a lookup that meets a declaration of the module, and none otherwise (section 3.8).

### 2.4 Comparison

| | (a1) strict rule | (a2) rule with skeletons | (b) groups and validation | (c2) rounds |
|---|---|---|---|---|
| P1 by construction | yes | yes, given the skeleton invariant | yes, with the component rule | yes |
| Program 1 (alias used by a given) | rejected | accepted | accepted | accepted |
| Program 4 (chain) | rejected | accepted | accepted | accepted |
| Programs 2, 3; `tests/05` | rejected | rejected | 2 accepted; 3 and 05 rejected | accepted |
| Contradictions (`tests/07`, `08`, `09`) | rejected | rejected | rejected | rejected |
| Lines added / removable | 25 / 60 | 225 / 60 | 330 / 0 | 220 / 260 |
| New invariants | none | skeletons over-approximate matching | four | restore is complete; hard reads are confluent; five smaller ones |
| Needs `mayMatch` | no | a variant of it | yes | no |

I choose (c2). On soundness, (a1), (b) and (c2) all give P1 and P2, and (c2) has the shortest argument with the fewest assumptions about matching. (a1) is simpler still, but it rejects ordinary programs, and it leaves forcing in place, which is the cause of the wrong rejections of section 1.5. If the language designers decide that programs such as Program 3 must be rejected, a rejection rule can be added on top of (c2) as a check on the stable table (section 7, question 1); the reverse is not possible.

The review qualifies this choice in one respect. The argument for (c2) is short, but it moves the burden to assumption A3 (hard reads are confluent), which is a property of the whole checker and which the first design itself broke. (a1) needs no such assumption. (c2) remains the choice because (a1) rejects Programs 1 and 4, but its "by construction" is conditional on A3 and must be watched by the self-check of section 4.2, in every round and on every test run.

## 3. The design

The existing lines quoted as anchors are from `Typer/Typer.swift` at commit `4e7a2aa` of `/home/user/hylo-impl`, the last commit before the implementation of the first design. Line numbers are not given, because the file is being changed by other work. Where the implementation at `cdb3415` already contains a change, the text says "implemented"; the corrections **[R1]** to **[R3]** are changes to make on top of it.

### 3.1 Terms

- A **context parameter** is a binding declared in a where clause: an anonymous requirement such as `T is P` (`role == .using`) or a named one such as `let u: P<T>` (`role == .given`; the parser creates both kinds, see `parseNamedContextParameter`). Its **owner** is the function, function bundle, extension or conformance whose `contextParameters.usings` contains it. Context parameters are typed by their owner, in order, by `initializeContext`, and the deliberate rule that hides the later ones while an earlier one is typed is unchanged.
- An **inferred given** is a `BindingDeclaration` with `role == .given` that is not a context parameter and has no complete ascription: no ascription at all (`given let g = e`) or one that contains a `WildcardLiteral`. Its type is only known by typing its initializer, and that may need the expression around it to be typed first (a lambda parameter without ascription, a variable bound by a pattern).
- A **node** **[R1]** is a declaration of the module being typed whose signature is written as a type expression and that lookups or resolutions select by that signature: an `ExtensionDeclaration`, a `ConformanceDeclaration`, or a `BindingDeclaration` with `role == .given` that is neither a context parameter nor an inferred given. (The first design took every binding with `role == .given`. `tests/23` to `tests/26` and `tests/28` show why that is wrong.)
- The **signature** of a node is what `extendeeType` or `declaredType(of:)` returns for it.
- A **soft read** of a node is a read of its signature made to decide whether it applies to a type or matches a goal: in `applies`, in the extension loop of `resolve(_:declaredIn:applyingTo:in:statically:)`, in `givens(visibleFrom:)`, and in `declaredType(of: Given)`. Every other read is a **hard read**: `typeOfSelf(in:)` from the members of the node, `check`, the round driver, and the two places of section 3.6 that compute an owner before what it contains.
- The **table** maps each node to its signature in the previous round, and has no entry for a node whose signature contained an error.

Aliases, functions, parameters and context parameters are not in the table. Their types are still computed on demand and memoized in the module, so they are recomputed in every round, because a round starts from the untouched state.

Inferred givens are not in the table either, and they are never typed while signatures are computed **[R1]**: `settleSignatures` evaluates type expressions only, never an initializer or a statement (assumption A7). An inferred given without a type is invisible to the resolutions made during `settleSignatures`, and each such given that a resolution would have enumerated is reported as an error once the table is stable: "the type of this given must be written: it is visible to the implicit resolutions made by the signatures of other declarations". After `settleSignatures` inferred givens behave as today: they are typed on demand, or when `check` reaches them. This rule is deliberately conservative. Ignoring the given silently would let a signature and a function body resolve the same goal differently; typing it on demand is what the first design did. It rejects a program that has both an inferred given and a signature that makes a resolution in its scope. `tests/35` is such a program: Program 1 with `given let w = 1` added. Today it is accepted in 16 of 24 orders; the first design accepts it in all 24, because it types `w` with the signatures; this rule rejects it in all 24. No program of `Tests/CompilerTests`, of the standard library or of `research/report/test-programs` contains an inferred given, so the rule changes nothing there. A less strict alternative keeps as nodes the inferred givens that are declared outside any function or lambda body, where no enclosing expression can be missing; it accepts `tests/35` in every order, at the price of typing initializers, and through them the bodies of lambdas, while signatures are computed, which weakens A7. Question 8 of section 7 asks the designers to choose.

### 3.2 Algorithm

```
settleSignatures():
  nodes    := all nodes of the module                       (from the syntax, before typing)
  pristine := (typing state of the module, memo cache)      (copy-on-write, O(1))
  table    := {}                                            (every node hidden)
  for round in 1 ... count(nodes) + 2:
      hiddenCandidateSeen := false; skippedInferredGivens := {}
      next := {}
      for n in nodes:
          for o in the owners that enclose n, outermost first:           [R2]
              compute the signature of o                    (hard; memoized in the module)
          t := signature of n, computed as today            (hard; memoized in the module)
          if t has no error: next[n] := t
      if next == table or (round == 1 and not hiddenCandidateSeen):
          table := next
          report each given in skippedInferredGivens                     [R1]
          return                                            (stable: keep the state of this round)
      if next was the table of an earlier round, or round == count(nodes) + 2:
          report the nodes whose entries differ between table and next; return
      table := next
      (typing state of the module, memo cache) := pristine  (discard the round)
```

During `settleSignatures`, a soft read of node `n` returns `table[n]`, and the node is ignored if it has no entry; `hiddenCandidateSeen` is set whenever a node is ignored for that reason. Being on `declarationsOnStack` no longer hides a node. An inferred given without a type is ignored and recorded in `skippedInferredGivens`. After `settleSignatures`, every node has a memoized signature and the existing code runs unchanged: `check` of each top-level declaration, with soft reads answered by the memoized signatures.

The test `round == 1 and not hiddenCandidateSeen` is an exact shortcut: if no lookup or resolution of round 1 had a node among its candidates, the round did not read the table, so round 2 would compute the same thing. On the implementation this is the case for the standard library (72 nodes, one round) and for every program of the compiler's tests (section 3.8), because no header there selects a member through a trait (section 2.1). It is not the case for a module with one where clause such as `where C is Collection, C.Element is Equatable`: the resolution of `Collection<C>` enumerates the givens of the module, none of which has an entry in round 1, so a second round is run to confirm the table (`tests/34`).

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

/// The inferred givens that a resolution of the current round ignored because they have no type
/// yet (`sigrounds`).                                                                       [R1]
private var skippedInferredGivens: Set<DeclarationIdentity> = []
```

The first three fields are implemented. The helpers (the first design had only `isSignatureNode`, with the test `role == .given`, and `computedSignature`):

```swift
/// Returns the context parameters of `d` if it is a declaration that can have a where clause.
private func contextParameters(of d: DeclarationIdentity) -> ContextParameters? {
  switch program.tag(of: d) {
  case ExtensionDeclaration.self:
    return program[castUnchecked(d, to: ExtensionDeclaration.self)].contextParameters
  case ConformanceDeclaration.self:
    return program[castUnchecked(d, to: ConformanceDeclaration.self)].contextParameters
  case FunctionDeclaration.self:
    return program[castUnchecked(d, to: FunctionDeclaration.self)].contextParameters
  case FunctionBundleDeclaration.self:
    return program[castUnchecked(d, to: FunctionBundleDeclaration.self)].contextParameters
  default:
    return nil
  }
}

/// Returns the declaration whose where clause introduces `d`, if `d` is a context parameter,
/// whether anonymous (`T is P`) or named (`let u: P<T>`).                                    [R1]
private func ownerOfContextParameter(_ d: BindingDeclaration.ID) -> DeclarationIdentity? {
  guard
    let o = program.parent(containing: d).node.flatMap({ (n) in program.castToDeclaration(n) }),
    let ps = contextParameters(of: o), ps.usings.contains(.init(d))
  else { return nil }
  return o
}

/// Returns `true` iff `d` is a given binding whose type is only known by typing its initializer.
private func isInferredGiven(_ d: DeclarationIdentity) -> Bool {                          // [R1]
  guard
    let b = program.cast(d, to: BindingDeclaration.self), program[b].role == .given,
    ownerOfContextParameter(b) == nil
  else { return false }
  guard let a = program[program[b].pattern].ascription else { return true }
  return containsWildcard(a)      // a walk of the ascription looking for a `WildcardLiteral`
}

/// Returns `true` iff `d` is a declaration of the module being typed that lookups and resolutions
/// select by a signature written as a type expression.
private func isSignatureNode(_ d: DeclarationIdentity) -> Bool {
  if d.module != module { return false }
  switch program.tag(of: d) {
  case ExtensionDeclaration.self, ConformanceDeclaration.self:
    return true
  case BindingDeclaration.self:
    let b = castUnchecked(d, to: BindingDeclaration.self)
    return (program[b].role == .given) && (ownerOfContextParameter(b) == nil)
      && !isInferredGiven(d)                                                              // [R1]
  default:
    return false
  }
}

/// Returns the signature of `d` computed now, memoized in the module.
private mutating func computedSignature(of d: DeclarationIdentity) -> AnyTypeIdentity {
  if let e = program.cast(d, to: ExtensionDeclaration.self) { return extendeeType(e) }
  return declaredType(of: d)
}

/// Computes the signatures of the declarations with a where clause that enclose `d`, outermost
/// first, so that nothing declared inside one of them is typed before its context parameters.
private mutating func computeOwners(enclosing d: DeclarationIdentity) {                   // [R2]
  var owners: [DeclarationIdentity] = []
  for s in program.scopes(from: program.parent(containing: d)) {
    if let o = s.node.flatMap({ (n) in program.castToDeclaration(n) }),
      let ps = contextParameters(of: o), !ps.usings.isEmpty
    { owners.append(o) }
  }
  for o in owners.reversed() { _ = computedSignature(of: o) }
}
```

The implementer must confirm two facts that the code above relies on, both with an `assert`: the parent scope of a context parameter is its owner (the implemented hook of section 3.6 already relies on it for anonymous requirements, and `tests/26` exercises a named one); and `isSignatureNode` and `isInferredGiven` give the same answer every time for a declaration (they read syntax only, so they can be memoized in two sets filled when `nodes` is listed).

### 3.4 The driver

In `apply()`, the existing lines are

```swift
    for d in program[module].topLevelDeclarations { check(d) }
    if TyperExperiments.givencheck { checkPendingGivens() }
```

Insert `if TyperExperiments.sigrounds { settleSignatures() }` before the loop (implemented). The driver below is the implemented one with the three corrections marked.

```swift
/// Computes the signature of each of `nodes` in order, reading the signatures used by lookups
/// and resolutions from `signatureTable`, and returns the signatures that have no error.
private mutating func signatureRound(
  _ nodes: [DeclarationIdentity]
) -> [DeclarationIdentity: AnyTypeIdentity] {
  hiddenCandidateSeen = false
  skippedInferredGivens = []                                                       // [R1]
  var next: [DeclarationIdentity: AnyTypeIdentity] = [:]
  for n in nodes {
    computeOwners(enclosing: n)                                                    // [R2]
    let t = computedSignature(of: n)
    if !t[.hasError] { next[n] = t }
  }
  TyperCounters.bump("sigrounds.rounds")
  return next
}

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
    let next = signatureRound(nodes)
    if TyperExperiments.selfcheck { selfCheckRound(nodes, next, from: pristine) }  // [R3]

    if (next == signatureTable) || ((round == 1) && !hiddenCandidateSeen) {
      signatureTable = next
      reportSkippedInferredGivens()                                                // [R1]
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

`selfCheckRound` **[R3]** is the implemented `selfCheckSignatures` called for every round instead of the stable one only: it saves the state that the round produced, restores `pristine`, runs `signatureRound(nodes.reversed())` with the same `signatureTable`, compares the table and the set of diagnostic messages with those of the forward run, reports a self-check violation if either differs, and puts the saved state back. Before comparing the messages it must replace the name in "definition of '…' refers to itself" by a fixed word and compare messages without their positions for that diagnostic and for "declaration refers to itself": which member of a cycle of hard reads is blamed depends on the member entered first (question 7), and the implemented check reports a false violation for `tests/38`, a cycle of two aliases entered from two extensions, although the table and the verdict are the same in both orders. It must also save and restore `hiddenCandidateSeen`, `skippedInferredGivens` and `reportedBudgetScopes`. The check of the stable round alone caught attack 3 on `tests/27`, `27b` and `28`; checking every round also covers a table that differs between the two orders in a round that is later discarded.

`reportSkippedInferredGivens` **[R1]** reports, for each declaration in `skippedInferredGivens` in the order of their sites, the error quoted in section 3.1, and bumps `sigrounds.inferredGivenSkipped`.

Notes for the implementer.

- `program[module]` is the whole `Module` value: syntax, types of nodes, name bindings, witness tables and diagnostics of every source file (`Module.SourceContainer`). Assigning it back discards everything the round wrote, including syntax replaced by elaboration and diagnostics. `Program.subscript(m: Module.ID)` has `get` and `_modify`, so both the copy and the assignment compile.
- `program.types` (the type store) is deliberately *not* restored: the table holds type identities that must stay valid. The store only grows; types created by a discarded round are unreachable garbage.
- `cache` must be restored: `scopeToSummoned`, `scopeToExtensionApplies`, `scopeToTypeOfSelf`, `witnessToAliases` and the coercion caches hold answers computed from the previous table.
- Typer fields that record what was reported must be reset with the state: `reportedBudgetScopes` today, and `skippedInferredGivens`, which `signatureRound` resets. If `sigrounds` is ever run together with `extorder` or `givencheck` during the transition, also `reportedCircularExtensions`, `reportedCircularGivens`, `extensionFrames`, `cycleGroups` and `pendingGivenChecks`; step 2 of section 6 switches those mechanisms off instead (section 3.7).
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
    if settlingSignatures && isInferredGiven(d)                                    // [R1]
      && (program[d.module].type(assignedTo: d) == nil)
    {
      skippedInferredGivens.insert(d)
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

This is implemented except for the lines marked **[R1]**. A context parameter is not a node, whether it is anonymous or named, so the deliberate hiding of the requirements of a where clause still goes through `declarationsOnStack` (the last `return`). In the first design a named requirement was a node: it was read from the table while an earlier requirement of the same clause was typed, which defeats the rule (`tests/25`). The other deliberate rule, "a conformance cannot use itself to satisfy the traits it refines", inserts the conformance in `declarationsOnStack` inside `check`, which runs after `settleSignatures`, where the last `return` applies.

The test `type(assignedTo: d) == nil` in the **[R1]** lines is always true during `settleSignatures` if assumption A7 holds, since nothing types an initializer there. It is kept so that a violation of A7 shows as a difference in the self-check and not as a wrong skip.

**Type of a given.** In `declaredType(of g: Given)`:

```swift
    case .user(let d):
      …
      return declaredType(of: d)

    case .nested(let p, let d):
      let c = contextOfSelf(in: p)
      let t = declaredType(of: d)
```

Insert in the `.user` case, before `return declaredType(of: d)` (implemented)

```swift
      if settlingSignatures && isSignatureNode(d) { return signatureTable[d] ?? .error }
      if settlingSignatures && isInferredGiven(d)                                  // [R1]
        && (program[d.module].type(assignedTo: d) == nil) { return .error }
```

The `.nested` case needs no change. The first design asked for one, but there `d` is a `Given`, not a declaration: `declaredType(of: d)` is the recursive call, which reaches the `.user` case above.

`?? .error` and the second line are reached only by callers that enumerate givens without the visibility filter; an error type matches nothing.

**Nothing else is a soft read.** The complete list of uses of `declarationsOnStack`, `notOnStack` and `extendeeType` in `Typer.swift` is short enough to audit: the three filters above and the one in `abstractModel`; the extension loop; `applies`; `check`; `typeOfSelf(in: ExtensionDeclaration)`; the insertions in the five `declaredType`/`extendeeType` bodies, in `initializeContext`, in `ignoring` and in `anonymousImplementation`; and the guards `!declarationsOnStack.isEmpty` of `givenIndex` and `abstractModel`. Every place that reads the type of a given for resolution obtains the given from `givens(visibleFrom:)`; the other enumerations (`givens(lexicallyIn:)` in the emptiness tests, in `abstractModel`, in `allGivensSettled` and in `recordSkippedGivens`) either read no type or belong to mechanisms that are off during `settleSignatures`. In the first design the index of givens and the abstract model are unavailable during `settleSignatures`, because the driver's node is always on the stack. With **[R2]** this is no longer automatic: `computeOwners` computes the signature of a function from the driver, a function does not put itself on the stack, and the types of its parameters are therefore evaluated with an empty stack. Keep the property explicitly: in `givenIndex` and in `abstractModel`, extend the guards `!declarationsOnStack.isEmpty` with `|| settlingSignatures` (the three guards that return `nil` or refuse to cache). The local part of the abstract model is built from `givens(lexicallyIn:)` filtered by `notOnStack`, not by `isVisible`, so without the guard it would count a node that has no entry in the table, with an erroneous type.

### 3.6 Hard reads: owners first

Hard reads are unchanged. The bodies of `declaredType(of: ConformanceDeclaration.ID)`, `declaredType(of: BindingDeclaration.ID)` and `extendeeType` still push the declaration on `declarationsOnStack` and still report "declaration refers to itself" when re-entered; now this can only happen through a chain of hard reads, which is a cycle in every order.

What is new is an invariant that on-demand evaluation gave for free and that the table takes away: **the context parameters of an owner are typed before anything declared inside the owner is.** Today a member of an extension or conformance `c` is only reached after `c` was forced, and the body of a function only after its signature. With the table, a lookup can select `c` from the previous round and evaluate one of its members before `c`'s signature was computed in the current round; and `settleSignatures` evaluates a given declared in a function body before the function is checked (`tests/15`). A resolution inside the member or the local given then asks for the type of a context parameter that `initializeContext` has not typed yet.

The first design restored the invariant lazily, with a hook in `declaredType(of: BindingDeclaration.ID)` that computes the owner's signature when an untyped requirement is asked for. The review showed that this is not enough. If the where clause of the owner refers to a declaration `m` inside the owner, there are two ways in. Entered at the owner, the where clause demands `m`, and `m` is typed with the requirements typed so far: no error (this is what the existing checker does, and it accepts `fun f<T where T is P, LA is Q>() { type LA = T.X }`). Entered at `m`, the resolution inside `m` triggers the hook, the hook types the where clause, the where clause demands `m`, which is on the stack: "definition of 'LA' refers to itself". Which way is taken depended on the order of the nodes: `tests/27` and `27b` differ by the order of two givens in a function body and got different verdicts, and `tests/28` got two verdicts depending on the order of two top-level declarations. The existing checker rejects all of them in every order.

The corrected design restores the invariant eagerly where that is possible and keeps the hook where it is not.

**Owners first, in the driver [R2].** Before the driver computes a node, it computes the signature of every enclosing declaration that has a where clause, outermost first (`computeOwners(enclosing:)`, sections 3.3 and 3.4). During `settleSignatures` the only ways into the body of a function are the driver, for a node declared there, and the signature of that function itself: lookups do not look into bodies, and a resolution only sees the givens of the scopes that enclose it. With **[R1]** no initializer is typed, so no top-level declaration reaches a function signature either (this was the second way in for `tests/28`). Hence a declaration inside a function is always entered through the function's signature, as in the existing checker.

**The hook, for members selected through the table.** A member of an extension or conformance can still be selected by a lookup before its owner was computed in the current round. For that case the hook stays (implemented, for `role == .using` only). In `declaredType(of d: BindingDeclaration.ID)`, after the two existing lines

```swift
    if let memoized = program[d.module].type(assignedTo: d) { return memoized }
    assert(d.module == module, "dependency is not typed")
```

it reads, with the test on the role replaced by the test on the owner **[R1]**, so that named requirements are covered and are never typed by the generic path below it:

```swift
    // A requirement of a where clause is typed by the declaration that introduces it, in order.
    if TyperExperiments.sigrounds, !declarationsOnStack.contains(.init(d)),
      let o = ownerOfContextParameter(d)
    {
      TyperCounters.bump("sigrounds.ownerFirst")
      _ = computedSignature(of: o)
      return program[d.module].type(assignedTo: d) ?? .error
    }
```

The two ways in still exist for a member `m` of an extension `e` when the where clause of `e` selects `m` again. For that, `e` must apply, according to the table, to the type on which its own where clause makes the lookup, so `e` must have had a signature in an earlier round in which that lookup did not need `e`. I could not construct such a program. At top level a failed lookup is an error, so `e` never enters the table, and a second extension that provides the member first makes the lookup ambiguous later (`tests/30` and `31` are the closest; both orders agree). In a function body a conformance with a where clause can shadow a top-level one for the lookup made by its own where clause, which avoids the ambiguity (`tests/37`, `37b`); but the associated type of a conformance that has a where clause is not reduced to its implementation, so the lookup does not type the member, and both orders agree. If a later change reduces such associated types, `tests/37` and `37b` are the programs to watch. It remains a risk, stated as assumption A3 and watched by the self-check **[R3]**. A counter `sigrounds.ownerFirst` above zero is normal for members; for a requirement whose owner is a function it must be zero after **[R2]**, which the implementer should assert.

### 3.7 What is switched off and later deleted

With `sigrounds`, guard with `&& !TyperExperiments.sigrounds`:

- the three uses of `extensionFrames` (the push and `popExtensionFrame()` in `extendeeType`, the append in the extension loop) and the call `noteExtensionCycle(through:)`;
- the two lines under `if TyperExperiments.givencheck {` in `summon(_:in:where:then:penalties:ancestors:)` and the call in `apply()`.

After step 4 of section 6: `noteExtensionCycle`, `popExtensionFrame`, `recordSkippedGivens`, `checkPendingGivens`, `mayMatch`, `reportCircularExtension`, `ExtensionFrame`, `extensionFrames`, `cycleGroups`, `nextCycleGroup`, `pendingGivenChecks`, `checkingPendingGivens`, the two `reportedCircular…` sets and `contextUsingsOnStack` can be deleted (about 170 lines), and so can `memberskip` with `appliesHasNoEffect`, `allGivensSettled`, `isSettled`, `appliesTriviallyFails`, `memoizedExtendeeShape` and two cache fields (about 90 lines). The review noted that the name filter of `extorder` "changes the meaning of some cyclic programs" because skipping an applicability test changes which signature is computed first. With `sigrounds` no signature is computed by an applicability test, so the filter cannot change a result, and `memberskip`, its result-preserving substitute, has nothing left to do.

### 3.8 Cost

The numbers below were measured on the implementation of the first design (`eq17`, `FULL,sigrounds`, without `selfcheck`, which adds one round). Counters, not times.

- Code in which no signature meets a declaration of its module: one round, no restore. The only overhead is listing the nodes and one copy-on-write of the buffers that the round mutates. Measured for the standard library bundled with the binary: `sigrounds.nodes=72 sigrounds.rounds=1`, and `summon.calls` and `summon.matches` equal with and without the flag (3,158 and 3,541). Measured for the 192 programs of `Tests/CompilerTests`: 127 have no node, 65 take one round, none restores, and no counter `sigrounds.lateNodes` or `sigrounds.ownerFirst` appears (`results/review-corpus-rounds.jsonl`).
- A where clause that selects a member through an earlier requirement, as in `given <C where C is Collection, C.Element is Equatable> => Wrapper<C> is Equatable`: two rounds and one restore (`tests/34`). The resolution of `Collection<C>` succeeds in round 1 through the requirement, but it enumerates the module's givens, which have no entry yet, so the table must be confirmed. With 40 such givens in a module, `summon.matches` of the user module goes from 5,260 to 8,920 and `summon.calls` from 40 to 80 (`results/review-cost.txt`): the resolution work of the signature phase about doubles. This is the ordinary shape of generic library code, so two rounds, not one, is the case to plan for. The cost of checking bodies is not affected.
- A signature that depends on a given or an extension of the same module (Program 1): three rounds, each evaluating every node signature once. A chain of `d` such dependencies takes `d + 2` rounds; a chain that goes through all `n` nodes takes `n + 1` (`tests/33`: 5 nodes, 6 rounds). Measured on generated chains (`results/review-cost.txt`): 5, 9 and 17 nodes take 6, 10 and 18 rounds, with `summon.matches` 1,780, 5,616 and 20,608, which is quadratic, as expected.
- Worst case: `count(nodes) + 2` rounds. A module with 1,000 nodes in which each depends on the previous one would evaluate a million signatures. If the census (plan item 2.1) finds deep chains in real code, the remedy is to recompute in a round only the nodes that read a changed entry; that needs a per-node restore and is not part of this design.
- During `settleSignatures` the index of givens and the abstract model are unavailable, as they are today whenever a declaration is on the stack, so every resolution made by a signature scans all visible givens.
- Counters are inflated by discarded rounds. Benchmarks must report `sigrounds.rounds` and `sigrounds.restores`.

## 4. Why it is correct

### 4.1 The argument

Write `T_k` for the table after round `k`, with `T_0` empty.

**Claim 1 (order independence).** For every `k`, `T_k` does not depend on the order of the declarations. Proof by induction. Round `k` starts from the pristine state (A2). Within it, the signature of a node is computed from: hard reads, whose values are determined by the program and `T_{k-1}` whichever computation asks first (A3); and soft reads, which return entries of `T_{k-1}` (A1). The order of declarations only changes the order in which nodes are evaluated and in which candidates are listed; neither changes a value (A3, A5). Whether an entry is absent is decided by `hasError`, which does not depend on which member of a cycle of hard reads was entered first (A4). Hence `T_k` is a function of the program and `T_{k-1}`. The stopping test, the reported nodes, the set of skipped inferred givens (which have no type during any round, by A7) and the state handed to the rest of the checker are functions of the sequence `T_0, T_1, …`.

The proof is only as good as A3, and A3 is where the first design failed: the value memoized for a local alias, and whether an error was reported, depended on whether the alias or the function around it was entered first (section 3.6). **[R2]** removes that case by making the function's signature the only way in; what remains of A3 is an assumption, not a theorem.

**Claim 2 (consistency).** If `settleSignatures` returns on `next == signatureTable`, the state it leaves was computed by a round in which every soft read returned the final signature of the node read. After it, every node is memoized, so no lookup or resolution in the rest of the checker computes a signature or skips a node; the only hidden declarations are those of the two deliberate rules. So no answer would change if a hidden declaration were visible: none is hidden. Inferred givens are the exception to "none is hidden": they are invisible during `settleSignatures` and visible afterwards. The claim holds for an accepted program because a program in which a resolution of `settleSignatures` could have seen one is rejected **[R1]**.

**Claim 3 (programs that the existing checker handles without hiding anything).** Suppose that on-demand evaluation, in some order, never skips a declaration that is on the stack and never reports a self-reference. Then the rounds stabilize on the signatures that this evaluation computes. Proof. Let `G` have an edge from `n` to `m` when the computation of `n`'s signature reads `m` hard or makes a lookup or resolution for which `m` is a candidate. The evaluation is a depth-first traversal of `G` without a back edge, so `G` is acyclic. A node whose candidates and hard dependencies all have their final signature in the table gets its final signature. So nodes at depth 0 are final from round 1 on and nodes at depth `i` from round `i + 1` on; a wrong entry of an earlier round belongs to a node that is deeper than every node it could mislead. The compiler's tests and the standard library are such programs: measured, each takes at most one round (section 3.8).

**Claim 4 (programs without a true cycle).** Let `σ` be a stable table. Call `m` a *true dependency* of `n` if `m` is read hard by `n`'s signature or is relevant, with its signature in `σ`, to a lookup or resolution that `n`'s signature makes. Suppose the true dependencies are acyclic, and suppose that a signature computed while one of its true dependencies is missing from the table is erroneous (the lookup fails) rather than different. Then every table of the iteration is a subset of `σ`, a node at depth `i` is present from round `i + 1` on, and the iteration stops at `σ` after at most `depth + 2` rounds. Programs 1 and 4 are such programs, with depths 1 and 2. The second hypothesis is what makes this weaker than "no true cycle implies acceptance": `tests/09` shows a lookup that succeeds differently when a candidate is missing, because of shadowing.

**Claim 5 (termination).** At most `count(nodes) + 2` rounds. Under the hypotheses of claim 3 or 4 the bound is never reached, since the depth is at most `count(nodes) - 1`.

What is *not* claimed: that a program with a cycle between signatures is accepted whenever it has exactly one consistent reading, nor that the reading found is the only one. The iteration can fail to reach a reading, and a second reading that is not reachable from the empty table is never seen. Both would need monotonicity, and lookup is not monotone: a new candidate can turn an answer into an ambiguity, or shadow another.

### 4.2 Assumptions, with the assertion that checks each

| | Assumption | Check |
|---|---|---|
| A1 | During `settleSignatures`, every soft read of a node goes through `signatureTable`. | A property of the code: the audit list of section 3.5. To keep it true, give the three signature bodies (`extendeeType`, `declaredType(of: ConformanceDeclaration.ID)`, `declaredType(of: BindingDeclaration.ID)` for a given) a debug check: when one starts computing while `settlingSignatures` and another node is on the stack, the caller must be `typeOfSelf(in:)` or the hook of section 3.6 (`computeOwners` runs with an empty stack). Record the caller in a Typer field set by these two and trap under `selfcheck` otherwise. Not implemented yet. |
| A2 | Restoring `program[module]` and `cache` restores everything a round wrote that a later round can read. | Under `selfcheck` (implemented for the stable round; **[R3]** for every round): restore and run the round once more with the same table; the new table and the diagnostics of the module must be equal. A leak (state kept in a Typer field, in another module, or in a cache of the type store that is not a pure function of types) makes them differ. |
| A3 | Within a round, the value memoized for a declaration that is not a node (alias, function, parameter, context parameter), and whether an error is reported while computing it, do not depend on which computation demanded it first. (Which member of a cycle is blamed does depend on it, today and here: `tests/10`, `tests/38`.) | Under `selfcheck`: the verification round of A2 is run with `nodes.reversed()`. This check exists and it caught the violation of the first design on `tests/27`, `27b` and `28` ("the stable round reports other diagnostics in reverse order"). Known ways to violate A3: (i) a declaration inside an owner is demanded before the owner's signature and its resolution types the owner's where clause, which needs that declaration. Closed for functions by **[R2]**; open in principle for a member of an extension or conformance selected through the table (section 3.6), where no program is known. (ii) Function signatures have no re-entrancy guard; no way to re-enter one is known. Reversing the nodes covers two of the possible orders, not all: the declaration-order fuzzer run with `selfcheck` covers more. |
| A4 | A type that depends on an erroneous type has `hasError`, and such a signature is never a candidate. | The table omits them by construction. Assert in `declaredType(of: Given)` and `applies` that a signature read softly has no error while `settlingSignatures`. Checked by the review for lookups: a candidate member with an erroneous type makes the lookup ambiguous, it is not dropped (`tests/30`, 24 orders, one outcome). |
| A5 | The result of a lookup or resolution does not depend on the order in which candidates are listed (two candidates give an ambiguity, not the first). | The declaration-order fuzzer: no verdict change on the 575 programs without signature dependencies (review, section 2.4). |
| A6 | After `settleSignatures`, no node signature is computed for the first time. | Counter `sigrounds.lateNodes` (implemented), incremented in the computing branch of the three bodies when `!settlingSignatures`; must be 0. With **[R1]** the branch for bindings must count only bindings that are nodes: an inferred given is typed late by design. |
| A7 | `settleSignatures` types no initializer and no statement: every signature it computes, and everything those signatures force, is a type expression. | **[R1]** makes this true for the nodes. Assert it: `inferredType(of: BindingDeclaration.ID, in:)` must not reach an initializer, and no statement must be checked, while `settlingSignatures`. A type expression that names a value (a global binding) is an error in every order and may trip the assertion; report it as the existing "expression does not denote a type" before typing the binding. The assertion will also show whether an ascription without a `WildcardLiteral` can still be partial (`isPartial` in `inferredType(of: BindingDeclaration.ID, in:)`); if it can, such a binding must be classified as an inferred given when that is discovered, in every round alike. |

A1 to A4, A6 and A7 are local to the mechanism. A5 is a property of the existing checker that the present mechanisms also need.

Why A7 matters: an initializer can need the expression around it. With the first design, `given let g = a` in the body of a lambda whose parameter `a` has no ascription was typed before the lambda, and reported "parameter declaration requires an ascription" (`tests/23`, accepted by base and FULL); with a variable bound by a `match` pattern it reached `unreachable("pattern is not typed")` (`tests/24`).

## 5. Test plan

### 5.1 The programs

`tests/` contains 42 programs: the 23 of the first version and 19 added by the review. Each starts with comment lines: the expected verdict after the change, the reason, the current verdicts, and for the review's programs what the first design does. `tests/MANIFEST.tsv` gives, for each, the number of leading declarations to keep in place when permuting and the expected verdict. Current verdicts are over permutations of the remaining declarations: all of them when there are at most 120 (24 for base and for the review's programs), otherwise the source order, its reverse and a seeded sample (`results/tests-orders.jsonl`, `results/review-new-tests.jsonl`). The review ran the 46 recorded verdicts of the first version again; all are reproduced, with the same diagnostics (`results/review-tests-eq9.jsonl`).

The column "first design" is what the implementation of the first design does under `FULL+sigrounds+selfcheck`. For the 23 programs of the first version it is the coordinator's run over the same orders as the FULL column (`../sigrounds/tests.jsonl`, binary `eq15`), which the review confirmed on `eq17` in up to 6 orders (`results/review-tests-sigrounds.jsonl`). For the review's programs it is the review's run on `eq17` in up to 24 orders, 60 for `06b` (`results/review-new-tests.jsonl`). "Rounds" is `sigrounds.rounds` in the source order without `selfcheck` (`results/review-tests-rounds.txt`); a dash means that the program has no node.

| Program | After the change | base now | FULL now | First design (measured) | Rounds |
|---|---|---|---|---|---|
| `01-alias-used-by-given` | accepted | 8 of 24 | 8 of 24 | accepted, 24 of 24 | 3 |
| `02-alias-and-extension-of-alias` | accepted | 8 of 24 | 8 of 24 | accepted, 24 of 24 | 3 |
| `03-given-and-extension` | accepted | 13 of 24 | 16 of 24 | accepted, 24 of 24 | 3 |
| `04-extension-of-alias-declares-looked-up-name` | accepted | 4 of 6 | 4 of 6 | accepted, 6 of 6 | 2 |
| `05-mutually-dependent-extensions` | accepted | 3 of 6 | 0 of 6 | accepted, 6 of 6 | 3 |
| `06-chain-of-aliases-and-givens` | **rejected** (the first version said accepted; section 1.5) | 0 of 24 | 0 of 120 | rejected, 0 of 120 | 3 |
| `06b-chain-through-alias` | accepted | 0 of 60 | 0 of 60 | accepted, 60 of 60 | 4 |
| `07-contradiction` | rejected | 5 of 24 | 0 of 120 | rejected, 0 of 120 | 3 |
| `08-extension-applies-to-its-own-lookup` | rejected | 3 of 6 | 0 of 6 | rejected, 0 of 6 | 3 |
| `09-two-readings`, `09b-…-swapped` | rejected, both | rejected, accepted | rejected, accepted | rejected, both | 4 |
| `10-alias-cycle` | rejected, same diagnostic | 0 of 6 | 0 of 6 | rejected, 0 of 6 | – |
| `11-requirement-order-in-where-clause` | rejected | rejected | rejected | rejected | – |
| `12-requirement-order-in-where-clause-ok` | accepted | accepted | accepted | accepted | – |
| `13-given-whose-subject-needs-a-resolution` | accepted | 24 of 24 | 120 of 120 | accepted, 120 of 120 | 3 |
| `14-given-needs-itself` | rejected | rejected | rejected | rejected | 1 |
| `15-local-given-uses-context-of-function` | accepted | 6 of 6 | 6 of 6 | accepted, 6 of 6 | 1 |
| `16` to `19` (copies of four positive compiler tests) | accepted | all orders | all orders | accepted, all orders | 1 |
| `20-corpus-trait-refinement` | rejected, same two diagnostics | all orders | all orders | rejected, 0 of 120 | 1 |
| `21-local-shadowing-given` | accepted | 6 of 6 | 6 of 6 | accepted, 6 of 6 | 1 |
| `22-ambiguous-member-through-alias` | rejected | 0 of 24 | 0 of 24 | rejected, 0 of 24 | 1 |
| `23-inferred-given-in-lambda` | accepted **[R1]** | 6 of 6 | 6 of 6 | rejected, 0 of 6 | 1 |
| `24-inferred-given-in-match` | as without the flag **[R1]** | crashes | accepted | crashes ("pattern is not typed") | – |
| `25-named-context-parameter-order` | rejected **[R1]** | rejected | rejected | accepted | 3 |
| `26-named-context-parameter` | accepted, 2 nodes | 2 of 2 | 2 of 2 | accepted, 2 of 2 | 3 |
| `27-local-alias-in-where-clause`, `27b-…-swapped` | accepted, both **[R2]** | rejected, both | rejected, both | 27 accepted, 27b rejected; self-check violation on both | 2 |
| `28-inferred-given-enters-function` | rejected in every order **[R1]** (one verdict in every order with **[R2]** alone) | 0 of 24 | 0 of 24 | **accepted in 12 of 24**; self-check violation in all | 2 |
| `29-extension-sees-itself` | rejected | 2 of 2 | 0 of 2 | rejected, 0 of 2 | 3 |
| `30-hard-cycle-two-entries` | rejected, same diagnostics | 0 of 24 | 0 of 24 | rejected, 0 of 24 | 3 |
| `31-member-of-itself-through-the-table` | rejected | 3 of 6 | 0 of 6 | rejected, 0 of 6 | 3 |
| `32-conformance-in-lambda` | accepted | 6 of 6 | 6 of 6 | accepted, 6 of 6 | 3 |
| `33-chain-of-five` | accepted | 0 of 24 | 0 of 24 | accepted, 24 of 24 | 6 |
| `34-member-through-requirement` | accepted | 24 of 24 | 24 of 24 | accepted, 24 of 24 | 2 |
| `35-inferred-given-at-top-level` | **rejected** **[R1]**, a deliberate choice (question 8) | 16 of 24 | 16 of 24 | accepted, 24 of 24 | 3 |
| `36-requirement-order-with-local-given` | rejected | rejected | rejected | rejected | 2 |
| `37-member-of-conditional-given`, `37b-…-swapped` | accepted, both | accepted, both | rejected, both | accepted, both | 3 |
| `38-alias-cycle-entered-from-two-extensions` | rejected, no self-check violation **[R3]** | 0 of 24 | 0 of 24 | rejected, 0 of 24; false self-check violation in all | 1 |

Programs 11 to 22, 26, 32, 34, 36, 37 and 37b are the ones the change must not break. For programs 23 to 28 and 35 the column "after the change" is a prediction for the corrected design: it cannot be measured until steps 2b and 2c of section 6 are implemented.

The seven programs of the review are accepted in every order by the implementation of the first design (measured by the coordinator, `../sigrounds/tests.jsonl`), and the corrections do not concern them: they contain no inferred given, no named requirement and no node declared inside a function, extension or conformance that has a where clause.

### 5.2 Acceptance

1. `scripts/run-tests.sh` and `scripts/run-seven.sh` with the new configuration: one outcome per program, equal to the expected verdict.
2. The review's fuzzer over `research/report/test-programs` and `Tests/CompilerTests`: no program with more than one verdict. Use `scripts/orders.py` rather than `permute.py`: its splitter keeps a multi-line declaration together and refuses a file it cannot split (1 of the 730 files, an intentionally unterminated one), where `permute.py` reported eleven artefacts; and its sample is reproducible, whereas `permute.py` seeds with `hash()` of a string, which Python randomizes per process.
3. `Tests/CompilerTests`: the semantic dump (types, bindings, witness tables, diagnostics, witnesses) identical with and without `sigrounds`, and `sigrounds.rounds` equal to 0 or 1 for every file including the standard library. Measured for the first design, verdicts and rounds only: 192 of 192 verdicts equal to FULL, 127 files with no node and 65 with one round (`results/review-corpus-rounds.jsonl`).
4. Under `selfcheck`: the checks of A2 and A3 pass in every round **[R3]** and `sigrounds.lateNodes` is 0, on all of the above, including every permutation tried by the fuzzer. The fuzzer permutes top-level declarations only; `tests/09`, `09b`, `27` and `27b` are pairs that differ by the order of declarations in a function body, and each pair must get one verdict.
5. No crash and no change of verdict on a program with an inferred given that no signature can see (`tests/23`, `24`).

The verdicts recorded in `research/report/test-programs/declaration-order/INDEX.md` change for the programs that FULL rejects with "circular extension" or "circular given" and that have a stable table. The first version predicted them with the model (`results/predicted-verdicts.txt`, for the 77 of the 129 programs that the model can express). The coordinator has since run the implementation of the first design on all 129, in up to 24 orders each (`../sigrounds/order-corpus.jsonl`):

- no program has two verdicts, and no self-check violation is reported;
- the 7 order-dependent programs are accepted in every order;
- 17 programs that FULL rejects in every order are accepted in every order: the 14 the model predicted and 3 it cannot express (`names-t02_names_worse`, `names-t03_names_worse`, `r2_bare`);
- no program goes from accepted to rejected;
- the model's verdict equals the implementation's for 74 of the 77 programs it can express. The 3 others (`g_dup0`, `names-n17_alias_cycle_generic`, `r1_alias`) are the ones the first version had already set aside as model errors unrelated to the design: the implementation rejects them, like FULL.

The 17 need to be reviewed with question 1 of section 7.

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

The model has no generic givens, no coercions, no where clauses, no given bindings and no scopes other than one function body, so it says nothing about A2, A3, A7 or the hook of section 3.6. All three defects found by the review lie there. On what the model does cover, the implementation confirmed it (section 5.2).

## 6. Implementation order

Each step builds and can be tested alone. Line counts are estimates, except those of the steps already done.

| Step | Change | Lines | Status | Test | Abandon or rethink if |
|---|---|---|---|---|---|
| 0 | Counters only: number of nodes per module; `sigrounds.lateNodes`; `sigrounds.ownerFirst`. | 15 | Done with step 2 (`cdb3415`). | Run on the standard library and both test directories. | – |
| 1 | Flag `sigeager`: `settleSignatures` reduced to one loop that computes every node signature before the checks. | – | Skipped: the first design was implemented in one change. Its purpose, to test that computing a signature before the declaration that contains it is harmless, was therefore not tested separately, and that is where the review found attacks 1 and 3. | – | – |
| 2 | Flag `sigrounds`: table, soft reads (section 3.5), rounds with restore, shortcut, bound, `reportUnstableSignatures`, the hook for `role == .using`, self-check of the stable round. `extorder` cycle rule and `givencheck` guarded off (section 3.7). | about 175 | Done (`cdb3415`). | Section 5.2, items 1 to 3: pass for the 23 programs of the first version except `06` (wrong expectation), for the seven programs, and for `Tests/CompilerTests` (identical verdicts, 0 or 1 round). Fail on `tests/23`, `24`, `25`, `27`, `27b`, `28`. | – |
| 2b | **[R1]** Nodes are extensions, conformances and given bindings that are neither context parameters nor inferred givens (`contextParameters(of:)`, `ownerOfContextParameter`, `isInferredGiven`, new `isSignatureNode`); the hook tests the owner instead of the role; inferred givens are skipped during `settleSignatures` and reported. | 30 | To do. | `tests/23` accepted; `tests/24` as without the flag; `tests/25` rejected; `tests/26` accepted with `sigrounds.nodes=2`; `tests/35` rejected with the new diagnostic; `Tests/CompilerTests` unchanged. | A program of `Tests/CompilerTests` or of the standard library has an inferred given that is skipped (none is known): then question 8 must be answered first. |
| 2c | **[R2]** `computeOwners(enclosing:)` called by the driver before each node; `givenIndex` and `abstractModel` unavailable while `settlingSignatures` (section 3.5). | 15 | To do. | `tests/27` and `27b` accepted; `tests/28` one verdict in all orders (rejected by **[R1]**; accepted if `w` is given an ascription); no self-check violation; `sigrounds.ownerFirst` is 0 for requirements of functions; `tests/15`, `18`, `21`, `32` unchanged. | A compiler test changes verdict: computing the signature of a function before the checks would then change real code. |
| 3 | **[R3]** Self-check of every round in both orders, with the blame of cycles normalised (section 3.4); assertions for A1, A4 and A7. | 40 | Partly done (stable round only; A6 counter). | Section 5.2, item 4, with the declaration-order fuzzer run under `selfcheck`; no violation on `tests/38`. | The A2 check fails and the leaking state cannot be put in `program[module]` or `cache`; or the A3 check fails after **[R2]** on a program that is not one of section 3.6. Either means the "by construction" argument does not hold in this code base. |
| 4 | Make `sigrounds` imply the name filter and switch `memberskip` off; verify identical results; then delete the code listed in section 3.7 and the flags `givencheck`, `memberskip`. | −260 | To do, and only after steps 2b, 2c and 3 pass. Until then `givencheck` and the cycle rule of `extorder` must stay available: they are the only order checks that work when `sigrounds` is off. | Everything again; timing with the method of plan item 0.3. | Type checking of the standard library is more than 2% slower with `sigrounds` than without (expected: not measurable, one round and no restore), or a real library needs more rounds than its depth of dependencies explains. |
| 5 | Documentation: replace `soundness/5-declaration-order.md`; regenerate the INDEX of the declaration-order programs after the designers answer question 1. | – | To do. | – | – |

Steps 2b and 2c are independent of each other and each is behind the existing flag, so no new flag is needed. If a separate flag is wanted for comparison, `sigstrict` could guard both.

## 7. Open questions for the language designers

1. **Are cyclic dependencies between signatures legal when the iteration finds a stable reading?** Program 3 and `tests/05` are accepted by this design and rejected by the current cycle rule. If the answer is no, the rule must be stated on the stable table, for example the component rule of section 2.2 evaluated on it. It cannot be "the table must be stable after two rounds", which would reject Program 1, nor "no declaration may be skipped" in the sense of the current mechanism, which rejects Program 4. If the answer is yes, is "the reading reached from the state where no extension or given of the module is visible" the intended meaning? `tests/09` shows that a program can have two consistent readings; this design rejects it because the table oscillates, but a program with two readings of which only one is reachable would be accepted with that one.
2. **Is the bound part of the language?** A program whose table needs more than `count(nodes) + 2` rounds is rejected. The bound is generous and I know no natural program that reaches it, but it is observable.
3. **May a given see itself?** Today a given is invisible while its own type is computed. In this design it sees its signature of the previous round, like every other given. `tests/14` is rejected either way. A given that is relevant to a resolution in its own header is rejected by `givencheck` today, and here it is rejected only if the table does not stabilize.
4. **Are erroneous givens and extensions invisible?** The table omits a node whose signature contains an error. After `settleSignatures` the existing code still tries such a declaration and fails to match it. The program is rejected in both cases; only the secondary diagnostics differ.
5. **Givens in a function body.** They are visible in the whole body, before their declaration, and the order of two of them is not supposed to matter (`tests/09`). The design treats conformances declared in a body like top-level ones. Is that the intent, or should a local given be visible only after its declaration, like a local binding?
6. **The order of requirements in a where clause stays significant** (`tests/11`, `tests/12`, and `tests/25` for a named requirement), by the existing deliberate rule. Confirm that this is intended; it is a place where textual order still changes a verdict, by design.
7. **Which declaration is blamed in a cycle of aliases** depends on the order (`tests/10`: "definition of 'X' refers to itself" names the alias entered first). The verdict does not. Should the diagnostic name every member?
8. **What is a given whose type is inferred from its initializer worth to the resolutions made by signatures?** (`given let g = e`, `tests/23`, `24`, `28`, `35`.) Its type cannot always be computed before the expression around it is typed. This design never types it while signatures are computed and rejects a program in which a signature's resolution could have seen it; the remedy for the programmer is to write the type. The alternatives are: to keep as nodes the inferred givens declared outside any function or lambda body, and apply the rule to the others only (it accepts `tests/35`, which the rule rejects although the first design accepts it in every order; it types initializers while signatures are computed); to ignore an inferred given silently in signatures (order-independent, but a signature and a body can then resolve the same goal differently); or to require an ascription on every given. Today such a given is typed on demand, which crashes the existing checker on `tests/24`. A related question is number 5: a given *binding* in a function body is a value, and using it before the statement that initializes it is questionable whatever its type.
9. **May a where clause refer to a declaration of the body it governs?** The existing checker accepts `fun f<T where T is P, LA is Q>() { type LA = T.X }`, and a given declared in a function body is visible to the resolutions made by the function's own where clause (`tests/27`). Both follow from how scopes are implemented, and the second is what makes `tests/36` report its error twice today. This design keeps both behaviours and makes them independent of order **[R2]**. If they are accidents, forbidding them would remove the need for the hook of section 3.6 on functions altogether.

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

The review added the following. Its scripts call the binary through `scripts/tcb.sh`, which holds a file lock so that only one `tc-bench` process runs at a time; `run.sh` takes the same lock. `scripts/review_orders.py` is `scripts/orders.py` with the binary chosen by the variable `TCB` (a directory name under `research/exp/bin`) and with configurations such as `FULL+sigrounds+selfcheck`; it records self-check violations and `sigrounds.lateNodes` with the diagnostics.

| Result | Command | Raw data |
|---|---|---|
| Recorded current verdicts of the 23 programs of the first version, run again (46 of 46 identical, diagnostics included) | `TCB=eq9-723cc0e6b0f8 scripts/review_orders.py OUT.jsonl FULL --max 120 --fix K tests/F.hylo`, then `base --max 24`, for each line of `tests/MANIFEST.tsv` | `results/review-tests-eq9.jsonl` |
| The seven programs under FULL, run again (7 of 7 identical) | the same with `--max 60` and the prefixes of `scripts/run-seven.sh` | `results/review-seven-eq9.jsonl` |
| Sections 1.2 to 1.5, run again (identical before Program 4 was replaced) | `scripts/run-problem.sh` | `results/problem.txt` |
| New programs `06b`, `23` to `38`: base and FULL (`eq9`), first design (`eq17`, `FULL+sigrounds+selfcheck`) | `scripts/review_orders.py results/review-new-tests.jsonl CONFIG --max 24 --fix K tests/F.hylo` (60 for `06b`) | `results/review-new-tests.jsonl` |
| The 23 programs of the first version with the first design on `eq17`, up to 6 orders (same verdicts as the coordinator's run on `eq15`, no self-check violation) | as above with `TCB=eq17-4c2982653305 … FULL+sigrounds+selfcheck --max 6` | `results/review-tests-sigrounds.jsonl` |
| Number of rounds of every program of `tests/`, source order, first design without `selfcheck` | `scripts/tcb.sh eq17-4c2982653305 FLAGS --count tests/F.hylo` | `results/review-tests-rounds.txt` |
| The 65 compiler tests that have a node, first design, up to 3 orders | `TCB=eq17-4c2982653305 scripts/review_orders.py OUT.jsonl FULL+sigrounds+selfcheck --max 3 FILE` | `results/review-compilertests-sigrounds.jsonl` |
| Rounds needed by the compiler's tests with the first design | `scripts/review_corpus_rounds.py OUT.jsonl` | `results/review-corpus-rounds.jsonl` |
| Cost on generated programs | `scripts/review_cost.py` | `results/review-cost.txt` |
| One program under base, FULL and the first design | `scripts/review_run3.sh FILE...` | – |

The coordinator's runs of the first design on the declaration-order programs are in `../sigrounds/` (`order-corpus.jsonl`, `tests.jsonl`, binary `eq15`); the review used them to compare the model's predictions with the implementation (section 5.2) and did not repeat them.

## 9. Review

This section was written by the adversarial reviewer of the first version. It says what was checked, what was wrong, which attacks the design withstands and which it does not, and ends with a recommendation. The rest of the document has been edited so that it is a single design; the marks **[R1]**, **[R2]** and **[R3]** show where.

### 9.1 What changed the nature of the review

The first version said that nothing in it had been validated by building the compiler. By the time of the review the coordinator had implemented it as written (commit `cdb3415`, flag `sigrounds`, binaries `eq15` to `eq17`) and run it on its test programs and on the 129 declaration-order programs. The review did not build or modify the compiler; it ran the `eq17` binary. Every statement below about "the first design" is therefore a measurement, and every statement about the corrections is reasoning.

### 9.2 The account of the existing code

Checked against the source and found right: the three ingredients of section 1.1 (forcing in `applies` and `expression(referringTo:)`, skipping, memoizing); the list of soft reads of section 3.5 (every read of a given's type for resolution goes through `givens(visibleFrom:)`, and `applies` is only called from the extension loop); `Module.setType` keeping the first assignment; that `program[module]` and `cache` can be copied and assigned back; the conditions under which `summon` and `applies` memoize (not while an implicit declaration is on the stack), which make the caches of a round consistent with its table.

Found wrong or incomplete:

| | What the first version said | What the code does | Consequence |
|---|---|---|---|
| E1 | The requirements of a where clause have `role == .using`; bindings with `role == .given` are givens. | A named requirement (`where let u: P<T>`) is parsed with `role == .given` (`parseNamedContextParameter`). | The first design puts it in the table: `sigrounds.nodes=3` for `tests/26`; attack 2. It is also typed twice, by the generic path and by `initializeContextParameter`, whose assertion "declaration already initialized" would fail in a debug build. |
| E2 | The signature of every node can be computed before the checks. | The type of a given binding without a complete ascription is inferred from its initializer (`inferredType(of: BindingDeclaration.ID, in:)`), and an initializer can refer to a lambda parameter whose type is only tentative while the lambda is typed, or to a variable bound by a pattern (`declaredType(of: VariableDeclaration.ID)` ends in `unreachable("pattern is not typed")`). | Attack 1. |
| E3 | The hook of section 3.6 restores "the where clause is typed before what it governs". | A where clause can refer to a declaration of the body it governs: a local alias by name, and a given of the body through any resolution (the scope of the body is visible from the where clause). The existing checker types such a declaration from inside the where clause. | Attack 3: two ways into the same cycle. |
| E4 | In `declaredType(of: Given)`, the `.nested` case must read the table for `d`. | There `d` is a `Given`; the proposed line would not compile and is not needed. | None; the implementation left it out. |
| E5 | Program 4 (`tests/06`) is rejected in every order because of forcing. | It is rejected in every order because `Foo<X>.F`, a member selected on a type application, is not accepted as a type expression at all. | The example and the expected verdict of `tests/06` were wrong; `06b` replaces it and does show the point (0 of 60 orders today, 60 of 60 with the first design). The model accepted `06`, so this is also a case where the model is not faithful. |
| E6 | One round for all code available today; cost expected nil. | True for the standard library and the compiler's tests (measured). But any where clause that selects a member through an earlier requirement needs two rounds. | Section 3.8 now gives measured costs. |
| E7 | The index and the abstract model are unavailable during `settleSignatures` because a node is always on the stack. | True for the first design; not once an owner that is a function is computed from the driver (**[R2]**). | Explicit guards, section 3.5. |

Not checked again: the count of qualified names in given and extension headers of section 2.1 (the conclusion it supports, that the strict rule violates nothing in the compiler's tests, was checked by running: no `extorder` or `givencheck` counter in `results/corpus-counters.jsonl`), and the 22,000 random programs of the model (the comparison of the model with the binary was run again and is identical).

### 9.3 Attacks that the first design does not withstand

All verdicts in the first two columns of results were observed; "first design" means binary `eq17` with `FULL,sigrounds,selfcheck`.

| | Program | Existing checker (base, FULL) | First design | Corrected design (predicted) |
|---|---|---|---|---|
| 1 | `tests/23`: `given let g = a` in a lambda whose parameter `a` has no ascription | accepted, 6 of 6 orders | rejected, 6 of 6: "parameter declaration requires an ascription" | accepted: `g` is not a node |
| 1 | `tests/24`: the same with a variable bound by a `match` pattern | base crashes, FULL accepts | crashes: "pattern is not typed" | as without the flag |
| 2 | `tests/25`: `fun f<T where T.X is Q, let u: P<T>>() { given Foo<T.X> is Q {} }` | rejected (requirement order) | accepted; the same function without the given is rejected | rejected |
| 3 | `tests/27`, `27b`: two givens of a function body in either order, the where clause uses a local alias | rejected, both | 27 accepted, 27b rejected; self-check violation on both | accepted, both |
| 3 | `tests/28`: the same entered from a top-level `given let w = f<A>()` | rejected, 24 of 24 orders | accepted in 12 of 24 orders (those with `w` before `f`), rejected in the others; self-check violation in all | rejected in every order (the type of `w` must be written); with an ascription, accepted in every order |

Attack 3 on `tests/28` is a failure of the acceptance test itself: a verdict that depends on the order of top-level declarations, on a program whose verdict does not depend on it today. It needs three things at once: a given without ascription whose initializer calls a generic function, a where clause that names a local alias, and a given in the body that uses the alias. That is far from ordinary code, but "by construction" does not allow exceptions, and the mechanism at fault, the hook, was added by the design.

What each attack has in common: the first design computes, before the checks and in an order of its own, things that the existing checker only computes inside their context. The model has none of the constructs involved, which is why 22,000 random programs did not find them.

### 9.4 Attacks that the design withstands

- **A hard cycle entered at two points** (`tests/30`, `31`): once the table says that `extension X { type M = Self }` extends `A`, the alias `X` and the extension depend on each other through hard reads. The cycle can be entered at the alias or at the extension. Assumption A4 says the table does not depend on which; it holds because a candidate with an erroneous type makes a lookup ambiguous instead of being dropped. 24 orders, one outcome, no self-check violation.
- **A declaration that sees itself** (`tests/29`): rejected in every order because the table oscillates; FULL rejects it too, base accepts it.
- **A conformance in a lambda** (`tests/32`), **a named requirement used in the right order** (`tests/26`), **a requirement in the wrong order with a given in the body** (`tests/36`): verdicts unchanged.
- **Attack 3 through a member instead of a local alias** (`tests/37`, `37b`): a conformance of a function body, with a where clause, that shadows a top-level one for the lookup made by its own where clause. Both orders are accepted and the hook does not fire, because the associated type of a conformance with a where clause is not reduced to its implementation. FULL rejects both ("circular given"), base accepts both.
- **Long chains** (`tests/33` and generated chains up to 17 nodes): accepted, `n + 1` rounds, never more than the bound.
- **Restore completeness (A2)**: the self-check of the stable round reports no violation on any program of `tests/`, except the three programs of attack 3, where the cause is A3 and not the restore, and `tests/38`, where it is a false alarm of the check itself (it compares which alias of a cycle is blamed; section 3.4); nor on the 129 declaration-order programs (coordinator).
- **The declaration-order fuzzer**: on the 129 declaration-order programs, no verdict depends on the order (coordinator). On the 65 programs of `Tests/CompilerTests` that have a node, in up to 3 orders each (185 runs with `selfcheck`, `results/review-compilertests-sigrounds.jsonl`): one verdict per program and no self-check violation, except `positive/inlining-with-extensions.hylo`, where the splitter separates the line `@inline(always)` from its declaration and the two permuted orders are syntax errors. The 127 programs without a node are not affected by the flag.
- **The verdicts of `Tests/CompilerTests`**: 192 of 192 unchanged, at most one round.
- **The model's predictions**: 74 of 77, the 3 others being errors of the model that the first version had already identified.
- **The recorded current verdicts**: 46 of 46, 7 of 7, and the problem tables, reproduced.

### 9.5 What the corrected design does not withstand, or leaves open

1. **It is not implemented.** Steps 2b, 2c and 3 of section 6 are about 85 lines. The predictions of the last column of 9.3 must be measured.
2. **A3 is still an assumption.** **[R2]** closes the way into a function body. For a member of an extension or conformance selected through the table, the hook remains, and with it the theoretical possibility of two ways into a cycle (section 3.6). I could not write such a program: every attempt needs the extension to be in the table before the lookup that puts it there succeeds. The safeguard is the self-check, which did catch attack 3 unprompted.
3. **It rejects `tests/35`**, which the first design accepts in every order and the existing checker in 16 of 24: a given without a written type that a signature's resolution can see. The rule is the simplest sound one and its scope is empty in every corpus available, but it is a new rejection and a language decision. Question 8 gives the alternative that accepts this program; it was not chosen because it types initializers while signatures are computed, which is the kind of out-of-context evaluation that attacks 1 and 3 used.
4. **It rejects programs that the existing checker accepts in every order with an order-dependent meaning.** `tests/09` without its last statement is accepted by base and FULL in both orders, with `A.E` meaning `Bool` in one and `Int` in the other; the first design rejects both ("no stable interpretation"). This is intended, and it is the right direction, but it is a change from accepted to rejected.
5. **Completeness is not claimed** (section 4.1): a program with a single consistent reading that the iteration does not reach is rejected, as is one that needs more than `count(nodes) + 2` rounds.
6. **Order inside function bodies is outside the fuzzer.** Three pairs of test programs cover it; a fuzzer that permutes the declarations of a body would be the proper test.
7. **Cost on real code is unknown.** Two rounds are the expected case for a generic library, and the index of givens is unavailable during the rounds. Measured only as counters on generated programs.
8. **The crash of base on `tests/24`** is a defect of the existing checker (a given typed on demand before the pattern that binds its initializer's variable). The corrected design does not introduce it and does not fix it when the flag is used without `index`.
9. **The self-check gives a false alarm on cycles of aliases** (`tests/38`) until the comparison of diagnostics is normalised (section 3.4). Until then a violation reported on a program whose only errors are "refers to itself" must be read with care, and the fuzzer cannot require "no violation" on such programs.

### 9.6 What the estimate of lines left out

The first version estimated 150 lines for the mechanism and 200 with counters and assertions. The implementation of steps 0 and 2 is about 175 lines without the assertions for A1, A4 and A7. Left out: the distinction between context parameters, inferred givens and nodes (30 lines), owners first and the guards on the index and the abstract model (15), the self-check of every round and the missing assertions (40). The total is about 260 lines added, for the same 260 removable at step 4.

### 9.7 Recommendation

**Implement as designed in this revised document**: keep the implementation of the first design, and apply steps 2b (**[R1]**), 2c (**[R2]**) and 3 (**[R3]**) before relying on it.

- Reason for going on: the mechanism is the only one of the three options that accepts cycle-free programs such as Programs 1 and 4, and on everything the first version had considered it behaves as predicted, on the implementation: no order-dependent verdict on the 129 declaration-order programs, on the 65 compiler tests that have a node, or on the 42 programs of `tests/` outside attack 3; no changed verdict in the compiler's tests; one round for the standard library.
- Reason for not stopping at the first design: it rejects a legal program, crashes on another, accepts a program that a deliberate rule rejects, and has an order-dependent verdict that the existing checker does not have. Each has a local correction that removes its cause and does not touch the round mechanism.
- Conditions. Until steps 2b, 2c and 3 pass on `tests/23` to `28`, `35` and `36` and on the fuzzer under `selfcheck`: do not add `sigrounds` to FIX or FULL, and do not carry out step 4 (the deletion of `givencheck`, of the cycle rule of `extorder` and of `memberskip`). If, after the corrections, the self-check reports a violation of A3 on a program that is not of the kind described in section 3.6, the "by construction" claim does not hold in this code base, and the fallback is option (a1), the strict rule, which needs no such assumption and violates nothing in the code available today.
