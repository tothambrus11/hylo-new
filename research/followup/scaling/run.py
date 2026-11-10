#!/usr/bin/env python3
"""Runs every (family, size, configuration) point of gen.py and appends one JSON line per point.

Usage:
    run.py [--timeout S] [--pass K] [--smoke] [--only FAMILY,...] [--configs base,FIX,MIN5,FULL]
           [--out results.jsonl]

One tc-bench process at a time, always under `timeout`. The output file is append-only; for a
given (family, size, configuration, pass) the LAST record wins.

Restartable: a point is run again only if it has no record, or if its record is a timeout (or a
skip caused by a timeout) obtained with a smaller --timeout than the current one. So the sweep
can be done first with a short timeout and then completed with the full 120 s.

Within one (family, configuration), sizes are run in increasing order and the series stops
(larger sizes are recorded as "skipped", with the reason) after
  - a timeout,
  - two consecutive crashes,
  - a run slower than 2 s whose power-law extrapolation to the next size (a lower bound for an
    exponential series) exceeds twice the timeout.

--pass K (K >= 1) measures again the points that finished in less than 5 s in pass 0. It serves
to take the minimum of several timings and to check that the counters are deterministic.
"""
import json, math, os, re, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402

B = "/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {
    "base": "",
    "FIX": FIX,
    "MIN5": "index,memberskip,typevec,symindex,traitindex",
    "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo",
}
MAIN = list(CONFIGS)
# Leave-one-out configurations, run on some families only (--configs FULL-eqsolve ...).
_full = CONFIGS["FULL"].split(",")
CONFIGS["FULL-eqsolve"] = ",".join(x for x in _full if x != "eqsolve")
CONFIGS["FULL-absmodel"] = ",".join(x for x in _full if x not in ("absmodel", "absquotient"))
CONFIGS["FULL-absquotient"] = ",".join(x for x in _full if x != "absquotient")


def parse(out):
    r = {"counters": {}, "ndiag": None, "diags": [], "type_user_ms": None, "type_stdlib_ms": None}
    for l in out.splitlines():
        if l.startswith("counters.user:"):
            r["counters"] = {k: int(v) for k, v in (x.split("=") for x in l.split()[1:])}
        elif l.startswith("diagnostics:"):
            r["ndiag"] = int(l.split()[1])
        elif l.startswith("type.user"):
            r["type_user_ms"] = float(l.split()[1])
        elif l.startswith("type.stdlib"):
            r["type_stdlib_ms"] = float(l.split()[1])
        elif r["ndiag"] and ("error:" in l or "warning:" in l) and len(r["diags"]) < 3:
            r["diags"].append(re.sub(r"^\s*\S*/([^/:]+\.hylo)", r"\1", l)[:300])
    return r


def run_once(path, flags, env_extra, timeout):
    env = dict(os.environ)
    env["HYLO_TC_EXPERIMENTS"] = flags
    env.update(env_extra)
    cmd = ["timeout", str(timeout), B, "--count", path]
    t = time.time()
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        p = subprocess.Popen(cmd, env=env, stdout=fo, stderr=fe)
        _, status, ru = os.wait4(p.pid, 0)
        wall = time.time() - t
        code = os.waitstatus_to_exitcode(status)
        p.returncode = code
        if code < 0:
            code = 128 - code   # killed by a signal: 134 = abort (out of memory), 139 = segfault
        fo.seek(0); fe.seek(0)
        out, err = fo.read().decode(errors="replace"), fe.read().decode(errors="replace")
    return code, wall, out, err, ru.ru_maxrss // 1024


def measure(family, n, cfg, timeout, pass_):
    g, sizes, verdict, env, counter = gen.FAMILIES[family]
    src = g(n)
    path = os.path.join(HERE, "progs", f"{family}-{n}.hylo")
    with open(path, "w") as f:
        f.write(src)
    env_extra = {k: v.format(n=n) for k, v in env.items()}
    code, wall, out, err, rss = run_once(path, CONFIGS[cfg], env_extra, timeout)
    r = parse(out)
    rec = {"family": family, "n": n, "config": cfg, "pass": pass_, "exit": code,
           "wall_s": round(wall, 2), "timeout_s": timeout, "env": env_extra, "intended": verdict,
           "bytes": len(src), "maxrss_mb": rss}
    if code == 124:
        rec["status"] = "timeout"
    elif code != 0:
        rec["status"] = "crash"
        rec["stderr"] = err.strip().splitlines()[-1][:200] if err.strip() else ""
    else:
        rec["status"] = "ok" if r["ndiag"] == 0 else "err"
    rec.update(ndiag=r["ndiag"], diags=r["diags"], counters=r["counters"],
               type_user_ms=r["type_user_ms"], type_stdlib_ms=r["type_stdlib_ms"])
    return rec


