# The coercion test in scopes with equalities (`coeset`, `stackscan`)

**Kind:** result-preserving. About 80 lines.

## The problem

When the type of a given and a goal differ at some position, matching asks whether an equality in scope could relate the two types found there (`coesrc.md` describes the test). The test compared the pair with *every* given in scope, one after the other.

While a where clause is being typed this is the dominant cost. Typing `where T0 is P, …, T0.X == T1.X, …` looks up `Tk.X` for each requirement; each lookup matches every requirement typed so far; each match runs the test, which visits every given again. With *n* equalities that is cubic, and the caches that normally absorb the cost are disabled while requirements are being typed. A helper used by the test also copied the whole program value at every call.

On a function with 16 equalities on associated types this took 320 ms, with 64 equalities 4 s. In the Swift standard library the number of equalities in scope is 15 at the 99th percentile and 44 at the maximum (`../follow-up/usage/`), because `Collection` alone brings seven.

## How it works

**`coeset`.** For closed types the test has a simple form: a closed type can be related by a closed equality only if it *is* one of its sides. The sides of all closed equalities visible from a scope are collected once into a set, for the current state of "what is being typed"; the test for a closed pair is then two lookups. Givens that are not closed equalities but can still produce a coercion (a given of type `<T> T`, an equality with parameters) are kept in a short list and tested as before, as are the hypotheses of the current derivation.

**`stackscan`.** The helper that asks whether a given is being typed iterates over the declarations being typed directly, instead of forming a closure that captures a copy of the program.

## Why results are preserved

The set contains exactly the types for which the per-given comparison succeeds, for closed types and closed equalities: that comparison is equality up to aliases, and the set stores types without aliases. Every other case takes the existing path. The set is recomputed whenever the declarations being typed change. The self-checking mode runs the pass over all givens next to every set lookup and compares the answers.

## Measurements

Time to type-check the user module, same binary, with and without the two flags (machine under load; indicative):

| Program | Without | With |
|---|---:|---:|
| 16 equalities between associated types | 336 ms | 17 ms |
| 64 | 4,234 ms | 175 ms |
| 128 | 17,067 ms | 375 ms |
| Swift `Collection` signature, translated (7 traits, 14 equalities) | 676 ms | 44 ms |
| Swift `StringProtocol`, translated | 874 ms | 53 ms |

The standard library, which has no equality, is unaffected.
