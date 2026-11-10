#!/usr/bin/env python3
"""Judge's re-runs. usage: j.py [-c base,FIX,FULL] [-t] [-e ENV=V ...] FILE...
Type-checks each file under each configuration (one tc-bench process at a time, 60 s limit)
and prints verdict and diagnostics. Every run is appended to judge/results.jsonl."""
import fcntl, hashlib, json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"base": "", "FIX": FIX,
           "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"}
OUT = os.path.join(HERE, "results.jsonl")
LOCK = os.path.join(HERE, ".lock")

def run(path, config, extra="", env=None, timeout=60, count=False):
    flags = CONFIGS[config] + ((("," if CONFIGS[config] else "") + extra) if extra else "")
    e = dict(os.environ, HYLO_TC_EXPERIMENTS=flags); e.update(env or {})
    with open(LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        t0 = time.time()
        p = subprocess.run(["timeout", str(timeout), B] + (["--count"] if count else []) + [path], env=e, capture_output=True, text=True, errors="replace")
        ms = int((time.time() - t0) * 1000)
    out = p.stdout
    errs = []
    for l in out.splitlines():
        m = re.match(r"^\s*.*?\.hylo:(\d+)\.\d+(?:-\d+(?:\.\d+)?)?: (error|warning|note): (.*)$", l)
        if m: errs.append("%s: L%s: %s" % (m.group(2), m.group(1), m.group(3)))
    rc = p.returncode
    if rc == 124: v = "timeout"
    elif rc != 0: v = "crash:%d" % rc
    elif "diagnostics:" not in out: v = "crash:noout"
    else: v = "reject" if any(x.startswith("error") for x in errs) else "accept"
    r = {"file": os.path.relpath(os.path.abspath(path), os.path.dirname(HERE)), "sha": hashlib.sha1(open(path, "rb").read()).hexdigest(),
         "config": config, "extra": extra, "env": env or {}, "verdict": v, "errors": errs, "ms": ms}
    with open(OUT, "a") as f: f.write(json.dumps(r) + "\n")
    return r, out

if __name__ == "__main__":
    a = sys.argv[1:]; configs = ["base", "FIX", "FULL"]; trace = False; env = {}; count = False
    while a and a[0].startswith("-"):
        if a[0] == "-c": configs = a[1].split(","); a = a[2:]
        elif a[0] == "-t": trace = True; a = a[1:]
        elif a[0] == "-n": count = True; a = a[1:]
        elif a[0] == "-e": k, v = a[1].split("=", 1); env[k] = v; a = a[2:]
    for f in a:
        for c in configs:
            r, out = run(f, c, "trace" if trace else "", env, count=count)
            print("%-5s %-9s %s" % (c, r["verdict"], f))
            for x in r["errors"]: print("        " + x)
            if trace:
                os.makedirs(os.path.join(HERE, "traces"), exist_ok=True)
                tp = os.path.join(HERE, "traces", r["file"].replace("/", "__") + "." + c + ".txt")
                open(tp, "w").write(out); print("   trace: " + tp)
            if count:
                for l in out.splitlines():
                    if count and l.startswith("counters.user"): print("   " + l)