def show(r):
    c = r.get("counters", {})
    print(f"{r['family']:18} n={r['n']:<5} {r['config']:5} {r['status']:8} "
          f"t={r.get('type_user_ms')} wall={r.get('wall_s')} "
          f"matches={c.get('summon.matches')} forks={c.get('solver.forks')} "
          f"applies={c.get('names.appliesCalls')} {r.get('why', '')}"
          f"{(r.get('diags') or [''])[0][:100]}", flush=True)


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    smoke = "--smoke" in a
    only = opt("--only", ",".join(gen.FAMILIES)).split(",")
    configs = opt("--configs", ",".join(MAIN)).split(",")
    out = opt("--out", os.path.join(HERE, "results.jsonl"))
    timeout = int(opt("--timeout", "120"))
    pass_ = int(opt("--pass", "0"))
    os.makedirs(os.path.join(HERE, "progs"), exist_ok=True)

    done = {}
    if os.path.exists(out):
        for l in open(out):
            if l.strip():
                r = json.loads(l)
                done[(r["family"], r["n"], r["config"], r.get("pass", 0))] = r

    def stale(r):
        """True iff `r` was cut short by a timeout smaller than the current one."""
        return (r["status"] == "timeout" or (r["status"] == "skipped" and "timeout" in r["why"])) \
            and r.get("timeout_s", 120) < timeout

    with open(out, "a") as f:
        for family in only:
            sizes = gen.FAMILIES[family][1]
            if smoke:
                sizes = sizes[:1]
            for cfg in configs:
                stop, crashes, prev = None, 0, []   # prev: (n, type_user_ms) of finished runs
                for n in sizes:
                    if pass_ > 0:
                        r0 = done.get((family, n, cfg, 0))
                        if (family, n, cfg, pass_) in done or r0 is None \
                                or r0["status"] not in ("ok", "err") or r0["wall_s"] >= 5:
                            continue
                        r = measure(family, n, cfg, timeout, pass_)
                        f.write(json.dumps(r) + "\n"); f.flush(); show(r)
                        continue
                    r = done.get((family, n, cfg, 0))
                    if r is None or stale(r):
                        if stop:
                            r = {"family": family, "n": n, "config": cfg, "pass": 0,
                                 "status": "skipped", "why": stop, "timeout_s": timeout}
                        else:
                            r = measure(family, n, cfg, timeout, 0)
                        f.write(json.dumps(r) + "\n"); f.flush(); show(r)
                    if r["status"] == "timeout":
                        stop = f"timeout ({r.get('timeout_s', 120)} s) at n={n}"
                    elif r["status"] == "crash":
                        crashes += 1
                        if crashes >= 2:
                            stop = f"two crashes, last at n={n} (exit {r['exit']})"
                    elif r["status"] == "skipped":
                        stop = stop or r["why"]
                    else:
                        crashes = 0
                        prev.append((n, r["type_user_ms"]))
                        i = sizes.index(n)
                        if len(prev) >= 2 and i + 1 < len(sizes) and prev[-1][1] > 2000 \
                                and prev[-1][1] > prev[-2][1]:
                            (n0, t0), (n1, t1) = prev[-2], prev[-1]
                            p = math.log(t1 / t0) / math.log(n1 / n0)
                            t2 = t1 * (sizes[i + 1] / n1) ** p / 1000
                            if t2 > 2 * timeout:
                                stop = (f"predicted timeout: {t1 / 1000:.0f} s at n={n}, power-law "
                                        f"extrapolation gives {t2:.0f} s at n={sizes[i + 1]}")


if __name__ == "__main__":
    main()
