# Valid programs that were rejected

The soundness fixes make the checker reject programs it should not accept. This folder is about the opposite failure: ordinary generic programs that the existing implementation rejects although they are well typed. They were found while designing the engine improvements and by testing against an independent reference resolver. Each is now accepted behind a flag.

| Problem | Example of a program that was rejected | Flag | Document |
|---|---|---|---|
| A requirement on an associated type of another requirement can never be satisfied by a caller | `fun f<T where T is P, T.X is Q>()` called from a function with the same requirements | `premsubst` | `1-dependent-requirements.md` |
| An associated type of a requirement in a signature is not the caller's associated type | `fun first<T where T is P>(t: T) -> T.X` applied to a value of a concrete type | `headsubst` | `2-projections-in-signatures.md` |
| An equality is used only if both of its sides are written and only at the innermost mismatch | `where T == Box<U>` with `given <X> => Box<X> is P` and a need for `T is P` | `eqfilter`, `eqouter`, `eqclass` (experiments) | `3-equalities-in-matching.md` |

The first two are fixes: they implement the dependent reading of a where clause, which the language already has for equalities in simple cases. The third group changes which givens match and therefore, in a few constructed programs, which conformance is selected or whether a use is ambiguous; it needs a decision from the language designers before it is adopted.

Together with `assocsubst` (`../soundness/6-generic-conformance-associated-types.md`), the first two make the following program type-check. The existing implementation rejects every call in it.

```hylo
trait Collection { type Element; fun first() -> Element }
trait Showable {}
struct Bag<T> { public memberwise init }
struct Int8 { public memberwise init }
given Int8 is Showable {}
given <T> => Bag<T> is Collection {
  type Element = T
  fun first() -> T { … }
}
fun head<C where C is Collection>(c: C) -> C.Element { c.first() }
fun show<C where C is Collection, C.Element is Showable>(c: C) {}

fun use(b: Bag<Int8>) {
  let x: Int8 = head(b)      // needs headsubst and assocsubst
  show(b)                    // needs premsubst and assocsubst
}
fun generic<D where D is Collection, D.Element is Showable>(d: D) {
  let y: D.Element = head(d) // needs headsubst
  show(d)                    // needs premsubst
}
```
