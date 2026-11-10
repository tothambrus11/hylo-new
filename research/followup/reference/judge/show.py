"""Prints the Hylo text of given queries: python3 judge/show.py ID:Q ..."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import to_hylo, reference
P = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "problems.jsonl")):
    p = json.loads(l); P[p["id"]] = p
for a in sys.argv[1:]:
    pid, q = a.split(":"); q = int(q)
    w = reference.load_world(P[pid]["world"])
    print("//", pid, "q%d" % q, {k: v for k, v in P[pid]["answers"][q].items() if k in ("verdict", "count", "sem", "ordered", "twin")})
    for l in to_hylo.declarations(w):
        if l.startswith("given"): print(l)
    print(to_hylo.query_line(w, q, w["queries"][q]))
