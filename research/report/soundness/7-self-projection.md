# 7. Inside a trait, `Self.X` is equated with another witness's `T.X`

**Status:** fixed by `abstractstrict`. The rule is in the existing implementation's unifier; the equality procedure had been written to agree with it. Whether the stricter behaviour is the intended one is a question for the language designers, discussed below.

## Symptom

```hylo
fun conv<A, B where A == B>(x: A) -> B { x }
fun check<T>(x: T) {}
trait P {
  type X
  fun cast<T, U where T == Self, T is P, T.X == U>(x: U) -> X { conv<U, X>(x) }
}
fun f<V, W where V == W, V is P, W is P>(v: V, x: W.X) {
  check<V.X>(v.cast<W, W.X>(x))       // accepted: a `W.X` is used as a `V.X`
}
```

The function `f` has the where clause of the compiler's negative test `associated-type-inequality.hylo`, which states that `V.X` and `W.X` are different types even though `V == W`: the two requirements `V is P` and `W is P` are two witnesses, which may define `X` differently. The program above performs that conversion through a method of the trait.

## Cause

Inside a trait `P`, `Self.X` denotes the associated type selected through the witness that the trait itself stands for. The unifier treated a selection through that witness as equal to a selection of `X` through *any* witness, provided the two types were equal:

- in `cast`, `T == Self` and `T is P` are requirements, so `Self.X` was unified with `T.X`;
- the caller chooses the witness of `T is P` independently of the witness of `Self`.

The equality procedure (`eqsolve`) contained the same rule in a narrower form (when the scope has exactly one conformance for a type equal to `Self`), which is what lets the whole program through; the existing implementation accepts the definition of `cast` alone.

## Fix

A selection through the witness that a trait or conformance declares is equal only to a selection through that same witness, at the same type (`TypeStore.unifiable` for associated types; the rule of the equality procedure is removed, and such selections are atoms for it). Two witness expressions are "the same" only if their types are syntactically equal up to open variables, not up to an equality in scope: one requirement instantiated at two equal types is two witnesses.

The liberal rule also did real work, which is now done explicitly:

- **A given declared in a trait about its associated type** (`trait P { type X; given X is Q }`) has the type "for every `Self` with a witness of `P`, `Self.X is Q`", where `Self.X` is selected through that witness. When such a given is matched against a goal `T.X is Q` in which `T.X` is selected through a known witness `w`, that match *decides* the premise: it is `w`. No other choice makes the two types equal.
- **A member of an extension** `extension <T where T is P> T { fun twice(x: T.X) }` used inside the trait at `T = Self` has its `T.X` replaced by the selection through the witness that made the extension apply, here the trait's own (see `../completeness/2-projections-in-signatures.md`).

A requirement `T == Self` without `T is P` still makes `T.X` available: resolution finds `T is P` from the trait's own witness, transported along the equality, and that selection is the same witness. Only the case with a *second* witness changes.

## What is rejected now

Seven programs of `test-programs/equalities` and one of `test-programs/cycles-and-crashes` that the existing and the revised implementation accepted. All have the shape

```hylo
trait P {
  type X
  fun f<T where T == Self, T is P>(x: X) { check<T.X>(x) }
}
```

that is, a second witness `T is P` for a type equal to `Self`. Each is the conversion that the negative test forbids, written inside a trait.

## The language question

If conformances were *coherent* (at most one conformance of a type to a trait, across equal types), `Self.X` and `T.X` would be the same type here, and so would `V.X` and `W.X` in the negative test. The compiler's tests say they are not. The fix follows the tests. If the designers choose coherence instead, the negative test changes and this rule, with several others, can be relaxed (`follow-up/designs/eqnorm.md`, question 1).

## Programs

`follow-up/reference/hand/self/`, `follow-up/reference/judge/p/u2-*.hylo`, `test-programs/equalities/v-abs-*.hylo`.
