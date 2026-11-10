#!/usr/bin/env python3
"""Metamorphic testing of the Hylo type checker.

usage:
  metamorphic.py baseline [--config C]             original and re-printed verdict of every program
  metamorphic.py run REL... [--config C] [--only SUBSTR] [--files LIST]
                                                   REL is r1..r8 or `all`
  metamorphic.py attribute                         base and FIX on every program with a FULL violation
  metamorphic.py show FILE REL [VID]               prints the variants of a program

Rows are appended to data/rows-<config>.jsonl (one row per variant) and the program-level
summaries to data/done-<config>.jsonl; a (program, relation, configuration) that is already in
the latter is skipped, so every command can be interrupted and restarted. Type-checker results
are cached by the hash of the program text in data/cache.jsonl."""
import importlib, json, os, random, sys, zlib
from common import *

RELATIONS = {"r1": "r1_permute_decls", "r2": "r2_permute_requirements", "r3": "r3_permute_members",
             "r4": "r4_tautology", "r5": "r5_alias", "r6": "r6_rename", "r7": "r7_equality_forms",
             "r8": "r8_unrelated"}
DATA = os.path.join(HERE, "data")
# Number of variants checked per program. Every relation lists its variants in a fixed priority
# order, so a larger budget (MM_BUDGET="r1=23,r4=12") only adds variants to those already checked.
BUDGET = {"r1": 5, "r2": 8, "r3": 6, "r4": 6, "r5": 8, "r6": 3, "r7": 6, "r8": 5}
for kv in filter(None, os.environ.get("MM_BUDGET", "").split(",")):
    BUDGET[kv.split("=")[0]] = int(kv.split("=")[1])


def budget(r, f):
    return max(BUDGET[r], 23) if r == "r1" and "declaration-order" in f else BUDGET[r]


def variants_of(path, r, src=None):
    """The variants of relation `r` for the program at `path`, in priority order. The random
    choices are seeded by the program text, so identical programs get identical variants."""
    src = open(path).read() if src is None else src
    F = File(src); F.path = rel(os.path.abspath(path))
    rng = random.Random(zlib.crc32((src + r).encode()))
    return F, module(r).variants(F, rng)


def module(r):
    return importlib.import_module("relations." + RELATIONS[r])


def load(path):
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def baselines(config):
    return {r["file"]: r for r in load(os.path.join(DATA, "baseline-%s.jsonl" % config))}


def cmd_baseline(config):
    out = os.path.join(DATA, "baseline-%s.jsonl" % config)
    done = baselines(config)
    with open(out, "a") as o:
        for grp, path in corpus():
            f = rel(path)
            if f in done: continue
            size = os.path.getsize(path)
            row = {"file": f, "group": grp, "config": config, "bytes": size}
            if size > MAX_BYTES:
                row["skip"] = "large"
            else:
                src = open(path).read()
                try:
                    F = File(src)
                except Exception as e:
                    F = None; row["skip"] = "unparsed: %s" % e
                a = check(src, config)
                row.update(verdict=a["verdict"], errors=a["errors"], syntax=a["syntax"], ms=a["ms"])
                if F is not None:
                    b = check(F.render(), config)
                    row.update(decls=len(F.pieces), reprint_verdict=b["verdict"],
                               reprint_same=(b["verdict"] == a["verdict"] and b["errors"] == a["errors"]),
                               tokens_same=[t.text for t in lex(F.render())] == [t.text for t in F.toks if t.text != ";" or True])
                    if a["syntax"]: row["skip"] = "syntax error in the original"
                    elif a["ms"] > 5000: row["skip"] = "slow"
            o.write(json.dumps(row) + "\n"); o.flush()


def run_one(path, r, config, base, o_rows):
    """Checks every variant of relation `r` on one program. Returns the summary row."""
    src = open(path).read()
    F, variants = variants_of(path, r, src)
    variants = variants[:budget(r, rel(path))]
    a = check(src, config)
    n = {"variants": 0, "verdict_changes": 0, "message_changes": 0, "invalid": 0}
    seen = set()
    for v in variants:
        text = v.render(F)
        if text in seen: continue
        seen.add(text)
        b = check(text, config)
        row = {"file": rel(path), "rel": r, "vid": v.vid, "kind": v.kind, "desc": v.desc, "config": config,
               "verdict": b["verdict"], "sha": b["sha"], "base_verdict": a["verdict"]}
        if b["syntax"] and not a["syntax"]:
            row["invalid"] = True; n["invalid"] += 1          # the transformation broke the syntax
        elif b["verdict"] != a["verdict"]:
            row["violation"] = True; row["errors"] = b["errors"]; row["base_errors"] = a["errors"]
            n["verdict_changes"] += 1
        elif not same_messages(a["errors"], b["errors"], v.rename):
            row["messages_differ"] = True; row["errors"] = b["errors"]; row["base_errors"] = a["errors"]
            n["message_changes"] += 1
        n["variants"] += 1
        o_rows.write(json.dumps(row) + "\n")
    o_rows.flush()
    return dict(n, file=rel(path), rel=r, config=config, base_verdict=a["verdict"], budget=budget(r, rel(path)))


