#!/usr/bin/env python3
"""Reduces a violation of a metamorphic relation.

usage: reduce.py FILE REL VID [--config C] [--out DIR]

Step 1 deletes top-level declarations from the original and from the variant together, as long
as both keep their verdicts (and the rejected one keeps one of its error messages).
Step 2 works on the reduced original: it deletes one member of a type body, one requirement of a
where clause or one statement line of a function body at a time, regenerates the variants of the
same kind, and keeps the deletion if one of them still shows the same pair of verdicts.
The result (a.hylo, b.hylo and info.json with the verdicts under base, FIX and FULL) is written
to DIR (default: violations/<REL>/<program>--<variant>)."""
import json, os, random, re, sys, zlib
from common import *
from metamorphic import module, variants_of, RELATIONS


def find_variant(path, r, vid):
    F, vs = variants_of(path, r)
    for v in vs:
        if v.vid == vid: return F, v
    return F, None


def holds(a_text, b_text, config, va, vb, ea, eb):
    a = check(a_text, config)
    if a["verdict"] != va or a["syntax"]: return False
    b = check(b_text, config)
    if b["verdict"] != vb or b["syntax"]: return False
    for res, es in ((a, ea), (b, eb)):
        want = {e for e in es if e.startswith("error")}
        if want and not (want & set(res["errors"])): return False
    return True


def step1(F, v, config, va, vb, ea, eb):
    keep = set(range(len(F.pieces)))
    changed = True
    while changed:
        changed = False
        for i in sorted(keep, reverse=True):
            k = keep - {i}
            if not k: continue
            if holds(IDENTITY.render(F, k), v.render(F, k), config, va, vb, ea, eb):
                keep = k; changed = True
    return keep


def inner_deletions(F):
    """Texts obtained from F by one small deletion inside a declaration."""
    out = []
    def cut(a, b):
        out.append(File(F.src[:a] + F.src[b:]).render())
    for d in F.all_decls():
        if d.members:
            prev = F.toks[d.body[0]].end
            for m in d.members:
                e = F.toks[m.t1 - 1].end
                cut(prev, e); prev = e
        c = d.clause
        if c is not None and c.reqs:
            if len(c.reqs) == 1:
                cut(F.toks[c.where].start, F.toks[c.gt].start)
            else:
                for i, (a, b) in enumerate(c.reqs):
                    if i == 0: cut(F.toks[a].start, F.toks[c.reqs[1][0]].start)
                    else: cut(F.toks[c.reqs[i - 1][1] - 1].end, F.toks[b - 1].end)
        if d.kind in ("fun", "init", "subscript") and d.body and d.members is None:
            lb, rb = d.body
            inner = F.src[F.toks[lb].end:F.toks[rb].start]
            if inner.strip():
                lines = inner.split("\n")
                if len([l for l in lines if l.strip()]) > 1:
                    for i, l in enumerate(lines):
                        if l.strip():
                            rest = "\n".join(lines[:i] + lines[i + 1:])
                            out.append(File(F.src[:F.toks[lb].end] + rest + F.src[F.toks[rb].start:]).render())
                else:
                    cut(F.toks[lb].end, F.toks[rb].start)
    return out


def step2(a_text, r, kind, config, va, vb, ea, eb, path):
    """Returns (a_text, b_text, variant description) after inner deletions."""
    def witness(text):
        F = File(text); F.path = rel(os.path.abspath(path))
        if check(text, config)["verdict"] != va: return None
        rng = random.Random(1)
        for v in module(r).variants(F, rng):
            if v.kind != kind: continue
            b = v.render(F)
            if holds(text, b, config, va, vb, ea, eb): return (b, v.desc)
        return None
    best = witness(a_text)
    if best is None: return None
    changed = True
    while changed:
        changed = False
        for cand in inner_deletions(File(a_text)):
            if cand == a_text: continue
            w = witness(cand)
            if w is not None:
                a_text, best, changed = cand, w, True
                break
    return a_text, best[0], best[1]


def reduce(path, r, vid, config="FULL", out=None, inner=True):
    src = open(path).read()
    F, v = find_variant(path, r, vid)
    if v is None: sys.exit("no such variant")
    a, b = check(src, config), check(v.render(F), config)
    va, vb, ea, eb = a["verdict"], b["verdict"], a["errors"], b["errors"]
    if va == vb: sys.exit("not a violation: %s / %s" % (va, vb))
    # Renderings are compared, so start from the re-printed original.
    if not holds(IDENTITY.render(F), v.render(F), config, va, vb, ea, eb):
        sys.exit("the re-printed original does not reproduce the violation")
    keep = step1(F, v, config, va, vb, ea, eb)
    a_text, b_text, desc = IDENTITY.render(F, keep), v.render(F, keep), v.desc
    if inner:
        s2 = step2(a_text, r, v.kind, config, va, vb, ea, eb, path)
        if s2 is not None: a_text, b_text, desc = s2
    name = os.path.basename(path)[:-5] + "--" + re.sub(r"[^A-Za-z0-9]+", "-", vid).strip("-")
    out = out or os.path.join(HERE, "violations", r, name)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "a.hylo"), "w").write(a_text)
    open(os.path.join(out, "b.hylo"), "w").write(b_text)
    info = {"file": rel(os.path.abspath(path)), "rel": r, "vid": vid, "kind": v.kind, "desc": desc, "found_in": config,
            "original": {"verdict": va, "errors": ea}, "variant": {"verdict": vb, "errors": eb}, "reduced": {}}
    for c in ("base", "FIX", "FULL"):
        ra, rb = check(a_text, c), check(b_text, c)
        info["reduced"][c] = {"a": ra["verdict"], "b": rb["verdict"], "a_errors": ra["errors"], "b_errors": rb["errors"]}
    json.dump(info, open(os.path.join(out, "info.json"), "w"), indent=1)
    return out, info


if __name__ == "__main__":
    args = sys.argv[1:]
    opt = {"--config": "FULL", "--out": None}
    for k in list(opt):
        if k in args:
            i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    out, info = reduce(args[0], args[1], args[2], opt["--config"], opt["--out"])
    print(out)
    print(open(os.path.join(out, "a.hylo")).read()); print("---- variant:", info["desc"])
    print(open(os.path.join(out, "b.hylo")).read())
    print(json.dumps(info["reduced"], indent=1))
