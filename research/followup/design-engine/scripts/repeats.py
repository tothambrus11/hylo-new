#!/usr/bin/env python3
"""Counts repeated subgoals in the resolutions of a program, from the trace of the existing checker.

Usage: repeats.py [--config base] [--label NAME] FILE.hylo...   (appends to experiments/repeats.jsonl)

The trace prints, for every derivation that completes, the goals it proved ("goal G <- try W"),
and for every resolution its query, the number of layers and the number of derivations found. It
does not print the subgoals of branches that fail, so the counts below are for the subgoals on
completed derivations; `summon.subgoals` (all subgoals posed, including those of failing branches)
is recorded next to them.

For each program: the number of resolutions, their distribution by layers, the number of subgoal
instances on completed derivations, how many of them are distinct, and how many are closed (no
unification variable, printed as %name) and posed with no pending premise, which is the case the
existing cache of `summon` could already serve.
"""
import argparse, collections, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R

GOAL = re.compile(r"^\[trace\]   goal (.*) <- try ")
PROVE = re.compile(r"now prove \$\d+: (.*) \[pending: (.*)\]$")
RESOLVE = re.compile(r"^\[trace\] resolve (.*): (\d+) layers, (\d+) done, (\d+) minimal$")


def analyse(lines):
    layers = collections.Counter()
    failing_layers = collections.Counter()
    goals = []          # (goal text, pending-is-empty) for each goal on a completed derivation
    block = None
    blocks = 0
    for l in lines:
        if l.startswith("[trace] DONE"):
            block = {"goals": [], "pending": []}
            blocks += 1
            continue
        m = RESOLVE.match(l)
        if m:
            n, done = int(m.group(2)), int(m.group(3))
            layers[min(n, 10)] += 1
            if done == 0:
                failing_layers[min(n, 10)] += 1
            block = None
            continue
        if block is None:
            continue
        m = PROVE.search(l)
        if m:
            block["pending"].append(m.group(2).strip() == "")
            continue
        m = GOAL.match(l)
        if m:
            # The k-th goal line of a block is the goal announced by the k-th "now prove" line,
            # except for the root goal of a resolution started by `summon`, which comes first.
            k = len(block["goals"])
            block["goals"].append(m.group(1))
            ps = block["pending"]
            empty = ps[len(ps) - 1] if ps else True
            goals.append((m.group(1), empty, len(ps) == 0))
    sub = [g for g in goals if not g[2]]          # goals that are premises (not roots)
    distinct = len(set(g[0] for g in sub))
    closed_empty = [g for g in sub if g[1] and "%" not in g[0]]
    return {
        "resolutions": sum(layers.values()),
        "layers": dict(sorted(layers.items())),
        "failing_by_layers": dict(sorted(failing_layers.items())),
        "completed_derivations": blocks,
        "premise_goals_on_completed": len(sub),
        "distinct_premise_goals": distinct,
        "closed_with_no_pending": len(closed_empty),
        "distinct_closed_with_no_pending": len(set(g[0] for g in closed_empty)),
        "top_repeated": collections.Counter(g[0] for g in sub).most_common(5),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--config", default="base")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--out", default=os.path.join(R.HERE, "experiments", "repeats.jsonl"))
    a = ap.parse_args()
    std = None
    for f in a.files:
        f = os.path.abspath(f)
        r = R.run(f, a.config, trace=True, timeout=a.timeout)
        t = r.pop("_trace", [])
        if os.path.basename(f) == "empty.hylo":
            std = len(t)
            part = t
        else:
            if std is None:
                e = R.run(os.path.join(R.HERE, "experiments", "empty.hylo"), a.config, trace=True)
                std = len(e["_trace"])
            part = t[std:]
        s = analyse(part)
        s.update(program=r["program"], config=a.config, verdict=r["verdict"],
                 subgoals_posed=r["counters"].get("summon.subgoals"),
                 matches=r["counters"].get("summon.matches"),
                 calls=r["counters"].get("summon.calls"),
                 cache_hits=r["counters"].get("summon.cacheHits"))
        with open(a.out, "a") as o:
            o.write(json.dumps(s) + "\n")
        print(json.dumps(s))


if __name__ == "__main__":
    main()
