#!/usr/bin/env python3
"""Re-runs chosen (file, configuration) points and appends the raw result to recheck.jsonl.

usage: python3 rerun.py CONFIG[,CONFIG...] FILE... [--timeout N] [--env K=V]...
CONFIG is base, FIX, FULL, or FIX+flag / FULL-flag / FIX-flag (comma-free edits of the flag list).
One checker process at a time.  Every counter of the user module and every message is kept.
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
def flags(c):
    m = re.match(r"(base|FIX|FULL)((?:[+-]\w+)*)$", c)
    fs = {"base": [], "FIX": FIX.split(","), "FULL": FULL.split(",")}[m.group(1)]
    for op, f in re.findall(r"([+-])(\w+)", m.group(2)):
        if op == "+": fs = fs + [f]
        else: fs = [x for x in fs if x != f]
    return ",".join(fs)
def main():
    args = sys.argv[1:]; timeout = 60; extra = {}
    while "--timeout" in args:
        i = args.index("--timeout"); timeout = int(args[i + 1]); del args[i:i + 2]
    while "--env" in args:
        i = args.index("--env"); k, v = args[i + 1].split("="); extra[k] = v; del args[i:i + 2]
    configs = args[0].split(","); files = args[1:]
    with open(os.path.join(HERE, "recheck.jsonl"), "a") as out:
        for f in files:
            for c in configs:
                env = dict(os.environ, HYLO_TC_EXPERIMENTS=flags(c), **extra)
                p = subprocess.run(["timeout", str(timeout), B, "--count", f], env=env, capture_output=True, text=True)
                rec = {"file": os.path.relpath(os.path.abspath(f), os.path.dirname(HERE)), "config": c, "env": extra, "timeout": timeout,
                       "sha1": hashlib.sha1(open(f, "rb").read()).hexdigest(), "exit": p.returncode,
                       "diagnostics": None, "messages": [], "user": {}, "stdlib": {}, "type_user_ms": None}
                for l in p.stdout.split("\n"):
                    for mod in ("user", "stdlib"):
                        if l.startswith("counters.%s:" % mod):
                            for kv in l.split()[1:]:
                                a, b = kv.split("="); rec[mod][a] = int(b)
                    if l.startswith("diagnostics:"): rec["diagnostics"] = int(l.split()[1])
                    elif l.startswith("type.user"): rec["type_user_ms"] = float(l.split()[1])
                    m = re.match(r"\s+\S+\.hylo:(\d+)\.[\d-]+: (error|warning): (.*)$", l)
                    if m: rec["messages"].append([int(m.group(1)), m.group(3)[:600]])
                out.write(json.dumps(rec) + "\n"); out.flush()
                u = rec["user"]
                keys = ["summon.calls", "summon.matches", "summon.layers", "summon.depthExhausted", "summon.budgetExhausted", "eqsolve.proved", "eqsolve.refuted", "eqsolve.untrusted", "eqmgu.solved", "index.unavailable", "index.skipped", "absmodel.refuted"]
                print("%s [%s] exit=%s diag=%s %s t=%s" % (rec["file"], c, rec["exit"], rec["diagnostics"], " ".join("%s=%s" % (k.split(".", 1)[1] if not k.startswith(("index", "abs", "eqmgu")) else k, u.get(k, 0)) for k in keys), rec["type_user_ms"]))
                for ln, msg in rec["messages"]: print("    line %d: %s" % (ln, msg[:300]))
                if p.returncode not in (0, 124) : print("    stderr:", p.stderr[-300:].replace("\n", " | "))
main()
