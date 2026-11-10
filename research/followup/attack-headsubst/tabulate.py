"""Writes RESULTS.md from results.jsonl: one row per program of p/, one column per configuration
(latest run on the binary BIN), with what the program tests and the correct verdict, both read
from its first comment. A cell is the verdict and the number of diagnostics.
usage: tabulate.py"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
BIN = "eq34-6718f1de213f"; OLD = "eq30-ae138265e872"
CONFIGS = ["base", "FULL", "NEW", "NEW+selfcheck", "NEW-headsubst", "FULL+headsubst"]
last, old = {}, {}
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l)
    if r["bin"] == BIN: last[(r["program"], r["config"])] = r
    if r["bin"] == OLD: old[(r["program"], r["config"])] = r
def cell(r):
    if r is None: return "-"
    v = {"accept": "accept", "reject": "reject %d" % len(r["errors"])}.get(r["verdict"], r["verdict"])
    return v + (" VIOLATION" if r["violations"] else "")
def comment(path):
    lines = []
    for l in open(path):
        if not l.startswith("//"): break
        lines.append(l[2:].strip())
    text = " ".join(lines)
    m = re.search(r"Correct verdict: *(.*)$", text)
    tests = re.sub(r"Correct verdict:.*$", "", text).strip()
    tests = re.sub(r"^Tests: *", "", tests)
    return tests, (m.group(1) if m else "")
rows = []
for f in sorted(os.listdir(os.path.join(HERE, "p"))):
    if not f.endswith(".hylo"): continue
    p = "p/" + f; tests, correct = comment(os.path.join(HERE, p))
    rows.append((f, tests, correct, [cell(last.get((p, c))) for c in CONFIGS]))
with open(os.path.join(HERE, "RESULTS.md"), "w") as o:
    o.write("# Results\n\nBinary `%s`. A cell is the verdict and the number of diagnostics. " % BIN)
    o.write("`NEW-headsubst` is NEW without the flag; `FULL+headsubst` is FULL with it. ")
    o.write("Raw data, with every message and the `headsubst.*` counters: `results.jsonl`.\n\n")
    o.write("| Program | " + " | ".join(CONFIGS) + " | Correct verdict | What it tests |\n")
    o.write("|---|" + "---|" * len(CONFIGS) + "---|---|\n")
    for f, tests, correct, cells in rows:
        o.write("| `%s` | %s | %s | %s |\n" % (f, " | ".join(cells), correct.replace("|", "\\|"), tests.replace("|", "\\|")))
    changed = []
    for (p, c), r in sorted(old.items()):
        n = last.get((p, c))
        if c == "NEW" and n is not None and cell(r) != cell(n): changed.append((p, cell(r), cell(n)))
    o.write("\n## Programs whose verdict under NEW differs between `%s` and `%s`\n\n" % (OLD, BIN))
    o.write("Only the programs `a*` and `b*` were run on the older binary.\n\n")
    o.write("| Program | NEW on %s | NEW on %s |\n|---|---|---|\n" % (OLD[:4], BIN[:4]))
    for p, a, b in changed: o.write("| `%s` | %s | %s |\n" % (p[2:], a, b))
    viol = sorted({r["program"] for r in last.values() if r["violations"]})
    crash = sorted({(r["program"], r["config"], r["verdict"]) for r in last.values() if r["verdict"] not in ("accept", "reject")})
    o.write("\nSelf-check violations: %s. Crashes and timeouts: %s.\n" % (", ".join(viol) or "none", ", ".join(map(str, crash)) or "none"))
print(len(rows), "programs")
