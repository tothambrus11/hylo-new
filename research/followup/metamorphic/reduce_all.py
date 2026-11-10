#!/usr/bin/env python3
"""Groups the violations found under FULL by signature (relation, kind of variant, pair of
verdicts, error messages with the quoted names blanked), reduces the smallest programs of each
group (at most MM_PER_GROUP, default 1), and writes violations/index.jsonl, which lists every
group with its members and with every reduction that exists for one of its members.
Restartable: a reduction whose directory already holds info.json is not repeated. With
MM_PER_GROUP=0 nothing is reduced and the index is only rebuilt.

usage: reduce_all.py [REL...]"""
import json, os, re, sys
from common import HERE, ROOT
from reduce import reduce

PER_GROUP = int(os.environ.get("MM_PER_GROUP", "1"))


PRIMARY = ["implicit resolution is too complex", "has no static member", "not enough context",
           "refers to itself", "ambiguous"]


def signature(r):
    """Groups violations: the errors that the rejected side has and the other side has not, with
    quoted names blanked; when one of the PRIMARY messages is among them, it alone (the others
    are its consequences)."""
    bad, good = (r["errors"], r["base_errors"]) if r["verdict"] != "accept" else (r["base_errors"], r["errors"])
    blank = lambda e: re.sub(r"'[^']*'", "'_'", e)
    errs = sorted({blank(e) for e in bad if e.startswith("error")} - {blank(e) for e in good})
    for p in PRIMARY:
        if any(p in e for e in errs): errs = [e for e in errs if p in e]; break
    return (r["rel"], r["kind"], r["base_verdict"], r["verdict"], tuple(errs))


def main():
    rels = sys.argv[1:]
    groups, seen = {}, set()
    for l in open(os.path.join(HERE, "data", "rows-FULL.jsonl")):
        r = json.loads(l)
        if not r.get("violation") or r.get("invalid") or (rels and r["rel"] not in rels): continue
        if (r["file"], r["rel"], r["vid"]) in seen: continue
        seen.add((r["file"], r["rel"], r["vid"]))
        groups.setdefault(signature(r), []).append(r)
    p = os.path.join(HERE, "violations", "index.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    index = [x for x in map(json.loads, open(p)) if rels and x["rel"] not in rels] if os.path.exists(p) else []
    for sig, rs in sorted(groups.items()):
        rs.sort(key=lambda r: (os.path.getsize(os.path.join(ROOT, r["file"])), r["file"], r["vid"]))
        entry = {"rel": sig[0], "kind": sig[1], "original": sig[2], "variant": sig[3], "errors": list(sig[4]),
                 "members": [[r["file"], r["vid"]] for r in rs], "programs": len({r["file"] for r in rs}), "reduced": []}
        done_files, new = set(), 0
        for r in rs:
            path = os.path.join(ROOT, r["file"])
            name = os.path.basename(path)[:-5] + "--" + re.sub(r"[^A-Za-z0-9]+", "-", r["vid"]).strip("-")
            out = os.path.join(HERE, "violations", r["rel"], name)
            if not os.path.exists(os.path.join(out, "info.json")):
                if new >= PER_GROUP or entry["reduced"] or r["file"] in done_files: continue
                done_files.add(r["file"]); new += 1
                try:
                    # Relation 1: only whole declarations are deleted (the inner step would
                    # try every permutation again for each candidate deletion).
                    reduce(path, r["rel"], r["vid"], "FULL", out, inner=r["rel"] != "r1")
                except SystemExit as e:
                    print("skipped", r["file"], r["vid"], e, flush=True); continue
            info = json.load(open(os.path.join(out, "info.json")))
            info["dir"] = os.path.relpath(out, HERE)
            entry["reduced"].append(info)
            print(info["dir"], {c: "%s/%s" % (v["a"], v["b"]) for c, v in info["reduced"].items()}, "group of", len(rs), flush=True)
        index.append(entry)
    with open(p, "w") as o:
        for x in index: o.write(json.dumps(x) + "\n")


if __name__ == "__main__":
    main()
