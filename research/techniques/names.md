# `names` (retired): name-filter extensions before checking applicability

## How it works

In `resolve(_:declaredIn:applyingTo:)`, skip an extension that does not declare the looked-up identifier *before* calling `applies(e, to: q)`.

## Why it is NOT sound

`applies` has side effects that later lookups depend on:
- it forces and permanently memoizes `extendeeType(e)`;
- on its slow path, it forces the declared types of givens.

Both happen under `declarationsOnStack`, where a result computed while a cycle is cut (an `.error`, or a lookup that silently skipped an on-stack extension) is memoized for good. Skipping `applies` changes which lookup first evaluates an extendee or a given, and so changes the result on programs with mutually dependent extensions.

Counterexamples (`research/review/names/`):
- the baseline accepts n04, n11 and n12, which `names` rejects;
- the baseline reports spurious cycles on n01, n05 and n17, which `names` "fixes".

## Replacement

`memberskip` gets nearly all of the gain and skips only calls that provably have no effect (see memberskip.md). The root cause, order-dependent memoization of cycle-truncated results, is a baseline bug. A taint counter that refuses to memoize results computed under a cycle cut would fix it. That would be a semantic change and belongs in its own PR.
