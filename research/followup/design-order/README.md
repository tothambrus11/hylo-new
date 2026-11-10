# A fix for declaration-order dependence that works by construction

## What was asked

The type checker computes the type of a declaration on demand, hides the declaration from lookups meanwhile, and remembers everything computed in the meantime. Two fixes (`extorder`, `givencheck`) check afterwards the lookups that skipped a hidden declaration. A declaration-order fuzzer showed that the verdict still depends on the order for 7 of 129 test programs. The task was to design a mechanism under which the verdict cannot depend on the order, to compare it with a language rule and with a uniform record-and-check mechanism, and to write the design for the engineer who will implement it. The compiler was not to be built or modified.

## What was done

- The code that computes declared types was read, and the sequence of events was worked out for each of the seven programs in an accepting and in a rejecting order.
- Four small programs that show the problem were written and checked on the binary, with 23 test programs for the change.
- Every program was type-checked in permuted declaration orders (all orders where there are at most 120), under the existing checker and under the full configuration.
- An executable model of the mechanism was written for a subset of Hylo. It implements the existing behaviour and the proposed one. It was compared with the binary and run on 22,000 random programs.
- The design was written: `DESIGN.md`.

## What was found

- The cause is not specific to cycles. A lookup or a resolution computes the type of every candidate it meets, inside the computation that asked. A candidate that is being computed is skipped. What is computed meanwhile is kept. Which dependency gets cut depends on where evaluation starts.
- The same mechanism rejects ordinary programs without any cycle in *every* order. `problem/p4-chain.hylo` (two aliases and three givens in a chain) is rejected in all orders tried, by the existing checker and by the full configuration. The fuzzer cannot find such programs, since their verdict does not vary.
- Checking skips afterwards cannot be made order-independent without checking every candidate inside every dependency cycle, including those that the traversal did not skip. That rule is sound but rejects programs with a single consistent reading, and it still needs computations that can be abandoned.
- A strict language rule (no lookup may meet a declaration being computed) is order-independent and changes no verdict in the compiler's tests or the standard library, but it rejects ordinary programs such as an alias defined through a conformance and used in the head of another given.
- The proposed design computes the types of extensions and givens in rounds. In a round, lookups and resolutions read these types from the previous round's table only, and each round starts from the untouched typing state of the module. Rounds repeat until the table is stable. The table after each round is a function of the program, so the order of declarations cannot matter. It needs about 150 new lines and makes about 260 existing lines removable (`givencheck`, the cycle rule of `extorder`, `mayMatch`, `memberskip`).
- On the model, the proposed behaviour accepts the seven failing programs in every order, accepts every program that the existing behaviour accepts in every order (1,262 random programs, with the same types), and rejects the programs without a consistent reading.

## What remains uncertain

- The design was not implemented. The model reproduces the binary's verdicts exactly for the existing checker on the 17 test programs it can express, and for the full configuration on all but two, whose difference is understood. It has no generic givens, no coercions and only one kind of nested scope.
- The argument relies on five assumptions about the rest of the type checker, listed in section 4.2 of the design with an assertion for each. The most important is that the typing state of a module can be restored completely between rounds.
- The design accepts programs that the current cycle rule rejects. Whether such programs should be legal is a question for the language designers, with six others in section 7.
- The cost was not measured. It is expected to be nil for the code available today (one round), and one extra pass over the signatures of extensions and givens per level of dependency otherwise.

## Contents

| Path | Content |
|---|---|
| `DESIGN.md` | The deliverable. |
| `problem/` | The programs of section 1 of the design, in an accepting and a rejecting order. |
| `tests/` | 23 programs, each with its expected verdict after the change, the reason, and its current verdicts; `MANIFEST.tsv` lists them. |
| `scripts/orders.py`, `show.py` | Type-check a program in permuted declaration orders, one process at a time; print the results. |
| `scripts/run-tests.sh`, `run-seven.sh`, `run-problem.sh`, `corpus_counters.py` | The runs behind the numbers of the design. |
| `scripts/model.py`, `compare_model.py`, `fuzz_model.py`, `predict.py` | The executable model, its comparison with the binary, random programs, and predicted verdicts. |
| `scripts/annotate_tests.py` | Writes the header comments of `tests/` from the results. |
| `run.sh` | Runs the binary on one program under a named configuration. |
| `results/` | Raw results (`.jsonl`) and the text summaries quoted in the design. |
