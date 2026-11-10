"""Judge's runner: runs each program alone under base, FIX and FULL (one compiler process at a
time, through the lock of tc.py) and appends the raw result to judge/runs.jsonl."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import tc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.jsonl")

def main(argv):
    configs = os.environ.get("TCC", "base,FIX,FULL").split(",")
    tb = int(os.environ.get("TB", "30"))
    for f in argv:
        row = {"file": os.path.abspath(f)}
        print("==", f)
        for c in configs:
            r = tc.run(f, c, timeout=tb if c == "base" else 60)
            row[c] = {"status": r["status"], "code": r["code"], "diags": r["diags"]}
            if r["status"] != "ok":
                print("  %-5s %s(%s)" % (c, r["status"], r["code"]))
            elif not r["diags"] and r.get("n", 0) == 0:
                print("  %-5s accept" % c)
            else:
                print("  %-5s reject n=%s" % (c, r.get("n")))
                for l, m in r["diags"]:
                    print("        line %d: %s" % (l, m[:150]))
        with open(OUT, "a") as o:
            o.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    main(sys.argv[1:])
