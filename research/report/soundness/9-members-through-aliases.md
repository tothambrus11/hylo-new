# 9. Members selected through an alias lose the type arguments

**Status:** fixed by `aliasargs`. The defect is in the existing implementation; it was found by metamorphic testing.

## Symptom

```hylo
struct K {}
struct A<U> {
  public fun f(x: U) {}
  public fun g() -> U { self.g() }
}
type AV = A<Void>
type AK = A<K>
fun use(a: AV, b: AK) { a.f(b.g()) }     // accepted: a `K` is passed where a `Void` is expected
```

Written with `A<Void>` and `A<K>` instead of the aliases, the call is rejected.

A member that is itself a type alias has the same problem without any alias at the use: with `struct Box<T> { type Elem = T }`, `Box<A>.Elem` and `Box<C>.Elem` are one type.

## Cause

A member found on an instance of a generic type must have the type's parameters replaced by the arguments of the instance. The replacement was made only when the type of the receiver was written as an application; through an alias the member kept the struct's own parameter `U`, which is equal to itself. For a member alias, the substitution did not reach the aliased type.

## Fix

The receiver's type is stripped of aliases before its arguments are read, and the substitution rewrites the aliased type of member aliases (`Typer.resolve(_:nativeMemberOf:statically:)`, and the members of extensions). About 15 lines.

## What remains

An alias of a *generic* type applied to arguments (`type AB<T> = Box<T>`, then `AB<A>`) is still not interchangeable with `Box<A>` in the heads of givens and extensions: such a program is rejected, not wrongly accepted.

## Programs

`follow-up/metamorphic/judge/progs/alias-args-*.hylo`, `follow-up/attack-assoc/p/a14*.hylo`.
