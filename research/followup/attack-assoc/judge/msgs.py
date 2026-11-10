"""Prints the diagnostics recorded in results.jsonl. usage: msgs.py BINPREFIX CONFIG;CONFIG name-prefix..."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for l in open(os.path.join(HERE, "results.jsonl")):
    r = json.loads(l)
    if r["bin"].startswith(sys.argv[1]) and r["config"] in sys.argv[2].split(";") and any(r["program"].startswith(x) for x in sys.argv[3:]):
        print(r["bin"][:4], r["program"][:34], r["config"], r["verdict"], r["violations"] or r["errors"])
