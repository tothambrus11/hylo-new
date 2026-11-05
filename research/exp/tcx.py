#!/usr/bin/env python3
"""tcx — resumable experiment harness for the Hylo type-checker optimization study.

Everything is append-only and idempotent: every command can be killed at any time (Ctrl-C, crash,
PC shutdown) and simply re-run; finished measurements are never repeated.

Commands
  freeze                      copy the current release build of tc-bench into exp/bin/<id>/
  semtest SPEC|--bin ID ...   semantic differential test (types, bindings, witnesses, diagnostics)
  run SPEC                    run (or continue) the experiment described by SPEC in the foreground
  start SPEC                  same, detached (nohup + setsid); safe to call when already running
  stop NAME                   ask a detached runner to stop after its current measurement
  queue SPEC...               run several experiments in order, detached; remembered in runs/QUEUE.json
  resume                      restart the remembered queue after a crash/reboot (no-op if running)
  status [NAME]               progress, rate and ETA of experiments
  analyze NAME                write exp/runs/NAME/report.md from the measurements

A SPEC is a JSON file (see exp/specs/). Designs:
  {"kind": "full"}                         all 2^n subsets of "flags"
  {"kind": "list", "configs": [[..], ..]}  explicit configurations
  {"kind": "ga", ...}                      deterministic genetic search (restart replays from cache)
  {"kind": "neighborhood", "center": [..]} center, all leave-one-out and add-one configurations
"""

import fcntl, resource, hashlib, itertools, json, math, os, random, re, shutil, signal, statistics
import subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))           # research/exp
RESEARCH = os.path.dirname(ROOT)
REPO = os.environ.get("TCX_REPO") or os.path.dirname(RESEARCH)                 # research/ lives in the repo
WORKLOADS = os.path.join(RESEARCH, "workloads")
TESTS = os.path.join(REPO, "Tests", "CompilerTests")
BUNDLE = "Hylo_StandardLibrary.bundle"

# ---------------------------------------------------------------------------------------------
# Binaries

def bin_dir(bid):
    return os.path.join(ROOT, "bin", bid)

def bin_path(bid):
    return os.path.join(bin_dir(bid), "tc-bench")

def cmd_freeze(argv):
    src = argv[0] if argv else os.path.join(REPO, ".build", "release")
    exe = os.path.join(src, "tc-bench")
    h = hashlib.sha256(open(exe, "rb").read()).hexdigest()[:12]
    label = argv[1] if len(argv) > 1 else ""
    bid = f"{label + '-' if label else ''}{h}"
    d = bin_dir(bid)
    if not os.path.exists(d):
        tmp = d + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        shutil.copy2(exe, tmp)
        shutil.copytree(os.path.join(src, BUNDLE), os.path.join(tmp, BUNDLE))
        os.rename(os.path.join(tmp, "tc-bench"), os.path.join(tmp, "tc-bench.real"))
        w = os.path.join(tmp, "tc-bench")
        open(w, "w").write('#!/bin/bash\n# Memory-capped wrapper.\nulimit -v ${TCX_MEM_LIMIT_KB:-2500000}\n'
                           'exec "$(dirname "$0")/tc-bench.real" "$@"\n')
        os.chmod(w, 0o755)
        os.rename(tmp, d)
    print(bid)
    return bid

# ---------------------------------------------------------------------------------------------
# Configurations

def cfg_key(flags):
    return ",".join(sorted(flags)) or "baseline"

def cfg_flags(key):
    return [] if key == "baseline" else key.split(",")

def env_for(spec_env, key):
    e = dict(os.environ)
    e.pop("HYLO_TC_EXPERIMENTS", None)
    e.update(spec_env or {})
    if key != "baseline":
        e["HYLO_TC_EXPERIMENTS"] = key
    return e

MEM_LIMIT = int(os.environ.get("TCX_MEM_LIMIT_MB", "2500")) * 1024 * 1024

def _limit():
    """Caps the address space of a child so that a runaway configuration fails instead of
    exhausting the machine's memory (which takes WSL down)."""
    resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))

