"""Judge: rerun alone a random sample of problems that only have a batch run, and compare."""
import json, os, random, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import harness, reference
P = {}
for l in open(os.path.join(HERE, "..", "problems.jsonl")):
    p = json.loads(l); P[p["id"]] = p
rows = collections.defaultdict(list)
for l in open(os.path.join(HERE, "..", "results.jsonl")):
    r = json.loads(l); rows[(r["id"], r["config"])].append(r)
rng = random.Random(20261110)
out = open(os.path.join(HERE, "recheck.jsonl"), "a")
same = diff = 0
for c, n in (("FIX", 14), ("FULL", 10)):
    only = sorted(k[0] for k, rs in rows.items() if k[1] == c and all(r.get("batch") for r in rs))
    # half of the sample from problems with a rejected derivable goal in the batch run
    def has_reject(pid):
        b = rows[(pid, c)][-1]
        return any(P[pid]["answers"][int(i)]["verdict"] == "derivable" and v == "reject" for i, v in b["verdicts"].items())
    rej = [p for p in only if has_reject(p)]
    sample = rng.sample(rej, n // 2) + rng.sample(only, n - n // 2)
    for pid in sample:
        w = reference.load_world(P[pid]["world"])
        r = harness.run_world(w, os.path.join(HERE, "p", "recheck.hylo"), configs=(c,))[c]
        b = rows[(pid, c)][-1]
        ok = r["status"] == "ok" and {str(k): v for k, v in r["verdicts"].items()} == b["verdicts"]
        same += ok; diff += not ok
        out.write(json.dumps({"id": pid, "config": c, "alone": r["verdicts"], "batch": b["verdicts"], "same": ok, "status": r["status"]}) + "\n")
        print(pid, c, "same" if ok else "DIFFERENT", r["status"])
print("same", same, "different", diff)
