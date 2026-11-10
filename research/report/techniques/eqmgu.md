# Solve "find a type equal to X" directly (`eqmgu`)

**Kind:** speed-up and correctness fix. Used together with `eqsolve`.

## Problem

Requirements of a callee are proved in reverse order. A requirement like `T == U` in

```hylo
fun pick<T, U where U is Q, T == U>(x: T) {}
```

is therefore often proved while `U` is still being inferred, which produces the goal `A ~ ?u`. The search then tries reflexivity, every equality fact, symmetry, and transitivity with a fresh unification variable as the middle type. Each of these binds `?u` differently, and each transitivity step creates more goals of the same form.

As a result, three-line programs exhausted memory. When the scope had a chain of equalities, several answers of equal cost for `?u` also made valid calls fail as ambiguous.

## How it works

A goal `?v ~ X` or `X ~ ?v`, where `?v` is a unification variable that does not occur in `X`, gets exactly one answer: `?v := X`, proved by reflexivity, with the penalty of the built-in rules.

## Why it is correct

`?v := X` is the most general answer. Any other answer binds `?v` to a type that is equal to `X`. Every remaining goal that mentions `?v` holds for one choice exactly when it holds for the other, because coercions carry proofs along proved equalities. So the other answers add only duplicate proofs, which used to surface as false ambiguity errors.

No new program is accepted: the single answer kept is one of the answers the search would have found.

**Deviation.** The existing implementation sometimes selected another member of `X`'s equality class. An equality fact carries a lower penalty than reflexivity, so with `X == B` in scope it bound `?v := B`. Both are equal in the theory, but a later step that compares types *syntactically* sees `X` instead of `B`. The new choice is canonical and does not depend on which facts are in scope. No test showed a difference.

## What it speeds up

| Program | Without | With |
|---|---:|---:|
| three-line valid program with open equality requirements | out of memory | 0.19–0.34 s |
| three-line ill-typed program | 24 s | 3 ms |

## Cost

One occurs check per open equality goal.
