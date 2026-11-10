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


if __name__ == "__main__":
    main()
