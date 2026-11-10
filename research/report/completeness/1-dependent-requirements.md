# 1. Requirements that mention another requirement

**Flag:** `premsubst`. About 320 lines. Design, invariants and test plan: `../follow-up/designs/engine.md`.

## Symptom

```hylo
trait P { type X }
trait Q {}
fun f<T where T is P, T.X is Q>() {}
fun g<U where U is P, U.X is Q>() { f<U>() }   // rejected
```

The caller has exactly the requirements of the callee, and the call is rejected: "no coercion from `(P<U>, Q<(U::P).X>) ==> …`". The same happens when the requirements belong to an extension or to a conditional conformance, with a concrete caller (`given A is P { type X = B }`, `given B is Q`, `f<A>()`), and with chains such as `T is P, T.X is P, T.X.X is Q`. There is no workaround in the language.

Only one form worked: an *equality* on the associated type with a generic caller (`T.X == B`), through a special case in the equality procedure.

## Cause

The type of `f` is `<T> (P<T>, Q<(T::$u).X>) ==> …`, where `$u` is the declaration that the where clause introduces for `T is P`, and `(T::$u).X` is the associated type selected through it. To call `f`, resolution assumes both requirements and proves them last first. When it proves `Q<(U::$u).X>`:

1. nothing says that `$u` is the first requirement of this very call: the implication records the types of its requirements, not the declarations they bind;
2. the first requirement has no witness yet, so even then `(U::$u).X` could not be compared with the caller's `U.X`, which is selected through the caller's requirement.

No given matches a type that mentions the callee's private declaration, so the call fails.

## Fix

1. **Binders.** The type of an implication records, for each requirement, the declaration through which later requirements refer to it (empty unless one does).
2. **Binding.** When resolution opens the implication and assumes a requirement, it rewrites the later requirements that refer to it so that they mention the assumption itself.
3. **Waiting.** A requirement that mentions an assumption without a witness is not a hypothesis. It waits until the requirements it mentions have been proved; their witnesses are then substituted into its type, and it is proved next.
4. **Definitions.** After substitution a type can have the form `(A::c).X`, where `c` is a conformance declaration. It is replaced by the definition of `X` in `c`, as name resolution does.

Every other requirement is treated as before, in the same order. For the example: `P<U>` is proved by the caller's requirement `$r`; the waiting requirement becomes `Q<(U::$r).X>`, which is the caller's second requirement, syntactically.

## Why it is correct

- Each requirement is proved once, and the witness substituted into the requirements that mention it is the one in the derivation. The elaborated call `f<U>($r)($s)` has `$s : Q<(U::$r).X>`, which is the dependent reading of the clause at `T = U`.
- The matcher never sees a type that mentions an unproved assumption: such requirements are off the list of hypotheses and are not unified with anything until released.
- A waiting requirement is always released: it mentions only requirements assumed before it, and it is released once those are proved and everything assumed after it has been discharged. The implementation counts the opposite case (`premsubst.stuck`), which must stay zero.
- A resolution in which no requirement mentions another one takes none of the new paths. The 216 files of the compiler's tests and workloads have the same semantic dump with and without the flag.

## What changes

| Programs of the design's test set | Existing | Revised without the flag | With `premsubst` |
|---|---|---|---|
| Six generic callers of dependent requirements | rejected | rejected | accepted |
| Three concrete callers | rejected or timeout | rejected | accepted |
| Two programs accepted through the special case of the equality procedure | accepted | accepted | accepted, without the special case |
| Three programs that must be rejected (a missing requirement, a requirement satisfied by another conformance, a concrete mismatch) | rejected | rejected | rejected |

## Limits

- A requirement that has two witnesses of equal rank, of which only one makes a dependent requirement hold, is accepted: the requirements are solved together. The alternative ("each requirement must have a unique witness on its own") is a language question.
- Members of a generic type whose own where clause mentions a requirement of the enclosing type are not covered: the binders are lost when the member's type is rebuilt.

## Programs

`follow-up/design-engine/tests/s1-*.hylo`.
