# 6. Associated types of a generic conformance are one type for every instance

**Status:** fixed by `assocsubst`. The defect is in the existing implementation; it was found by differential testing against an independent reference resolver.

## Symptom

```hylo
trait P { type X; fun get() -> X; fun put(x: X) }
struct A { public memberwise init }
struct C { public memberwise init }
given <T> => T is P {
  type X = T
  fun get() -> T { self }
  fun put(x: T) {}
}
fun q(a: A, c: C) { c.put(a.get()) }    // accepted: an `A` reaches code that expects a `C`
```

The same holds for a conformance of a generic type, `given <T> => Box<T> is P { type X = T }`: `Box<A>.X` and `Box<C>.X` are accepted as the same type. Conversely `Box<A>.X` is not accepted where an `A` is expected, so valid programs are rejected as well.

## Cause

The associated type of a conformance is read from the declaration `type X = T` inside it, as written. `T` is the conformance's own type parameter. The witness that resolution found for `Box<A> is P` is the conformance *applied to* `A`, but its type arguments were not substituted into the definition. Every instance of the conformance therefore had the associated type `T`, equal to itself and to nothing else.

The path that reads members of generic *extensions* does substitute the type arguments; the path for conformances did not.

## Fix

When the associated type is read through a witness that applies a conformance to arguments, the arguments are substituted into the definition (`Typer.typeOfImplementation(satisfying:in:)`):

- the **type arguments** replace the conformance's type parameters, also inside the aliased type of a type alias, which the general substitution leaves alone;
- for a conditional conformance, the **witnesses of its requirements** replace the references to those requirements. With `given <T where T is Q> => Box<T> is P { type X = T.Y }`, `Box<A>.X` is `A.Y` *through the conformance of `A` to `Q` that the witness contains*, and is then reduced to its definition. Without this second substitution `Box<A>.X` is one type whatever conformance `A` has, which matters as soon as two scopes see different conformances.

After the fix, in the example, `a.get()` has type `A` and `c.put` expects a `C`: the call is rejected. `Box<A>.X` is `A`.

Two related cases are handled with it:

- A conformance required by a trait (`trait R refines P`) defines nothing. The associated type selected through it is the one selected through that very witness; before, it stayed a selection through "the witness of the trait", equal for every witness of the same type.
- An instantiated associated type can mention a generic parameter of the requirement being typed (inside a generic method that calls itself at another type). The bound parameters of the requirement are renamed first, since substitution is not capture-avoiding.

About 110 lines in all.

## Effect on existing code

None of the compiler's tests and none of the standard library declares an associated type in a generic conformance, so no result changes there. The reference-testing campaign's 43 unsound acceptances and 12 related ones are all of this kind and are all rejected with the fix (`follow-up/reference/`).

## What remains

A struct declared *inside* a generic conformance or a generic type is one type for all instances, because nested nominal types do not capture the parameters of the declaration that contains them (`follow-up/attack-assoc/p/a13-struct-in-conformance.hylo`). This is a property of the front end outside the mechanisms studied here.

A conformance parameter that neither the head nor a requirement determines (`given <T, U> => Box<T> is P { type X = U }`) gives a fresh type at each use, without a diagnostic at the declaration.

## Programs

`follow-up/reference/hand/blanket-*.hylo`, `follow-up/reference/judge/p/u1-*.hylo`, `follow-up/attack-assoc/p/a*.hylo` and `c*.hylo`.
