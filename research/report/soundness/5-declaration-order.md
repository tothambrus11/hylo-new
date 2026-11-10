# 5. Results depend on declaration order

**Status:** reduced, not eliminated, by `givencheck` (givens) and `extorder` (extensions). See "What the fix achieves" below.

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

The existing implementation accepts it in one order and rejects it in the other.

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

## What the fix achieves

The checks use only the final types, and for extensions they examine every lookup of a cycle group, not only the one that closed the cycle. If no hidden declaration could have taken part, every skip was exact, and the program is accepted with the same meaning as before.

Declaration-order fuzzing measures the effect. For each of 129 programs constructed for this problem, up to 24 permutations of the top-level declarations are type-checked, and the verdicts compared:

| | Programs whose verdict depends on the order |
|---|---:|
| existing implementation | 52 of 129 |
| with `givencheck` and `extorder` | 7 of 129 |

On 575 other programs (the remaining test programs and the compiler's tests), no verdict depends on the order.

## What remains order-dependent

The seven remaining programs have two shapes.

**A cycle through a type alias:**

```hylo
struct A {}
struct B {}
extension X { type Me = Int }
extension A { type Me = B }
type X = A.Me            // accepted in this order
fun f(x: X.Me) {}        // "definition of 'X' refers to itself" if this declaration comes first
```

**A cycle through a given and an extension together** (for example `names-n11_poison_via_summon.hylo`).

The cause is structural. A cycle is detected from the state of the evaluation stack when a declaration is re-entered, by a separate mechanism for each kind of declaration. Whether the cycle is seen therefore depends on where evaluation enters it. A uniform solution needs either explicit dependency tracking, with cycles detected on the dependency graph, or a language rule that excludes such dependencies.

## Limitation

The rule is conservative. Two extensions whose extended types depend on each other's members are rejected even when only one reading is consistent:

```hylo
struct A { struct Inner {} }
extension A.Inner.Foo { type Inner = Bool }
extension A.Inner { type Foo = Int }
fun use(x: Int.Inner) {}
```

The existing implementation accepts this program only when the declarations are computed in a favourable order. Accepting it in every order would need a fixed-point computation, with the ability to undo remembered results.
