#!/usr/bin/env python3
"""Fits growth laws to results.jsonl and writes tables.md and fits.json.

For each (family, configuration) and each quantity (the family's primary counter, type.user
time, and every other counter), the completed points (n_i, y_i) are fitted with two models, each
with a constant term because every program pays a fixed cost (for example the givens of the
standard library are candidates for every goal):

    polynomial   y = a + c * n^p        (p searched in 0.05 .. 14)
    exponential  y = a + c * r^n        (r searched in 1.01 .. 40)

with a >= 0, c > 0, minimizing the root-mean-square error of log y ("rms", so 0.05 means the
model is within about 5% of the data). The plain two-parameter fits (log-log and semi-log
regressions, a = 0) are reported as well, with their R^2, over the upper half of the size range
where the constant term matters least.

Decision:
    flat          max y / min y <= 1.25
    too few       fewer than 4 completed points, or (for a polynomial claim) sizes spanning less
                  than a factor of 4, or the two models fit about equally well
    polynomial    rms_poly <= 0.6 * rms_exp (or both negligible and the range is >= 8x with
                  exponent stable), and rms_poly < 0.25
    exponential   rms_exp <= 0.6 * rms_poly, rms_exp < 0.25, and y grows by at least 8x
"""
import json, math, os, sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402

CONFIGS = ["base", "FIX", "MIN5", "FULL"]
EXTRA = ["FULL-eqsolve", "FULL-absmodel", "FULL-absquotient"]   # leave-one-out, on some families


def load(path):
    pts = {}
    times = defaultdict(list)
    nondet = []
    for l in open(path):
        if not l.strip():
            continue
        r = json.loads(l)
        k = (r["family"], r["n"], r["config"])
        if r.get("pass", 0) == 0:
            pts[k] = r
        if r.get("type_user_ms") is not None and r["status"] in ("ok", "err"):
            times[k].append((r.get("pass", 0), r["type_user_ms"], r.get("counters"), r["status"]))
    for k, r in pts.items():
        if r["status"] in ("ok", "err"):
            ts = [t for (p, t, c, s) in times[k]]
            r["time_ms"] = min(ts)
            r["time_n"] = len(ts)
            for (p, t, c, s) in times[k]:
                if p != 0 and (c != r["counters"] or s != r["status"]):
                    nondet.append(k)
    return pts, sorted(set(nondet))


# ---------------------------------------------------------------- fitting

def _wls(f, y):
    """Best a >= 0, c > 0 for y ~ a + c*f in relative error; returns (a, c) or None."""
    w = 1.0 / y
    A = np.stack([w, f * w], axis=1)
    sol, *_ = np.linalg.lstsq(A, np.ones_like(y), rcond=None)
    a, c = sol
    if a < 0:
        a = 0.0
        c = float(np.sum(f * w) / np.sum((f * w) ** 2))
    if c <= 0 or not np.isfinite(c):
        return None
    return a, c


def _rms(y, model):
    if np.any(model <= 0) or not np.all(np.isfinite(model)):
        return math.inf
    return float(np.sqrt(np.mean((np.log(y) - np.log(model)) ** 2)))


def fit_poly(n, y):
    best = (math.inf, None, None, None)
    for p in np.arange(0.05, 14.001, 0.05):
        f = (n / n.max()) ** p
        s = _wls(f, y)
        if s is None:
            continue
        e = _rms(y, s[0] + s[1] * f)
        if e < best[0] - 1e-12:
            best = (e, float(p), s[0], s[1])
    return best


def fit_exp(n, y):
    best = (math.inf, None, None, None)
    for lr in np.linspace(math.log(1.01), math.log(40), 500):
        f = np.exp(lr * (n - n.max()))
        s = _wls(f, y)
        if s is None:
            continue
        e = _rms(y, s[0] + s[1] * f)
        if e < best[0] - 1e-12:
            best = (e, float(math.exp(lr)), s[0], s[1])
    return best


def linreg(x, y):
    if len(x) < 2 or np.ptp(x) == 0:
        return None, None
    s, i = np.polyfit(x, y, 1)
    res = y - (s * x + i)
    tot = y - y.mean()
    r2 = 1 - float(res @ res) / float(tot @ tot) if float(tot @ tot) > 0 else 1.0
    return float(s), r2