def cmd_run(rels, config, only=None, files=None):
    base = baselines("FULL")
    done = {}
    for row in load(os.path.join(DATA, "done-%s.jsonl" % config)):
        done[(row["file"], row["rel"])] = max(done.get((row["file"], row["rel"]), 0), row.get("budget", 0))
    with open(os.path.join(DATA, "rows-%s.jsonl" % config), "a") as o_rows, \
         open(os.path.join(DATA, "done-%s.jsonl" % config), "a") as o_done:
        for r in rels:
            for grp, path in corpus():
                f = rel(path)
                if only and only not in f: continue
                if files is not None and f not in files: continue
                if done.get((f, r), -1) >= budget(r, f) or f not in base or base[f].get("skip"): continue
                try:
                    row = run_one(path, r, config, base, o_rows)
                except Exception as e:
                    row = {"file": f, "rel": r, "config": config, "exception": repr(e)}
                row["group"] = grp
                o_done.write(json.dumps(row) + "\n"); o_done.flush()


def cmd_attribute(only_violating=("r2", "r4")):
    """Runs FIX and base on the programs that show a violation under FULL: every variant that was
    checked under FULL, except for the relations in `only_violating` (many programs, one cause),
    where only the violating variants are run."""
    full = {}
    for row in load(os.path.join(DATA, "rows-FULL.jsonl")):
        full[(row["file"], row["rel"], row["vid"])] = row
    bad = {(f, r) for (f, r, _), row in full.items() if row.get("violation")}
    todo = {}
    for (f, r, vid), row in full.items():
        if (f, r) in bad and (row.get("violation") or r not in only_violating):
            todo.setdefault((f, r), []).append(vid)
    for config in ("FIX", "base"):
        have = {(x["file"], x["rel"], x["vid"]) for x in load(os.path.join(DATA, "rows-%s.jsonl" % config))}
        with open(os.path.join(DATA, "rows-%s.jsonl" % config), "a") as o:
            for (f, r), vids in sorted(todo.items()):
                if all((f, r, v) in have for v in vids): continue
                path = os.path.join(ROOT, f)
                src = open(path).read()
                F, vs = variants_of(path, r, src)
                a = check(src, config)
                for v in vs:
                    if v.vid not in vids or (f, r, v.vid) in have: continue
                    b = check(v.render(F), config)
                    row = {"file": f, "rel": r, "vid": v.vid, "kind": v.kind, "desc": v.desc, "config": config,
                           "verdict": b["verdict"], "sha": b["sha"], "base_verdict": a["verdict"],
                           "errors": b["errors"], "base_errors": a["errors"]}
                    if b["verdict"] != a["verdict"]: row["violation"] = True
                    elif not same_messages(a["errors"], b["errors"], v.rename): row["messages_differ"] = True
                    o.write(json.dumps(row) + "\n"); o.flush()


def cmd_show(path, r, vid=None):
    F, vs = variants_of(path, r)
    for v in vs:
        if vid is None: print(v.vid, "--", v.desc)
        elif v.vid == vid: sys.stdout.write(v.render(F))


def main():
    args = sys.argv[1:]
    opt = {"--config": "FULL", "--only": None, "--files": None}
    for k in list(opt):
        if k in args:
            i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    os.makedirs(DATA, exist_ok=True)
    cmd = args.pop(0)
    if cmd == "baseline": cmd_baseline(opt["--config"])
    elif cmd == "run":
        rels = sorted(RELATIONS) if args == ["all"] else args
        files = set(open(opt["--files"]).read().split()) if opt["--files"] else None
        cmd_run(rels, opt["--config"], opt["--only"], files)
    elif cmd == "attribute": cmd_attribute()
    elif cmd == "show": cmd_show(*args)
    else: sys.exit(__doc__)


if __name__ == "__main__":
    main()
