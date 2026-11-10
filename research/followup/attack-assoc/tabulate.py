"""Writes RESULTS.md from results.jsonl and permute.jsonl: one row per program, one column per configuration.

A cell is `accept`, `reject(n)` with n the number of diagnostics, `timeout` or `crash N`; an empty
cell means the configuration was not run. Only the records of the current text of each program are used."""
import glob, hashlib, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["base", "FULL", "NEW", "NEW+selfcheck", "FULL+assocsubst", "NEW-assocsubst", "FULL+abstractstrict",
        "NEW-abstractstrict", "FULL+headsubst", "NEW-headsubst"]
rows = {}
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l); rows[(r["sha"], r["config"])] = r
def cell(r):
    if r is None: return ""
    v = r["verdict"] + (f"({len(r['errors'])})" if r["verdict"] == "reject" else "")
    return v + (" VIOLATION" if r["violations"] else "")
def table(files, out):
    out.append("| program | " + " | ".join(COLS) + " | what it tests |")
    out.append("|" + "---|" * (len(COLS) + 2))
    for f in files:
        text = open(f).read(); sha = hashlib.sha1(text.encode()).hexdigest()[:12]
        first = [l[2:].strip() for l in text.splitlines() if l.startswith("//")]
        out.append(f"| `{os.path.relpath(f, HERE)}` | " + " | ".join(cell(rows.get((sha, c))) for c in COLS)
                   + " | " + (first[0] if first else "") + " |")
out = ["# Results", "",
       "Binary `eq22-554540c3a507`. Columns are configurations of `run.py` (`X-flag` is X without the flag, `X+flag` is X with it).",
       "Raw records, with every diagnostic: `results.jsonl`. Regenerate with `python3 tabulate.py`.", "",
       "## Attack programs (`p/`)", ""]
table(sorted(glob.glob(os.path.join(HERE, "p", "*.hylo"))), out)
out += ["", "## Permutations of the where clause and of the parameters of e02 (`p/wo/`)", ""]
table(sorted(glob.glob(os.path.join(HERE, "p", "wo", "*.hylo"))), out)
out += ["", "## Permutations of top-level declarations under NEW (`permute.py`, files in `perm/`)", "",
        "| program | permutations | verdicts |", "|---|---|---|"]
perm = {}
if os.path.exists(os.path.join(HERE, "permute.jsonl")):
    for l in open(os.path.join(HERE, "permute.jsonl")):
        r = json.loads(l); perm.setdefault(r["program"], {})[r["sha"]] = (r["verdict"], len(r["errors"]))
for p in sorted(perm):
    vs = {}
    for v in perm[p].values(): vs[v] = vs.get(v, 0) + 1
    out.append(f"| `{p}` | {len(perm[p])} | " + "; ".join(f"{v}({e}) x{n}" if v == "reject" else f"{v} x{n}" for (v, e), n in vs.items()) + " |")
open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(out) + "\n")
print(len(out), "lines")
