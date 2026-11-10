# 4. The bound on the size of a derivation

**Flag:** `heightbound`. Experiment: every derivation found today is still found; larger ones are found as well. About 60 lines. Design: `../follow-up/designs/engine.md`, section 9.

## Symptom

Implicit resolution gives up after ten steps. A step is one given used, anywhere in the derivation, so the bound limits the *size* of a derivation: the number of givens used for all the requirements of a call together.

| Program | Givens needed | Today |
|---|---:|---|
| a 4-tuple is `Copyable` | 10 | accepted |
| a 5-tuple is `Copyable` | 12 | rejected |
| a function with three requirements, each "a pair is `Copyable`" (5 steps each, accepted one at a time) | 16 | rejected |
| `where S<C> is Q, C is P` | 12 | rejected; accepted with the two requirements swapped |

The failure is reported as "no coercion", without mention of the bound. In the scaling experiment, every configuration rejects valid programs with ten or more requirements on a callee.

## The experiment

The bound is put on the *height* of a derivation instead: the nesting depth of premises. The premises of the goal are at level 1; the premises of a given that matched a goal of level *n*, and the equalities assumed for that match, are at level *n* + 1; a premise above level 9 is not proved. Height does not depend on the order of requirements or on how many requirements a call has.

A derivation of at most ten steps has no premise above level 9, so the search is identical to today's through the tenth step: every resolution that completes today completes with the same results. Only resolutions that reach the size bound today continue. They may try a bounded number of further candidates (100,000 by default); past that they fail, silently, as they did.

## What changes

All four programs above are accepted; the programs that must stay rejected stay rejected (a chain of conformances nested ten deep). The semantic dump of the compiler's tests is unchanged: no resolution there reaches the bound.

## Why it is an experiment

- A resolution that fails at the size bound today can cost up to the work budget before it fails (on one constructed program: 52,000 candidate matches become 325,000).
- An extension or overload that did not apply because its resolution ended at the bound can apply now.
- Whether the bound is part of the language, and whether its exhaustion should be an error rather than a silent failure, are questions for the designers.

## Programs

`follow-up/design-engine/tests/s3-*.hylo`.
