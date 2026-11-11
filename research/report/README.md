# Hylo Type-Checker Optimizations

Techniques that make Hylo's type checker faster, fixes for nine soundness problems of the existing implementation, and fixes that let ordinary generic programs with associated types type-check.

**Start with `START-HERE.html`.** It summarizes the findings, states the open questions on the language with a program for each, and says how to reproduce everything (about 20 minutes). `report.html` is the complete overview (about 30 minutes). The rest of this folder gives the details behind them.

| Folder | Contents |
|---|---|
| `START-HERE.html` | Entry point: what is asked of a reviewer, the findings, eighteen questions on the language, how to reproduce |
| `reproducers/` | One small program per finding, with the observed output of the existing implementation and of the fixes |
| `questions/` | The programs of the questions, the questions as text, and the observed output |
| `report.html` | The overview: background, results, every technique, the soundness fixes, the programs that were wrongly rejected, an assessment of what is worth its complexity, limitations, validation and related work |
| `techniques/` | One document per performance technique: the problem, how it works, why it is correct, what it speeds up, what it costs |
| `soundness/` | One document per soundness problem of the existing implementation: symptom with an example, cause, fix, what remains |
| `completeness/` | One document per kind of valid program that was rejected |
| `rejected/` | Approaches that are faster but change results, and why |
| `validation/` | Test-suite comparison, verdicts on 1,651 programs, declaration-order sweeps and timings, with raw data |
| `test-programs/` | About 540 small programs, grouped by topic, each folder with an index of verdicts |
| `follow-up/` | The supporting studies: measurements of the problem space, independent tests, designs with their reviews, attacks, and their test programs (about 1,000 more) |
| `experiments/inferred-givens/` | Four options for givens with an inferred type declared outside a function; none is adopted |
| `patches/` | The implementation as a patch series against `main`, with instructions to build and run it |
| `papers/` | The cited papers available in PDF form, linked from the references of `report.html` |

## Performance techniques

| Problem | Technique | Document |
|---|---|---|
| Too many candidate givens | index givens by head | `techniques/index.md` |
| | skip givens that cannot coerce | `techniques/coesrc.md` |
| Equality constraints | equality decision procedure | `techniques/eqsolve.md` |
| | "find a type equal to X" | `techniques/eqmgu.md` |
| | keep the index under equalities; decide equalities at once | `techniques/eqindex-eqeager.md` |
| | set-based coercion test | `techniques/coeset.md` |
| Overloaded names | share work between candidates | `techniques/overload.md` |
| Searches that must fail | abstract model of the givens | `techniques/absmodel.md`, `techniques/absquotient.md` |
| | bound runaway searches | `techniques/budget.md` |
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
6. Associated types of a generic conformance are one type for every instance: `soundness/6-generic-conformance-associated-types.md`
7. Inside a trait, `Self.X` is equated with another witness's `T.X`: `soundness/7-self-projection.md`
8. A conformance satisfies the trait it refines with itself: `soundness/8-refinement-satisfied-by-itself.md`
9. Members selected through an alias lose the type arguments: `soundness/9-members-through-aliases.md`

## Valid programs that were rejected

1. Requirements that mention another requirement: `completeness/1-dependent-requirements.md`
2. Associated types of a requirement in a signature: `completeness/2-projections-in-signatures.md`
3. Equalities that matching does not use (experiments): `completeness/3-equalities-in-matching.md`
4. The bound on the size of a derivation (experiment): `completeness/4-derivation-size.md`
