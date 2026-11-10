"""Lists the candidate source programs and records their unmutated results under every configuration.
Restartable: rows already in baseline.jsonl are skipped."""
import glob, json, os, sys
import tc

def sources():
    out = []
    for f in sorted(glob.glob(os.path.join(tc.ROOT, "Tests/CompilerTests/positive/*.hylo"))):
        out.append(("tests", f))
    for f in sorted(glob.glob(os.path.join(tc.ROOT, "research/workloads/*.hylo"))):
        if os.path.basename(f) != "empty.hylo": out.append(("workloads", f))
    for f in sorted(glob.glob(os.path.join(tc.ROOT, "research/workloads/round3/*.hylo"))):
        out.append(("round3", f))
    return out

def corpus():
    """Programs of research/report/test-programs that both the old and the new checker accept (per INDEX.md)."""
    import re
    out = []
    root = os.path.join(tc.ROOT, "research/report/test-programs")
    for d in sorted(os.listdir(root)):
        idx = os.path.join(root, d, "INDEX.md")
        if not os.path.exists(idx): continue
        for ln in open(idx):
            m = re.match(r"\| `([^`]+\.hylo)` \| accepted \| accepted \|", ln)
            if m and os.path.exists(os.path.join(root, d, m.group(1))):
                out.append(("corpus", os.path.join(root, d, m.group(1))))
    return out

def stdlib_files():
    out = []
    for d, _, fs in os.walk(tc.ORIG_STD):
        for f in fs:
            if f.endswith(".hylo"): out.append(os.path.relpath(os.path.join(d, f), tc.ORIG_STD))
    return sorted(out)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "main"
    path = os.path.join(tc.HERE, "baseline.jsonl" if which == "main" else "baseline-corpus.jsonl")
    done = set()
    if os.path.exists(path):
        for ln in open(path):
            r = json.loads(ln)
            if "all" in r: done.add((r["file"], r["config"]))   # early rows lack the full counters: redone
    with open(path, "a") as out:
        todo = [("stdlib", "<stdlib>")] + sources() if which == "main" else corpus()
        for src, f in todo:
            for name, flags in tc.CONFIGS.items():
                rel = f if f == "<stdlib>" else os.path.relpath(f, tc.ROOT)
                if (rel, name) in done: continue
                r = tc.run(tc.EMPTY if f == "<stdlib>" else f, flags, timeout=120 if which == "main" else 30)
                row = {"source": src, "file": rel, "config": name}
                row.update(tc.summarize(r, "stdlib" if f == "<stdlib>" else "user"))
                out.write(json.dumps(row) + "\n"); out.flush()
                print(src, rel, name, row["status"], row["diags"], row["matches"], row["ms"], flush=True)
