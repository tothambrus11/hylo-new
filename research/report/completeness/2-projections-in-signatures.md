# 2. Associated types of a requirement in a signature

**Flag:** `headsubst`. About 330 lines. It shares the recording of binders with `premsubst`.

## Symptom

```hylo
trait P { type X; fun get() -> X }
struct A { public memberwise init }
struct C { public memberwise init }
given A is P { type X = C
  fun get() -> C { C() } }

fun pick<T where T is P>(t: T) -> T.X { t.get() }
fun use<T where T is P>(t: T, x: T.X) {}

fun q(a: A, c: C) {
  let r: C = pick(a)     // rejected
  use(a, c)              // rejected
}
fun g<U where U is P>(u: U, y: U.X) {
  use<U>(u, y)           // rejected: "cannot pass value of type '(U::P).X' to parameter '(U::P).X'"
}
```

Any generic function whose parameters or result mention an associated type of one of its own requirements cannot be called, with a concrete or with a generic argument.

## Cause

The type of `use` is `<T> P<T> ==> (T, (T::$u).X) -> Void`, where `$u` is the declaration of the requirement `T is P`. The constraint solver opens this type before the witness of the requirement is known and checks the arguments against a parameter type that still names the callee's private declaration `$u`. The witness that resolution later finds for `T is P` is never fed back. The caller's `U.X` is selected through the caller's requirement, a different term; for a concrete `A`, `(A::$u).X` is never reduced to `C`.

## Fix

1. The type of a function records the declaration through which its parameters and result refer to each requirement (the binders of `premsubst`, extended to the head).
2. When the solver decomposes a call, every associated type in the callee's parameters and result that is selected through one of these declarations is replaced by a fresh type variable. The callee itself is still elaborated against its unmodified type.
3. When the elaboration of the callee succeeds, it contains one witness per requirement. Each variable is then equated with the associated type selected through the witness passed for its requirement, reduced to its definition if that witness is a conformance declaration.
4. An argument is not coerced to such a variable before the variable is resolved, so that an equality in the caller's scope (`U.X == B`) can still be used.

In addition, two associated types selected through the *same* declared witness unify when the types of the witness are syntactically equal up to open variables, which is needed while type arguments are still being inferred. (Equal up to an equality in scope is not enough: one requirement instantiated at two equal types is two witnesses.)

The same substitution is applied in two other places where a type written in terms of a declaration's requirements is used through a witness:

- **Members of extensions.** A member of `extension <T where T is P> Box<T>` is written in terms of the extension's requirement. When the extension is found to apply, the witnesses of its requirements are substituted into the member's type, with its type arguments.
- **Heads of givens and extensions.** For `given <T where T is P> => Holder<T.X> is Q`, the head mentions the requirement. When the given is matched against a goal `Holder<A.X> is Q` in which `A.X` is selected through a known witness, that match decides the requirement: it is proved by that witness.

Requirements are substituted in order, so that chains such as `T.X.X` under `T is P, T.X is P` resolve.

In the example: `pick(a)` infers `T = A`, elaborates `pick<A>(c)` where `c` is the conformance of `A`, and equates the result with `(A::c).X = C`. In `g`, the witness is the caller's requirement, and the parameter type becomes the caller's `U.X`.

## Why it is correct

The equation added for each variable is the dependent reading of the signature: the parameter type `T.X` of a call that passes the witness `w` for `T is P` is the associated type selected through `w`. The witness is the one in the elaborated call, so the types the callee's body relies on are those the caller provides. Nothing is assumed about uniqueness of conformances: if the caller's scope has a nearer conformance of `A` to `P`, that one is passed, and its associated type is the one used.

If the callee cannot be elaborated, the variables stay unresolved and the call is reported as before.

## What changes

All programs of `follow-up/headsubst/tests` behave as expected: the valid calls are accepted (concrete and generic callers, parameters and results, nested projections such as `Box<T.X>`, two requirements, a generic conformance, an equality on the projection, a chain `use(u, pick(u))`), and the invalid ones are rejected (a wrong argument type, a wrong result annotation, swapped arguments, another conformance of an equal type, a wrong instance of a generic conformance).

Four patterns translated from the Swift and Rust standard libraries that the revised implementation rejected are accepted with `premsubst` and `headsubst` (`follow-up/usage/benchmarks/`): the Rust `Flatten` iterator, a conformance conditioned on an associated type of its parameter, a conformance with two equality conditions, and member lookup through a given that a trait declares on its associated type.

The semantic dump of the compiler's tests is unchanged: no signature there mentions an associated type of a requirement in a function that is called.

## What the review found

The first implementation's unification rule for selections through one declared witness compared the witness types up to the equalities in scope. Members of an extension of the conforming types then converted `W.X` into `V.X` under `V == W`, the conversion that `../soundness/7-self-projection.md` closes; the rule is now syntactic. The same review found that an elaboration that cannot be decomposed left the associated types selected through the callee's own requirements, which made them equal across calls; they are now erroneous, and the equalities that resolve them are subgoals of the callee's coercion, so that a failure is always diagnosed.

## Limits

- A reference to a generic function that is not called at once is not covered.
- A variable that would be assigned a type mentioning an undecided premise fails the match; such a goal is rejected where the liberal rule of the existing implementation accepted it.
- This mechanism was designed and implemented without an independent design document. Its adversarial reviews are in `../follow-up/attack-assoc/` and `../follow-up/attack-headsubst/`.

## Programs

`follow-up/headsubst/tests/`, `follow-up/reference/judge/p/u1-call*.hylo`.
