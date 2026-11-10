"""Aggregates results.jsonl: per query and configuration, the class of (dis)agreement.

    python3 report.py            tables
    python3 report.py --list CLASS [--config FIX] [--kind eq-app] [-n 20]   examples
"""
import argparse
import collections
import json
import os

import explain
import harness
import reference
import to_hylo

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    problems = {}
    for l in open(os.path.join(HERE, "problems.jsonl")):
        p = json.loads(l)
        problems[p["id"]] = p
    runs = collections.defaultdict(dict)       # (id, config) -> world row, isolated rows
    for l in open(os.path.join(HERE, "results.jsonl")):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        key = (r["id"], r["config"])
        if r["isolated"] is None:
            # A world run alone overrides its row from a batch run.
            if "world" in runs[key] and r.get("batch") and not runs[key]["world"].get("batch"):
                continue
            if "world" in runs[key] and runs[key]["world"].get("batch") and not r.get("batch"):
                runs[key]["confirmed"] = runs[key]["world"]
            runs[key]["world"] = r
        else:
            runs[key].setdefault("isolated", {})[r["isolated"]] = r
    return problems, runs


def verdict_of(run, i):
    """The compiler's verdict on query i: accept, reject, crash, timeout, invalid, or None."""
    w = run.get("world")
    if w is None:
        return None, ""
    if w["status"] == "ok":
        return w["verdicts"][str(i)], w["messages"].get(str(i), "")
    if w["status"] == "invalid":
        return "invalid", w["messages"].get("-1", "")
    iso = run.get("isolated", {}).get(i)
    if iso is None:
        return w["status"], ""
    if iso["status"] == "ok":
        return iso["verdicts"][str(i)], iso["messages"].get(str(i), "")
    return iso["status"], ""


def rows(problems, runs, configs=("base", "FIX", "FULL")):
    for pid, p in problems.items():
        for i, a in enumerate(p["answers"]):
            for c in configs:
                run = runs.get((pid, c))
                if not run:
                    continue
                v, msg = verdict_of(run, i)
                if v is None:
                    continue
                if v in ("accept", "reject"):
                    k = harness.classify(a, v)
                    if a.get("twin"):
                        k = "agree" if v == "reject" else "AMBIGUITY-MISSED"
                    if v == "reject" and "too complex" in msg:
                        # The resource bound of `budget` was reached.
                        k = "BUDGET-" + ("agree" if k == "agree" else k)
                    if k == "INCOMPLETE" and a.get("ordered") is False and "no static member" in msg:
                        k = "WHERE-ORDER"
                else:
                    k = v.upper()
                yield {"id": pid, "q": i, "kind": p["kind"], "config": c, "verdict": v,
                       "class": k, "msg": msg, "answer": a}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list")
    ap.add_argument("--config")
    ap.add_argument("--kind")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--tags", help="with --list: only rows whose explanation is this (e.g. '' or DECOMP)")
    ap.add_argument("--markdown", action="store_true", help="tables for the README")
    args = ap.parse_args()
    problems, runs = load()
    rs = list(rows(problems, runs))
    worlds = {}

    def tags_of(r):
        if r["id"] not in worlds:
            worlds[r["id"]] = reference.load_world(problems[r["id"]]["world"])
        w = worlds[r["id"]]
        key = (r["id"], r["q"])
        if key not in tag_memo:
            tag_memo[key] = "+".join(sorted(explain.tags(w, w["queries"][r["q"]])))
        return tag_memo[key]
    tag_memo = {}

    if args.list:
        n = 0
        for r in rs:
            if r["class"] != args.list or (args.config and r["config"] != args.config) \
                    or (args.kind and r["kind"] != args.kind):
                continue
            if args.tags is not None and tags_of(r) != args.tags:
                continue
            w = reference.load_world(problems[r["id"]]["world"])
            a = r["answer"]
            print("%s q%d %s: %s | ref=%s n=%s size=%s eq=%s cong=%s sem=%s" % (
                r["id"], r["q"], r["config"], r["verdict"], a["verdict"], a["count"], a["size"],
                a["eq_needed"], a["congruence"], a["sem"]))
            print("   ", to_hylo.query_line(w, r["q"], w["queries"][r["q"]]))
            if r["msg"]:
                print("    msg:", r["msg"][:150])
            n += 1
            if n >= args.n:
                break
        return

    if args.markdown:
        markdown(problems, runs, rs, tags_of)
        return

    configs = ("base", "FIX", "FULL")
    print("worlds run:", {c: sum(1 for (i, k) in runs if k == c) for c in configs})
    print("queries compared:", {c: sum(1 for r in rs if r["config"] == c) for c in configs})
    print()
    classes = sorted({r["class"] for r in rs})
    print("## classes by configuration")
    t = collections.Counter((r["class"], r["config"]) for r in rs)
    for k in classes:
        print("%-18s" % k, "  ".join("%s=%-6d" % (c, t[(k, c)]) for c in configs))
    print()
    print("## classes by kind and configuration")
    t = collections.Counter((r["kind"], r["class"], r["config"]) for r in rs)
    for kind in sorted({r["kind"] for r in rs}):
        for k in classes:
            if any(t[(kind, k, c)] for c in configs):
                print("%-9s %-18s" % (kind, k), "  ".join("%s=%-6d" % (c, t[(kind, k, c)]) for c in configs))
    print()
    print("## derivable goals with one derivation: accepted / total, by smallest derivation")
    t = collections.Counter()
    for r in rs:
        a = r["answer"]
        if a["verdict"] == "derivable" and not (a["count"] or 0) >= 2 and r["verdict"] in ("accept", "reject"):
            key = (a["size"], min(a["eq_needed"], 4), bool(a["congruence"]))
            t[(key, r["config"], r["verdict"])] += 1
    keys = sorted({k for (k, c, v) in t})
    for key in keys:
        cells = []
        for c in configs:
            acc, rej = t[(key, c, "accept")], t[(key, c, "reject")]
            cells.append("%s=%d/%d" % (c, acc, acc + rej))
        print("conf steps=%d equalities=%d congruence=%-5s" % key, "  ".join(cells))
    print()
    explanation_table(rs, tags_of)




