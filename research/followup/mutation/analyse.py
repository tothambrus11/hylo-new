"""Analyses results.jsonl and writes analysis.md (tables) and classified.jsonl (one row per mutant).

Cost of a mutant under a configuration = the work counters of the module that contains the mutation
(counters.user for a mutated program, counters.stdlib for a mutated standard library), compared with
the same counters of the unmutated source under the same configuration.
"""
import collections, json, math, os, random, sys
import tc

CFGS = ["base", "min5", "min5abs", "full"]
FLOOR = 1000          # "non-trivial" cost: at least this many candidate matches


def load():
    mutants = {}
    for ln in open(os.path.join(tc.HERE, "mutants.jsonl")):
        m = json.loads(ln); mutants[m["id"]] = m
    base = collections.defaultdict(dict)
    for name in ("baseline.jsonl", "baseline-corpus.jsonl"):
        p = os.path.join(tc.HERE, name)
        if not os.path.exists(p): continue
        for ln in open(p):
            r = json.loads(ln); base[r["file"]][r["config"]] = r
    res = collections.defaultdict(dict)
    for ln in open(os.path.join(tc.HERE, "results.jsonl")):
        r = json.loads(ln); res[r["id"]][r["config"]] = r
    return mutants, base, res


def classify(rows):
    """Class of a mutant from its result under base."""
    b = rows["base"]
    if b["status"] == "timeout": return "timeout"
    if b["status"] != "ok": return "crash"
    if any(tc.SYNTAX_PAT.search(m) for m in b["msgs"]): return "syntax"
    return "equivalent" if b["diags"] == 0 else "rejected"


def verdict(r):
    if r["status"] != "ok": return r["status"]
    return "accepted" if r["diags"] == 0 else "rejected"


def ratio(a, b):
    return a / max(1, b)


def quantile(xs, q):
    xs = sorted(xs)
    if not xs: return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def binom_cdf(k, n, p):
    if p <= 0: return 1.0
    if p >= 1: return 1.0 if k >= n else 0.0
    s = 0.0
    for i in range(0, k + 1):
        s += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                      + i * math.log(p) + (n - i) * math.log(1 - p))
    return min(1.0, s)


def clopper_pearson(k, n, alpha=0.05):
    """Exact two-sided confidence interval of a binomial proportion."""
    if n == 0: return (0.0, 1.0)
    def solve(f, lo, hi):
        for _ in range(60):
            mid = (lo + hi) / 2
            if f(mid): lo = mid
            else: hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) < alpha / 2, 0.0, 1.0)
    upper = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) > alpha / 2, 0.0, 1.0)
    return (lower, upper)


def cluster_bootstrap(items, pred, key, reps=4000, seed=1):
    """95% interval of the share of items satisfying `pred`, resampling whole clusters (source files)."""
    clusters = collections.defaultdict(list)
    for it in items: clusters[key(it)].append(1 if pred(it) else 0)
    cl = list(clusters.values())
    if not cl: return (0.0, 1.0)
    rng = random.Random(seed)
    shares = []
    for _ in range(reps):
        k = n = 0
        for _ in range(len(cl)):
            c = rng.choice(cl); k += sum(c); n += len(c)
        shares.append(k / n if n else 0.0)
    return (quantile(shares, 0.025), quantile(shares, 0.975))


def pct(x): return f"{100 * x:.2f}%"


def fmt(x):
    if x != x: return "–"
    if x >= 100: return f"{x:.0f}"
    if x >= 10: return f"{x:.1f}"
    return f"{x:.2f}"


