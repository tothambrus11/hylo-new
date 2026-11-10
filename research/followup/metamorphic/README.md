# Metamorphic testing of the type checker

## What was asked

Apply, systematically, eight transformations that should not change whether a program type-checks, and compare the verdicts. Each of them had exposed a defect once when applied by hand. For every change of verdict: reduce the program, check that the transformed program is a correct instance of the relation, and decide whether the change is legitimate in this language or a defect, and in which configuration.

## What was done

`metamorphic.py` generates the variants of a program for one relation, type-checks the original and each variant with `tc-bench` (one process at a time, 60 s limit), and records one row per variant. A verdict is `accept`, `reject`, `crash:<code>` or `timeout`. A row is a *violation* when the verdict of the variant differs from the verdict of the original. When the verdicts agree but the sets of error messages differ (source positions removed), the row is marked `messages_differ`.

Every transformation edits the original text; nothing is re-printed from a syntax tree, so comments, whitespace and operator spacing are preserved. `hylosyn.py` is a lexer that follows the compiler's lexer, plus a parser of the declaration structure (declarations, type bodies, context clauses).

| File | Content |
|---|---|
| `metamorphic.py` | driver: `baseline`, `run`, `attribute`, `show` |
| `relations/r1_*.py` … `r8_*.py` | one module per relation; the docstring of each defines its variants |
| `hylosyn.py`, `common.py` | lexer and declaration parser; running `tc-bench`, cache, corpus |
| `reduce.py`, `reduce_all.py` | reduction of one violation; grouping and reduction of all of them |
| `report.py` | the tables of this document, from the raw rows |
| `tc.sh` | `./tc.sh (base\|FIX\|FULL) file.hylo` prints the diagnostics of one program |
| `data/baseline-FULL.jsonl` | original and re-printed verdict of each program |
| `data/rows-FULL.jsonl`, `rows-FIX.jsonl`, `rows-base.jsonl` | one row per variant |
| `data/done-FULL.jsonl` | one row per (program, relation): makes `run` restartable |
| `data/cache.jsonl` | every type-checker result, keyed by the hash of the program text |
| `data/summary.md` | output of `report.py` |
| `violations/<relation>/<program>--<variant>/` | `a.hylo` (reduced original), `b.hylo` (reduced variant), `info.json` (verdicts under the three configurations) |
| `violations/index.jsonl` | the violations grouped by signature, with the members of each group |

### Programs

@PROGRAMS@

### The relations

1. **Order of top-level declarations.** The reversal, the rotation by one, then other permutations.
2. **Order of requirements and of generic parameters.** `reqs`: a permutation of the requirements after `where`. `reqs-dep`: a permutation that keeps every requirement mentioning a projection `T.X` after the requirements that preceded it. `params`: a permutation of the generic parameters, only for conformances, extensions and functions never applied to explicit type arguments. `swap-names`: two generic parameters exchange their names throughout the declaration.
3. **Order of members** of a struct, enum, trait, extension or conformance body. Stored properties and enum cases keep their relative order.
4. **Tautology or unused parameter.** `X == X` added to the where clause of a function, conformance or extension, as the last or as the first requirement, where X is a generic parameter (`taut-param`), an associated type `T.X` (`taut-assoc`), a type application of the head such as `Box<T>` (`taut-app`) or a non-generic struct (`taut-ground`; a declaration without a context clause gets `<where A == A>`). `unused-param`: an extra generic parameter that nothing mentions.
5. **Type alias.** `intro-all`: every occurrence, in a type position, of a closed type expression (`A`, `Box<A>`, `A.Me`) is replaced by a new alias declared at the end of the file (`intro-all-top`: at the beginning; `intro-one`: only the first occurrence). `intro-generic`: `type Alq<T> = Box<T>` is declared and applications `Box<...>` are spelled `Alq<...>`. `expand`: every use of an existing non-generic alias is replaced by its definition (`expand-drop`: and the alias is removed).
6. **Renaming.** Every identifier token with the old name is replaced. `one`: one declared name gets a prefix. `all`: every declared name gets the prefix. `reverse`: every declared name gets a new name such that the alphabetical order of the names is reversed. Names that the standard library declares or uses as labels are never renamed.
7. **Forms of an equality.** `sym`: `B == A` for `A == B`. `dup`: `A == B, A == B`. `dup-sym`: `A == B, B == A`.
8. **Unrelated declaration.** `conf`: a new struct and its conformance to an existing trait of the file (only traits without requirements other than associated types). `struct-top`: a new struct at the beginning. `gconf`: a new generic struct and a generic conformance `given <T> => N<T> is P`.

Each relation lists its variants in a fixed priority order and the driver checks the first *n* of them: @BUDGETS@. The random choices are seeded by the program text, so a run is reproducible.

### Validation of the declaration splitter

The pilot's splitter worked on lines and brace counts. The new one works on tokens: a declaration starts at an annotation, a modifier or an introducer, and ends at the closing brace of its body, at a `;`, or where the next declaration starts on a new line. It handles multi-line heads, modifiers on their own line, tuple types written with braces in a head (`given {Void, Void} is P {`), access effects after a parameter list (`fun f() inout -> T`) and `memberwise init`.

Three checks:
- the re-printed file (the identity permutation) has the same token sequence as the original, for all @NFILES@ files;
- the re-printed file gets the same verdict and the same messages as the original under FULL: @REPRINT@;
- no variant of relation 1 introduced a syntax error (@R1INVALID@ of @R1VARIANTS@).

## Results

@TABLE@

@KINDS@

@FINDINGS@
