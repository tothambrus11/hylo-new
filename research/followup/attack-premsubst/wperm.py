"""Permutes the requirements of where clauses and compares the verdicts under NEW.

usage: wperm.py [N]
Each case is a program template with one where clause replaced by `{W}` and a list of requirements;
a requirement may only come after the ones it mentions (given as indices). Every such order is tried
(or a seeded sample of N, default 24). Programs go to wperm/, results to wperm.jsonl (restartable)."""
import hashlib, itertools, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run, tcrun
OUT = os.path.join(HERE, "wperm.jsonl")
PRE = """trait P { type X }
trait P2 { type Y }
trait Q {}
trait R {}
trait S0 {}
struct A {}
struct B {}
struct C {}
struct D {}
struct Pair<X, Y> {}
struct W<X> {}
given A is P { type X = B }
given C is P2 { type Y = D }
given B is Q {}
given D is R {}
given Pair<B, D> is S0 {}
given <V where V is Q> => W<V> is R {}
"""
REQS = [("T is P", []), ("U is P2", []), ("T.X is Q", [0]), ("U.Y is R", [1]), ("Pair<T.X, U.Y> is S0", [0, 1])]
CALLER = [("V is P", []), ("Z is P2", []), ("V.X is Q", [0]), ("Z.Y is R", [1]), ("Pair<V.X, Z.Y> is S0", [0, 1])]
CASES = {
  # the callee's clause is permuted; concrete and generic callers
  "callee": (PRE + "fun f<T, U where {W}>() {}\nfun g<V, Z where V is P, Z is P2, V.X is Q, Z.Y is R, Pair<V.X, Z.Y> is S0>() { f<V, Z>() }\npublic fun main() { f<A, C>() }\n", REQS),
  # the caller's clause is permuted
  "caller": (PRE + "fun f<T, U where T is P, U is P2, T.X is Q, U.Y is R, Pair<T.X, U.Y> is S0>() {}\nfun g<V, Z where {W}>() { f<V, Z>() }\n", CALLER),
  # a clause with an equality between two projections and a requirement provable from a hypothesis
  "mixed": (PRE + "fun f<T, U where {W}>() {}\nfun g<V, Z where V is P, Z is P, V.X == Z.X, V.X is Q>() { f<V, Z>() }\npublic fun main() { f<A, A>() }\n",
            [("T is P", []), ("U is P", []), ("T.X == U.X", [0, 1]), ("T.X is Q", [0]), ("W<U.X> is R", [1])]),
}
def orders(reqs):
    for p in itertools.permutations(range(len(reqs))):
        pos = {r: i for i, r in enumerate(p)}
        if all(pos[d] < pos[r] for r in range(len(reqs)) for d in reqs[r][1]): yield p
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    done = {}
    if os.path.exists(OUT):
        for l in open(OUT): r = json.loads(l); done[r["file"]] = r
    os.makedirs(os.path.join(HERE, "wperm"), exist_ok=True)
    tcrun.CONFIGS["_"] = run.flags("NEW")
    for name, (template, reqs) in CASES.items():
        os_ = list(orders(reqs)); random.Random(1).shuffle(os_); os_ = sorted(os_[:n])
        verdicts = {}
        for p in os_:
            file = f"wperm/{name}-{''.join(map(str, p))}.hylo"
            if file not in done:
                open(os.path.join(HERE, file), "w").write(template.replace("{W}", ", ".join(reqs[i][0] for i in p)))
                x = tcrun.run(run.BIN, "_", os.path.join(HERE, file), 60)
                done[file] = {"file": file, "verdict": x["verdict"], "errors": len(x["errors"]), "first": (x["errors"] or [""])[0],
                              "stuck": x["counters"].get("premsubst.stuck", 0)}
                with open(OUT, "a") as o: o.write(json.dumps(done[file]) + "\n")
            r = done[file]
            verdicts.setdefault((r["verdict"], r["errors"]), []).append(file)
        print(f"{name:8} {len(os_):3} of {len(list(orders(reqs)))} orders  " + "  ".join(f"{v}/{e} errors: {len(fs)}" for (v, e), fs in verdicts.items())
              + ("   <-- ORDER " + " ".join(min(verdicts.items(), key=lambda kv: len(kv[1]))[1][:2]) if len({v for v, _ in verdicts}) > 1 else ""))
if __name__ == "__main__":
    main()