PHASE = re.compile(r"^(parse|scope|type\.stdlib|type\.user)\s+([0-9.]+) ms", re.M)

def invoke(spec, key, wl, inner=None):
    """Runs one timed invocation; returns a result record (without bookkeeping fields)."""
    exe = bin_path(spec["bin"])
    args = [exe, "--quiet", "--repeat", str(inner or spec.get("inner", 2)),
            os.path.join(WORKLOADS, wl["file"])]
    if spec.get("cpu") is not None:
        args = ["taskset", "-c", str(spec["cpu"])] + args
    t0 = time.time()
    try:
        p = subprocess.run(args, env=env_for(spec.get("env"), key), capture_output=True,
                           text=True, timeout=spec.get("timeout", 120), preexec_fn=_limit)
        ph = {k: float(v) for k, v in PHASE.findall(p.stdout)}
        ok = p.returncode == 0 and "type.user" in ph
        return {"ok": ok, "timeout": False, "phases": ph, "exit": p.returncode,
                "wall": round(time.time() - t0, 3)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "phases": {}, "exit": None,
                "wall": round(time.time() - t0, 3)}

# ---------------------------------------------------------------------------------------------
# Semantic dumps (the soundness oracle)

NORMALIZE = re.compile(r"\(erased: [0-9]+\)")

def dump(bid, env, key, path, timeout=300):
    """Returns (status, sha, text) of the semantic dump of `path` under configuration `key`."""
    out = os.path.join(ROOT, "tmp", f"{os.getpid()}-{hashlib.md5((key + path).encode()).hexdigest()}.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        p = subprocess.run([bin_path(bid), "--quiet", "--dump", out, path],
                           env=env_for(env, key), capture_output=True, text=True, timeout=timeout,
                           preexec_fn=_limit)
        if p.returncode != 0 or not os.path.exists(out):
            return ("crash", f"exit{p.returncode}", p.stderr[-2000:])
        text = NORMALIZE.sub("(erased: _)", open(out).read())
        return ("ok", hashlib.sha256(text.encode()).hexdigest()[:16], text)
    except subprocess.TimeoutExpired:
        return ("timeout", "timeout", "")
    finally:
        if os.path.exists(out):
            os.remove(out)

def corpus(kind):
    fs = []
    if kind in ("tests", "all"):
        for sub in ("positive", "negative"):
            d = os.path.join(TESTS, sub)
            fs += sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".hylo"))
    if kind in ("workloads", "all"):
        fs += sorted(os.path.join(WORKLOADS, f) for f in os.listdir(WORKLOADS) if f.endswith(".hylo"))
    return fs

def semtest(bid, configs, files, env=None, jobs=8, timeout=300, verbose=True):
    """Compares each configuration's dump against the baseline's for every file.

    Baseline dumps are cached in exp/semcache/<bin>/. Returns {config: [mismatching files]}.
    """
    cache = os.path.join(ROOT, "semcache", bid)
    os.makedirs(cache, exist_ok=True)
    envkey = hashlib.md5(json.dumps(env or {}, sort_keys=True).encode()).hexdigest()[:6]

    def base(f):
        c = os.path.join(cache, f"{envkey}-{hashlib.md5(f.encode()).hexdigest()}.json")
        if os.path.exists(c):
            return json.load(open(c))
        s, h, t = dump(bid, env, "baseline", f, timeout)
        r = {"status": s, "sha": h, "text": t}
        json.dump(r, open(c + ".tmp", "w")); os.replace(c + ".tmp", c)
        return r

    with ThreadPoolExecutor(jobs) as ex:
        bases = dict(zip(files, ex.map(base, files)))
    report = {}
    for key in configs:
        def check(f):
            s, h, t = dump(bid, env, key, f, timeout)
            b = bases[f]
            if (s, h) == (b["status"], b["sha"]):
                return None
            if s == "timeout" and b["status"] == "timeout":
                return None
            detail = ""
            if s == "ok" and b["status"] == "ok":
                import difflib
                detail = "".join(itertools.islice(difflib.unified_diff(
                    b["text"].splitlines(True), t.splitlines(True), "baseline", key, n=0), 40))
            else:
                detail = f"baseline={b['status']} config={s}\n{t[-800:] if s == 'crash' else ''}"
            return (f, detail)
        with ThreadPoolExecutor(jobs) as ex:
            bad = [x for x in ex.map(check, files) if x]
        report[key] = bad
        if verbose:
            print(f"[{key}] {len(files) - len(bad)}/{len(files)} identical")
            for f, d in bad:
                print(f"  MISMATCH {os.path.relpath(f, os.path.dirname(RESEARCH))}")
                for l in d.splitlines()[:25]:
                    print("     ", l)
    return report