def explanation_table(rs, tags_of, configs=("FIX", "FULL")):
    """Tests the hypotheses of explain.py on the goals with exactly one derivation."""
    t = collections.Counter()
    for r in rs:
        a = r["answer"]
        if r["config"] not in configs or a["verdict"] != "derivable" or (a["count"] or 0) >= 2:
            continue
        if r["verdict"] not in ("accept", "reject") or r["class"] == "WHERE-ORDER":
            continue
        t[(tags_of(r) or "(none)", r["config"], r["verdict"])] += 1
    print("## explanation of rejections (explain.py): predicted cause, accepted / rejected")
    for k in sorted({k for (k, c, v) in t}):
        print("%-28s" % k, "  ".join("%s=%d/%d" % (c, t[(k, c, "accept")], t[(k, c, "reject")]) for c in configs))


def markdown(problems, runs, rs, tags_of):
    configs = ("base", "FIX", "FULL")
    kinds = ["conf", "eq-param", "eq-app", "chain", "cond", "assoc", "blanket", "twin"]

    def table(header, lines):
        print("| " + " | ".join(header) + " |")
        print("|" + "|".join("---" if i == 0 else "---:" for i in range(len(header))) + "|")
        for l in lines:
            print("| " + " | ".join(str(x) for x in l) + " |")
        print()

    print("### Problems and queries checked\n")
    nw = collections.Counter((problems[i]["kind"], c) for (i, c) in runs if "world" in runs[(i, c)])
    nq = collections.Counter((r["kind"], r["config"]) for r in rs)
    gen_w = collections.Counter(p["kind"] for p in problems.values())
    gen_q = collections.Counter()
    for p in problems.values():
        gen_q[p["kind"]] += len(p["answers"])
    lines = [[k, gen_w[k], gen_q[k]] + ["%d / %d" % (nw[(k, c)], nq[(k, c)]) for c in configs] for k in kinds]
    lines.append(["total", sum(gen_w.values()), sum(gen_q.values())] +
                 ["%d / %d" % (sum(nw[(k, c)] for k in kinds), sum(nq[(k, c)] for k in kinds)) for c in configs])
    table(["Kind", "Problems", "Queries"] + ["%s: problems / queries" % c for c in configs], lines)

    print("### Reference answers of the generated queries\n")
    t = collections.Counter()
    for p in problems.values():
        for a in p["answers"]:
            v = a["verdict"]
            if v == "derivable":
                v = "derivable, several derivations" if (a["count"] or 0) >= 2 else "derivable, one derivation"
            elif v == "underivable":
                v = "underivable, " + {"invalid": "invalid in the model", "valid": "valid with injectivity",
                                        "vacuous": "scope has no solution"}[a["sem"]]
            t[(v, p["kind"])] += 1
    vs = sorted({v for (v, k) in t})
    table(["Reference answer"] + kinds + ["total"],
          [[v] + [t[(v, k)] for k in kinds] + [sum(t[(v, k)] for k in kinds)] for v in vs])

    print("### Classes by configuration\n")
    t = collections.Counter((r["class"], r["config"]) for r in rs)
    classes = sorted({r["class"] for r in rs}, key=lambda k: (k == "agree", k))
    table(["Class"] + list(configs), [[k] + [t[(k, c)] for c in configs] for k in classes])

    print("### Classes by kind (FIX / FULL)\n")
    t = collections.Counter((r["class"], r["kind"], r["config"]) for r in rs)
    table(["Class"] + kinds, [[k] + ["%d / %d" % (t[(k, kind, "FIX")], t[(k, kind, "FULL")]) for kind in kinds]
                              for k in classes])

    print("### Goals with exactly one derivation: accepted / total, by size of the smallest derivation\n")
    t = collections.Counter()
    for r in rs:
        a = r["answer"]
        if a["verdict"] == "derivable" and not (a["count"] or 0) >= 2 and r["verdict"] in ("accept", "reject") \
                and r["class"] != "WHERE-ORDER":
            key = (min(a["size"], 3), min(a["eq_needed"], 3), "yes" if a["congruence"] else "no")
            t[(key, r["config"], r["verdict"])] += 1
    keys = sorted({k for (k, c, v) in t})
    lines = []
    for key in keys:
        cells = []
        for c in configs:
            acc, rej = t[(key, c, "accept")], t[(key, c, "reject")]
            cells.append("%d / %d" % (acc, acc + rej) if acc + rej else "")
        lines.append(["%s%d" % ("≥" if key[0] == 3 else "", key[0]), "%s%d" % ("≥" if key[1] == 3 else "", key[1]), key[2]] + cells)
    table(["Conformance steps", "Equalities needed", "Congruence needed"] + list(configs), lines)

    print("### Predicted cause of rejection (explain.py) against the verdict, goals with one derivation\n")
    t = collections.Counter()
    for r in rs:
        a = r["answer"]
        if r["config"] == "base" or a["verdict"] != "derivable" or (a["count"] or 0) >= 2:
            continue
        if r["verdict"] not in ("accept", "reject") or r["class"] == "WHERE-ORDER":
            continue
        t[(tags_of(r) or "none (predicted: accepted)", r["config"], r["verdict"])] += 1
    ks = sorted({k for (k, c, v) in t}, key=lambda k: (not k.startswith("none"), k))
    table(["Predicted cause", "FIX accepted", "FIX rejected", "FULL accepted", "FULL rejected"],
          [[k, t[(k, "FIX", "accept")], t[(k, "FIX", "reject")], t[(k, "FULL", "accept")], t[(k, "FULL", "reject")]]
           for k in ks])

    print("### FIX against FULL, and base against FIX\n")
    by = collections.defaultdict(dict)
    for r in rs:
        by[(r["id"], r["q"])][r["config"]] = r
    d = collections.Counter()
    for key, m in by.items():
        if "FIX" in m and "FULL" in m:
            d[("FIX/FULL", m["FIX"]["verdict"], m["FULL"]["verdict"])] += 1
        if "FIX" in m and "base" in m:
            a = m["FIX"]["answer"]
            ref = a["verdict"] if a["verdict"] != "derivable" else \
                ("derivable (several)" if (a["count"] or 0) >= 2 else "derivable (one)")
            d[("base/FIX", ref, m["base"]["verdict"], m["FIX"]["verdict"])] += 1
    table(["FIX verdict", "FULL verdict", "Queries"],
          [[k[1], k[2], n] for k, n in sorted(d.items()) if k[0] == "FIX/FULL"])
    table(["Reference", "base verdict", "FIX verdict", "Queries"],
          [[k[1], k[2], k[3], n] for k, n in sorted(d.items()) if k[0] == "base/FIX"])

    print("### Batch runs confirmed alone\n")
    n = same = 0
    for key, run in runs.items():
        if "confirmed" in run and run["world"]["status"] == "ok":
            n += 1
            same += {str(k): v for k, v in run["confirmed"]["verdicts"].items()} == \
                {str(k): v for k, v in run["world"]["verdicts"].items()}
    print("%d (problem, configuration) pairs with a disagreement in a batch were rerun alone; "
          "%d gave the same verdicts for every query.\n" % (n, same))


if __name__ == "__main__":
    main()
