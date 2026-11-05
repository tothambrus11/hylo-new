#!/usr/bin/env python3
"""Random differential testing of the `index` experiment against the baseline.

usage: fuzz.py SEED_FROM SEED_TO [configs]
Programs go to fuzz/, a summary line per seed is printed.
"""
import os, random, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

B = "/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench"
D = "/home/user/hylo-new/research/review/index/v2/fuzz"
os.makedirs(D, exist_ok=True)
NORM = re.compile(r"\(erased: \d+\)")


def gen(seed):
    r = random.Random(seed)
    nt = r.randint(2, 4)
    out = []
    for i in range(nt):
        if i > 0 and r.random() < 0.3:
            out.append(f"trait P{i} refines P{r.randrange(i)} {{}}")
        else:
            out.append(f"trait P{i} {{}}")
    out += ["struct A { public memberwise init }", "struct B { public memberwise init }",
            "struct Box<T> { public memberwise init }", "struct Pair<T, U> { public memberwise init }",
            "type XA = A", "type XB = Box<A>", "type XC = XB", "type XP = Pair<A, B>"]
    tys = ["A", "B", "Box<A>", "Box<B>", "Box<Box<A>>", "Pair<A, B>", "Pair<B, A>", "XA", "XB",
           "XC", "XP", "Box<XA>", "Void", "{A, B}", "Int", "Bool"]
    P = lambda: f"P{r.randrange(nt)}"

    def given_decl(local=False):
        k = r.randrange(12)
        if k == 9: return f"given <T, U where T == U> => Box<T> is {P()} {{}}"
        if k == 10: return f"given <T where T == {r.choice(['A','B','XA'])}> => T is {P()} {{}}"
        if k == 11 and local: return r.choice(["given let la = A()", "given let lb = Box<A>()", "given let lt = {A(), B()}"])
        if k == 0: return f"given {r.choice(tys)} is {P()} {{}}"
        if k == 1: return f"given <T where T is {P()}> => Box<T> is {P()} {{}}"
        if k == 2: return f"given <T, U where T is {P()}, U is {P()}> => Pair<T, U> is {P()} {{}}"
        if k == 3: return f"given <T> => Box<T> is {P()} {{}}"
        if k == 4: return f"given <where {r.choice(tys)} is {P()}> => {r.choice(tys)} is {P()} {{}}"
        if k == 5: return f"given {r.choice(['XA', 'XB', 'XC', 'XP'])} is {P()} {{}}"
        if k == 6: return f"given <T where T is {P()}> => T is {P()} {{}}" if r.random() < 0.3 else f"given A is {P()} {{}}"
        if k == 7 and local: return r.choice(["given A = A()", "given Box<A> = Box<A>()", "given Void = ()"])
        return f"given {{{r.choice(['A', 'B'])}, {r.choice(['A', 'B'])}}} is {P()} {{}}"

    for _ in range(r.randint(3, 10)):
        out.append(given_decl())
    for i in range(nt):
        out.append(f"fun need{i}<T is P{i}>() {{}}")
    out.append("fun check<T>(x: T) {}")
    for f in range(r.randint(2, 5)):
        kind = r.randrange(5)
        body = []
        if kind == 0:
            sig = f"fun f{f}()"
        elif kind == 1:
            sig = f"fun f{f}<T is {P()}>()"
        elif kind == 2:
            sig = f"fun f{f}<T, U where T == U, T is {P()}>()"
        elif kind == 3:
            sig = f"fun f{f}<where let a: A, {B_ty(r)} is {P()}>()"
        else:
            sig = f"fun f{f}<T where let t: T, let b: Box<A>>()"
        def stmts(depth):
            s = []
            for _ in range(r.randint(1, 4)):
                c = r.randrange(6)
                if c == 0 and depth < 2:
                    s.append("if true {")
                    s += ["  " + x for x in stmts(depth + 1)]
                    s.append("}")
                elif c == 1:
                    s.append(given_decl(local=True))
                elif c == 2:
                    pre = r.choice(["let _ = ", "check(", "_ = "]); s.append(pre + f"summon[{P()}<{query_ty(r, kind, tys)}>]" + (")" if pre == "check(" else ""))
                elif c == 3:
                    s.append(f"check(summon[{r.choice(['A', 'Box<A>', 'Void'])}])" if kind in (0, 3) and r.random() < 0.3 else f"need{r.randrange(nt)}<{query_ty(r, kind, tys)}>()")
                else:
                    s.append(f"need{r.randrange(nt)}<{query_ty(r, kind, tys)}>()")
            return s
        body = stmts(0)
        out.append(sig + " {")
        out += ["  " + x for x in body]
        out.append("}")
    return "\n".join(out) + "\n"


def B_ty(r):
    return r.choice(["A", "Box<A>", "B"])


def query_ty(r, kind, tys):
    if kind in (1, 2) and r.random() < 0.5:
        return r.choice(["T", "Box<T>", "Pair<T, A>"] + (["U", "Box<U>"] if kind == 2 else []))
    return r.choice(tys)


def run(cfg, path):
    env = dict(os.environ)
    env.pop("HYLO_TC_EXPERIMENTS", None)
    if cfg: env["HYLO_TC_EXPERIMENTS"] = cfg
    env["HYLO_TC_ABSDEPTH"] = "2"
    out = path + f".{cfg or 'base'}.dump"
    try:
        p = subprocess.run([B, "--quiet", "--dump", out, path], env=env, capture_output=True,
                           text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return ("timeout", "")
    if p.returncode != 0 or not os.path.exists(out):
        return (f"crash{p.returncode}", "")
    t = NORM.sub("(erased: _)", open(out).read())
    os.remove(out)
    return ("ok", t)


def one(seed, cfgs):
    path = os.path.join(D, f"s{seed}.hylo")
    open(path, "w").write(gen(seed))
    b = run("", path)
    res = []
    for c in cfgs:
        x = run(c, path)
        if x == b:
            res.append(f"{c}=same")
        else:
            res.append(f"{c}=DIFF({x[0]} vs {b[0]})")
            if x[0] == "ok" and b[0] == "ok":
                import difflib
                d = "".join(list(difflib.unified_diff(b[1].splitlines(True), x[1].splitlines(True), n=0))[:30])
                open(path + f".{c}.diff", "w").write(d)
    nd = sum(1 for l in b[1].splitlines() if l.startswith("diag"))
    return f"seed {seed}: base={b[0]} diags={nd} " + " ".join(res)


if __name__ == "__main__":
    a, z = int(sys.argv[1]), int(sys.argv[2])
    cfgs = (sys.argv[3] if len(sys.argv) > 3 else "index").split(";")
    with ThreadPoolExecutor(2) as ex:
        for line in ex.map(lambda s: one(s, cfgs), range(a, z)):
            print(line, flush=True)
