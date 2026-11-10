"""Type-checks programs under one or more configurations and prints one line per run.

usage: tcrun.py BINID CONFIG[;CONFIG...] FILE... [--counters prefix,prefix] [--timeout S]
A configuration is base, FIX, FULL, MIN5 or NEW, optionally followed by +flag+flag.
NEW is FULL with the cycle rules replaced by sigrounds, plus the later fixes."""
import os, re, subprocess, sys
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
PERF = "symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {"base": "", "FIX": FIX, "FULL": FIX + "," + PERF, "MIN5": "index,memberskip,typevec,symindex,traitindex",
           "NEW": FIX + "," + PERF + ",sigrounds,assocsubst,eqindex,eqeager,premsubst,headsubst,abstractstrict"}
def flags(config):
    parts = config.split("+")
    return ",".join(x for x in [CONFIGS.get(parts[0], parts[0])] + parts[1:] if x)
def run(binid, config, path, timeout=60):
    b = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    try:
        p = subprocess.run([b, "--count", path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags(config)),
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"verdict": "timeout", "errors": [], "counters": {}, "violations": []}
    m = re.search(r"diagnostics: (\d+)", p.stdout)
    c = re.search(r"counters.user:(.*)", p.stdout)
    return {"verdict": ("crash %d" % p.returncode) if p.returncode else ("accept" if m and m.group(1) == "0" else "reject"),
            "errors": [re.sub(r"^.*?: error: ", "", l.strip()) for l in p.stdout.splitlines() if ": error: " in l],
            "counters": {k: int(v) for k, v in (x.split("=") for x in (c.group(1).split() if c else []))},
            "violations": sorted(set(re.findall(r"\[selfcheck\] VIOLATION: (.*)", p.stdout)))}
if __name__ == "__main__":
    a = sys.argv[1:]; prefixes, timeout = [], 60
    if "--counters" in a: i = a.index("--counters"); prefixes = a[i + 1].split(","); del a[i:i + 2]
    if "--timeout" in a: i = a.index("--timeout"); timeout = int(a[i + 1]); del a[i:i + 2]
    for f in a[2:]:
        for c in a[1].split(";"):
            r = run(a[0], c, f, timeout)
            cs = " ".join(f"{k}={v}" for k, v in r["counters"].items() if any(k.startswith(p) for p in prefixes))
            print(f"{os.path.basename(f)[:44]:44} {c[:22]:22} {r['verdict']:8} {cs} {(r['violations'] or r['errors'] or [''])[0][:110]}")
