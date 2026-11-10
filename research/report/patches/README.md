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
HYLO_TC_EXPERIMENTS=occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo .build/release/tc-bench program.hylo
```

| Variable | Meaning |
|---|---|
| `HYLO_TC_EXPERIMENTS` | Comma-separated techniques to enable. Add `trace` to print each completed proof. |
| `HYLO_TC_BUDGET` | The limit used by `budget` (default 100,000 live alternatives). |
| `HYLO_TC_MAXDEPTH` | The search depth cap (default 10). |
| `HYLO_TC_ABSDEPTH` | The cut-off depth of the abstract model (default 2). |

The correctness fixes depend on each other and should be enabled, or merged, together:
- `fixsubst` needs `occurs` (otherwise cyclic bindings crash);
- `fixsubst` also needs `eqsolve` (otherwise equality chains hit the depth cap).

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

Patches 0005 and 0007 also contain two rejected experiments (`coercememo`, `eqrefute`, `cyclecut`), still behind flags that are off by default. They can be dropped when merging.
