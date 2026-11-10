"""Hand-written programs about `Self.X` (section 5.4 of spec.md), outside the generated fragment.

For each program, the verdict expected from the specification (rule: `Self.X` is the associated
type of the trait's own witness, and a requirement `T is P` is a different witness) is compared
with the compiler's verdict. Rows go to self-results.jsonl; rerunning skips programs done.
"""
import json
import os

import tc

HERE = os.path.dirname(os.path.abspath(__file__))
EQ = "/home/user/hylo-new/research/report/test-programs/equalities/"
OUT = os.path.join(HERE, "self-results.jsonl")

# (program, expected verdict, reason)
CASES = [
    (EQ + "a01-self-trait.hylo", "accept", "T == Self and Self.X == U are facts"),
    (EQ + "e09-trait-self-assoc.hylo", "accept", "X == Y and Y == U are facts"),
    (EQ + "absleak-0.hylo", "accept", "t.get() instantiates Self's witness with T's requirement"),
    (EQ + "absinst-ok.hylo", "accept", "V.X == Bool is a fact"),
    (EQ + "v-abs-1.hylo", "reject", "T is P is a second witness: T.X is not Self.X"),
    (EQ + "v-abs-2.hylo", "reject", "same"),
    (EQ + "v-abs-3.hylo", "reject", "same"),
    (EQ + "v-abs-4.hylo", "reject", "same, through T == U == Self"),
    (EQ + "v-abs-5.hylo", "reject", "U == T.X, and T.X is not Self.X"),
    (EQ + "v-abs-6.hylo", "reject", "same"),
    (EQ + "v-abs-7.hylo", "reject", "same (equality goal)"),
    (EQ + "v-abs-8.hylo", "reject", "same, in an extension of the trait"),
    (EQ + "v-abs-9.hylo", "reject", "same"),
    (EQ + "abs-trans-0.hylo", "reject", "T.X and U.X are two witnesses"),
    (EQ + "abs-trans-1.hylo", "reject", "same"),
    (EQ + "abs-trans-2.hylo", "reject", "same"),
    (EQ + "abs-trans-3.hylo", "reject", "same"),
    (EQ + "abs-trans-4.hylo", "reject", "same"),
    (EQ + "abs-trans-5.hylo", "reject", "same"),
    (EQ + "absleak-1.hylo", "reject", "t.get() has type T.X, not U.X"),
    (EQ + "absinst-0.hylo", "reject", "V.X == Bool is not known, only W.X == Bool"),
    (EQ + "abs-launder.hylo", "reject", "the body of cast needs T.X == Self.X"),
    (os.path.join(HERE, "hand/self/cast-only.hylo"), "reject", "the body of cast needs T.X == Self.X"),
    (os.path.join(HERE, "hand/self/cast-two.hylo"), "reject", "same, with two other witnesses"),
    (os.path.join(HERE, "hand/self/launder-5-def.hylo"), "reject", "conv<U, X> needs U == Self.X; only U == T.X is known"),
    (os.path.join(HERE, "hand/self/launder-5.hylo"), "reject", "converts W.X to V.X: the conversion that associated-type-inequality.hylo forbids"),
    (os.path.join(HERE, "hand/self/launder-6.hylo"), "reject", "same"),
]


def main():
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l)
            done[r["program"]] = r
    with open(OUT, "a") as out:
        for path, expect, why in CASES:
            name = os.path.basename(path)
            if name not in done:
                row = {"program": name, "expect": expect, "why": why, "runs": {}}
                for c in ("base", "FIX", "FULL"):
                    r = tc.run(path, c, timeout=20 if c == "base" else 60)
                    row["runs"][c] = r["status"] if r["status"] != "ok" else ("accept" if r["n"] == 0 else "reject")
                out.write(json.dumps(row) + "\n")
                out.flush()
                done[name] = row
            row = done[name]
            print("| `%s` | %s | %s | %s | %s | %s |" % (name, row["expect"], row["runs"]["base"],
                  row["runs"]["FIX"], row["runs"]["FULL"], row["why"]))


if __name__ == "__main__":
    main()
