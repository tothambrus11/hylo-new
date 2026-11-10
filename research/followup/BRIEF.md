# Shared brief for follow-up work on the Hylo type checker

Read this first. It gives the context, the tools and the rules that every task shares.

## Context

Hylo's type checker spends most of its time in *implicit resolution*: finding a derivation of a goal such as `T is P` (internally `P<T>`) or `A ~ B` from the *givens* in scope (conformance declarations, where-clause requirements, built-in equality rules). A set of optimizations and soundness fixes has been implemented behind runtime flags. A critical review found which parts are solid and which are not. Your task is one item of the follow-up plan.

Background reading, in order of usefulness:
- `/home/user/hylo-new/research/followup/REVIEW-AND-PLAN.md`: the review and the plan (your task comes from it).
- `/home/user/hylo-new/research/report/techniques/*.md`: one document per technique.
- `/home/user/hylo-new/research/report/soundness/*.md`: the soundness problems of the existing checker.
- `/home/user/hylo-new/research/report/rejected/README.md`: approaches that change results.
- `/home/user/hylo-new/research/report/test-programs/*/INDEX.md`: about 540 small programs with verdicts.

## Source code (read-only)

`/home/user/hylo-impl` is the compiler with every patch applied. **Do not modify it and do not build it.** Key places:
- `Sources/FrontEnd/Typer/Typer.swift`: the type checker.
  - Resolution: `summon`, `formThread`, `match`, `threadContinuation`, `takeSummonResults`, `canDeriveCoercions`, `coerced`.
  - Equality procedure: `solveEquality`, `mostGeneralEqualityThread`.
  - Abstract model glue: `abstractModel`, `mayDerive`, `equalityOpaqueTypes`, `indexedSummon`.
  - Member lookup: `resolve(_:declaredIn:applyingTo:in:statically:)`, `applies`, `extendeeType`.
  - Order-dependence fixes: `noteExtensionCycle`, `popExtensionFrame`, `recordSkippedGivens`, `checkPendingGivens`, `mayMatch`.
  - `declarationsOnStack` is the set of declarations whose type is being computed (hidden from lookups).
- `Sources/FrontEnd/Typer/AbstractResolution.swift`: the abstract model.
- `Sources/FrontEnd/Typer/Solver.swift`: the constraint solver (overload resolution).
- `Sources/FrontEnd/Types/TypeStore.swift`: unification (`unifiable`), `reify`.
- `Sources/FrontEnd/Typer/TyperCounters.swift`: every flag and counter.

## The type-checker binary

```
B=/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench
HYLO_TC_EXPERIMENTS=<flags> timeout 60 $B [--count] [--dump FILE] [--repeat N] program.hylo
```

It parses, scopes and type-checks the standard library and the program, then prints:
- `counters.stdlib:` and `counters.user:` (only with `--count`): work counters for each module;
- `diagnostics: N` followed by the error messages (N = 0 means the program is accepted);
- phase timings in ms (`type.stdlib`, `type.user`).

A crash gives a non-zero exit code (139 = stack overflow, 134 = out of memory; the wrapper caps memory at 2.5 GB).

Configurations (`HYLO_TC_EXPERIMENTS`, comma-separated):
- **base**: empty string. The existing checker.
- **FIX**: `occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget`
- **FULL**: FIX + `,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo`
- **MIN5**: `index,memberskip,typevec,symindex,traitindex` (result-preserving, gives most of the real-code gain)
- Add `trace` to print every completed resolution with its derivations and penalties.

Other environment variables: `HYLO_TC_MAXDEPTH` (search depth bound, default 10), `HYLO_TC_BUDGET` (frontier limit of `budget`, default 100000), `HYLO_TC_ABSDEPTH` (abstract model depth, default 2).

Useful counters: `summon.calls`, `summon.subgoals`, `summon.matches` (candidate givens tried), `summon.layers`, `summon.depthExhausted`, `summon.budgetExhausted`, `coerced.slowPath`, `solver.forks`, `solver.overloads`, `absmodel.refuted`, `index.skipped`, `eqsolve.proved`, `eqsolve.refuted`, `eqsolve.untrusted`, `eqmgu.solved`, `names.appliesCalls` (extension applicability tests).

## Rules

1. **Never build the compiler** (`swift build` is forbidden) and never modify `/home/user/hylo-impl`. Compiler changes are made by the coordinator, one at a time.
2. **Run at most one `tc-bench` process at a time**, always under `timeout` (60 s unless you need more). Other tasks share this 4-core machine.
3. **Wall-clock times are unreliable here**, because other jobs run concurrently. Use the work counters as the primary cost metric. Report times only as indicative, and say so.
4. Write only inside your output directory (given in your task) under `/home/user/hylo-new/research/followup/`. Do not commit or push.
5. Do not trust a program you wrote until the existing checker (base) parses it: a message containing `expected` or `is not a valid identifier` is a syntax error in your program, not a finding. Copy syntax from `/home/user/hylo-new/Tests/CompilerTests/positive/*.hylo` and from the test programs.
6. Claims must be reproducible: keep the scripts (restartable, with raw results in `.jsonl`), and state for each finding the exact program and configuration.
7. Write the README of your output directory for a human reader: plain sentences, what was asked, what was done, what was found, what remains uncertain. No history of your process.

## Hylo syntax, by example

```hylo
trait P { type X }                                   // trait with an associated type
trait Q {}
struct A { public memberwise init }
struct Box<T> { public memberwise init }
given A is P { type X = A }                          // conformance
given <T where T is Q> => Box<T> is Q {}             // conditional generic conformance (note the =>)
fun need<T where T is Q>() {}
fun check<T>(x: T) {}
fun f<T, U where T == U, T is P>(x: U.X) {           // equality and conformance requirements
  check<T.X>(x)                                      // uses T.X == U.X
}
extension <T where T is P> Box<T> { fun first() {} } // conditional extension
extension A { type Me = A }                          // extension adding a member type
type Alias = A.Me                                    // type alias
public fun main() { need<Box<A>>() }                 // ill-typed unless A is Q
```

A first line `//! stage:typing no-std` appears in some tests; it is a directive for the test driver and harmless here.
