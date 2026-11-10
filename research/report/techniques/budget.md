# Bound runaway searches (`budget`)

**Kind:** correctness fix: a crash becomes an error.

## Problem

The search keeps every live alternative of the current layer. Some goals cannot be refuted by the abstract model: those with branching givens and facts deeper than its cut-off. On those, the number of alternatives grows exponentially until memory runs out, and the compiler crashes.

## How it works

When a search layer ends with no complete proof and more than 100,000 live alternatives, the resolution is abandoned. The checker reports "implicit resolution is too complex: … consider adding explicit type arguments or annotations", once per scope. The limit can be changed with `HYLO_TC_BUDGET`.

## Why it is correct

Abandoning a resolution can only make a goal fail. A failed resolution could, in principle, steer the checker to another overload or another extension, which would change the program's meaning without any error. Abandonment is therefore always reported as an error, and the program is rejected.

## Effect

| Program | Without | With |
|---|---:|---:|
| branching divergence, fixes only | out of memory after 38 s | rejected in 3.4 s |
| branching divergence, all techniques | rejected in 11.9 s | rejected in 5.8 s |

## Cost

A valid program that genuinely needs a larger search is rejected; the old checker ran out of memory on it. With the abstract model enabled, none of the test programs reaches the limit, except programs that are rejected anyway. The limit is a tunable, not a rule of the language; a stronger abstract model would make it unnecessary.
