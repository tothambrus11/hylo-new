# Hylo Type-Checker Optimizations

Techniques that make Hylo's type checker 4.1× faster on the standard library and up to three orders of magnitude faster on workloads designed to stress resolution, together with fixes for five soundness problems of the existing implementation.

**Start with `report.html`.** It is the complete overview, readable in any browser in about 20 minutes. The rest of this folder gives the details behind it.

| Folder | Contents |
|---|---|
| `report.html` | The overview: background, results, every technique, the soundness fixes, limitations, validation and related work |
| `techniques/` | One document per technique: the problem, how it works, why it is correct, what it speeds up, what it costs |
| `soundness/` | One document per soundness problem of the existing implementation: symptom with an example, cause, fix, what remains |
| `rejected/` | Approaches that are faster but change results, and why |
| `validation/` | Test-suite comparison, adversarial test results and timings, with raw data |
| `test-programs/` | About 540 small programs, grouped by topic, each folder with an index of old and new verdicts |
| `patches/` | The implementation as a patch series, with instructions to build and run it |
| `papers/` | The cited papers available in PDF form, linked from the references of `report.html` |

## Techniques

| Problem | Technique | Document |
|---|---|---|
| Too many candidate givens | index givens by head | `techniques/index.md` |
| | skip givens that cannot coerce | `techniques/coesrc.md` |
| Searches that must fail | abstract model of the givens | `techniques/absmodel.md` |
| | …also with equalities in scope | `techniques/absquotient.md` |
| | bound runaway searches | `techniques/budget.md` |
| Equality constraints | equality decision procedure | `techniques/eqsolve.md` |
| | "find a type equal to X" | `techniques/eqmgu.md` |
| Member lookup | skip irrelevant extensions | `techniques/memberskip.md` |
| | index traits by member name | `techniques/traitindex.md` |
| Overheads | type storage, substitution, unification, symbol table | `techniques/constant-factors.md` |
| Crashes on cyclic types | occurs check | `techniques/occurs.md` |

## Soundness problems fixed

1. Unrelated equalities make types interchangeable: `soundness/1-unrelated-equalities.md`
2. Equality chains time out or are rejected: `soundness/2-equality-chains.md`
3. Associated types through a callee's requirements are not simplified: `soundness/3-unsimplified-projections.md`
4. Cyclic type bindings crash the compiler: `soundness/4-cyclic-bindings.md`
5. Results depend on declaration order: `soundness/5-declaration-order.md`
