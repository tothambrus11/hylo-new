# Type-checker speed-up techniques

One document per technique. Each document covers:
- how the technique works;
- why it is sound, i.e. why the elaboration and the diagnostics are unchanged, or else why the technique is retired;
- which programs it speeds up, with measurements;
- what it costs.

Every technique sits behind a runtime flag: `HYLO_TC_EXPERIMENTS=a,b,…` (see `Sources/FrontEnd/Typer/TyperCounters.swift`).

## Status

| Flag | Area | Status | Doc |
|---|---|---|---|
| `symindex` | stdlib symbol table | sound, recommended | [symindex.md](symindex.md) |
| `memberskip` | member lookup through extensions | sound, recommended (replaces `names`) | [memberskip.md](memberskip.md) |
| `traitindex` | member lookup through traits | sound, recommended | [traitindex.md](traitindex.md) |
| `coesrc` | coercion-derivability pre-check | sound, recommended | [coesrc.md](coesrc.md) |
| `index` | implicit resolution: candidate selection | sound, recommended | [index.md](index.md) |
| `absmodel` | implicit resolution: refutation ("will fail") | sound after the round-2 fixes, recommended | [absmodel.md](absmodel.md) |
| `unify` | unification constant factor | sound in release builds, recommended | [unify.md](unify.md) |
| `coercememo` | memo of coercion queries under assumptions | sound, **no measurable gain**, not recommended | [coercememo.md](coercememo.md) |
| `names` | member lookup through extensions | **unsound**, retired | [names.md](names.md) |
| `loopcheck` | implicit resolution: ancestor loop check | **unsound**, retired | [loopcheck.md](loopcheck.md) |
| `solver` | overload resolution: deferred branching | **unsound**, needs a redesign | [solver.md](solver.md) |

**Soundness oracle.** `research/exp/tcx.py semtest` compares a dump of every type, every name binding (including implicit and witness arguments), every witness table and every diagnostic against the baseline. Unless a document says otherwise, "identical" means identical on:
- the 192 compiler tests;
- the 24 workloads;
- the topic's review programs (`research/review/<topic>/`).

**Measurements.** "Speed" numbers are user-typing times in ms, best of `--repeat 3`, pinned to one core. They are single runs on a 4-core cloud VM, so treat differences under about 10% as noise. Raw numbers: `research/round3/bench.md`.
