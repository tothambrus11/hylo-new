# Approaches that do not work

Each of these is faster, and each changes results, so none is used. They are recorded because each fails for a reason that also constrains future work.

## Skip extensions without the looked-up name, unconditionally

**Idea.** In a member lookup, skip every extension that declares no member with the name looked up, before checking whether it applies.

**Why it fails.** Checking whether an extension applies is not a pure query. It forces the computation of the extension's extended type, and sometimes of given types. Those results are remembered, including results computed while some declaration is hidden from lookups. Skipping the check changes which lookup computes a type first, and so changes the results of programs whose extensions depend on each other: several were accepted where they had been rejected, and the other way round.

**What works instead.** `memberskip` skips only checks whose every input is already computed.

## Prune a goal that repeats one of its ancestors (loop check)

**Idea.** In a smallest proof, no goal repeats one of its ancestors, since the ancestor could use the repeated goal's proof directly (Bol, Apt and Klop, 1991). So repeated goals could be pruned.

**Why it fails.** The argument assumes plain logic-programming search. Hylo lets the pending requirements of a given serve as assumptions for its other requirements, ranks proofs by search layer and penalty, and reports ties as ambiguity. With a pending requirement in play, the repeated goal can be *cheaper* than its ancestor. Pruning it changed the chosen proof, lost proofs found within the depth cap, and hid ambiguities.

**What works instead.** The abstract model (`absmodel`) handles every looping case without that assumption.

## Delay overload choices and try the most constrained first

**Idea.** In overload resolution, set aside overloaded calls until the rest is solved, and branch first on the call with the fewest viable candidates. That turns `kⁿ` combinations into roughly `k·n`.

**Why it fails.** The order in which the solver branches and ranks overloads is part of the meaning of a program: it decides which solution is preferred, and which ambiguities are reported. Changing the order flipped acceptance in both directions and changed inferred types.

**Way forward.** Resolve each overload set where the existing solver would. Probe each candidate only up to the next overload set, so that the probe's error count bounds the candidate from below. Commit to a sole survivor, and otherwise branch in the original order.

## Refute equalities by grouping types into classes, without congruence

**Idea.** Put the types related by equality facts into classes, and reject an equality between two types of different classes.

**Why it fails.** It rejected a valid program: inside a trait, `Self.X` is equal to `T.X` when `T == Self`, through the trait's own associated type, which simple grouping cannot see. Congruence closure, with the rule for `Self` described in `techniques/eqsolve.md`, handles it.

## Undo every result computed during a cyclic lookup

**Idea.** Fix the order-dependence of issue 5 by evaluating each lookup that may run into a cycle as a transaction, and rolling back everything it computed if it does.

**Why it fails.** It accepted a program that is ambiguous by the checker's own rules, and its verdict still depended on order. Rolling back was also expensive, and the same work was repeated. The record-and-check rule of `extorder` and `givencheck` replaces it.

## Cache coercion checks made under assumptions

**Idea.** Remember whether a coercion can be derived, also when the current proof has assumptions, keyed by those assumptions.

**Result.** Correct, but no faster. The cached checks were already cheap, and the cost of equality reasoning was in the search itself, which `eqsolve` removes.