def main():
    mutants, base, res = load()
    out = []
    P = out.append
    rows = []            # one record per complete mutant
    incomplete = 0
    for mid, m in mutants.items():
        r = res.get(mid, {})
        if any(c not in r for c in CFGS):
            incomplete += 1; continue
        key = "<stdlib>" if m["group"] == "stdlib" else m["file"]
        b = base[key]
        rec = {"id": mid, "group": m["group"], "op": m["op"], "variant": m["variant"], "file": m["file"],
               "line": m["line"], "orig": m["orig"], "repl": m["repl"], "cls": classify(r)}
        for c in CFGS:
            rec[c] = r[c]
            rec["v_" + c] = verdict(r[c])
            rec["o_" + c] = b[c]
            rec["rm_" + c] = ratio(r[c]["matches"], b[c]["matches"]) if r[c]["status"] == "ok" else float("inf")
            rec["rt_" + c] = (r[c]["ms"] / max(0.5, b[c]["ms"])) if r[c]["status"] == "ok" and r[c]["ms"] is not None else float("inf")
        rows.append(rec)
    with open(os.path.join(tc.HERE, "classified.jsonl"), "w") as f:
        for rec in rows:
            slim = {k: v for k, v in rec.items() if k not in CFGS and not k.startswith("o_")}
            for c in CFGS:
                slim[c] = {k: rec[c][k] for k in ("status", "diags", "matches", "subgoals", "layers", "depthExhausted", "refuted", "ms")}
                slim["orig_" + c] = {k: rec["o_" + c][k] for k in ("matches", "subgoals", "layers", "ms")}
            f.write(json.dumps(slim) + "\n")

    groups = sorted({r["group"] for r in rows})
    ops = sorted({r["op"] for r in rows})
    P(f"# Mutation results (generated by analyse.py)\n")
    P(f"{len(rows)} mutants with results under all four configurations ({incomplete} not run yet).\n")

    # 1. classification
    P("## 1. Mutants by class (class is decided by the existing checker, `base`)\n")
    P("| group | operator | mutants | rejected | equivalent | syntax error | timeout | crash |")
    P("|---|---|---:|---:|---:|---:|---:|---:|")
    for g in groups + ["all"]:
        for o in ops + ["all"]:
            sel = [r for r in rows if (g == "all" or r["group"] == g) and (o == "all" or r["op"] == o)]
            if not sel: continue
            if g == "all" and o != "all": continue
            c = collections.Counter(r["cls"] for r in sel)
            P(f"| {g} | {o} | {len(sel)} | {c['rejected']} | {c['equivalent']} | {c['syntax']} | {c['timeout']} | {c['crash']} |")
    P("")

    rej = [r for r in rows if r["cls"] == "rejected"]
    hard = [r for r in rows if r["cls"] in ("timeout", "crash")]

    # 2. distribution of the cost ratio
    P("## 2. Cost of rejected mutants relative to the unmutated source\n")
    P("Ratio = `summon.matches` of the mutant / `summon.matches` of the unmutated source, same configuration "
      "(a denominator of 0 is taken as 1). A run that timed out or crashed counts as an infinite ratio.\n")
    for metric, label in (("rm_", "summon.matches"), ("rt_", "typing time (indicative only)")):
        P(f"### {label}\n")
        P("| group | config | n | median | p90 | p99 | max | share > 2× | share > 10× | share > 100× |")
        P("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for g in groups + ["all"]:
            sel = [r for r in rej if g == "all" or r["group"] == g]
            if not sel: continue
            for c in CFGS:
                xs = [r[metric + c] for r in sel]
                fin = [x for x in xs if x != float("inf")]
                mx = "∞" if len(fin) < len(xs) else fmt(max(xs))
                P(f"| {g} | {c} | {len(xs)} | {fmt(quantile(xs, .5))} | {fmt(quantile(xs, .9))} | {fmt(quantile(xs, .99))} | {mx} | "
                  f"{pct(sum(x > 2 for x in xs) / len(xs))} | {pct(sum(x > 10 for x in xs) / len(xs))} | {pct(sum(x > 100 for x in xs) / len(xs))} |")
        P("")

    # 2b. absolute cost
    P("### Absolute cost of rejected mutants (`summon.matches` of the mutated module)\n")
    P("| group | config | n | median | p90 | p99 | max | unmutated: median | unmutated: max |")
    P("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for g in groups:
        sel = [r for r in rej if r["group"] == g]
        if not sel: continue
        for c in CFGS:
            xs = [r[c]["matches"] for r in sel if r[c]["status"] == "ok"]
            os_ = [r["o_" + c]["matches"] for r in sel]
            P(f"| {g} | {c} | {len(xs)} | {quantile(xs, .5):.0f} | {quantile(xs, .9):.0f} | {quantile(xs, .99):.0f} | {max(xs):.0f} | "
              f"{quantile(os_, .5):.0f} | {max(os_):.0f} |")
    P("")

    # 3. expensive mutants
    P("## 3. Mutants much more expensive than the unmutated source (> 10× in `summon.matches`)\n")
    exp_any = [r for r in rej + hard if r["rm_base"] > 10 or r["rm_min5"] > 10]
    P(f"Rejected mutants (plus timeouts and crashes under base): {len(rej) + len(hard)}. "
      f"More than 10× under base: {sum(r['rm_base'] > 10 for r in rej + hard)}. "
      f"More than 10× under MIN5: {sum(r['rm_min5'] > 10 for r in rej + hard)}. Either: {len(exp_any)}.\n")
    P("| mutant | mutation | diags | base: matches (×orig) | MIN5: matches (×orig) | MIN5+abs: matches (×orig) | FULL: matches (×orig) | MIN5 / MIN5+abs | ms base / MIN5 / MIN5+abs / FULL |")
    P("|---|---|---:|---:|---:|---:|---:|---:|---|")
    def cell(r, c):
        x = r[c]
        if x["status"] != "ok": return x["status"]
        return f"{x['matches']} ({fmt(r['rm_' + c])}×)"
    def gain(r):
        if r["min5"]["status"] != "ok" or r["min5abs"]["status"] != "ok": return float("nan")
        return ratio(r["min5"]["matches"], r["min5abs"]["matches"])
    def extra(r, c):
        return r[c]["matches"] - r["o_" + c]["matches"]
    def mscell(r):
        return " / ".join("–" if r[c]["ms"] is None else f"{r[c]['ms']:.0f}" for c in CFGS)
    def mut(r):
        o = r["orig"].replace("\n", " ").replace("|", "\\|")[:50]
        return f"{r['op']} in `{os.path.basename(r['file'])}`:{r['line']} `{o}` → `{r['repl'][:30]}`"
    for r in sorted(exp_any, key=lambda r: -max(r["rm_base"], r["rm_min5"])):
        P(f"| {r['id']} | {mut(r)} | {r['base']['diags']} | {cell(r, 'base')} | {cell(r, 'min5')} | {cell(r, 'min5abs')} | {cell(r, 'full')} | {fmt(gain(r))} | {mscell(r)} |")
    P("")

    # 4. the criterion
    P("## 4. Effect of the abstract model on rejected mutants (MIN5 versus MIN5 + absmodel,absquotient)\n")
    ok = [r for r in rej if r["min5"]["status"] == "ok" and r["min5abs"]["status"] == "ok"]
    notok = [r for r in rej if r not in ok]
    P(f"Rejected mutants: {len(rej)}; with both runs completed: {len(ok)}; one of the two runs failed or timed out: {len(notok)}.\n")
    crit = {
        "matches: MIN5 / MIN5+abs > 10": lambda r: gain(r) > 10,
        f"same, and MIN5 matches ≥ {FLOOR}": lambda r: gain(r) > 10 and r["min5"]["matches"] >= FLOOR,
        "matches: MIN5 / MIN5+abs > 2": lambda r: gain(r) > 2,
        f"same, and MIN5 matches ≥ {FLOOR}": lambda r: gain(r) > 2 and r["min5"]["matches"] >= FLOOR,
        "literal criterion, but the unmutated source does not already gain > 10": lambda r: gain(r) > 10 and ratio(r["o_min5"]["matches"], r["o_min5abs"]["matches"]) <= 10,
        "extra matches caused by the mutation: MIN5 extra > 10 × MIN5+abs extra (extra ≥ 1)": lambda r: extra(r, "min5") >= 1 and extra(r, "min5") > 10 * max(1, extra(r, "min5abs")),
        f"same, and MIN5 extra ≥ {FLOOR}": lambda r: extra(r, "min5") >= FLOOR and extra(r, "min5") > 10 * max(1, extra(r, "min5abs")),
        "subgoals: MIN5 / MIN5+abs > 10": lambda r: ratio(r["min5"]["subgoals"], r["min5abs"]["subgoals"]) > 10,
        "typing time: MIN5 / MIN5+abs > 10 (indicative)": lambda r: r["min5"]["ms"] / max(0.5, r["min5abs"]["ms"]) > 10,
        "typing time: MIN5 / MIN5+abs > 2 (indicative)": lambda r: r["min5"]["ms"] / max(0.5, r["min5abs"]["ms"]) > 2,
        "typing time: MIN5+abs / MIN5 > 2 (slower with the model; indicative)": lambda r: r["min5abs"]["ms"] / max(0.5, r["min5"]["ms"]) > 2,
    }
    P("| criterion | group | mutants meeting it | of | share | exact 95% interval | interval resampling source files |")
    P("|---|---|---:|---:|---:|---|---|")
    seen_names = set()
    for name, pred in crit.items():
        for g in ["all"] + groups:
            sel = [r for r in ok if g == "all" or r["group"] == g]
            if not sel: continue
            k = sum(1 for r in sel if pred(r))
            lo, hi = clopper_pearson(k, len(sel))
            blo, bhi = cluster_bootstrap(sel, pred, lambda r: r["file"])
            P(f"| {name} | {g} | {k} | {len(sel)} | {pct(k / len(sel))} | {pct(lo)} – {pct(hi)} | {pct(blo)} – {pct(bhi)} |")
    P("")
    P("Distribution of the gain MIN5 / MIN5+abs in `summon.matches` over rejected mutants:\n")
    P("| group | n | min | p10 | median | p90 | p99 | max |")
    P("|---|---:|---:|---:|---:|---:|---:|---:|")
    for g in ["all"] + groups:
        xs = [gain(r) for r in ok if g == "all" or r["group"] == g]
        if xs: P(f"| {g} | {len(xs)} | {fmt(min(xs))} | {fmt(quantile(xs, .1))} | {fmt(quantile(xs, .5))} | {fmt(quantile(xs, .9))} | {fmt(quantile(xs, .99))} | {fmt(max(xs))} |")
    P("")
    P("Same gain measured on the unmutated (valid) sources, for comparison:\n")
    P("| group | n | median | p90 | max |")
    P("|---|---:|---:|---:|---:|")
    srcs = {}
    for r in rows: srcs[(r["group"], "<stdlib>" if r["group"] == "stdlib" else r["file"])] = (r["o_min5"]["matches"], r["o_min5abs"]["matches"])
    for g in ["all"] + groups:
        xs = [ratio(a, b) for (gg, _), (a, b) in srcs.items() if g == "all" or gg == g]
        if xs: P(f"| {g} | {len(xs)} | {fmt(quantile(xs, .5))} | {fmt(quantile(xs, .9))} | {fmt(max(xs))} |")
    P("")
    P("Mutants with the largest gain from the abstract model (top 15 by MIN5 / MIN5+abs in matches):\n")
    P("| mutant | mutation | MIN5 matches | MIN5+abs matches | gain | absmodel.refuted | MIN5 ms | MIN5+abs ms |")
    P("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in sorted(ok, key=lambda r: -gain(r))[:15]:
        P(f"| {r['id']} | {mut(r)} | {r['min5']['matches']} | {r['min5abs']['matches']} | {fmt(gain(r))} | {r['min5abs']['refuted']} | {r['min5']['ms']:.0f} | {r['min5abs']['ms']:.0f} |")
    P("")
    P("Mutants with the largest absolute saving (top 15 by MIN5 − MIN5+abs matches):\n")
    P("| mutant | mutation | MIN5 matches | MIN5+abs matches | saved | gain | MIN5 ms | MIN5+abs ms |")
    P("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in sorted(ok, key=lambda r: -(r["min5"]["matches"] - r["min5abs"]["matches"]))[:15]:
        P(f"| {r['id']} | {mut(r)} | {r['min5']['matches']} | {r['min5abs']['matches']} | {r['min5']['matches'] - r['min5abs']['matches']} | {fmt(gain(r))} | {r['min5']['ms']:.0f} | {r['min5abs']['ms']:.0f} |")
    P("")
    P("Depth exhaustion among rejected mutants (`summon.depthExhausted` > 0), and refutations by the model:\n")
    P("| group | n | base: depthExhausted>0 | MIN5 | MIN5+abs | FULL | MIN5+abs: absmodel.refuted>0 | total refuted |")
    P("|---|---:|---:|---:|---:|---:|---:|---:|")
    for g in ["all"] + groups:
        sel = [r for r in ok if g == "all" or r["group"] == g]
        if not sel: continue
        P(f"| {g} | {len(sel)} | " + " | ".join(str(sum(r[c]["depthExhausted"] > 0 for r in sel)) for c in CFGS)
          + f" | {sum(r['min5abs']['refuted'] > 0 for r in sel)} | {sum(r['min5abs']['refuted'] for r in sel)} |")
    P("")

    P("Extra `summon.matches` caused by the mutation (mutant − unmutated source), rejected mutants:\n")
    P("| group | config | n | share with extra > 0 | median | p90 | p99 | max |")
    P("|---|---|---:|---:|---:|---:|---:|---:|")
    for g in ["all"] + groups:
        sel = [r for r in rej if g == "all" or r["group"] == g]
        for c in CFGS:
            xs = [extra(r, c) for r in sel if r[c]["status"] == "ok"]
            if xs: P(f"| {g} | {c} | {len(xs)} | {pct(sum(x > 0 for x in xs) / len(xs))} | {quantile(xs, .5):.0f} | {quantile(xs, .9):.0f} | {quantile(xs, .99):.0f} | {max(xs):.0f} |")
    P("")
    P("Mutants with the largest extra cost under MIN5 (top 15), and what the model does to it:\n")
    P("| mutant | mutation | unmutated MIN5 | mutant MIN5 | extra MIN5 | unmutated MIN5+abs | mutant MIN5+abs | extra MIN5+abs | FULL: unmutated → mutant |")
    P("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for r in sorted(ok, key=lambda r: -extra(r, "min5"))[:15]:
        fu = f"{r['o_full']['matches']} → {r['full']['matches']}" if r["full"]["status"] == "ok" else r["full"]["status"]
        P(f"| {r['id']} | {mut(r)} | {r['o_min5']['matches']} | {r['min5']['matches']} | {extra(r, 'min5')} | {r['o_min5abs']['matches']} | {r['min5abs']['matches']} | {extra(r, 'min5abs')} | {fu} |")
    P("")
    have = [r for r in ok if "all" in r["min5abs"]]
    if have:
        P("The model's own work (`absmodel.work` = saturation steps, `absmodel.micros` = time spent building models), MIN5+abs, rejected mutants:\n")
        P("| group | n | median work | max work | median ms building | max ms building | median share of typing time |")
        P("|---|---:|---:|---:|---:|---:|---:|")
        for g in ["all"] + groups:
            sel = [r for r in have if g == "all" or r["group"] == g]
            if not sel: continue
            w = [r["min5abs"]["all"].get("absmodel.work", 0) for r in sel]
            u = [r["min5abs"]["all"].get("absmodel.micros", 0) / 1000 for r in sel]
            sh = [x / max(0.5, r["min5abs"]["ms"]) for x, r in zip(u, sel)]
            P(f"| {g} | {len(sel)} | {quantile(w, .5):.0f} | {max(w)} | {quantile(u, .5):.2f} | {max(u):.2f} | {pct(quantile(sh, .5))} |")
        P("")
    tp = os.path.join(tc.HERE, "timing.jsonl")
    if os.path.exists(tp):
        P("Repeated timing (minimum over the runs, ms) of the mutants that meet the literal criterion or save the most matches:\n")
        P("| mutant | mutation | MIN5 matches | MIN5+abs matches | MIN5 ms (min) | MIN5+abs ms (min) | time ratio | model building ms |")
        P("|---|---|---:|---:|---:|---:|---:|---:|")
        byid = {r["id"]: r for r in rows}
        for ln in open(tp):
            t = json.loads(ln)
            r = byid.get(t["id"])
            if not r or not t["min5_ms"] or not t["min5abs_ms"]: continue
            a, b = min(t["min5_ms"]), min(t["min5abs_ms"])
            P(f"| {t['id']} | {mut(r)} | {r['min5']['matches']} | {r['min5abs']['matches']} | {a:.1f} | {b:.1f} | {a / max(b, 0.01):.2f} | {min(t['absmodel_micros']) / 1000:.2f} |")
        P("")

    # 5. verdict / diagnostics differences
    P("## 5. Differences in verdict or in number of diagnostics relative to base\n")
    P("Syntactically invalid mutants are excluded. `acc`/`rej n` = accepted / rejected with n diagnostics.\n")
    def vd(x):
        if x["status"] != "ok": return x["status"]
        return "acc" if x["diags"] == 0 else f"rej {x['diags']}"
    for c in ["min5", "min5abs", "full"]:
        diff_v = [r for r in rows if r["cls"] != "syntax" and r["v_" + c] != r["v_base"]]
        diff_d = [r for r in rows if r["cls"] != "syntax" and r["v_" + c] == r["v_base"] and r[c]["status"] == "ok" and r[c]["diags"] != r["base"]["diags"]]
        P(f"### {c}: {len(diff_v)} verdict differences, {len(diff_d)} differences in the number of diagnostics only\n")
        if diff_v or diff_d:
            P("| mutant | mutation | base | " + c + " | unmutated source under " + c + " | first message (base) | first message (" + c + ") |")
            P("|---|---|---|---|---|---|---|")
            for r in diff_v + diff_d:
                mb = (r["base"]["msgs"][0] if r["base"]["msgs"] else "").replace("|", "\\|")[:110]
                mc = (r[c]["msgs"][0] if r[c]["msgs"] else "").replace("|", "\\|")[:110]
                P(f"| {r['id']} | {mut(r)} | {vd(r['base'])} | {vd(r[c])} | {vd(r['o_' + c])} | {mb} | {mc} |")
            P("")
    # also: min5abs vs min5
    d = [r for r in rows if r["cls"] != "syntax" and (r["v_min5abs"] != r["v_min5"] or r["min5abs"]["diags"] != r["min5"]["diags"])]
    P(f"MIN5+abs versus MIN5 directly: {len(d)} differences in verdict or number of diagnostics"
      + (": " + ", ".join(r["id"] for r in d) if d else ".") + "\n")
    dm = [r for r in rows if r["cls"] != "syntax" and r["min5"]["status"] == "ok" and r["min5abs"]["status"] == "ok"
          and r["min5"]["msgs"] != r["min5abs"]["msgs"]]
    P(f"MIN5+abs versus MIN5, text of the diagnostics (first 12 messages compared): {len(dm)} mutants differ"
      + (": " + ", ".join(r["id"] for r in dm) if dm else ".") + "\n")
    dm = [r for r in rows if r["cls"] != "syntax" and r["min5"]["status"] == "ok" and r["base"]["status"] == "ok"
          and r["min5"]["msgs"] != r["base"]["msgs"]]
    P(f"MIN5 versus base, text of the diagnostics: {len(dm)} mutants differ"
      + (": " + ", ".join(r["id"] for r in dm) if dm else ".") + "\n")

    # 6. timeouts and crashes
    P("## 6. Timeouts and crashes\n")
    bad = [r for r in rows if any(r[c]["status"] != "ok" for c in CFGS)]
    if bad:
        P("| mutant | mutation | base | MIN5 | MIN5+abs | FULL |")
        P("|---|---|---|---|---|---|")
        for r in bad:
            P(f"| {r['id']} | {mut(r)} | " + " | ".join(f"{vd(r[c])} (exit {r[c]['exit']})" if r[c]["status"] != "ok" else f"{vd(r[c])}, {r[c]['matches']} matches" for c in CFGS) + " |")
    else:
        P("None.")
    P("")

    # 7. by kind of error
    P("## 7. Cost by operator (rejected mutants, MIN5): which errors are expensive\n")
    P("| operator | n | median ratio | p90 ratio | max ratio | max matches | max gain from absmodel |")
    P("|---|---:|---:|---:|---:|---:|---:|")
    for o in ops:
        sel = [r for r in ok if r["op"] == o]
        if not sel: continue
        xs = [r["rm_min5"] for r in sel]
        P(f"| {o} | {len(sel)} | {fmt(quantile(xs, .5))} | {fmt(quantile(xs, .9))} | {fmt(max(xs))} | {max(r['min5']['matches'] for r in sel)} | {fmt(max(gain(r) for r in sel))} |")
    P("")
    dp = os.path.join(tc.HERE, "depth.jsonl")
    if os.path.exists(dp):
        P("## 8. Dependence on the depth bound `HYLO_TC_MAXDEPTH`\n")
        P("`summon.matches` (typing ms, indicative); `to` = timeout at 120 s, `oom` = aborted at the 2.5 GB memory cap.\n")
        d = collections.defaultdict(dict)
        for ln in open(dp):
            x = json.loads(ln); d[(x["id"], x["what"])][(x["config"], x["depth"])] = x
        byid = {r["id"]: r for r in rows}
        P("| mutant | program | base 10 | base 12 | base 14 | MIN5 10 | MIN5 12 | MIN5 14 | MIN5+abs 10 | MIN5+abs 12 | MIN5+abs 14 |")
        P("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        def dc(x):
            if x is None: return "–"
            if x["status"] == "timeout": return "to"
            if x["status"] != "ok": return "oom" if x["exit"] in (-6, 134) else f"crash {x['exit']}"
            return f"{x['matches']} ({x['ms']:.0f}) d{x['diags']}"
        for (mid, what), cells in d.items():
            P(f"| {mid} | {what} | " + " | ".join(dc(cells.get((c, dd))) for c in ("base", "min5", "min5abs") for dd in (10, 12, 14)) + " |")
        P("")
    # sources with and without equality requirements
    import re, mutate
    eqcache = {}
    def has_eq(r):
        m = mutants[r["id"]]
        pth = os.path.join(tc.ORIG_STD, m["file"][len("stdlib:"):]) if m["group"] == "stdlib" else os.path.join(tc.ROOT, m["file"])
        if pth not in eqcache:
            eqcache[pth] = bool(re.search(r"where[^{}()\n]*==", mutate.mask(open(pth).read())))
        return eqcache[pth]
    P("## 12. Outcome under base by whether the source program has an equality requirement (`where ... ==`)\n")
    P("`wrongly accepted` = accepted by base, rejected by FULL (each one inspected: all are ill-typed).\n")
    P("| source has an equality requirement | group | mutants | rejected normally | memory exhausted | wrongly accepted | still valid | syntax error |")
    P("|---|---|---:|---:|---:|---:|---:|---:|")
    for eq in (True, False):
        for g in ["all"] + groups:
            sel = [r for r in rows if has_eq(r) == eq and (g == "all" or r["group"] == g)]
            if not sel: continue
            wrong = sum(r["cls"] == "equivalent" and r["full"]["status"] == "ok" and r["full"]["diags"] > 0 for r in sel)
            c = collections.Counter(r["cls"] for r in sel)
            P(f"| {'yes' if eq else 'no'} | {g} | {len(sel)} | {c['rejected']} | {c['crash'] + c['timeout']} | {wrong} | {c['equivalent'] - wrong} | {c['syntax']} |")
    P("")
    ap = os.path.join(tc.HERE, "attrib.jsonl")
    if os.path.exists(ap):
        P("## 9. Which technique removes the blow-ups\n")
        P("Each mutant that exhausted memory under base, under MIN5 plus one or several fixes (memory cap 600 MB, 60 s). "
          "`rej n: m` = rejected with n diagnostics after m candidate matches (typing ms, indicative); `oom` = memory exhausted; `to` = timeout.\n")
        d = collections.defaultdict(dict)
        cfgs = []
        for ln in open(ap):
            x = json.loads(ln); d[x["id"]][x["config"]] = x
            if x["config"] not in cfgs: cfgs.append(x["config"])
        def ac(x):
            if x is None: return "–"
            if x["status"] == "timeout": return "to"
            if x["status"] != "ok": return "oom" if x["exit"] in (-6, 134) else f"crash {x['exit']}"
            return (f"rej {x['diags']}" if x["diags"] else "acc") + f": {x['matches']} ({x['ms']:.0f})"
        P("| mutant | " + " | ".join(("MIN5+" + c[5:] if c.startswith("min5+") else "FULL−" + c[5:] if c.startswith("full-") else "FIX−" + c[4:] if c.startswith("fix-") else c.upper()) for c in cfgs) + " |")
        P("|---|" + "---|" * len(cfgs))
        for mid, cells in d.items():
            P(f"| {mid} | " + " | ".join(ac(cells.get(c)) for c in cfgs) + " |")
        P("")
        P("| configuration | mutants run | rejected normally | memory exhausted | timeout |")
        P("|---|---:|---:|---:|---:|")
        for c in cfgs:
            xs = [cells[c] for cells in d.values() if c in cells]
            P(f"| {c} | {len(xs)} | {sum(x['status'] == 'ok' and x['diags'] > 0 for x in xs)} | {sum(x['status'] == 'crash' for x in xs)} | {sum(x['status'] == 'timeout' for x in xs)} |")
        P("")
    rp = os.path.join(tc.HERE, "recheck.jsonl")
    if os.path.exists(rp):
        P("## 10. Blow-ups re-run with the default 2.5 GB memory cap (120 s)\n")
        P("| mutant | config | result | wall time (s) |")
        P("|---|---|---|---:|")
        for ln in open(rp):
            x = json.loads(ln)
            st = "memory exhausted" if x["status"] == "crash" and x["exit"] in (-6, 134) else x["status"] if x["status"] != "ok" else f"rej {x['diags']}, {x['matches']} matches"
            P(f"| {x['id']} | {x['config']} | {st} | {x['wall']:.0f} |")
        P("")
    sp = os.path.join(tc.HERE, "shapes.jsonl")
    if os.path.exists(sp):
        P("## 11. Library-shaped probe: one missing conformance under a trait hierarchy (shapes.py)\n")
        P("h = number of refinement steps, n = nesting depth of the type in the failing goal. Cells: `summon.matches` (typing ms, indicative); "
          "`to` = timeout at 60 s, `oom` = memory exhausted. `@14` = with HYLO_TC_MAXDEPTH=14.\n")
        d = collections.defaultdict(dict)
        for ln in open(sp):
            x = json.loads(ln); d[(x["shape"], x["h"], x["n"])][(x["valid"], x["config"], x["depth"])] = x
        def sc(x):
            if x is None: return "–"
            if x["status"] == "timeout": return "to"
            if x["status"] != "ok": return "oom" if x["exit"] in (-6, 134) else f"crash {x['exit']}"
            return f"{x['matches']} ({x['ms']:.0f})" + ("" if x["diags"] else " acc")
        P("| shape | h | n | valid: base | valid: MIN5 | valid: MIN5+abs | valid: FULL | error: base | error: MIN5 | error: MIN5+abs | error: FULL | error: MIN5 @14 | error: MIN5+abs @14 |")
        P("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for (shape, h, n), cells in sorted(d.items()):
            row = [sc(cells.get((True, c, 10))) for c in CFGS] + [sc(cells.get((False, c, 10))) for c in CFGS] \
                + [sc(cells.get((False, "min5", 14))), sc(cells.get((False, "min5abs", 14)))]
            P(f"| {shape} | {h} | {n} | " + " | ".join(row) + " |")
        P("")
    open(os.path.join(tc.HERE, "analysis.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
