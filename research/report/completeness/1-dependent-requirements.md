# 1. Requirements that mention another requirement

**Update:** the language designer's answer is that the requirements of a clause are solved together: any witness that satisfies the whole clause will do. The commitment rule below (`premcommit`) is therefore withdrawn from the recommended configuration, and the last limit listed at the end no longer applies. See `../questions/ANSWERS.md`, question 8.

**Flags:** `premsubst`; `premcommit` is the withdrawn rule. About 450 lines. Design, invariants, test plan and adversarial review: `../follow-up/designs/engine.md`.

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
4. **The form name resolution gives.** After substitution a type can have the form `(A::c).X`, where `c` is a conformance declaration: it is replaced by the definition of `X` in `c`. A selection through a witness that is a coercion of another witness loses the coercion. Both are what name resolution does when the caller writes `A.X`, so that the callee's requirement and the caller's fact are the same type.
5. **Commitment (`premcommit`).** A requirement that another one mentions must be proved by the witness that resolving it *alone* gives; if that is ambiguous, the call fails. Without this rule the engine would choose, among all witnesses of `A is P`, one for which `A.X is Q` happens to hold: a shadowed or more distant conformance could be selected, and the type of the call would not be the type its signature gives when read at the call site, where `A.X` means the associated type of the nearest conformance.
6. **Capture.** When a clause is instantiated at itself with explicit type arguments (a recursive call such as `f<W<A.X>>()` inside `f<V where A is P, A.X is Q, V is R>`), the type arguments contain references that the *caller* wrote to the same requirement. If the caller can name the witness that such a reference denotes, the premise must be proved by that very witness, so that both kinds of reference read as written.

Every other requirement is treated as before, in the same order. The declarations recorded in step 1 survive the adaptation of methods, initializers and trait requirements, so the same holds for them. For the example: `P<U>` is proved by the caller's requirement `$r`; the waiting requirement becomes `Q<(U::$r).X>`, which is the caller's second requirement, syntactically.

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

## What the review found

The first implementation followed the design as written. An adversarial review ran it and found one wrong acceptance (the capture of step 6: a recursive call accepted with an ill-typed witness), valid programs still rejected (a first requirement proved through an equality; methods, initializers and trait requirements), and the unstated choice that step 5 now settles. All have regression tests (`s1-attack-*.hylo`), and the 46 programs of the design and its review now behave as the review predicts for the corrected design.

## Limits

- With `premcommit`, a requirement that has two witnesses of equal rank is ambiguous even if only one makes a dependent requirement hold. Whether that is the language's rule is a question for its designers; the alternative (requirements solved together) is `premsubst` without `premcommit`.
- A premise with unification variables cannot be resolved alone and keeps the joint reading.
- Near the bound on the size of a derivation, the order of two dependent requirements still decides the verdict, as it does for ordinary requirements (`s1-attack-where-order-a`, `-b`); see `4-derivation-size.md`.

## Programs

`follow-up/design-engine/tests/s1-*.hylo`.
