# 2. Associated types of a requirement in a signature

**Flag:** `headsubst`. About 150 lines. Needs `premsubst` only for the shared recording of binders.

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

In addition, two associated types selected through the *same* declared witness unify when the types of the witness do, which is needed while type arguments are still being inferred.

In the example: `pick(a)` infers `T = A`, elaborates `pick<A>(c)` where `c` is the conformance of `A`, and equates the result with `(A::c).X = C`. In `g`, the witness is the caller's requirement, and the parameter type becomes the caller's `U.X`.

## Why it is correct

The equation added for each variable is the dependent reading of the signature: the parameter type `T.X` of a call that passes the witness `w` for `T is P` is the associated type selected through `w`. The witness is the one in the elaborated call, so the types the callee's body relies on are those the caller provides. Nothing is assumed about uniqueness of conformances: if the caller's scope has a nearer conformance of `A` to `P`, that one is passed, and its associated type is the one used.

If the callee cannot be elaborated, the variables stay unresolved and the call is reported as before.

## What changes

All twelve programs of `follow-up/headsubst/tests` behave as expected: eight valid calls are accepted (concrete and generic callers, parameters and results, nested projections such as `Box<T.X>`, two requirements, a generic conformance, an equality on the projection, a chain `use(u, pick(u))`), and four invalid ones are rejected (a wrong argument type, swapped arguments, another conformance of an equal type, a wrong instance of a generic conformance).

The semantic dump of the compiler's tests is unchanged: no signature there mentions an associated type of a requirement in a function that is called.

## Limits

- Calls only. A reference to a generic function that is not called at once, and the members of extensions and conformances with dependent requirements in their *head* (`given <T where T is P> => Box<T.X> is Q`), are not covered.
- This mechanism was designed and implemented without an independent design document; it is the least reviewed of the new mechanisms. An adversarial review is reported in `../follow-up/attacks/`.

## Programs

`follow-up/headsubst/tests/`, `follow-up/reference/judge/p/u1-call*.hylo`.