def exact_poly(n, y, maxdeg=5):
    """The exact polynomial through a suffix of the (noise-free) series, if there is one.

    Returns (start index, degree, coefficients, highest first) for the longest suffix that lies
    on a polynomial of degree k <= maxdeg to a relative precision of 1e-6, with at least k + 3
    points (so at least two points check the k + 1 coefficients). None otherwise.
    """
    for start in range(0, len(n)):
        ns_, ys_ = n[start:], y[start:]
        for k in range(0, maxdeg + 1):
            if len(ns_) < k + 3:
                break
            with np.errstate(all="ignore"):
                try:
                    co = np.polyfit(ns_ / ns_.max(), ys_, k)
                except Exception:
                    continue
            if np.max(np.abs(np.polyval(co, ns_ / ns_.max()) - ys_) / ys_) < 1e-6:
                co = co / ns_.max() ** np.arange(k, -1, -1)
                if k > 0 and co[0] <= 0:
                    continue
                return start, k, [float(c) for c in co]
    return None


def poly_text(co):
    k = len(co) - 1
    def num(c):
        return f"{c:.4g}" if abs(c - round(c)) > 1e-6 else f"{int(round(c)):,}"
    ts = []
    for i, c in enumerate(co):
        d = k - i
        if abs(c) < 1e-9:
            continue
        v = num(abs(c))
        t = v if d == 0 else (("" if v == "1" else v) + ("n" if d == 1 else f"n^{d}"))
        ts.append(("− " if c < 0 else "+ ") + t)
    return " ".join(ts).lstrip("+ ") if ts else "0"


