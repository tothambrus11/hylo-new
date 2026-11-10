"""Shared helpers: running tc-bench (one process at a time) and parsing its output."""
import os, re, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # /home/user/hylo-new
ORIG_BIN = os.path.join(ROOT, "research/exp/bin/eq9-723cc0e6b0f8")
BIN = os.path.join(HERE, "bin")                                       # private copy (stdlib is mutated here)
TC = os.path.join(BIN, "tc-bench")
STD = os.path.join(BIN, "Hylo_StandardLibrary.resources")
ORIG_STD = os.path.join(ORIG_BIN, "Hylo_StandardLibrary.resources")
EMPTY = os.path.join(ROOT, "research/workloads/empty.hylo")

MIN5 = "index,memberskip,typevec,symindex,traitindex"
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL = FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
CONFIGS = {
    "base": "",
    "min5": MIN5,
    "min5abs": MIN5 + ",absmodel,absquotient",
    "full": FULL,
}

def parse(out):
    """Parses the output of tc-bench into a dictionary."""
    r = {"counters": {"stdlib": {}, "user": {}}, "diagnostics": None, "messages": [], "ms": {}}
    lines = out.splitlines()
    i = 0
    seen_diag = False
    for ln in lines:
        m = re.match(r"counters\.(stdlib|user):\s*(.*)$", ln)
        if m and not seen_diag:
            for kv in m.group(2).split():
                k, _, v = kv.partition("=")
                try: r["counters"][m.group(1)][k] = int(v)
                except ValueError: pass
            continue
        m = re.match(r"diagnostics: (\d+)\s*$", ln)
        if m and not seen_diag:
            r["diagnostics"] = int(m.group(1)); seen_diag = True
            continue
        m = re.match(r"(parse|scope|type\.stdlib|type\.user)\s+([0-9.]+) ms\s*$", ln)
        if m:
            r["ms"][m.group(1)] = float(m.group(2))
            continue
        if seen_diag:
            r["messages"].append(ln)
    return r

def run(program, flags, timeout=120, env_extra=None, tc=TC):
    """Runs tc-bench on `program` with HYLO_TC_EXPERIMENTS=`flags`; returns a result dictionary."""
    env = dict(os.environ)
    env["HYLO_TC_EXPERIMENTS"] = flags
    if env_extra: env.update(env_extra)
    t0 = time.time()
    p = subprocess.run(["timeout", "-k", "5", str(timeout), tc, "--count", program],
                       env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wall = time.time() - t0
    out = p.stdout.decode("utf-8", "replace")
    r = parse(out)
    r["exit"] = p.returncode
    r["wall"] = round(wall, 3)
    if p.returncode == 124 or p.returncode == 137:
        r["status"] = "timeout"
    elif p.returncode != 0:
        r["status"] = "crash"
        r["stderr"] = p.stderr.decode("utf-8", "replace")[:600]
    elif r["diagnostics"] is None:
        r["status"] = "noparse"
    else:
        r["status"] = "ok"
    return r

SYNTAX_PAT = re.compile(r"expected|is not a valid identifier|unexpected|unterminated")

def summarize(r, part):
    """Flattens a run into the fields recorded for a mutant; `part` is 'user' or 'stdlib'."""
    c = r["counters"][part]
    msgs = r["messages"]
    return {
        "status": r["status"], "exit": r["exit"], "diags": r["diagnostics"],
        "matches": c.get("summon.matches", 0), "subgoals": c.get("summon.subgoals", 0),
        "layers": c.get("summon.layers", 0), "calls": c.get("summon.calls", 0),
        "depthExhausted": c.get("summon.depthExhausted", 0),
        "budgetExhausted": c.get("summon.budgetExhausted", 0),
        "refuted": c.get("absmodel.refuted", 0),
        "applies": c.get("names.appliesCalls", 0),
        "forks": c.get("solver.forks", 0), "goalSteps": c.get("solver.goalSteps", 0),
        "slowPath": c.get("coerced.slowPath", 0),
        "ms": r["ms"].get("type." + part), "wall": r["wall"],
        "syntax": any(SYNTAX_PAT.search(m) for m in msgs),
        "msgs": [m[:300] for m in msgs[:12]],
        "all": dict(c),
    }