def cmd_semtest(argv):
    """semtest --bin ID --configs a,b;c --corpus tests|workloads|all [--files f..] [--jobs N]"""
    opts = {"--bin": None, "--configs": "", "--corpus": "all", "--jobs": "8", "--env": "{}"}
    files, i = [], 0
    while i < len(argv):
        if argv[i] == "--files":
            files = argv[i + 1:]; break
        opts[argv[i]] = argv[i + 1]; i += 2
    bid = opts["--bin"] or cmd_freeze([])
    configs = [cfg_key(c.split(",")) for c in opts["--configs"].split(";") if c]
    files = [os.path.abspath(f) for f in files] or corpus(opts["--corpus"])
    rep = semtest(bid, configs, files, json.loads(opts["--env"]), int(opts["--jobs"]))
    sys.exit(1 if any(rep.values()) else 0)

# ---------------------------------------------------------------------------------------------
# Experiments

class Store:
    """The append-only measurement log of an experiment."""

    def __init__(self, name):
        self.dir = os.path.join(ROOT, "runs", name)
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "results.jsonl")
        self.rows = []
        if os.path.exists(self.path):
            for line in open(self.path):
                try:
                    self.rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass                                     # torn last line after a crash
        self.done = {(r["cfg"], r["wl"], r["rep"]) for r in self.rows if r.get("kind") == "time"}
        self.sem = {(r["cfg"], r["wl"]): r for r in self.rows if r.get("kind") == "sem"}

    def append(self, row):
        row["at"] = round(time.time(), 1)
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush(); os.fsync(f.fileno())
        self.rows.append(row)
        if row["kind"] == "time":
            self.done.add((row["cfg"], row["wl"], row["rep"]))
        else:
            self.sem[(row["cfg"], row["wl"])] = row

STOP = False

def _on_term(*_):
    global STOP
    STOP = True

