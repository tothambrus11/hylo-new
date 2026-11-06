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
| `typevec` | type-store storage | sound, recommended | [typevec.md](typevec.md) |
| `coercememo` | memo of coercion queries under assumptions | sound, **no measurable gain**, not recommended | [coercememo.md](coercememo.md) |
| `occurs`, `arrowenv` | **fix**: occurs check in unification (now DAG-linear, root case fixed, arrow environments visible) | semantic fix, final configuration | [occurs.md](occurs.md) |
| `fixsubst` | **fix**: keep substitutions when `match` assumes coercions | semantic fix of bug #1's root cause; requires `occurs` and `eqsolve` | [../round3/soundness.md §1–2](../round3/soundness.md) |
| `eqsolve` | **fix**: decide closed equality goals by congruence closure (with abstract-projection bans, premise projections and search-equivalent costs) | semantic fix + speed-up, final configuration | [eqsolve.md](eqsolve.md) |
| `eqmgu` | **fix**: solve `?v ~ X` by its most general unifier | semantic fix + speed-up, final configuration | [eqmgu.md](eqmgu.md) |
| `extorder` | **fix**: order-independent extension lookup (deferred circularity check) | semantic fix, final configuration (replaces `cyclecut`) | [extorder.md](extorder.md) |
| `givencheck` | **fix**: givens skipped while their type is computed are checked afterwards | semantic fix, final configuration | [givencheck.md](givencheck.md) |
| `budget` | **fix**: abandon and report runaway resolutions instead of exhausting memory | semantic fix, final configuration | [budget.md](budget.md) |
| `absquotient` | `absmodel` stays conclusive under ground equalities | sound, recommended (FULL) | [absquotient.md](absquotient.md) |
| `reifymemo` | reify each subterm once | sound, recommended (FULL) | [reifymemo.md](reifymemo.md) |
| `eqrefute` | refute equality goals outside the equivalence classes | **unsound as implemented**; superseded by `eqsolve` | [../round3/soundness.md §1](../round3/soundness.md) |
| `cyclecut` | transactional evaluation across cycle cuts | **unsound**; superseded by `extorder` | [../round3/soundness.md §5](../round3/soundness.md) |
| `names` | member lookup through extensions | **unsound**, retired | [names.md](names.md) |
| `loopcheck` | implicit resolution: ancestor loop check | **unsound**, retired | [loopcheck.md](loopcheck.md) |
| `solver` | overload resolution: deferred branching | **unsound**, needs a redesign | [solver.md](solver.md) |

**Soundness oracle.** `research/exp/tcx.py semtest` compares a dump of every type, every name binding (including implicit and witness arguments), every witness table and every diagnostic against the baseline. Unless a document says otherwise, "identical" means identical on:
- the 192 compiler tests;
- the 24 workloads;
- the topic's review programs (`research/review/<topic>/`).

**Measurements.** "Speed" numbers are user-typing times in ms, best of `--repeat 3`, pinned to one core. They are single runs on a 4-core cloud VM, so treat differences under about 10% as noise. Raw numbers: `research/round3/bench.md`.

## Final configuration

- **FIX** (semantic fixes only): `occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget`.
- **FULL**: FIX plus `symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo`.

Both are 216/216 identical to the baseline on the corpus (`../round3/soundness/oracle-final-config.txt`). Every program of both adversarial reviews is re-run in `../round3/soundness/regress-final.md`, and the timings are in `../round3/soundness/bench-final.md`. The write-up is `../round3/soundness.md`, section "Final configuration".

## All sound flags together

`symindex, coesrc, traitindex, memberskip, unify, index, absmodel, typevec` (`../round3/bench.md`, ms):

| stdlib | members-big | breadth40 | div-loop-20 | div-branch | wide-tuple-5 | trans-8 | assoceq-5 | coerc-cache | refine-8 | nestwide-8 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1007 → **235** (4.3×) | 20109 → 959 (21×) | 7424 → 79 (94×) | 191 → 5 (42×) | 2220 → 3 (864×) | 85 → 5 (18×) | 1855 → 1375 (1.3×) | 2619 → 2000 (1.3×) | 3532 → 2771 (1.3×) | 78 → 6 (13×) | 99 → 9 (11×) |

Equality reasoning (`trans`, `assoceq`, `coerc-cache`) is the one pattern that is still slow: only `typevec` helps there. See `../round3/README.md` §2.
