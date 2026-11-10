"""Prints one line per program of p/ with its verdict under each configuration (from results.jsonl,
for the current content of the file). `--md` writes RESULTS.md."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = ["FULL", "NEW", "NEW+selfcheck", "NEW-premsubst", "FULL+premsubst"]
def rows(only=None):
    rs = {}
    for l in open(os.path.join(HERE, "results.jsonl")):
        r = json.loads(l); rs[(r["program"], r["sha"], r["config"])] = r
    out = []
    for f in sorted(os.listdir(os.path.join(HERE, "p"))):
        if not f.endswith(".hylo") or (only and not any(f.startswith(o) for o in only)): continue
        path = os.path.join(HERE, "p", f)
        sha = hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]
        lines = open(path).read().splitlines()
        what = " ".join(l[2:].strip() for l in lines[:12] if l.startswith("//"))
        row = {"program": f, "what": what, "runs": {c: rs.get(("p/" + f, sha, c)) for c in CONFIGS}}
        out.append(row)
    return out
def short(r):
    if r is None: return "-"
    v = r["verdict"]
    if r["violations"]: v += "!VIOL"
    if r["counters"].get("premsubst.stuck"): v += "!STUCK"
    return v
if __name__ == "__main__":
    a = sys.argv[1:]
    md = "--md" in a
    a = [x for x in a if x != "--md"]
    rs = rows(a)
    if md:
        with open(os.path.join(HERE, "RESULTS.md"), "w") as o:
            o.write("# Results\n\nOne row per program of `p/`. Verdicts of binary `eq22-554540c3a507`; `NEW-premsubst` is NEW without the flag, "
                    "`FULL+premsubst` is FULL with it. `!VIOL` marks a `[selfcheck] VIOLATION` line, `!STUCK` a positive `premsubst.stuck`. "
                    "The last column is the first comment of the program (what it tests and the correct verdict). Raw output: `results.jsonl`.\n\n")
            o.write("| Program | " + " | ".join(CONFIGS) + " | First message under NEW | What it tests |\n|---|" + "---|" * (len(CONFIGS) + 2) + "\n")
            for r in rs:
                n = r["runs"]["NEW"]
                msg = ((n["violations"] or n["errors"] or [""])[0][:90] if n else "").replace("|", "\\|")
                o.write(f"| `{r['program']}` | " + " | ".join(short(r["runs"][c]) for c in CONFIGS) + f" | {msg} | {r['what'].replace('|', chr(92) + '|')} |\n")
    else:
        for r in rs:
            n = r["runs"]["NEW"]
            cs = " ".join(f"{k.split('.')[-1][:5]}={v}" for k, v in (n["counters"].items() if n else []) if k.startswith("premsubst") or k in ("eqsolve.premises", "summon.depthExhausted"))
            msg = (n["errors"] or [""])[0][:70] if n else ""
            print(f"{r['program'][:44]:44} " + " ".join(f"{short(r['runs'][c])[:7]:7}" for c in CONFIGS) + f" {cs} | {msg}")
