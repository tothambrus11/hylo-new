# Equality decision procedure (`eqsolve`)

**Kind:** speed-up and correctness fix. Required by `fixsubst`.

## Problem

The checker proves equalities between types the same way it proves conformances: by searching, here through the built-in reflexivity, symmetry and transitivity rules and the equality facts in scope. Symmetry and transitivity each open new goals with unknown middle types, so proving `T0 == T3` from a chain `T0 == T1, T1 == T2, T2 == T3` is exponential in the length of the chain. It also needs about two search steps per link, so from five links on the 10-step cap is exceeded and valid programs are rejected:

```hylo
fun f<T0, T1, T2, T3 where T0 == T1, T1 == T2, T2 == T3, T0 is P>(x: T3.X) {
  g<T3>()
  check<T0.X>(x)
}
```

With eight links this takes 1.1 s.

## How it works

When a goal is an equality `A ~ B` with no unknowns:

1. **Facts.** Collect the equality facts in force: those assumed in the current proof, then those visible from the scope. Each fact records the penalty the search would charge for using it.
2. **Shortcut.** If `A` and `B` are identical after expanding aliases, answer with reflexivity.
3. **Term graph.** Every subterm of the goal and the facts becomes a node. A compound node records its constructor and attributes: arity, function style and effects, parameter labels and access. Its children are its parts.
4. **Congruence closure.** Merge the two sides of each fact, then repeatedly merge any two compound nodes whose constructors agree and whose children are already merged (`Box<A>` and `Box<B>` once `A` and `B` are). A signature table and use lists make this `O(n log n)` (Nelson–Oppen, Downey–Sethi–Tarjan).
5. **Associated types.** These need two additional rules, described below.
6. **Answer.** If `A` and `B` are in different classes, the goal fails immediately. Otherwise a proof is built from the cheapest path between them in the graph. It uses the facts, symmetry for facts used backwards, transitivity to chain them, and a coercion for each congruence step. Edges are weighted with the penalties the search would charge, so when several proofs exist, the checker chooses among them as it did before.

### Associated types

**Through a concrete conformance.** A type like `(T::w).X`, the associated type `X` of `T` through the conformance `w`, is an atom. It equals another type only through facts.

**Abstract (`Self.X`).** Inside a trait, `Self.X` is the trait's own, abstract associated type. Two rules of the language pull in different directions:
- `Self.X` equals `T.X` when `T == Self` (accepted test `v-abs-7`);
- `T.X` and `U.X` from two different conformances are different, even if `T == U` (negative test `associated-type-inequality`).

Applying the first rule freely gives `T.X == Self.X == U.X` whenever `T == Self` and `U == Self`, which contradicts the second. So `Self.X` is equated with `T.X` only if the scope has **exactly one** conformance to the trait for a type equal to `Self`, and no generic or conditional conformance to it. This is decided from the scope's own declarations, never from the goal or from temporary assumptions. The answer is therefore the same everywhere in the scope, and assuming more never takes a conclusion back.

**Through a requirement not yet proved.** A caller may meet `T.Element` through a callee's requirement `T is Collection` that has not been proved yet; such requirements are proved in reverse order. That `T.Element` is identified with the one through the witness that *will* prove the requirement, under two conditions:
- resolving `T is Collection` in the environment where the requirement will be proved has exactly one answer;
- nothing involved is still unknown.

Resolution is deterministic, so that answer is the witness that will actually be used. If the condition does not hold, the projection stays an atom, and a "not equal" verdict that depends on it is not trusted: the search decides instead.

## Why it is correct

**Decidability.** Equality of closed terms under finitely many closed equations is decidable, and congruence closure decides it. The search uses no injectivity rule (`Box<A> == Box<B>` does not give `A == B`), and the procedure uses none either, so it decides exactly the theory the search explores, up to the depth cap.

**Undecidable or expensive cases are left to the search**, which behaves as before:
- the goal has unknowns (rigid E-unification);
- an equality given is generic or conditional (the word problem);
- a given could prove anything.

**Temporary assumptions.** The equalities assumed in a proof are facts only within that proof, and each must itself be proved before the proof is accepted.

**Proof terms.** Each step is checked against the type it must have. Symmetry, in particular, is instantiated with its arguments in the right order.

## What it speeds up

| Program | Without | With |
|---|---:|---:|
| chain of 8 equalities | 1.1 s | 7.5 ms |
| equalities between associated types (8) | 2.7 s | 92 ms |
| many coercions through equalities | 2.2 s | 12 ms |
| 31 equalities between 32-element tuples | out of memory | 64 ms |
| ill-typed equality chain (8) | 2.5 s, wrongly accepted | 79 ms, rejected |
| conditional extension `where T.Element == Flag` | 1.4 s | 17 ms |

## Cost

A small graph per closed equality goal, linear-logarithmic in the size of the equalities in scope. Resolving a pending requirement ahead of time costs one nested resolution, with nesting limited to depth 2.
