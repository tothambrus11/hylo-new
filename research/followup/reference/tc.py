"""Run the type-checker binary under a named configuration; one process at a time."""
import fcntl, os, re, subprocess, sys

B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {"base": "", "FIX": FIX, "FULL": FULL}
LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tc.lock")
DIAG = re.compile(r"^\s+(\S+?):(\d+)\.(\d+)(?:-(\d+))?(?::\d+)?: error: (.*)$")


def run(path, config, timeout=60, extra_env=None):
    """Returns a dict: status in {ok, crash, timeout}, diagnostics [(line, message)], exit code."""
    env = dict(os.environ)
    env["HYLO_TC_EXPERIMENTS"] = CONFIGS.get(config, config)
    if extra_env:
        env.update(extra_env)
    # A lock shared by every script of this directory: at most one compiler process at a time.
    with open(LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            p = subprocess.run(["timeout", str(timeout), B, path], env=env, capture_output=True,
                               text=True, errors="replace")
        except Exception as e:  # pragma: no cover
            return {"status": "crash", "code": -1, "diags": [], "raw": str(e)}
    out = p.stdout
    if p.returncode == 124:
        return {"status": "timeout", "code": 124, "diags": [], "raw": out[-400:]}
    m = re.search(r"^diagnostics: (\d+)", out, re.M)
    if p.returncode != 0 or not m:
        return {"status": "crash", "code": p.returncode, "diags": [],
                "raw": (out[-300:] + p.stderr[-300:])}
    diags = []
    for line in out.splitlines():
        d = DIAG.match(line)
        if d and d.group(1).endswith(os.path.basename(path)):
            diags.append((int(d.group(2)), d.group(5)))
    return {"status": "ok", "code": 0, "n": int(m.group(1)), "diags": diags, "raw": ""}


if __name__ == "__main__":
    for f in sys.argv[1:]:
        row = []
        for c in os.environ.get("TCC", "base,FIX,FULL").split(","):
            r = run(f, c)
            if r["status"] != "ok":
                row.append(f"{c}={r['status']}({r['code']})")
            else:
                row.append(f"{c}=" + ("accept" if r["n"] == 0 else "reject@" + ",".join(str(l) for l, _ in r["diags"])))
        print(os.path.basename(f), " ".join(row))
        if "-v" in os.environ.get("TCV", ""):
            for l, m in r["diags"]:
                print("    ", l, m)
