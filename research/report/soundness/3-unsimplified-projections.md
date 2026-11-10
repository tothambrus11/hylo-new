# 3. Associated types through a callee's requirements are not simplified

**Status:** the common case is fixed by `eqsolve`; other forms remain.

## Symptom

```hylo
trait Collection { type Element }
struct Box<T> { public memberwise init }
struct Flag { public memberwise init }
extension <T where T is Collection, T.Element == Flag> Box<T> {
  type Element = Flag
  fun first() -> Element { Flag() }
}
fun g<T where T is Collection, T.Element == Flag>(b: Box<T>) {
  let f: Flag = b.first()
}
```

The existing implementation accepts this program after an expensive search (1.4 s). Similar programs, such as generic callers of functions whose parameter types mention `T.X`, are rejected or exhaust memory.

## Cause

To check that the extension applies to `Box<T>`, the checker proves the extension's requirements, in reverse order. When it proves `T.Element == Flag`, the `T.Element` in that requirement is qualified by the extension's own requirement `T is Collection`. That requirement has not been proved yet, so it is not known to be the caller's `T is Collection`. The caller's fact speaks about the caller's `T.Element`, a different term, and nothing connects the two.

## Fix

Before deciding such an equality, `eqsolve` resolves the pending requirement in the environment in which it will later be proved, that is, under the assumptions made before it. If that resolution has exactly one answer `w`, and nothing involved still contains unification variables, the requirement's `T.Element` is identified with `T.Element` through `w`. Resolution is deterministic, so `w` is the witness that will actually be used. The example then takes 17 ms.

If the condition does not hold, the projection is left as it is. A "not equal" answer that depends on it is not trusted, and the search decides instead, as before. The verdict therefore never depends on how deeply the query happens to be nested.

## Remaining

Projections through other forms of pending requirements, such as a requirement reached through a coercion, are not simplified. A general fix would substitute each proved requirement into the types of the requirements still pending.
