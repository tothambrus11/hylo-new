"""Copies the follow-up material into this archive (follow-up/), from ../followup.

usage: python3 collect.py
Only documents, test programs, scripts and small result files are copied; raw data that can be
regenerated stays in ../followup."""
import glob, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "followup"); DST = os.path.join(HERE, "follow-up")
def cp(src, dst):
    s = os.path.join(SRC, src); d = os.path.join(DST, dst)
    if not os.path.exists(s): print("missing", src); return
    os.makedirs(os.path.dirname(d), exist_ok=True)
    if os.path.isdir(s):
        if os.path.exists(d): shutil.rmtree(d)
        shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__", "*.jsonl", "*.log", "*.dump", "scratch", "current.jsonl"))
    else: shutil.copyfile(s, d)
for old in ["ablation.jsonl", "ablation.py", "greedy-stdlib.json", "greedy.py", "permute-base.jsonl", "permute-full.jsonl", "permute.py",
            "witness-oracle.jsonl", "witness_oracle.py"]:
    p = os.path.join(DST, old)
    if os.path.exists(p): os.remove(p)
for name in ["order", "eqnorm", "engine", "overload"]:
    cp(f"design-{name}/DESIGN.md", f"designs/{name}.md"); cp(f"design-{name}/tests", f"design-{name}/tests")
for name in ["assoc", "sigrounds", "premsubst", "headsubst"]:
    cp(f"attack-{name}/README.md", f"attack-{name}/README.md"); cp(f"attack-{name}/p", f"attack-{name}/p")
    if os.path.exists(os.path.join(SRC, f"attack-{name}/JUDGEMENT.md")): cp(f"attack-{name}/JUDGEMENT.md", f"attack-{name}/JUDGEMENT.md")
for f in ["README.md", "JUDGEMENT.md", "spec.md", "hand", "minimized", "judge/p", "tables.md"]: cp("reference/" + f, "reference/" + f)
for f in ["README.md", "JUDGEMENT.md", "judge/progs", "violations"]: cp("metamorphic/" + f, "metamorphic/" + f)
for f in ["README.md", "gen.py"]: cp("scaling/" + f, "scaling/" + f)
for f in ["README.md", "analysis.md", "examples"]: cp("mutation/" + f, "mutation/" + f)
for f in ["README.md", "benchmarks", "results/tables.md", "bench-results.md", "census.py"]: cp("usage/" + f, "usage/" + f)
cp("headsubst/tests", "headsubst/tests"); cp("sigrounds/tests", "sigrounds/tests"); cp("overload", "overload")
for f in ["tcrun.py", "regress.py", "compare2.py", "final_timing.py", "selfcheck.py", "census.py", "greedy.py", "ablation.py", "permute.py",
          "witness_oracle.py", "timing.py", "BRIEF.md", "BRIEF2.md", "REVIEW-AND-PLAN.md"]:
    cp(f, "scripts/" + f)
cp("sigrounds/orders.py", "scripts/orders.py"); cp("profile/sample.py", "scripts/sample.py")
for f in ["compare-final.jsonl", "compare-rec.jsonl", "final-timing.jsonl", "greedy-stdlib.json", "ablation.jsonl", "census.json", "oracle-final.txt",
          "witness-oracle.jsonl", "permute-full.jsonl", "permute-base.jsonl", "selfcheck.jsonl"]:
    if os.path.exists(os.path.join(SRC, f)): shutil.copyfile(os.path.join(SRC, f), os.path.join(DST, "data", f)) if os.makedirs(os.path.join(DST, "data"), exist_ok=True) is None else None
if os.path.exists(os.path.join(SRC, "sigrounds/order-final.jsonl")): shutil.copyfile(os.path.join(SRC, "sigrounds/order-final.jsonl"), os.path.join(DST, "data", "order-final.jsonl"))
for f in ["compare-joint.jsonl", "compare-eqsize.jsonl", "witness-size.jsonl", "size-parity.jsonl", "oracle-eq48.txt"]:
    if os.path.exists(os.path.join(SRC, "answers", f)):
        os.makedirs(os.path.join(DST, "data", "answers"), exist_ok=True); shutil.copyfile(os.path.join(SRC, "answers", f), os.path.join(DST, "data", "answers", f))
n = sum(len(fs) for _, _, fs in os.walk(DST)); print("follow-up:", n, "files")
