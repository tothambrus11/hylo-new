#!/usr/bin/env python3
"""Records, for every program of Tests/CompilerTests, the verdict and the sigrounds counters of the
user module under FULL+sigrounds (binary eq17), one process at a time (through tcb.sh).

usage: review_corpus_rounds.py OUT.jsonl      Restartable.
"""
import glob, json, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
out = sys.argv[1]
done = {json.loads(l)["file"] for l in open(out)} if os.path.exists(out) else set()
with open(out, "a") as o:
    for f in sorted(glob.glob("/home/user/hylo-new/Tests/CompilerTests/*/*.hylo")):
        if f in done: continue
        p = subprocess.run([os.path.join(here, "tcb.sh"), "eq17-4c2982653305", FULL + ",sigrounds", "--count", f],
                           capture_output=True, text=True, timeout=600)
        u = re.search(r"counters.user:(.*)", p.stdout)
        m = re.search(r"diagnostics: (\d+)", p.stdout)
        c = {k: int(v) for k, v in (x.split("=") for x in (u.group(1).split() if u else [])) if k.startswith("sigrounds")}
        errs = sorted(re.sub(r"^.*?: error: ", "", l.strip()) for l in p.stdout.splitlines() if ": error: " in l)
        o.write(json.dumps({"file": f, "exit": p.returncode, "verdict": "accept" if m and m.group(1) == "0" else "reject",
                            "errors": errs, "sigrounds": c}) + "\n"); o.flush()
