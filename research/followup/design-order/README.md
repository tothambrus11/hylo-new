# A fix for declaration-order dependence that works by construction

## What was asked

The type checker computes the type of a declaration on demand, hides the declaration from lookups meanwhile, and remembers everything computed in the meantime. Two fixes (`extorder`, `givencheck`) check afterwards the lookups that skipped a hidden declaration. A declaration-order fuzzer showed that the verdict still depends on the order for 7 of 129 test programs. The task had two parts:

1. Design a mechanism under which the verdict cannot depend on the order, compare it with a language rule and with a uniform record-and-check mechanism, and write the design for the engineer who will implement it.
2. Review that design adversarially: check its account of the existing code, attack its correctness argument with programs, check its feasibility and its test plan, and revise the document.

The compiler was not to be built or modified by either part.

## What was done

- The code that computes declared types was read, and the sequence of events was worked out for each of the seven programs in an accepting and in a rejecting order.
- Four small programs that show the problem were written and checked on the binary, with 23 test programs for the change.
- Every program was type-checked in permuted declaration orders (all orders where there are at most 120), under the existing checker and under the full configuration.
- An executable model of the mechanism was written for a subset of Hylo. It implements the existing behaviour and the proposed one. It was compared with the binary and run on 22,000 random programs.
- The design was written: `DESIGN.md`.
- The design as first written was then implemented by the coordinator behind the flag `sigrounds` (commit `cdb3415` of the implementation, binary `eq17`). The review used that binary. It ran the recorded verdicts again, wrote 19 more programs, most of them attacks, measured the number of rounds on the compiler's tests and on generated programs, and revised `DESIGN.md`. Its conclusions are in section 9 of the design.

## What was found

By the design:

- The cause is not specific to cycles. A lookup or a resolution computes the type of every candidate it meets, inside the computation that asked. A candidate that is being computed is skipped. What is computed meanwhile is kept. Which dependency gets cut depends on where evaluation starts.
- The same mechanism rejects ordinary programs without any cycle in *every* order. `problem/p4-chain.hylo` (five aliases and three givens in a chain) is rejected in all 60 orders tried, by the existing checker and by the full configuration. The fuzzer cannot find such programs, since their verdict does not vary.
- Checking skips afterwards cannot be made order-independent without checking every candidate inside every dependency cycle, including those that the traversal did not skip. That rule is sound but rejects programs with a single consistent reading, and it still needs computations that can be abandoned.
- A strict language rule (no lookup may meet a declaration being computed) is order-independent and changes no verdict in the compiler's tests or the standard library, but it rejects ordinary programs such as an alias defined through a conformance and used in the head of another given.
- The proposed design computes the types of extensions and givens in rounds. In a round, lookups and resolutions read these types from the previous round's table only, and each round starts from the untouched typing state of the module. Rounds repeat until the table is stable.

By the review, on the implementation of the first design:

- The recorded verdicts are right: all 46 verdict counts of the 23 test programs, the fractions of the seven failing programs and the tables of the problem section were reproduced exactly.
- The mechanism does what the design said on every program the design had considered. The seven failing programs are accepted in every order. On the 129 declaration-order programs no verdict depends on the order, 17 programs that the full configuration rejects in every order become accepted, and none goes from accepted to rejected (the coordinator's runs). The 192 programs of the compiler's tests keep their verdicts and need at most one round, like the standard library.
- Three defects were found, each with a program that the existing checker treats differently:
  - A given whose type is inferred from its initializer was computed before the expression around it. A legal program is rejected (`tests/23`) and another crashes (`tests/24`).
  - A named requirement of a where clause (`where let u: P<T>`) was treated as a given of the table. A program that the rule on the order of requirements rejects is accepted (`tests/25`).
  - The verdict of `tests/28` depends on the order of two top-level declarations, and that of `tests/27` on the order of two givens in a function body. The existing checker rejects both programs in every order. The cause is the design's own hook for where clauses, which can type a where clause from inside a declaration that the where clause needs. The implementation's self-check reports the violation.
- One example of the first version was wrong: its chain program (`tests/06`) is rejected in every order for an unrelated reason, because the existing checker does not accept a member selected on a type application (`Foo<X>.F`) as a type expression. `tests/06b` and `problem/p4-chain.hylo` now select the members on aliases.
- The cost is not nil for ordinary generic code. A where clause that selects a member through an earlier requirement (`C.Element`) makes the module need two rounds, which about doubles the resolution work of the signature phase. A chain of `n` dependent givens needs `n + 1` rounds.

The revised design corrects the three defects with about 45 lines: only declarations whose signature is a type expression are in the table; the signature of an enclosing function, extension or conformance is computed before anything declared inside it; and the self-check compares both evaluation orders in every round.

## What remains uncertain

- The corrections are not implemented. What the design says about `tests/23` to `28` and `35` after the change is reasoning, not measurement.
- The argument for order independence rests on one assumption about the whole checker: the value memoized for an alias, a function or a requirement must not depend on which computation asked for it first. The first design violated it. The corrected design closes the case that was found; a similar case for members of extensions selected through the table could not be constructed but is not excluded. The self-check is the safeguard.
- The corrected design rejects a program that has both a given without a written type and a signature that makes a resolution which can see it (`tests/35`, accepted today in 16 of 24 orders and by the first design in all 24). No such given exists in the compiler's tests, the standard library or the test programs. Whether to reject, to ignore such a given in signatures, or to require a type on every given is a question for the language designers (question 8 of the design).
- The design accepts programs that the current cycle rule rejects. Whether such programs should be legal is the first of nine questions for the language designers in section 7.
- The implementation's self-check reports a false violation on a cycle of aliases that is entered from two declarations (`tests/38`): it compares which alias is blamed. Until that comparison is normalised, a violation on a program whose only errors are "refers to itself" proves nothing.
- The fuzzer permutes top-level declarations only. The order of declarations inside a function body is covered by three pairs of test programs and by the self-check, not by a fuzzer.
- Costs were measured as work counters on generated programs, not as times, and not on a real library.

## Contents

| Path | Content |
|---|---|
| `DESIGN.md` | The deliverable, revised by the review. Section 9 is the review. |
| `problem/` | The programs of section 1 of the design, in an accepting and a rejecting order. |
| `tests/` | 42 programs, each with its expected verdict after the change, the reason, and its current verdicts; `MANIFEST.tsv` lists them. Programs `06b` and `23` to `38` come from the review. |
| `scripts/orders.py`, `show.py` | Type-check a program in permuted declaration orders, one process at a time; print the results. |
| `scripts/run-tests.sh`, `run-seven.sh`, `run-problem.sh`, `corpus_counters.py` | The runs behind the numbers of the first version. |
| `scripts/model.py`, `compare_model.py`, `fuzz_model.py`, `predict.py` | The executable model, its comparison with the binary, random programs, and predicted verdicts. |
| `scripts/annotate_tests.py` | Writes the header comments of the first 23 programs of `tests/` from the results. It leaves `06` and the programs of the review alone: their headers were written by hand. |
| `scripts/tcb.sh`, `review_orders.py`, `review_run3.sh`, `review_corpus_rounds.py`, `review_cost.py` | The review's runs: a locked wrapper around the binary, permuted orders with a choice of binary and flags, one program under three configurations, the rounds needed by the compiler's tests, and the cost on generated programs. |
| `run.sh` | Runs the binary on one program under a named configuration. |
| `results/` | Raw results (`.jsonl`) and the text summaries quoted in the design. Files named `review-*` come from the review. |
