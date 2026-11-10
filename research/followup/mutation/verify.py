"""Independent re-runs and a few additional measurements. Appends to verify.jsonl (restartable: a
(set, id, what, config, depth, memcap) tuple already there is skipped). One tc-bench process at a time.

Usage: python3 verify.py SET ...     SET in: sample, basecap, depthblow, depthfull, capcheck, timing, attribwrong, eqsolvecap

  sample     re-runs of points behind the main claims (default 2.5 GB cap)
  basecap    blow-ups under base and MIN5+abs with the default 2.5 GB cap (most were run at 1 GB)
  depthblow  three blow-ups at HYLO_TC_MAXDEPTH 6..9 under base, MIN5, MIN5+abs
  depthfull  the ill-typed mutants that reach the depth bound under FULL, at depth 10, 12, 14,
             under FULL and FULL without absmodel,absquotient
  capcheck   the attribution cells that exhausted the 600 MB cap, at 2.5 GB
  timing     unmutated source and mutant alternately, five times each (typing ms)
  attribwrong  the 29 mutants that base accepts and FULL rejects, under MIN5 plus individual fixes
  eqsolvecap   MIN5 + eqsolve on four blow-ups with the default 2.5 GB cap
  bigcap       one blow-up at the default depth bound with a 5 GB cap
  basecap2     the remaining blow-ups under base with the default 2.5 GB cap

Each row records the peak resident memory of the process (maxrss_mb), so that an abort can be told
from a memory exhaustion.
"""
import json, os, subprocess, sys, time
import tc, run

OUT = os.path.join(tc.HERE, "verify.jsonl")
FULL_NOABS = ",".join(f for f in tc.FULL.split(",") if f not in ("absmodel", "absquotient"))
FLAGS = dict(tc.CONFIGS)
FLAGS["full-abs"] = FULL_NOABS
FLAGS["min5+budget"] = tc.MIN5 + ",budget"
FLAGS["fix-eqsolve"] = ",".join(f for f in tc.FIX.split(",") if f != "eqsolve")
FLAGS["fix-eqmgu"] = ",".join(f for f in tc.FIX.split(",") if f != "eqmgu")
FLAGS["fix"] = tc.FIX
FLAGS["min5+eqsolve"] = tc.MIN5 + ",eqsolve"
FLAGS["min5+eqmgu"] = tc.MIN5 + ",eqmgu"
FLAGS["min5+occurs,fixsubst,eqsolve"] = tc.MIN5 + ",occurs,fixsubst,eqsolve"