class Runner:

    def __init__(self, spec):
        self.spec = spec
        self.store = Store(spec["name"])
        self.wls = spec["workloads"]
        self.reps = spec.get("reps", 5)
        self.flags = spec.get("flags", [])
        self.status = os.path.join(self.store.dir, "status.json")
        self.planned = set()

    # -- measuring --------------------------------------------------------------------------

    def measure(self, key, wl, rep):
        if (key, wl["name"], rep) in self.store.done:
            return
        if STOP:
            raise KeyboardInterrupt
        r = invoke(self.spec, key, wl)
        r.update(kind="time", cfg=key, wl=wl["name"], rep=rep, bin=self.spec["bin"],
                 load=round(os.getloadavg()[0], 2))
        self.store.append(r)
        self.heartbeat()

    def check(self, key, wl):
        """Records whether `key` elaborates `wl` exactly like the baseline (untimed)."""
        if not self.spec.get("semcheck", True) or (key, wl["name"]) in self.store.sem:
            return
        path = os.path.join(WORKLOADS, wl["file"])
        to = self.spec.get("semtimeout", 600)
        if ("baseline", wl["name"]) not in self.store.sem:
            s, h, _ = dump(self.spec["bin"], self.spec.get("env"), "baseline", path, to)
            self.store.append({"kind": "sem", "cfg": "baseline", "wl": wl["name"], "status": s,
                               "sha": h})
        if key != "baseline":
            s, h, _ = dump(self.spec["bin"], self.spec.get("env"), key, path, to)
            self.store.append({"kind": "sem", "cfg": key, "wl": wl["name"], "status": s, "sha": h})

    def heartbeat(self, extra=None):
        n = sum(1 for (c, w, r) in self.planned if (c, w, r) in self.store.done)
        st = {"name": self.spec["name"], "pid": os.getpid(), "updated": time.time(),
              "done": n, "planned": len(self.planned), "rows": len(self.store.rows)}
        if extra:
            st.update(extra)
        tmp = self.status + ".tmp"
        json.dump(st, open(tmp, "w")); os.replace(tmp, self.status)

    def evaluate(self, configs, reps=None):
        """Measures every configuration in `configs` on every workload, rep-major and shuffled
        within each repetition block so that partial results are balanced across configs."""
        reps = reps or self.reps
        rng = random.Random(f"{self.spec.get('seed', 0)}/{len(self.planned)}/{','.join(configs)}")
        for key in configs:
            for wl in self.wls:
                for r in range(reps):
                    self.planned.add((key, wl["name"], r))
        for key in configs:
            for wl in self.wls:
                self.check(key, wl)
        for r in range(reps):
            block = [(k, w) for k in configs for w in self.wls]
            rng.shuffle(block)
            for k, w in block:
                self.measure(k, w, r)

    # -- objective --------------------------------------------------------------------------

    def score(self, key):
        """Geometric mean, over workloads, of median(config) / median(baseline). Lower is better.
        A configuration whose elaboration differs from the baseline anywhere scores +inf."""
        a = Analysis(self.spec, self.store.rows, max_rep=self.reps)
        return a.objective(key)

    # -- designs ----------------------------------------------------------------------------

    def run(self):
        d = self.spec["design"]
        base = ["baseline"]
        if d["kind"] == "full":
            cfgs = [cfg_key(c) for n in range(len(self.flags) + 1)
                    for c in itertools.combinations(self.flags, n)]
            self.evaluate(cfgs)
        elif d["kind"] == "list":
            self.evaluate(list(dict.fromkeys(base + [cfg_key(c) for c in d["configs"]])))
        elif d["kind"] == "neighborhood":
            c = set(d["center"])
            cfgs = [cfg_key(c)] + [cfg_key(c - {f}) for f in sorted(c)] + \
                   [cfg_key(c | {f}) for f in self.flags if f not in c]
            self.evaluate(list(dict.fromkeys(base + cfgs)), d.get("reps"))
        elif d["kind"] == "ga":
            self.ga(d)
        else:
            raise SystemExit(f"unknown design {d['kind']}")
        self.heartbeat({"finished": True})
        print("experiment complete:", self.spec["name"])

    def ga(self, d):
        """A deterministic (mu + lambda) genetic search over flag subsets.

        Determinism makes restarts free: the random stream is seeded, and every fitness value is
        recomputed from the measurement log, so a restarted run replays the same trajectory and only
        measures what is missing.
        """
        rng = random.Random(d.get("seed", 1))
        n, pop_n, gens = len(self.flags), d.get("pop", 12), d.get("gens", 10)
        pmut, elite = d.get("mut", 1.0 / max(1, n)), d.get("elite", 3)
        log = open(os.path.join(self.store.dir, "ga.log"), "a")
        def genome_key(g):
            return cfg_key([f for f, b in zip(self.flags, g) if b])
        seeds = [tuple([0] * n), tuple([1] * n)] + [tuple(x) for x in d.get("seed_configs", [])]
        pop = list(dict.fromkeys(seeds))
        while len(pop) < pop_n:
            pop.append(tuple(rng.random() < 0.5 for _ in range(n)))
        pop = [tuple(int(b) for b in g) for g in pop]
        self.evaluate(["baseline"])
        for gen in range(gens):
            self.evaluate([genome_key(g) for g in pop])
            ranked = sorted(set(pop), key=lambda g: (self.score(genome_key(g)), sum(g)))
            best = ranked[0]
            log.write(json.dumps({"gen": gen, "best": genome_key(best),
                                  "score": self.score(genome_key(best)),
                                  "top": [[genome_key(g), self.score(genome_key(g))]
                                          for g in ranked[:5]]}) + "\n"); log.flush()
            self.heartbeat({"generation": gen, "best": genome_key(best)})
            def tournament():
                a, b = rng.choice(ranked), rng.choice(ranked)
                return a if ranked.index(a) < ranked.index(b) else b
            nxt = ranked[:elite]
            while len(nxt) < pop_n:
                p, q = tournament(), tournament()
                child = tuple((x if rng.random() < 0.5 else y) for x, y in zip(p, q))
                child = tuple((1 - b) if rng.random() < pmut else b for b in child)
                nxt.append(child)
            pop = nxt
        # Confirmation: the final top configurations and the best one's neighborhood get extra reps.
        ranked = sorted({genome_key(g) for g in pop}, key=lambda k: self.score(k))
        best = set(cfg_flags(ranked[0]))
        hood = [cfg_key(best - {f}) for f in sorted(best)] + \
               [cfg_key(best | {f}) for f in self.flags if f not in best]
        self.evaluate(list(dict.fromkeys(["baseline"] + ranked[:d.get("confirm_top", 4)] + hood)),
                      d.get("confirm_reps", self.reps * 2))

