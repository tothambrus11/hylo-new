# 5. Results depend on declaration order

**Status:** fixed by `givencheck` (givens) and `extorder` (extensions).

## Symptom

```hylo
trait P { type Y }
trait Q { type O }
struct T {}
struct U {}
given T is P { type Y = U }
given U is Q { type O = T }
given Z.O is P { type Y = Int }   // accepted…
type Z = T.Y                      // …but rejected ("refers to itself") if these two lines are swapped
fun k(z: Z) {}
```

This program has no consistent reading:
- if `Z.O` is `T`, then `T` has two `P` conformances, so `T.Y`, and hence `Z`, is ambiguous;
- otherwise `Z = T.Y = U` and `Z.O = U.O = T`, a contradiction.

The old checker accepts it in one order and rejects it in the other.

Extensions whose extended type depends on members of other extensions behave the same way:

```hylo
struct A {}
extension X { type Me = Int }
extension A { type Me = A }
type X = A.Me     // accepted, although whether the first extension applies to A depends on X itself
```

## Cause

While the checker computes the type of a declaration, it hides that declaration from lookups, to avoid infinite recursion. Lookups made meanwhile are answered without it, and their answers, along with the types computed from them, are remembered. Nothing checks afterwards whether the hidden declaration would have changed the answer. Which declaration is computed first, and therefore which one is hidden when it matters, depends on the order of declarations.

## Fix

Every lookup or resolution that skipped a hidden declaration is recorded, together with what it was looking for and the assumptions in force at that point. Once the types of all declarations involved are known, each record is checked.

**Givens (`givencheck`).** A skipped given is checked once its type is known. If it could have matched the goal it was hidden from, it is reported: "circular given: the type of this given depends on an implicit resolution of … that it may satisfy". "Could have matched" means its conclusion unifies with the goal, up to coercions the assumptions allow.

Two kinds of hiding are deliberate scoping rules, and they are not checked:
- a where-clause requirement is invisible while the requirements before it are computed;
- a conformance cannot use itself to satisfy the traits it refines.

**Extensions (`extorder`).**
- A lookup ignores extensions that do not declare the name looked up, without computing anything about them.
- A lookup that reaches an extension whose extended type is being computed closes a cycle. The extensions on that cycle form a group.
- Once the whole group is computed, every lookup made by its members is checked against every member that declares the name. If a member could apply to the type looked into, the group is reported as circular.

## Why the verdict no longer depends on order

The checks use only the final types. They examine every lookup of a cycle group, not just the one that happened to close the cycle, so the verdict is the same whichever member is computed first. If no hidden declaration could have taken part, every skip was exact, and the program is accepted with the same meaning as before.

## Limitation

The rule is conservative. Two extensions whose extended types depend on each other's members are rejected even when only one reading is consistent:

```hylo
struct A { struct Inner {} }
extension A.Inner.Foo { type Inner = Bool }
extension A.Inner { type Foo = Int }
fun use(x: Int.Inner) {}
```

The old checker accepted this only when the declarations happened to be computed in a favourable order. Accepting it in every order would need a fixed-point computation, with the ability to undo remembered results.
