# Givens with an inferred type declared outside a function: options

Status: experiments. None of the flags below is in the recommended configuration, and the report does not rely on them. The code is `0032-*.patch` in this folder, to be applied after the series of `../../patches`.

## The problem

`sigrounds` makes the result independent of declaration order for declarations whose type is written. A given whose type is inferred (`given let g = e`) is still typed on demand, nested in the first resolution that meets it. Outside a function this depends on the order of declarations, in the existing implementation and in the recommended configuration alike:

| Program (`tests/`) | Accepted orders of 24 |
|---|---:|
| `g01` a given initialized from a global binding | 12 |
| `g04` a given whose initializer needs another inferred given | 12 |
| `g09` a given initialized by a generic call on a global binding | 22 |
| `g12` a chain of three inferred givens | 5 |

Two mechanisms produce this. When the initializer of a declaration `D` makes a resolution, every inferred given in scope is typed there and then; if its initializer reads `D`, the error "declaration refers to itself" is reported (`g01`). And a given being typed is hidden from the resolutions made meanwhile, including those of another given whose typing was started from inside it (`g04`, `g12`).

## Options tried

Each was run on the 12 programs of `tests/` and on the 23 earlier programs about inferred givens (`../../follow-up/design-order/tests/23`–`28`, `35`; `../../follow-up/attack-sigrounds/p/k2*`, `b0*`, `f0*`, `s0*`), in every order up to 24, with the self-check on. "A" accepted, "R" rejected, in the number of orders given.

| Program | Existing and recommended | 1. `givenwritten` | 2. `givenlazy` | 3. `givennodes` | 4. `givennodes,givencycle` |
|---|---|---|---|---|---|
| `g01` given from a global binding | A12/R12 | R24 | A24 | A24 | A24 |
| `g02` two unrelated givens | A24 | R24 | A24 | A24 | A24 |
| `g03` global binding that needs the given | A24 | R24 | A24 | A24 | A24 |
| `g04` given that needs another given | A12/R12 | R24 | A12/R12 | A24 | A24 |
| `g05` given initialized with itself | R24 | R24 | R24 | **A24** | R24 |
| `g06` cycle through a global binding | R24 | R24 | R24 | **A24** | R24 |
| `g07` signature that could see the given | A24 / R24 | R24 | R24 | A24 | A24 |
| `g08` two givens of one type (ambiguous) | R24 | R24 | R24 | R24 | R24 |
| `g09` given from a generic call | A22/R2 | R24 | A24 | A24 | A24 |
| `g10` two givens initialized with each other | R24 | R24 | R24 | **A24** | R24 |
| `g11` initializer needs its own type; a written given exists | A24 | R24 | A24 | R24 | R24 |
| `g12` chain of three givens | A5/R19 | R24 | A5/R19 | A24 | A24 |

(`g07`: the existing implementation accepts, the recommended configuration rejects with "the type of this given must be written".)

1. **`givenwritten`: a language rule.** A given declared outside a function must have a written type. About 8 lines. Order-independent by construction, and it makes the existing rule "the type of this given must be written" unconditional instead of dependent on what signatures resolve. It rejects every program above, including the plainly valid `g02` and `g03`. No compiler test and nothing in the standard library declares such a given.

2. **`givenlazy`: abandon a forced typing that reaches the declaration being typed.** When a resolution made while `D` is typed meets an untyped inferred given, its type is computed; if that reads a declaration being typed, everything it computed is undone and the given is not a candidate for this resolution. About 20 lines. It repairs the first mechanism (`g01`, `g09`) and not the second (`g04`, `g12`), so it is a partial fix. Extending it to the second mechanism by also abandoning when a candidate was hidden rejects `g04` in the other half of the orders; that variant was not built.

3. **`givennodes`: inferred givens outside functions are entries of the table of signatures.** One line. Every program has one verdict. But a given then sees its own entry of the previous round, so a given initialized with itself, or two initialized with each other, are accepted (`g05`, `g06`, `g10`): the checker accepts a program whose given can never be initialized. This is the reason such givens were excluded from the table in the first place.

4. **`givennodes,givencycle`: option 3 with isolation and a cycle check.** About 70 lines. In each round the type of an inferred given is computed in isolation (what its initializer made the checker compute is discarded), and the inferred givens selected by the resolutions made meanwhile are recorded. After the table is stable, a given that reaches itself through these uses is reported: "the initializer of this given is resolved with the given itself". The types are then computed once more in the state that is kept. Every program has one verdict in every order, the three cyclic programs are rejected, and the self-check reports no violation. On the other 23 programs the only changes are `28`, `k28` and `35`, which the recommended configuration rejects with "the type of this given must be written" and which are now accepted in all 24 orders, and `f04`, now accepted in all 24.

