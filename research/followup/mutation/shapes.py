"""Supplementary probe: one missing conformance in library-shaped generic code.

The mutation sample contains little code with conditional conformances over a trait hierarchy, which
is what a generic library looks like. This script generates such programs at several sizes and
measures the valid program and the same program with one conformance deleted.

Shape `opt`:  traits T0 <- T1 <- ... <- Th (each refines the previous one), a wrapper Opt<T> that
              conforms to each Ti when T does, a leaf type X conforming to Th, and one use that needs
              T0 for Opt<...Opt<X>> nested n times.  Error: the conformance of X is deleted.
Shape `list`: the same with a two-parameter Cons<T, U> conforming to Ti when both T and U do, used
              on a list of n elements whose last element lacks the conformance in the erroneous variant.

Usage: python3 shapes.py   (writes shapes/*.hylo, appends to shapes.jsonl; restartable)
"""
import json, os, sys
import tc

OUT = os.path.join(tc.HERE, "shapes.jsonl")
DIR = os.path.join(tc.HERE, "shapes")

def program(shape, h, n, valid):
    L = ["trait T0 {}"]
    for i in range(1, h + 1): L.append(f"trait T{i} refines T{i-1} {{}}")
    L.append("struct X {}")
    L.append("struct Y {}")
    L.append(f"given X is T{h} {{}}")
    if valid: L.append(f"given Y is T{h} {{}}")
    if shape == "opt":
        L.append("struct Opt<T> {}")
        for i in range(h + 1): L.append(f"given <T is T{i}> => Opt<T> is T{i} {{}}")
        t = "Y"
        for _ in range(n): t = f"Opt<{t}>"
    else:
        L.append("struct Cons<T, U> {}")
        for i in range(h + 1): L.append(f"given <T is T{i}, U is T{i}> => Cons<T, U> is T{i} {{}}")
        t = "Y"
        for _ in range(n): t = f"Cons<X, {t}>"
    L.append("fun need<T is T0>() {}")
    L.append(f"public fun main() {{ need<{t}>() }}")
    return "\n".join(L) + "\n"

def main():
    os.makedirs(DIR, exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln); done.add((r["program"], r["config"], r["depth"]))
    cases = [(s, h, n) for s in ("opt", "list") for h in (1, 2, 4) for n in (2, 4, 8)]
    with open(OUT, "a") as out:
        for (s, h, n) in cases:
            for valid in (True, False):
                name = f"{s}-h{h}-n{n}-{'valid' if valid else 'error'}.hylo"
                path = os.path.join(DIR, name)
                open(path, "w").write(program(s, h, n, valid))
                for c in tc.CONFIGS:
                    for depth in ((10,) if valid else (10, 14)):
                        if c in ("full", "base") and depth != 10: continue
                        if (name, c, depth) in done: continue
                        r = tc.run(path, tc.CONFIGS[c], timeout=60, env_extra={"HYLO_TC_MAXDEPTH": str(depth)})
                        row = {"program": name, "shape": s, "h": h, "n": n, "valid": valid, "config": c, "depth": depth}
                        row.update(tc.summarize(r, "user"))
                        out.write(json.dumps(row) + "\n"); out.flush()
                        print(name, c, depth, row["status"], row["diags"], row["matches"], row["ms"], row["msgs"][:1], flush=True)

if __name__ == "__main__":
    main()
