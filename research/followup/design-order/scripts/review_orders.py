#!/usr/bin/env python3
"""Type-checks permutations of the top-level declarations of Hylo programs, one process at a time.

usage: orders.py OUT.jsonl CONFIG[,CONFIG...] [--max N] [--fix K] [--count] FILE...

For each FILE and each CONFIG (base, FIX or FULL, optionally followed by +flag+flag; binary from $TCB), type-checks every permutation of the top-level
declarations if there are at most N of them (default 720), and otherwise the source order, its
reverse and a sample of N-2 permutations drawn with a fixed seed. Appends one JSON line per
(file, config) to OUT.jsonl: the number of permutations and, for each distinct outcome, the number
of permutations that give it and one example. Restartable: (file, config) pairs already in
OUT.jsonl are skipped.

With --fix K, the first K declarations stay in place and only the others are permuted.

A top-level declaration starts at a line whose first character is not a space, '}' or ')', and
extends to the next such line; comment lines directly above a declaration move with it. A file
in which some declaration has unbalanced braces is reported with "split": false and not permuted.
"""
import hashlib, itertools, json, math, os, random, re, subprocess, sys, tempfile

B = os.environ.get("TCB", "eq9-723cc0e6b0f8")
TCBSH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcb.sh")
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"base": "", "FIX": FIX,
           "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"}

def flags_of(config):
    """`FULL+sigrounds+selfcheck` is FULL with two more flags."""
    parts = config.split("+")
    return ",".join(x for x in [CONFIGS.get(parts[0], parts[0])] + parts[1:] if x)

def strip(line):
    return re.sub(r'"(\\.|[^"\\])*"', '""', line.split("//")[0])

def split(text):
    """Returns (header, declarations) or None if the text cannot be split reliably."""
    lines = text.split("\n")
    header = []
    while lines and (lines[0].startswith("//!") or not lines[0].strip()):
        header.append(lines.pop(0))
    decls, cur, pending = [], [], []
    def flush():
        nonlocal cur
        if cur:
            while cur and not cur[-1].strip(): cur.pop()
            decls.append("\n".join(cur)); cur = []
    for l in lines:
        starts = bool(l) and l[0] not in " \t})" and not l.startswith("//")
        if l.startswith("//") and not (cur and depth_of(cur) > 0):
            flush(); pending.append(l); continue
        if starts and not (cur and depth_of(cur) > 0):
            flush(); cur = pending + [l]; pending = []
        elif cur:
            cur.append(l)
        elif l.strip():
            return None
    flush()
    if pending: decls.append("\n".join(pending))
    for d in decls:
        if depth_of(d.split("\n")) != 0: return None
    return header, decls

def depth_of(lines):
    code = "\n".join(strip(l) for l in lines)
    return (code.count("{") - code.count("}")) + (code.count("(") - code.count(")")) \
        + (code.count("[") - code.count("]"))

def outcome(flags, text, count=False):
    with tempfile.NamedTemporaryFile("w", suffix=".hylo", delete=False, dir=os.environ.get("TMPDIR")) as f:
        f.write(text); path = f.name
    try:
        args = [TCBSH, B, flags, "--count", path]
        p = subprocess.run(args, env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags),
                           capture_output=True, text=True, timeout=300)
        if p.returncode != 0: return ["crash", [str(p.returncode)], ""]
        errs = sorted(re.sub(r"^.*?: error: ", "", l.strip()) for l in p.stdout.splitlines() if ": error: " in l)
        errs += sorted(set(re.findall(r"\[selfcheck\] (VIOLATION: .*)", p.stdout)))
        late = re.search(r"sigrounds\.lateNodes=(\d+)", p.stdout)
        if late: errs.append("lateNodes=" + late.group(1))
        m = re.search(r"diagnostics: (\d+)", p.stdout)
        c = re.search(r"counters.user:(.*)", p.stdout)
        return ["accept" if m and m.group(1) == "0" else "reject", errs, c.group(1).strip() if c else ""]
    except subprocess.TimeoutExpired:
        return ["timeout", [], ""]
    finally:
        os.unlink(path)

def main():
    args = sys.argv[1:]
    nmax, count, fix = 720, False, 0
    if "--fix" in args:
        i = args.index("--fix"); fix = int(args[i + 1]); del args[i:i + 2]
    if "--max" in args:
        i = args.index("--max"); nmax = int(args[i + 1]); del args[i:i + 2]
    if "--count" in args:
        args.remove("--count"); count = True
    out, configs, files = args[0], args[1].split(","), args[2:]
    done = set()
    if os.path.exists(out):
        done = {(r["file"], r["config"]) for r in map(json.loads, open(out))}
    with open(out, "a") as o:
        for path in files:
            for config in configs:
                if (path, config) in done: continue
                s = split(open(path).read())
                if s is None:
                    o.write(json.dumps({"file": path, "config": config, "split": False}) + "\n"); o.flush(); continue
                header, decls = s
                k = len(decls)
                head = tuple(range(min(fix, k)))
                if math.factorial(k - len(head)) <= nmax:
                    perms = [head + q for q in itertools.permutations(range(len(head), k))]
                else:
                    seed = int(hashlib.sha1(os.path.basename(path).encode()).hexdigest()[:8], 16)
                    rng = random.Random(seed)
                    perms = [tuple(range(k)), head + tuple(reversed(range(len(head), k)))]
                    while len(perms) < nmax:
                        p = list(range(len(head), k)); rng.shuffle(p); perms.append(head + tuple(p))
                seen = {}
                for p in perms:
                    r = outcome(flags_of(config), "\n".join(header + [decls[i] for i in p]) + "\n", count)
                    key = json.dumps(r[:2])
                    e = seen.setdefault(key, {"outcome": r[0], "errors": r[1], "n": 0, "example": list(p), "counters": r[2]})
                    e["n"] += 1
                o.write(json.dumps({"file": path, "config": config, "split": True, "decls": k, "fixed": len(head),
                                    "perms": len(perms), "outcomes": list(seen.values())}) + "\n"); o.flush()

if __name__ == "__main__":
    main()
