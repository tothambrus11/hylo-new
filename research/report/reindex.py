"""Adds the verdicts of the recommended configuration to the indexes of test-programs/.

usage: python3 reindex.py ../followup/compare-final.jsonl
The column "Final" is the verdict under the recommended configuration (every fix and technique of
the report except the experiments); "New" stays the verdict of the first half of the work."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rows = {}
for l in open(sys.argv[1]):
    r = json.loads(l)
    if "test-programs/" in r["file"]:
        rows[r["file"].split("test-programs/")[1]] = r
W = {"accept": "accepted", "reject": "rejected", "timeout": "timeout"}
for topic in sorted(os.listdir(os.path.join(HERE, "test-programs"))):
    p = os.path.join(HERE, "test-programs", topic, "INDEX.md")
    if not os.path.exists(p): continue
    out, n, changed = [], 0, 0
    for line in open(p).read().split("\n"):
        m = re.match(r"\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|(?: ([^|]*) \|)? (.*) \|$", line)
        if line.startswith("| Program |"):
            out.append("| Program | Old | New | Final | First error (final) |"); continue
        if line.startswith("|---"):
            out.append("|---|---|---|---|---|"); continue
        if line.startswith("Verdicts of the existing implementation"):
            out.append('Verdicts of the existing implementation ("Old"), of the revised implementation of the first half of the work with all its techniques ("New"), and of the recommended configuration of the report ("Final"), with a 30 s limit ("Final": 60 s).'); continue
        if not m: out.append(line); continue
        name, old, new = m.group(1), m.group(2).strip(), m.group(3).strip()
        r = rows.get(topic + "/" + name)
        if r is None: out.append(f"| `{name}` | {old} | {new} | not run | |"); continue
        v = r["new"]["verdict"]; f = W.get(v, "crash" if v.startswith("crash") else v)
        e = (r["new"]["errors"] or [""])[0].replace("|", "\\|")[:150]
        n += 1; changed += f != new
        out.append(f"| `{name}` | {old} | {new} | {f} | {e} |")
    open(p, "w").write("\n".join(out))
    print(topic, n, "programs,", changed, "differ from New")