# ---------------------------------------------------------------------------------------------
# Analysis

def gmean(xs):
    xs = list(xs)
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")

class Analysis:

    def __init__(self, spec, rows, max_rep=None):
        self.spec = spec
        self.wls = [w["name"] for w in spec["workloads"]]
        self.metric = {w["name"]: w.get("metric", "type.user") for w in spec["workloads"]}
        self.weight = {w["name"]: w.get("weight", 1.0) for w in spec["workloads"]}
        self.timeout_ms = spec.get("timeout", 120) * 1000.0
        self.samples = {}      # (cfg, wl) -> [ms]
        self.stdlib = {}       # cfg -> [ms], from every invocation
        self.sem = {}
        for r in rows:
            if r.get("kind") == "sem":
                self.sem[(r["cfg"], r["wl"])] = (r["status"], r["sha"])
            elif r.get("kind") == "time":
                if max_rep is not None and r["rep"] >= max_rep:
                    continue
                if r["timeout"]:
                    v = self.timeout_ms
                elif r["ok"]:
                    v = r["phases"].get(self.metric[r["wl"]])
                else:
                    v = None
                if v is not None:
                    self.samples.setdefault((r["cfg"], r["wl"]), []).append(max(v, 1e-3))
                if r["ok"] and "type.stdlib" in r["phases"]:
                    self.stdlib.setdefault(r["cfg"], []).append(r["phases"]["type.stdlib"])
        for w in self.wls:                       # "stdlib" pools samples from all invocations
            if self.metric[w] == "type.stdlib":
                for c, xs in self.stdlib.items():
                    self.samples[(c, w)] = xs

    def configs(self):
        return sorted({c for (c, _) in self.samples})

    def sound(self, cfg):
        bad = []
        for w in self.wls:
            b, x = self.sem.get(("baseline", w)), self.sem.get((cfg, w))
            if b and x and b != x:
                bad.append(w)
        return bad

    def median(self, cfg, wl):
        xs = self.samples.get((cfg, wl))
        return statistics.median(xs) if xs else None

    def ratio(self, cfg, wl):
        a, b = self.median(cfg, wl), self.median("baseline", wl)
        return a / b if a and b else None

    def objective(self, cfg, wls=None):
        if self.sound(cfg):
            return float("inf")
        wls = wls or self.wls
        rs = [(self.ratio(cfg, w), self.weight[w]) for w in wls]
        if any(r is None for r, _ in rs):
            return float("inf")
        tw = sum(wt for _, wt in rs)
        return math.exp(sum(wt * math.log(r) for r, wt in rs) / tw)

    def bootstrap(self, fn, n=400, seed=7):
        """95% percentile interval of `fn(sampler)` resampling each (cfg, wl) sample set."""
        rng = random.Random(seed)
        vals = []
        for _ in range(n):
            res = {k: [rng.choice(v) for _ in v] for k, v in self.samples.items()}
            med = lambda c, w: statistics.median(res[(c, w)]) if (c, w) in res else None
            try:
                vals.append(fn(med))
            except (TypeError, ZeroDivisionError, ValueError):
                pass
        vals.sort()
        if not vals:
            return (float("nan"), float("nan"))
        return (vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))])

    def obj_fn(self, cfg, wls=None, rel="baseline"):
        wls = wls or self.wls
        def f(med):
            tw = sum(self.weight[w] for w in wls)
            return math.exp(sum(self.weight[w] * math.log(med(cfg, w) / med(rel, w)) for w in wls) / tw)
        return f

