"""Judge's independent tabulation of results.jsonl against the reference answers of
problems.jsonl. It does not import report.py or harness.py."""
import json, collections, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = {}
for l in open(os.path.join(HERE, "..", "problems.jsonl")):
    p = json.loads(l); P[p["id"]] = p
rows = collections.defaultdict(list)
keys = collections.Counter()
for l in open(os.path.join(HERE, "..", "results.jsonl")):
    r = json.loads(l)
    keys[tuple(sorted(r.keys()))] += 1
    rows[(r["id"], r["config"])].append(r)
print("row shapes:", dict(keys))
nq = sum(len(p["answers"]) for p in P.values())
print("problems", len(P), "queries", nq)

# batch vs alone
for c in ("base", "FIX", "FULL"):
    ids = [k for k in rows if k[1] == c]
    nb = sum(1 for k in ids for r in rows[k] if r.get("batch") and r["isolated"] is None)
    na = sum(1 for k in ids for r in rows[k] if not r.get("batch") and r["isolated"] is None)
    ni = sum(1 for k in ids for r in rows[k] if r["isolated"] is not None)
    both = [k for k in ids if any(r.get("batch") for r in rows[k]) and any((not r.get("batch")) and r["isolated"] is None for r in rows[k])]
    diff = 0
    for k in both:
        b = [r for r in rows[k] if r.get("batch")][-1]
        a = [r for r in rows[k] if not r.get("batch") and r["isolated"] is None][-1]
        if a["status"] != "ok" or a["verdicts"] != b["verdicts"]:
            diff += 1
    print(c, "problems", len(ids), "batch rows", nb, "alone rows", na, "isolated-query rows", ni,
          "problems with both", len(both), "of which verdicts differ", diff)

def verdict(pid, c, i):
    rs = rows.get((pid, c))
    if not rs: return None, ""
    whole = [r for r in rs if r["isolated"] is None]
    alone = [r for r in whole if not r.get("batch")]
    w = (alone or whole or [None])[-1]
    if w is not None and w["status"] == "ok":
        return w["verdicts"][str(i)], w["messages"].get(str(i), "")
    iso = [r for r in rs if r["isolated"] == i]
    if iso:
        r = iso[-1]
        if r["status"] == "ok":
            return r["verdicts"][str(i)], r["messages"].get(str(i), "")
        return r["status"], ""
    return (w["status"] if w else None), ""

def refclass(a):
    v = a["verdict"]
    if v == "derivable":
        return "deriv-1" if a["count"] in (None, 1) else "deriv-n"
    if v == "underivable":
        return "under-" + a["sem"]
    return v

T = collections.Counter(); K = collections.Counter(); ran = collections.Counter()
ref = collections.Counter()
samefull = collections.Counter()
budget = collections.Counter()
for pid, p in P.items():
    for i, a in enumerate(p["answers"]):
        rc = refclass(a)
        ref[(p["kind"], rc)] += 1
        vs = {}
        for c in ("base", "FIX", "FULL"):
            v, m = verdict(pid, c, i)
            if v is None: continue
            vs[c] = v
            ran[(c, p["kind"])] += 1
            T[(c, rc, v)] += 1
            K[(c, p["kind"], rc, v)] += 1
            if "too complex" in m: budget[(c, rc, p["kind"])] += 1
            if "no static member" in m: budget[(c, rc, "NOSTATIC", a.get("ordered"))] += 1
        if "FIX" in vs and "FULL" in vs:
            samefull[(vs["FIX"], vs["FULL"])] += 1
print("\nreference answers by kind:")
for k in sorted(ref): print("  ", k, ref[k])
print("\nqueries run by config and kind:")
for k in sorted(ran): print("  ", k, ran[k])
print("\nconfig, reference class, verdict:")
for k in sorted(T): print("  ", k, T[k])
print("\nFIX vs FULL:", dict(samefull))
print("\nmessages:")
for k in sorted(budget, key=str): print("  ", k, budget[k])
if "-k" in sys.argv:
    print("\nby kind:")
    for k in sorted(K): print("  ", k, K[k])
