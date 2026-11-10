# Remember givens that can never produce a coercion (`coesrc`)

**Kind:** speed-up; results are unchanged.

## Problem

When a given almost matches a goal (`P<A>` against `P<B>`), the checker may assume `A == B`, but only if some given could prove that equality. To find out, it scans every visible given and classifies its type:
- an equality `T ~ U` can produce coercions between types that match its sides;
- a fully generic given `<T> T` can produce anything;
- every other given can produce nothing.

The scan is repeated for every new pair of types, and each visit re-derives the classification.

## How it works

The first time a given is classified as "can produce nothing", it is added to a set, and later scans skip it.

## Why it is correct

The classification depends only on the given's own declared type, never on the pair being asked about. A skipped given would have contributed "no" to the answer, so the answer is unchanged.

The classification is recorded only when the type is final: it has no error, and no declaration is hidden at the time. A type computed provisionally is therefore never cached.

## What it speeds up

Programs with many givens in scope and structural mismatches.

| Program | Without | With `coesrc` alone |
|---|---:|---:|
| standard library | 1.0 s | 0.81 s (1.2×) |
| 40 unrelated conformances in scope | 7.4 s | 0.99 s (7.5×) |

## Cost

One set of givens per module.
