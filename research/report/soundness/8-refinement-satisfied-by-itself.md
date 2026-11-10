# 8. A conformance satisfies the trait it refines with itself

**Status:** fixed by `hidecache`. The defect is in the existing implementation; it was found by the adversarial review of the order-independence mechanism.

## Symptom

```hylo
trait Base { fun f() }
trait Derived refines Base { fun g() }
struct B { public memberwise init }
given B is Derived {
  public fun g() { self.f() }
}
fun callBase<T where T is Base>(x: T) { x.f() }
fun callDerived<T where T is Derived>(x: T) { callBase(x) }
public fun main() { callDerived(B()) }     // accepted: calls `Base.f` on a `B`, which has none
```

`B is Derived` requires `B is Base`, which nothing provides. The same program with an empty body for `g` is rejected: "no given instance of 'Base<B>' in this scope".

## Cause

A conformance must not use itself to satisfy the traits it refines, so it is hidden while that requirement is checked. But the members of the conformance are checked first, and the body of `g` resolves `Base<B>` with the conformance visible: the answer "through `B is Derived` itself" is memoized for the scope of the conformance. The later check, made with the conformance hidden, asks the same question in the same scope and gets the memoized answer without looking at what is hidden.

## Fix

The memo of resolutions is not read while a given is deliberately hidden (`Typer.summon(_:in:)`). It was already not written in that situation. Five lines.

## Effect

The example is rejected, as its twin without a body. No program of the compiler's tests changes.

## Programs

`follow-up/attack-sigrounds/p/q03*.hylo`, `q04*.hylo`.
