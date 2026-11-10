"""Declaration-order fuzzing: does the verdict of a program depend on the order of its
top-level declarations?

usage: permute.py BINID OUT.jsonl DIR... [--config NAME] [--max N] [--jobs J]
For each .hylo file under DIR, splits it into top-level declarations, type-checks up to N
permutations (all of them if there are at most N; a seeded sample otherwise), and records the
set of distinct outcomes. An outcome is (accept | reject | crash | timeout) plus the sorted error
messages with source positions removed. Restartable."""
import itertools, json, math, os, random, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"base": "", "FIX": FIX,
           "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"}

def split(text):
    """Returns (header, declarations): the leading `//!` lines and the top-level declarations."""
    lines = text.split("\n")
    header = []
    while lines and (lines[0].startswith("//!") or not lines[0].strip()):
        header.append(lines.pop(0))
    decls, cur, depth, pending = [], [], 0, []
    for l in lines:
        s = l.strip()
        if depth == 0 and not cur:
            if not s: continue
            if s.startswith("//") or s.startswith("@"):
                pending.append(l); continue
        cur.append(l)
        code = re.sub(r'"(\\.|[^"\\])*"', '""', l.split("//")[0])
        depth += code.count("{") - code.count("}")
        if depth <= 0 and cur:
            # A declaration ends when braces balance; one-line declarations end at the line.
            decls.append("\n".join(pending + cur)); cur, pending, depth = [], [], 0
    if cur: decls.append("\n".join(pending + cur))
    return header, decls

def outcome(binary, flags, text):
    with tempfile.NamedTemporaryFile("w", suffix=".hylo", delete=False) as f:
        f.write(text); path = f.name
    try:
        p = subprocess.run([binary, path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags),
                           capture_output=True, text=True, timeout=30)
        if p.returncode != 0: return ("crash", ())
        errs = sorted(re.sub(r"^.*?: error: ", "", l.strip()) for l in p.stdout.splitlines() if ": error: " in l)
        m = re.search(r"diagnostics: (\d+)", p.stdout)
        return ("accept" if m and m.group(1) == "0" else "reject", tuple(errs))
    except subprocess.TimeoutExpired:
        return ("timeout", ())
    finally:
        os.unlink(path)

def main():
    args = sys.argv[1:]
    opt = {"--config": "FULL", "--max": "24", "--jobs": "3"}
    for k in list(opt):
        if k in args:
            i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    binid, out, dirs = args[0], args[1], args[2:]
    binary = os.path.join(RES, "exp", "bin", binid, "tc-bench")
    flags, nmax = CONFIGS[opt["--config"]], int(opt["--max"])
    files = sorted(os.path.join(d, f) for r in dirs for d, _, fs in os.walk(r) for f in fs if f.endswith(".hylo"))
    done = set()
    if os.path.exists(out):
        done = {(r["file"], r["config"]) for r in map(json.loads, open(out))}
    def one(path):
        if (path, opt["--config"]) in done: return None
        header, decls = split(open(path).read())
        k = len(decls)
        if k < 2: return {"file": path, "config": opt["--config"], "decls": k, "perms": 0, "outcomes": []}
        if math.factorial(k) <= nmax:
            perms = list(itertools.permutations(range(k)))
        else:
            rng = random.Random(hash(os.path.basename(path)) & 0xffff)
            perms = [tuple(range(k)), tuple(reversed(range(k)))]
            while len(perms) < nmax:
                p = list(range(k)); rng.shuffle(p); perms.append(tuple(p))
        seen = {}
        for p in perms:
            o = outcome(binary, flags, "\n".join(header + [decls[i] for i in p]) + "\n")
            seen.setdefault(json.dumps(o), list(p))
        return {"file": path, "config": opt["--config"], "decls": k, "perms": len(perms),
                "outcomes": [{"outcome": json.loads(o), "example": p} for o, p in seen.items()]}
    with open(out, "a") as o, ThreadPoolExecutor(int(opt["--jobs"])) as ex:
        for r in ex.map(one, files):
            if r: o.write(json.dumps(r) + "\n"); o.flush()

if __name__ == "__main__":
    main()