def execute(program, flags, timeout, env_extra):
    env = dict(os.environ); env["HYLO_TC_EXPERIMENTS"] = flags
    env.update(env_extra or {})
    t0 = time.time()
    p = subprocess.Popen(["timeout", "-k", "5", str(timeout), tc.TC, "--count", program], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.stdout.read(), p.stderr.read()
    _, status, ru = os.wait4(p.pid, 0)
    code = os.waitstatus_to_exitcode(status)
    r = tc.parse(out.decode("utf-8", "replace"))
    r["exit"] = code; r["wall"] = round(time.time() - t0, 3)
    r["status"] = "timeout" if code in (124, 137) else "crash" if code != 0 else "noparse" if r["diagnostics"] is None else "ok"
    r["maxrss_mb"] = round(ru.ru_maxrss / 1024)
    r["stderr"] = err.decode("utf-8", "replace")[:300]
    return r


def specs(name):
    """Yields (id, what, config, depth or None, memcap_kb or None, timeout)."""
    if name == "sample":
        pts = {
            "tests/repl-typearg/007": ["full"],
            "corpus/del-bound/015": ["min5abs", "full"],
            "corpus/del-where-req/009": ["full", "min5"],
            "tests/del-where-req/016": ["base", "min5abs", "full"],
            "corpus/repl-typearg/033": ["base", "full"],
            "workloads/del-ext-member/001": ["min5", "min5abs"],
            "stdlib/del-given/002": ["base", "min5", "min5abs", "full"],
            "stdlib/del-given/025": ["min5", "min5abs"],
            "workloads/swap-args/000": ["base", "min5"],
            "tests/del-given/004": ["base", "min5", "min5abs"],
            "corpus/del-bound/011": ["full"],
            "workloads/del-bound/031": ["base", "full"],
            "workloads/del-bound/002": ["min5", "min5abs"],
            "corpus/del-where-req/017": ["min5", "min5abs", "full"],
            "workloads/repl-typearg/041": ["min5", "min5abs"],
            "corpus/repl-typearg/004": ["base", "full"],
        }
        for i, cs in pts.items():
            for c in cs: yield (i, "mutant", c, None, None, 150)
    elif name == "basecap":
        for i in ["tests/repl-typearg/007", "corpus/del-bound/014", "corpus/del-where-req/013", "corpus/del-given/031",
                  "corpus/del-bound/011", "tests/del-where-req/012"]:
            yield (i, "mutant", "base", None, None, 240)
        for i in ["corpus/del-bound/014", "tests/del-where-req/012"]:
            yield (i, "mutant", "min5abs", None, None, 240)
    elif name == "depthblow":
        for i in ["tests/repl-typearg/007", "corpus/del-where-req/013", "corpus/del-bound/015"]:
            for c in ["base", "min5", "min5abs"]:
                for d in [6, 7, 8, 9]:
                    yield (i, "mutant", c, d, None, 150)
    elif name == "depthfull":
        for i in ["corpus/del-bound/011", "corpus/del-where-req/025", "corpus/repl-typearg/004", "corpus/repl-typearg/011"]:
            for c in ["full", "full-abs"]:
                for d in [10, 12, 14]:
                    yield (i, "mutant", c, d, None, 150)
    elif name == "capcheck":
        yield ("corpus/del-bound/015", "mutant", "min5+budget", None, None, 150)
        yield ("tests/del-where-req/012", "mutant", "min5+budget", None, None, 150)
        yield ("tests/del-where-req/019", "mutant", "fix-eqsolve", None, None, 150)
    elif name == "attribwrong":
        # the mutants that base accepts and FULL rejects, under MIN5 plus individual fixes
        ids = sorted(json.loads(l)["id"] for l in open(os.path.join(tc.HERE, "classified.jsonl"))
                     if json.loads(l)["cls"] == "equivalent" and json.loads(l)["full"]["diags"] > 0)
        for i in ids:
            for c in ["min5+budget", "min5+eqmgu", "min5+eqsolve", "min5+occurs,fixsubst,eqsolve", "fix", "fix-eqmgu", "fix-eqsolve"]:
                yield (i, "mutant", c, None, None, 60)
    elif name == "eqsolvecap":
        for i in ["corpus/del-bound/011", "corpus/del-bound/014", "corpus/del-bound/015", "corpus/del-bound/027"]:
            yield (i, "mutant", "min5+eqsolve", None, None, 150)
    elif name == "basecap2":
        # the remaining blow-ups under base with the default cap (tests/del-where-req/019 is the same program as workloads/del-where-req/016)
        for i in ["corpus/del-where-req/025", "corpus/del-where-req/026", "corpus/del-bound/027", "corpus/del-bound/028",
                  "corpus/repl-typearg/018", "corpus/repl-typearg/005", "workloads/del-where-req/016", "corpus/del-where-req/000",
                  "corpus/del-bound/015"]:
            yield (i, "mutant", "base", None, None, 240)
    elif name == "bigcap":
        # one blow-up at the default depth with a 5 GB cap: does the search end?
        yield ("corpus/del-where-req/013", "mutant", "min5", None, 5000000, 400)
    elif name == "timing":
        for i, c in [("stdlib/del-given/002", "base"), ("stdlib/del-type-member/020", "base"), ("stdlib/del-given/002", "min5"),
                     ("tests/del-type-member/001", "base"), ("corpus/del-bound/003", "base")]:
            for k in range(5):
                yield (i, "original", c, None, None, 60, k)
                yield (i, "mutant", c, None, None, 60, k)


def main():
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["set"], r["id"], r["what"], r["config"], r["depth"], r["rep"]))
    mutants = {m["id"]: m for m in run.load_mutants()}
    os.environ.pop("TCX_MEM_LIMIT_KB", None)
    with open(OUT, "a") as out:
        for name in sys.argv[1:]:
            for sp in specs(name):
                mid, what, c, depth, cap, timeout = sp[:6]
                rep = sp[6] if len(sp) > 6 else 0
                if (name, mid, what, c, depth, rep) in done: continue
                m = mutants[mid]
                try:
                    if what == "mutant": prog, part = run.materialize(m)
                    elif m["group"] == "stdlib": run.restore_stdlib(); prog, part = tc.EMPTY, "stdlib"
                    else: prog, part = run.source_path(m), "user"
                    env = {}
                    if depth is not None: env["HYLO_TC_MAXDEPTH"] = str(depth)
                    if cap is not None: env["TCX_MEM_LIMIT_KB"] = str(cap)
                    r = execute(prog, FLAGS[c], timeout, env)
                    row = {"set": name, "id": mid, "what": what, "config": c, "depth": depth, "rep": rep,
                           "memcap_kb": cap or 2500000, "maxrss_mb": r["maxrss_mb"], "stderr": r["stderr"]}
                    row.update(tc.summarize(r, part))
                    out.write(json.dumps(row) + "\n"); out.flush()
                    print(name, mid, what, c, depth, row["status"], row["exit"], "diags", row["diags"], "matches", row["matches"],
                          "ms", row["ms"], "rss", row["maxrss_mb"], "wall", row["wall"], flush=True)
                finally:
                    if m["group"] == "stdlib": run.restore_stdlib()


if __name__ == "__main__":
    main()
