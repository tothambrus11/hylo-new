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

When the associated type is read through a witness that applies a conformance to type arguments, the arguments are substituted into the definition (`Typer.typeOfImplementation(satisfying:in:)`). The substitution also rewrites the aliased type of a type alias, which the general substitution leaves alone (`TypeStore.substituteThroughAliases`). About 45 lines.

After the fix, in the example, `a.get()` has type `A` and `c.put` expects a `C`: the call is rejected. `Box<A>.X` is `A`.

## Effect on existing code

None of the compiler's tests and none of the standard library declares an associated type in a generic conformance, so no result changes there. The reference-testing campaign's 43 unsound acceptances and 12 related ones are all of this kind and are all rejected with the fix (`follow-up/reference/`).

## Programs

`follow-up/reference/hand/blanket-*.hylo`, `follow-up/reference/judge/p/u1-*.hylo`.
