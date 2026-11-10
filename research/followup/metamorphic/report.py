#!/usr/bin/env python3
"""Summarises data/rows-*.jsonl: per relation, the programs and variants checked and the
violations; per kind of variant; and the list of violating (program, variant) pairs with the
verdicts under each configuration. Writes data/summary.md and prints it."""
import collections, json, os, sys
from common import HERE

DATA = os.path.join(HERE, "data")
NAMES = {"r1": "1 order of top-level declarations", "r2": "2 order of requirements and generic parameters",
         "r3": "3 order of members", "r4": "4 tautology or unused parameter", "r5": "5 type alias",
         "r6": "6 renaming", "r7": "7 forms of an equality", "r8": "8 unrelated declaration"}


def rows(config):
    p = os.path.join(DATA, "rows-%s.jsonl" % config)
    seen = {}
    if os.path.exists(p):
        for l in open(p):
            r = json.loads(l)
            seen[(r["file"], r["rel"], r["vid"])] = r
    return seen


def main():
    full, fix, base = rows("FULL"), rows("FIX"), rows("base")
    bl = {}
    p = os.path.join(DATA, "baseline-FULL.jsonl")
    for l in open(p):
        r = json.loads(l); bl[r["file"]] = r
    out = []
    w = out.append
    skipped = collections.Counter(r.get("skip", "").split(":")[0] for r in bl.values() if r.get("skip"))
    w("Programs: %d; skipped: %s; re-printed program differs from the original: %d (verdict), %d (verdict or messages)." % (
        len(bl), dict(skipped),
        sum(1 for r in bl.values() if "reprint_verdict" in r and r["reprint_verdict"] != r["verdict"]),
        sum(1 for r in bl.values() if r.get("reprint_same") is False)))
    w("")
    w("| Relation | Programs with a variant | Variants | Invalid variants | Programs with a verdict change | Variants with a verdict change | Variants with only the messages changed |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for r in sorted(NAMES):
        rs = [x for x in full.values() if x["rel"] == r]
        valid = [x for x in rs if not x.get("invalid")]
        viol = [x for x in valid if x.get("violation")]
        w("| %s | %d | %d | %d | %d | %d | %d |" % (NAMES[r], len({x["file"] for x in valid}), len(valid), len(rs) - len(valid),
                                                    len({x["file"] for x in viol}), len(viol), sum(1 for x in valid if x.get("messages_differ"))))
    w("")
    w("| Relation | Kind of variant | Variants | Verdict changes | Message-only changes |")
    w("|---|---|---:|---:|---:|")
    kinds = collections.defaultdict(lambda: [0, 0, 0])
    for x in full.values():
        if x.get("invalid"): continue
        k = kinds[(x["rel"], x["kind"])]
        k[0] += 1; k[1] += bool(x.get("violation")); k[2] += bool(x.get("messages_differ"))
    for (r, k), v in sorted(kinds.items()):
        w("| %s | %s | %d | %d | %d |" % (r, k, v[0], v[1], v[2]))
    w("")
    w("Violating variants under FULL, with the verdicts original -> variant under each configuration:")
    w("")
    w("| Relation | Program | Variant | FULL | FIX | base |")
    w("|---|---|---|---|---|---|")
    def vv(tab, key):
        x = tab.get(key)
        return "not run" if x is None else "%s -> %s" % (x["base_verdict"], x["verdict"])
    for key in sorted(k for k, x in full.items() if x.get("violation")):
        f, r, vid = key
        w("| %s | %s | %s | %s | %s | %s |" % (r, f.replace("research/report/test-programs/", ""), vid, vv(full, key), vv(fix, key), vv(base, key)))
    w("")
    for config, tab in (("FIX", fix), ("base", base)):
        if not tab: continue
        w("Under %s (only the programs with a FULL violation were run): %d variants, %d verdict changes in %d programs." % (
            config, len(tab), sum(1 for x in tab.values() if x.get("violation")), len({x["file"] for x in tab.values() if x.get("violation")})))
    text = "\n".join(out) + "\n"
    open(os.path.join(DATA, "summary.md"), "w").write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
