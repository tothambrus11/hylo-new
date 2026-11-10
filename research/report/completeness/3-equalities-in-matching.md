# 3. Equalities that matching does not use

**Flags:** `eqfilter`, `eqouter`, `eqclass`. Experiments: sound, but they change which givens match. About 170 lines.

## Symptom

The equality procedure decides whether two closed types are equal under the equalities in scope. Matching a given against a goal consults it in a restricted way, so three kinds of valid programs are rejected:

```hylo
// (a) A type equal by transitivity and congruence, but not written in an equality
fun a<T, U where T == A, U == Box<T>>(x: U) { check<Box<A>>(x) }

// (b) An equality between compound types, needed above the innermost difference
given Box<A> is P {}
fun b<T where Box<A> == Box<T>>() { need<Box<T>>() }

// (c) A generic conformance, for a type equal to an instance of its head
given <X> => Box<X> is P {}
fun c<T, U where T == Box<U>>() { need<T>() }
```

In the reference-testing campaign, 735 of 9,975 goals with exactly one derivation (7.4%) are rejected for these reasons, by the existing and by the revised implementation alike.

## Cause

When the type of a given and a goal have the same shape, matching descends to the innermost positions at which they differ and asks, for each such pair, whether an equality could relate them.

- The test is syntactic: both types of the pair must be written as a side of some equality in scope. In (a), `Box<A>` is not.
- Only the innermost pair is asked. In (b) the innermost pair is `(A, T)`, which is not derivable without injectivity of `Box`; the enclosing pair `(Box<A>, Box<T>)` is the stated equality.
- A pair in which one side still has unification variables never passes. In (c) the pair is `(Box<?x>, T)`.

## What the three flags do

- **`eqfilter`.** A closed pair also passes if the equality procedure proves it.
- **`eqouter`.** When an innermost pair does not pass, the outermost enclosing pairs that do are used instead, for type applications and tuples. The pair of the two whole types is excluded, as today.
- **`eqclass`.** When one side of a pair has unification variables, it is instantiated with each type written in an equality in scope that it unifies with and that may be equal to the other side. Each instance is matched again; the remaining pair is closed and is handled as usual.

In every case the pair is still assumed and then proved by the existing mechanism. The flags add candidates; they never accept a match without the proof. No program is accepted that the equality theory does not justify.

## What changes

- All six "gain" programs of the equality design and all nine minimized incompleteness programs of the reference campaign are accepted (`follow-up/design-eqnorm/tests/gain-*.hylo`, `follow-up/reference/minimized/inc-*.hylo`).
- A given that could not match before can match now. In constructed programs this turns an accepted use into an ambiguity (`attack-08`: two written members of one equality class with equal arguments) or selects another conformance without a diagnostic (`attack-07`). No such change occurs in the compiler's tests.

## Why these are experiments

Hylo selects a conformance by the way a type is written: with `T == U`, `T is P` and `U is P`, the types `T.X` and `U.X` differ. A mechanism that lets more givens match through equalities must choose a spelling for the instantiated variables, and any deterministic choice either depends on the order of the where clause or reports ambiguities that a user may not expect. The design chooses the ambiguity. Whether that is acceptable, or whether conformances should be coherent across equal types (which would make a true normal form possible), is the first question of `../follow-up/designs/eqnorm.md`.

## Programs

`follow-up/design-eqnorm/tests/`, `follow-up/reference/minimized/`, `follow-up/reference/judge/p/i*.hylo`.