def cmd_analyze(argv):
    name = argv[0]
    spec = json.load(open(os.path.join(ROOT, "runs", name, "spec.json")))
    a = Analysis(spec, Store(name).rows)
    flags = spec.get("flags", [])
    cfgs = [c for c in a.configs() if all(a.median(c, w) for w in a.wls)]
    out = [f"# Experiment `{name}`\n", f"binary `{spec['bin']}`, workloads: " +
           ", ".join(f"{w} ({a.metric[w]}, w={a.weight[w]})" for w in a.wls) + "\n"]
    n_time = sum(len(v) for (c, w), v in a.samples.items() if a.metric[w] != "type.stdlib")
    out.append(f"{len(cfgs)} complete configurations, {n_time} timed samples (+ stdlib from every invocation)\n")
    unsound = {c: a.sound(c) for c in cfgs if a.sound(c)}
    if unsound:
        out.append("## Elaboration mismatches (disqualified)\n")
        for c, ws in unsound.items():
            out.append(f"- `{c}`: {', '.join(ws)}")
        out.append("")
    stress = [w for w in a.wls if a.metric[w] != "type.stdlib"]
    std = [w for w in a.wls if a.metric[w] == "type.stdlib"]
    ranked = sorted(cfgs, key=lambda c: a.objective(c))
    out.append("## Ranking (objective = weighted geomean of median ratio vs baseline; lower is better)\n")
    hdr = "| # | config | flags | objective [95% CI] | " + " | ".join(a.wls) + " |"
    out += [hdr, "|" + "---|" * (4 + len(a.wls))]
    top = ranked[: int(spec.get("report_top", 40))]
    for i, c in enumerate(top):
        lo, hi = a.bootstrap(a.obj_fn(c), n=200)
        cells = []
        for w in a.wls:
            m, r = a.median(c, w), a.ratio(c, w)
            cells.append(f"{m:.1f} ({r:.2f})" if m and r else "–")
        out.append(f"| {i+1} | `{c}` | {len(cfg_flags(c))} | {a.objective(c):.3f} "
                   f"[{lo:.3f}, {hi:.3f}] | " + " | ".join(cells) + " |")
    if ranked:
        best = ranked[0]
        out.append(f"\n## Is every flag of the winner `{best}` necessary?\n")
        out.append("Ratio objective(winner − flag) / objective(winner); CI excluding 1.0 ⇒ the flag matters.\n")
        out.append("| removed | all workloads [95% CI] | stdlib only [95% CI] | verdict |")
        out.append("|---|---|---|---|")
        for f in cfg_flags(best):
            c = cfg_key(set(cfg_flags(best)) - {f})
            if c not in cfgs:
                continue
            fa = a.obj_fn(c, rel=best)
            lo, hi = a.bootstrap(fa, n=300)
            s = ""
            if std:
                fs = a.obj_fn(c, std, rel=best)
                slo, shi = a.bootstrap(fs, n=300)
                s = f"{fs(a.median):.3f} [{slo:.3f}, {shi:.3f}]"
            v = "needed" if lo > 1.0 else ("harmful" if hi < 1.0 else "no significant effect")
            out.append(f"| {f} | {fa(a.median):.3f} [{lo:.3f}, {hi:.3f}] | {s} | {v} |")
        out.append(f"\n## Does adding any flag to the winner help?\n")
        out.append("| added | all workloads [95% CI] | verdict |\n|---|---|---|")
        for f in flags:
            if f in cfg_flags(best):
                continue
            c = cfg_key(set(cfg_flags(best)) | {f})
            if c not in cfgs:
                continue
            fa = a.obj_fn(c, rel=best)
            lo, hi = a.bootstrap(fa, n=300)
            v = "helps" if hi < 1.0 else ("hurts" if lo > 1.0 else "no significant effect")
            out.append(f"| {f} | {fa(a.median):.3f} [{lo:.3f}, {hi:.3f}] | {v} |")
        # Parsimony: the smallest configuration statistically indistinguishable from the winner.
        out.append("\n## Parsimonious choice\n")
        cand = []
        for c in ranked:
            fa = a.obj_fn(c, rel=best)
            lo, hi = a.bootstrap(fa, n=200)
            if lo <= 1.02:
                cand.append((len(cfg_flags(c)), a.objective(c), c, lo, hi))
        cand.sort()
        for k, o, c, lo, hi in cand[:8]:
            out.append(f"- `{c}` ({k} flags): objective {o:.3f}, vs winner [{lo:.3f}, {hi:.3f}]")
    # Factorial effects (exact when the design is a full factorial over `flags`).
    full = all(cfg_key(c) in cfgs for n in range(len(flags) + 1)
               for c in itertools.combinations(flags, n))
    if full and flags:
        out.append("\n## Factorial effects on log(time)\n")
        out.append("Main effect = mean log ratio with flag − without (negative = faster; ×-factor shown).")
        out.append("Interaction AB > 0 ⇒ the pair is sub-additive (overlapping benefits / redundancy).\n")
        def eff(term, wls):
            tot = 0.0
            for c in cfgs:
                if c not in [cfg_key(x) for n in range(len(flags) + 1) for x in itertools.combinations(flags, n)]:
                    continue
                s = 1
                fl = set(cfg_flags(c))
                for f in term:
                    s *= 1 if f in fl else -1
                tot += s * sum(math.log(a.median(c, w)) for w in wls) / len(wls)
            return tot / (2 ** (len(flags) - 1))
        for label, wls in (("all workloads", a.wls), ("stdlib", std), ("stress", stress)):
            if not wls:
                continue
            out.append(f"### {label}\n")
            out.append("| term | effect | ×factor |\n|---|---|---|")
            terms = [(f,) for f in flags] + list(itertools.combinations(flags, 2))
            es = sorted(((eff(t, wls), t) for t in terms), key=lambda x: -abs(x[0]))
            for e, t in es[:len(flags) + 10]:
                out.append(f"| {'×'.join(t)} | {e:+.3f} | {math.exp(e):.2f} |")
            out.append("")
    open(os.path.join(ROOT, "runs", name, "report.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))

# ---------------------------------------------------------------------------------------------
# Process control

def load_spec(path):
    spec = json.load(open(path))
    d = os.path.join(ROOT, "runs", spec["name"])
    os.makedirs(d, exist_ok=True)
    saved = os.path.join(d, "spec.json")
    if os.path.exists(saved):
        old = json.load(open(saved))
        if old.get("bin") != spec.get("bin"):
            raise SystemExit(f"spec bin changed ({old['bin']} -> {spec['bin']}); use a new name")
    json.dump(spec, open(saved, "w"), indent=1)
    return spec

def cmd_run(argv):
    spec = load_spec(argv[0])
    lock = open(os.path.join(ROOT, "runs", spec["name"], "lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("already running:", spec["name"]); return
    signal.signal(signal.SIGTERM, _on_term)
    open(os.path.join(ROOT, "runs", spec["name"], "pid"), "w").write(str(os.getpid()))
    stopfile = os.path.join(ROOT, "runs", spec["name"], "STOP")
    if os.path.exists(stopfile):
        os.remove(stopfile)
    r = Runner(spec)
    orig = r.measure
    def measure(*a):
        if os.path.exists(stopfile):
            raise KeyboardInterrupt
        orig(*a)
    r.measure = measure
    try:
        r.run()
    except KeyboardInterrupt:
        print("stopped; re-run to continue")

def cmd_start(argv):
    spec = load_spec(argv[0])
    d = os.path.join(ROOT, "runs", spec["name"])
    log = open(os.path.join(d, "runner.log"), "a")
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "run", os.path.abspath(argv[0])],
                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    print(f"started {spec['name']} (pid {p.pid}); log: {os.path.join(d, 'runner.log')}")

QUEUE = os.path.join(ROOT, "runs", "QUEUE.json")

def cmd_queue(argv):
    os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
    specs = [os.path.abspath(a) for a in argv]
    for sp in specs:
        load_spec(sp)                                    # validate early
    json.dump({"specs": specs}, open(QUEUE, "w"), indent=1)
    cmd_resume([])

def cmd_resume(argv):
    if not os.path.exists(QUEUE):
        print("no queue"); return
    log = open(os.path.join(ROOT, "runs", "queue.log"), "a")
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "_runqueue"], stdout=log,
                         stderr=subprocess.STDOUT, start_new_session=True)
    print(f"queue runner started (pid {p.pid}); log: {os.path.join(ROOT, 'runs', 'queue.log')}")

def cmd_runqueue(argv):
    lock = open(QUEUE + ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("queue already running"); return
    for sp in json.load(open(QUEUE))["specs"]:
        name = json.load(open(sp))["name"]
        st = os.path.join(ROOT, "runs", name, "status.json")
        if os.path.exists(st) and json.load(open(st)).get("finished"):
            continue
        print(time.strftime("%F %T"), "running", name, flush=True)
        subprocess.run([sys.executable, os.path.abspath(__file__), "run", sp])
        if os.path.exists(os.path.join(ROOT, "runs", name, "STOP")):
            print("stopped by request"); return
        if not (os.path.exists(st) and json.load(open(st)).get("finished")):
            print(time.strftime("%F %T"), name, "did not finish; run `tcx.py resume` to continue",
                  flush=True)
            return
        subprocess.run([sys.executable, os.path.abspath(__file__), "analyze", name],
                       stdout=subprocess.DEVNULL)
    print(time.strftime("%F %T"), "queue complete", flush=True)

def cmd_stop(argv):
    open(os.path.join(ROOT, "runs", argv[0], "STOP"), "w").close()
    print("stop requested")

def cmd_status(argv):
    runs = os.path.join(ROOT, "runs")
    for name in (argv or sorted(os.listdir(runs) if os.path.isdir(runs) else [])):
        sp = os.path.join(runs, name, "status.json")
        if not os.path.exists(sp):
            print(f"{name}: no status yet"); continue
        st = json.load(open(sp))
        rows = Store(name).rows
        alive = False
        try:
            os.kill(st["pid"], 0); alive = True
        except OSError:
            pass
        ts = [r["at"] for r in rows if r.get("kind") == "time"][-200:]
        rate = (len(ts) - 1) / (ts[-1] - ts[0]) if len(ts) > 2 and ts[-1] > ts[0] else 0
        left = st["planned"] - st["done"]
        eta = f"{left / rate / 3600:.1f} h" if rate else "?"
        state = "finished" if st.get("finished") else ("running" if alive else "STOPPED (re-run to resume)")
        extra = f" gen={st['generation']} best={st['best']}" if "generation" in st else ""
        print(f"{name}: {state}; {st['done']}/{st['planned']} planned measurements, "
              f"{rate * 60:.1f}/min, ETA {eta}{extra}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); return
    cmd, argv = sys.argv[1], sys.argv[2:]
    {"freeze": cmd_freeze, "semtest": cmd_semtest, "run": cmd_run, "start": cmd_start,
     "stop": cmd_stop, "status": cmd_status, "analyze": cmd_analyze, "queue": cmd_queue,
     "resume": cmd_resume, "_runqueue": cmd_runqueue}[cmd](argv)

if __name__ == "__main__":
    main()