## What option 4 costs and leaves open

- `g11` is rejected where the existing implementation accepts it: the given is a candidate for the goal of its own initializer, next to a written given of the same type. The existing rule (a given is invisible in its own initializer) accepts it; with the table the given is visible, which is what makes the result independent of order. Whether a given should be visible in its own initializer is question 3 of `../../follow-up/designs/order.md`, section 7, and question 13 of `../../START-HERE.html`.
- The isolation computes the initializer of each such given twice per round. Not measured beyond the counters of these programs; existing code has none.
- The cycle check sees uses between inferred givens only. A cycle through a given with a written type (`../../follow-up/attack-sigrounds/p/s02`) is accepted, as it is by every configuration.
- Regression: 150 of the 152 expected verdicts of `../../follow-up/scripts/regress.py`; the two differences are `28` and `35`, intended. On the compiler's tests and the programs of the order design and attack (351 files), no other verdict changes and no self-check violation. The semantic oracle on the 216 test-suite files was not re-run for this flag; the suite has no such given, so no difference is expected.
- It has not been reviewed adversarially. Program `28` is the one that broke the first attempt at treating these givens as entries (accepted in 12 of 24 orders then); it now has one verdict, but one program is not a proof.

## After the designer's answers: option 5

The designer answered that a given is not a candidate in its own initializer, and that a given with an inferred type is worth the value of its initializer (`../../questions/ANSWERS.md`, question 13). That excludes option 1, and it asks of option 4 that the given be hidden in its own initializer, which is what made option 4 reject `g11`.

**Option 5: `givenself,givennodes,givencycle`** (`0034-*.patch`, about 30 lines on top of option 4). While the initializer of a given is typed, that given is not a candidate; as soon as another declaration is typed from inside the initializer, it is visible again. The rule is modelled on what the compiler already does for a conformance: `anonymousImplementation` in `Typer.swift` puts the conformance on the stack of hidden declarations around the one resolution that finds the traits it refines ("we cannot use `d` to resolve `P<Self>`"). Here the scope of the hiding is one initializer. The answers computed meanwhile are not memoized, and the index of givens is not used.

It also applies to a given with a written type, which today is a candidate in its own initializer.

| Program | Existing and recommended | Option 4 | Option 5 |
|---|---|---|---|
| `g01` given from a global binding | A12/R12 | A24 | A24 |
| `g04` given that needs another given | A12/R12 | A24 | A24 |
| `g05` given initialized with itself | R24 | R24 | R24 |
| `g06` cycle through a global binding | R24 | R24 | R24 |
| `g09` given from a generic call | A22/R2 | A24 | A24 |
| `g10` two givens initialized with each other | R24 | R24 | R24 |
| `g11` initializer needs its own type; a written given exists | A24 | **R24** | A24 |
| `g12` chain of three givens | A5/R19 | A24 | A24 |
| `questions/q13b` written given, only candidate for its own initializer | **A24** | A24 | R24 |

Validation of option 5:

- 38 programs about givens (the 12 of `tests/`, the three of question 13 and the 23 earlier ones), each in up to 24 orders with the self-check on: one verdict per program, no violation (`orders-givenself.jsonl`). `givenself` alone leaves the order dependence, as expected.
- 1,708 programs, against the recommended configuration: 10 verdicts change, all of them programs about the initializer of a given: 8 become accepted (inferred givens that were order-dependent or rejected with "the type of this given must be written"), 2 become rejected (a written given that is the only candidate for its own initializer: `q13b` and `attack-sigrounds/p/s02`). No self-check violation (`compare-givenself.jsonl`).
- Semantic dump of the compiler's tests: identical to the existing implementation, 216 of 216 files.
- 150 of the 152 regression verdicts; the other two are `28` and `35`, which expected the rule "the type of this given must be written".

What it leaves open is what option 4 leaves open, minus `g11`: the cycle check sees uses between inferred givens only, the initializer of each such given is typed twice per round, and it has not been reviewed adversarially. One imprecision is inherited from the pattern it copies: a declaration whose type is first computed from inside the initializer, such as a global binding with an inferred type, is typed with the given visible, which is the lexical reading; a resolution made directly in the initializer is the only place where the given is hidden.

## Data

`orders.jsonl` (the 12 programs, options 1 to 4), `orders2.jsonl` (the 23 earlier programs, recommended configuration and option 4), `compare-d.jsonl` (recommended against option 4, 351 files), `orders-givenself.jsonl` and `compare-givenself.jsonl` (option 5).
