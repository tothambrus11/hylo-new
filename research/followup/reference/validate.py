"""Checks the reference and the printer on the hand-written cases (handcases.py).

For every case: the reference answer of each query is compared with the verdict expected by
hand; the printed program is run under base, FIX and FULL; and, when the case transcribes an
existing program, the compiler's verdict on the original is compared with its verdict on the
printed program (same configuration). Rows go to hand-results.jsonl; rerunning skips cases
already done (delete the file to start again).
"""
import hashlib
import json
import os
import sys

import dsl
import harness
import reference
import tc
from handcases import CASES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hand-results.jsonl")


def expected_matches(expect, a):
    v, n = a["verdict"], a["count"]
    if expect == "D":
        return v == "derivable" and (n is None or n == 1)
    if expect == "D2":
        return v == "derivable" and n is not None and n >= 2
    if expect == "U":
        return v == "underivable"
    if expect == "I":
        return v == "illformed-goal"
    if expect == "?":
        return v == "unspecified"
    return False


def main():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l)
            done[(r["case"], r["hash"])] = r
    bad = 0
    with open(OUT, "a") as out:
        for name, original, text in CASES:
            h = hashlib.sha1(text.encode()).hexdigest()[:12]
            if (name, h) in done:
                row = done[(name, h)]
            else:
                world, expect = dsl.parse(text)
                answers = []
                for q in world["queries"]:
                    a = reference.answer(world, q)
                    a.pop("goal", None)
                    answers.append(a)
                path = os.path.join(HERE, "hand", name.replace(".hylo", "") + ".hylo")
                runs = harness.run_world(world, path)
                row = {"case": name, "hash": h, "expect": expect, "reference": answers,
                       "runs": runs, "original": None}
                if original:
                    row["original"] = {}
                    for c in ("base", "FIX", "FULL"):
                        r = tc.run(original, c, timeout=harness.TIMEOUT[c])
                        row["original"][c] = r["status"] if r["status"] != "ok" else \
                            ("accept" if r["n"] == 0 else "reject")
                out.write(json.dumps(row) + "\n")
                out.flush()
            # Report.
            for i, a in enumerate(row["reference"]):
                ok = expected_matches(row["expect"][i], a)
                cells = []
                for c in ("base", "FIX", "FULL"):
                    r = row["runs"][c]
                    v = r["verdicts"].get(str(i), r["verdicts"].get(i)) if r["status"] == "ok" else r["status"]
                    k = harness.classify(a, v) if r["status"] == "ok" else r["status"].upper()
                    cells.append("%s=%s%s" % (c, v, "" if k == "agree" else "[" + k + "]"))
                if not ok:
                    bad += 1
                print("%-34s q%-2d expect=%-2s ref=%-12s n=%s size=%s eq=%s sem=%-7s %s  %s" % (
                    row["case"], i, row["expect"][i], a["verdict"], a["count"], a["size"],
                    a["eq_needed"], a["sem"], "ok " if ok else "REFERENCE-MISMATCH", " ".join(cells)))
            if row["original"]:
                for c in ("base", "FIX", "FULL"):
                    r = row["runs"][c]
                    printed = r["status"] if r["status"] != "ok" else \
                        ("accept" if all(v == "accept" for v in r["verdicts"].values()) else "reject")
                    if printed != row["original"][c]:
                        print("    PRINTER-MISMATCH %s: original=%s printed=%s" % (c, row["original"][c], printed))
    print("reference mismatches with the hand expectations:", bad)


if __name__ == "__main__":
    main()
