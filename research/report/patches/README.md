# Patches

A `git format-patch` series against the Hylo front end, to be applied on top of branch `tc/research` of `tothambrus11/hylo-new`. That branch provides the benchmarking harness, the flag mechanism and the first techniques (`index`, `absmodel`, `unify`).

## Applying and building

```bash
git checkout -b type-checker-optimizations origin/tc/research
```

```bash
git am patches/*.patch
```

```bash
git submodule update --init
```

```bash
swift build -c release --product tc-bench
```

A clean release build takes about 20 minutes on 4 cores, and needs up to 3.5 GB of memory. Avoid running several builds at once.

## Running

```bash
HYLO_TC_EXPERIMENTS=index,typevec,symindex,traitindex,memberskip,twins,stackscan,coeset .build/release/tc-bench program.hylo
```

That list is the result-preserving set for the existing implementation. The recommended configuration adds the fixes and the techniques that depend on them:

```bash
HYLO_TC_EXPERIMENTS=index,typevec,symindex,traitindex,twins,stackscan,coeset,reifymemo,occurs,fixsubst,eqsolve,eqmgu,arrowenv,budget,sigrounds,assocsubst,abstractstrict,hidecache,aliasargs,premsubst,premcommit,headsubst,dedup,eqindex,eqeager,cleanfirst,lookahead .build/release/tc-bench program.hylo
```

| Variable | Meaning |
|---|---|
| `HYLO_TC_EXPERIMENTS` | Comma-separated techniques to enable. Add `trace` to print each completed proof, `selfcheck` to re-do the work each technique avoids and report disagreements, `census` to print one line per resolution. |
| `HYLO_TC_BUDGET` | The limit used by `budget` (default 100,000 live alternatives). |
| `HYLO_TC_MAXDEPTH` | The bound on the size of a derivation (default 10). |
| `HYLO_TC_HEIGHTBUDGET` | The work allowed past that bound with `heightbound` (default 100,000 candidate matches). |
| `HYLO_TC_ABSDEPTH` | The cut-off depth of the abstract model (default 2). |

Dependencies between flags:
- `fixsubst` needs `occurs` (otherwise cyclic bindings crash) and `eqsolve` (otherwise equality chains hit the bound);
- `premcommit` and `dedup` belong with `premsubst`; `headsubst` needs `assocsubst` and `abstractstrict`;
- `cleanfirst` and `lookahead` are result-preserving only with `sigrounds`;
- with `sigrounds`, the earlier order checks (`extorder`, `givencheck`) and `memberskip` are inactive.

## Contents

| Patch | Techniques |
|---|---|
| 0001 | `symindex`, `coesrc`; the abstract model's default depth becomes 2 |
| 0002–0003 | `traitindex`, `memberskip` |
| 0004 | soundness corrections to `absmodel` |
| 0005 | a coercion cache (rejected, kept behind a flag), and `HYLO_TC_MAXDEPTH` |
| 0006 | `typevec` |
| 0007 | `occurs`, `fixsubst`, and the `trace` option |
| 0008 | `eqsolve`, `extorder` |
| 0009 | `arrowenv`, `eqmgu`, `givencheck`; the congruence closure and proof costs of `eqsolve` |
| 0010 | `absquotient`, `budget`, `reifymemo`; pending-requirement projections in `eqsolve` |
| 0011 | `extorder` checks whole cycles of extensions |
| 0012 | per-constructor opacity in `absquotient`; the scope-level rule for `Self` projections in `eqsolve`; recorded assumptions in `givencheck` |
| 0013 | the semantic dump also records the witness selected at each elaborated site (validation only) |
| 0014 | `selfcheck`, `census`; equalities between method types; no crash on a case outside an enum |
| 0015–0016 | `eqindex`, `eqeager` |
| 0017 | `sigrounds`, `assocsubst` |
| 0018 | `premsubst`, `headsubst` |
| 0019 | `abstractstrict`; corrections to `eqindex` and `eqeager` |
| 0020 | experiments `eqfilter`, `eqouter`, `eqclass` |
| 0021 | `twins`, `cleanfirst`, `lookahead` |
| 0022 | corrections to `sigrounds`; experiment `heightbound` |
| 0023–0024 | corrections to `assocsubst`, `abstractstrict`, `headsubst`, `premsubst`; `premcommit`; the rule of `twins` for searches without failure |
| 0025 | `hidecache`, `aliasargs`; owner before member in `sigrounds` |
| 0026 | `coeset`, `stackscan` |
| 0027–0030 | memoized scans; `dedup`; corrections to `headsubst` and `aliasargs` |
| 0031 | the self-checking mode follows a thread whose head is bound to a premise for one more step |

Patches 0005 and 0007 also contain rejected experiments (`coercememo`, `eqrefute`, `cyclecut`), still behind flags that are off by default. They can be dropped when merging, as can `extorder`'s cycle rule, `givencheck` and `memberskip` once `sigrounds` is adopted.