def classify(ns, ys, noisy=False):
    """Returns a dict describing the growth of ys over ns.

    The models are fitted to the whole series and to its suffixes (dropping up to the first
    points while at least 5 points spanning a factor of 4 remain), because several families
    change regime at small sizes (for example when the search first reaches the depth bound).
    The longest suffix that one model fits well is used, and its first size is reported.
    """
    pts = [(n, y) for n, y in zip(ns, ys) if y is not None and y > 0]
    out = {"k": len(pts)}
    if len(pts) < 2:
        out.update(kind="none", law="–")
        return out
    n = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    out.update(nmin=n.min(), nmax=n.max(), ymin=float(y.min()), ymax=float(y.max()),
               span=float(n.max() / n.min()), ratio=float(y.max() / y.min()))
    # plain fits on the upper half of the range (at least 3 points)
    h = max(3, (len(n) + 1) // 2)
    nu, yu = n[-h:], y[-h:]
    out["loglog_p"], out["loglog_r2"] = linreg(np.log(nu), np.log(yu))
    s, out["semilog_r2"] = linreg(nu, np.log(yu))
    out["semilog_r"] = math.exp(s) if s is not None else None
    out["last_p"] = float(math.log(y[-1] / y[-2]) / math.log(n[-1] / n[-2])) if y[-2] > 0 else None
    if out["ratio"] <= (1.6 if noisy else 1.25):
        out.update(kind="flat", law="flat")
        return out
    if len(pts) < 4:
        out.update(kind="few", law=f"too few points ({len(pts)})")
        return out
    if not noisy:
        ex = exact_poly(n, y)
        # Accept the exact polynomial unless it only covers a short tail of the series.
        if ex is not None and (ex[0] == 0 or (n[-1] / n[ex[0]] >= 4 and len(n) - ex[0] >= 5)
                               or len(n) - ex[0] >= max(5, len(n) - 2)):
            start, k, co = ex
            frm = f", n ≥ {int(n[start])}" if start > 0 else ""
            out.update(kind="poly" if k > 0 else "flat", exponent=float(k), exact=True, coeffs=co,
                       fit_from=float(n[start]), fit_span=float(n[-1] / n[start]),
                       law=(f"{poly_text(co)} (exact{frm})" if k > 0 else f"constant (exact{frm})"))
            return out
    good = 0.12 if noisy else 0.03       # a fit this close is accepted
    lim = 0.35 if noisy else 0.25
    q = lambda e: f"rms {e:.2f}" if e >= 0.005 else "rms <0.01"
    cands = []
    for start in range(0, max(1, len(n) - 4)):
        ns_, ys_ = n[start:], y[start:]
        if start > 0 and (len(ns_) < 5 or ns_.max() / ns_.min() < 4):
            break
        if ys_.max() / ys_.min() <= (1.6 if noisy else 1.25):
            break
        ep, p, ap, cp = fit_poly(ns_, ys_)
        ee, r, ae, ce = fit_exp(ns_, ys_)
        if p is not None and p >= 13.9:   # exponent at the edge of the search: not a polynomial
            ep = math.inf
        cands.append((start, ep, p, ee, r, ns_, ys_))
        if min(ep, ee) < good:
            break
    start, ep, p, ee, r, ns_, ys_ = min(cands, key=lambda c: (min(c[1], c[3]) >= good, c[0]))         if any(min(c[1], c[3]) < good for c in cands) else cands[0]
    span = float(ns_.max() / ns_.min())
    ratio = float(ys_.max() / ys_.min())
    out.update(poly_rms=ep, poly_p=p, exp_rms=ee, exp_r=r, fit_from=float(ns_.min()), fit_span=span)
    frm = f" for n ≥ {int(ns_.min())}" if start > 0 else ""
    poly_ok = ep < lim and (ep <= 0.6 * ee or (ep < 0.02 and ee > 0.03))
    exp_ok = ee < lim and (ee <= 0.6 * ep or (ee < 0.02 and ep > 0.03)) and ratio >= 8
    if poly_ok and not exp_ok:
        if span < 4:
            out.update(kind="few", law=f"too small a range ({span:.1f}x); n^{p:.1f} fits ({q(ep)})")
        else:
            out.update(kind="poly", law=f"n^{p:.2f}{frm} ({q(ep)})", exponent=p)
    elif exp_ok and not poly_ok:
        out.update(kind="exp", law=f"{r:.2f}^n{frm} ({q(ee)})", base=r)
    else:
        out.update(kind="undecided",
                   law=f"undecided: n^{p:.1f} ({q(ep)}) or {r:.2f}^n ({q(ee)})")
    return out


# ---------------------------------------------------------------- report

def fmt_count(v):
    if v is None:
        return "–"
    return f"{v:,}"


def fmt_ms(v):
    if v is None:
        return "–"
    return f"{v:.1f}" if v < 100 else f"{v:,.0f}"


def cell(r, counter, intended):
    """(counter text, time text) for one point."""
    if r is None:
        return "", ""
    s = r["status"]
    if s == "timeout":
        return f"timeout", f">{r.get('timeout_s', 120)} s"
    if s == "crash":
        kind = {134: "out of memory", 139: "stack overflow"}.get(r["exit"], f"exit {r['exit']}")
        return f"crash ({kind})", f"{r['wall_s']:.0f} s wall"
    if s == "skipped":
        return "not run", ""
    c = r["counters"].get(counter, 0)
    mark = ""
    if s != intended:
        c_ = r["counters"]
        why = "depth" if c_.get("summon.depthExhausted") else ""
        if c_.get("summon.budgetExhausted"):
            why = "budget"
        mark = (" ✗" + (f"({why})" if why else "")) if intended == "ok" else " (accepted!)"
    return fmt_count(c) + mark, fmt_ms(r["time_ms"])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results.jsonl")
    pts, nondet = load(path)
    fits = {}
    md = []
    summary = []
    xsummary = []
    wrong = []
    for fam, (g, sizes, intended, env, counter) in gen.FAMILIES.items():
        rows = {n: {c: pts.get((fam, n, c)) for c in CONFIGS + EXTRA} for n in sizes}
        if not any(rows[n][c] for n in sizes for c in CONFIGS):
            continue
        extra = [c for c in EXTRA if any(rows[n][c] for n in sizes)]
        md.append(f"### {fam}\n")
        doc = " ".join(g.__doc__.split())
        envs = ", ".join(f"`{k}={v.replace('{n}', 'n')}`" for k, v in env.items())
        md.append(f"{doc} Intended verdict: {'accepted' if intended == 'ok' else 'rejected'}. "
                  f"Primary counter: `{counter}`." + (f" Environment: {envs}." if envs else "") + "\n")
        md.append("| n | " + " | ".join(f"{c} count | {c} ms" for c in CONFIGS) + " |")
        md.append("|---:|" + "---:|" * (2 * len(CONFIGS)))
        for n in sizes:
            cs = []
            for c in CONFIGS:
                a, b = cell(rows[n][c], counter, intended)
                cs += [a, b]
            if any(cs):
                md.append(f"| {n} | " + " | ".join(cs) + " |")
        md.append("")
        md.append("| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base "
                  "(counter, upper half) | Fastest other counter | Ends with |")
        md.append("|---|---|---|---|---|---|")
        srow = [fam]
        for c in CONFIGS + extra:
            good = [(n, rows[n][c]) for n in sizes if rows[n][c] and rows[n][c]["status"] in ("ok", "err")]
            ns = [n for n, r in good]
            fc = classify(ns, [r["counters"].get(counter, 0) for n, r in good])
            ft = classify(ns, [r["time_ms"] for n, r in good], noisy=True)
            # Times below a few milliseconds are dominated by fixed costs and noise.
            if ft.get("ymax", 0) < 20 and ft["kind"] not in ("none",):
                ft["law"] = f"below 20 ms throughout ({ft['law']})" if ft["kind"] != "flat" else "flat (below 20 ms)"
                ft["kind"] = "small"
            # other counters
            names = sorted({k for n, r in good for k in r["counters"]} - {counter, "absmodel.micros"})
            worst = None
            for k in names:
                fk = classify(ns, [r["counters"].get(k, 0) for n, r in good])
                rank = {"exp": 100, "poly": fk.get("exponent", 0)}.get(fk["kind"], -1)
                if worst is None or rank > worst[0]:
                    worst = (rank, k, fk)
            mine = {"exp": 100, "poly": fc.get("exponent", 0), "flat": 0}.get(fc["kind"], -1)
            other = "–"
            if worst and worst[0] > 0 and (worst[0] > mine + 0.3 or mine < 0):
                other = f"`{worst[1]}`: {worst[2]['law']}"
            # how the series ends
            last = [rows[n][c] for n in sizes if rows[n][c]]
            bad = [r for r in last if r["status"] in ("timeout", "crash")]
            end = "completed"
            if bad:
                r = bad[0]
                end = (f"timeout (>{r.get('timeout_s', 120)} s) at n={r['n']}" if r["status"] == "timeout"
                       else f"crash (exit {r['exit']}) at n={r['n']}")
            elif any(r["status"] == "skipped" for r in last):
                r = [r for r in last if r["status"] == "skipped"][0]
                end = f"stopped before n={r['n']}: {r['why']}"
            verd = [r["status"] for n, r in good]
            flips = [n for n, r in good if r["status"] != intended]
            if flips:
                wrong.append((fam, c, intended, flips, good))
                end += f"; verdict differs from the intended one at n={flips[0]}" + ("" if len(flips) == 1 else f"..{flips[-1]}")
            ll = "–"
            if fc.get("loglog_p") is not None:
                ll = f"n^{fc['loglog_p']:.2f} (R² {fc['loglog_r2']:.3f}) / {fc['semilog_r']:.2f}^n (R² {fc['semilog_r2']:.3f})"
            md.append(f"| {c} | {fc['law']} | {ft['law']} | {ll} | {other} | {end} |")
            fits[f"{fam}/{c}"] = {"counter": counter, "counter_fit": fc, "time_fit": ft, "end": end,
                                  "other": other, "sizes": ns}
            short = lambda f: {"flat": "flat", "poly": (f"n^{f.get('exponent', 0):.0f} exact" if f.get("exact") else f"n^{f.get('exponent', 0):.1f}"),
                               "exp": f"{f.get('base', 0):.1f}^n", "few": "too few",
                               "undecided": "undecided", "none": "–", "small": "<20 ms"}[f["kind"]]
            tail = ""
            if bad:
                tail = " †" if bad[0]["status"] == "timeout" else " ‡"
            elif "stopped" in end:
                tail = " †"
            if flips:
                tail += " ✗"
            if c in CONFIGS:
                srow.append(f"{short(fc)} / {short(ft)}{tail}")
            else:
                xsummary.append([fam, c, f"{short(fc)} / {short(ft)}{tail}", end])
        summary.append(srow)
        md.append("")
        if extra:
            md.append("Leave-one-out configurations (same counter):\n")
            md.append("| n | " + " | ".join(f"{c} count | {c} ms" for c in extra) + " |")
            md.append("|---:|" + "---:|" * (2 * len(extra)))
            for n in sizes:
                cs = []
                for c in extra:
                    a, b = cell(rows[n][c], counter, intended)
                    cs += [a, b]
                if any(cs):
                    md.append(f"| {n} | " + " | ".join(cs) + " |")
            md.append("")

    head = ["## Summary: growth of the primary counter / of the time\n",
            "| Family | " + " | ".join(CONFIGS) + " |", "|---|" + "---|" * len(CONFIGS)]
    for s in summary:
        head.append("| " + " | ".join(s) + " |")
    head.append("")
    head.append("† the series ends with a timeout (or was stopped because a timeout was predicted); "
                "‡ it ends with a crash; ✗ at some size the verdict differs from the intended one.\n")
    if xsummary:
        head += ["## Summary: leave-one-out configurations\n", "| Family | Configuration | Growth (counter / time) | Ends with |", "|---|---|---|---|"]
        head += ["| " + " | ".join(x) + " |" for x in xsummary]
        head.append("")
    with open(os.path.join(HERE, "tables.md"), "w") as f:
        f.write("\n".join(head) + "\n## Tables per family\n\n" + "\n".join(md) + "\n")
    with open(os.path.join(HERE, "fits.json"), "w") as f:
        json.dump(fits, f, indent=1, default=float)
    print("\n".join(head))
    if nondet:
        print("NON-DETERMINISTIC counters or verdicts:", nondet)
    print("\nVerdicts that differ from the intended one:")
    for fam, c, intended, flips, good in wrong:
        r = [r for n, r in good if n == flips[0]][0]
        cs = r["counters"]
        print(f"  {fam:18} {c:5} intended={intended} differs at n={flips} "
              f"depthEx={cs.get('summon.depthExhausted')} budgetEx={cs.get('summon.budgetExhausted')} "
              f"{(r['diags'] or [''])[0][:160]}")


if __name__ == "__main__":
    main()
