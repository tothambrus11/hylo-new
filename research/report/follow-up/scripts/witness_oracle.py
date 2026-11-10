"""Output-equivalence check that includes the witnesses of elaborated expressions.

usage: witness_oracle.py BINID OUT.jsonl [jobs]
For every corpus file, dumps the typing results under the baseline and under each configuration,
and compares them line by line in three classes:
  core      types, name bindings, witness tables, diagnostics (what the original oracle compared)
  syn.norm  witnesses of elaborated expressions with equality proofs erased
  syn.raw   the same witnesses, verbatim"""
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RES, "exp"))
import tcx
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"FIX": FIX,
           "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo",
           "MIN5": "index,extorder,typevec,symindex,traitindex"}
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench")

def dump(path, flags):
    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as f: out = f.name
    try:
        p = subprocess.run([B, "--dump", out, path], env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags),
                           capture_output=True, text=True, timeout=300)
        if p.returncode != 0: return None
        return tcx.NORMALIZE.sub("(erased: _)", open(out).read()).split("\n")
    except subprocess.TimeoutExpired:
        return None
    finally:
        if os.path.exists(out): os.unlink(out)

def classes(lines):
    c = {"core": [], "syn.norm": [], "syn.raw": []}
    for l in lines:
        k = "syn.raw" if " syn.raw " in l else "syn.norm" if " syn.norm " in l else "core"
        c[k].append(l)
    return c

def one(path):
    base = dump(path, "")
    r = {"file": os.path.relpath(path, RES), "base": base is not None, "configs": {}}
    if base is None: return r
    b = classes(base)
    r["sites"] = len(b["syn.raw"])
    for name, flags in CONFIGS.items():
        d = dump(path, flags)
        if d is None: r["configs"][name] = "crash"; continue
        c = classes(d)
        diff = {}
        for k in b:
            x, y = set(b[k]), set(c[k])
            if x != y: diff[k] = {"only_base": sorted(x - y)[:5], "only_cfg": sorted(y - x)[:5], "n": len(x ^ y)}
        r["configs"][name] = diff
    return r

if __name__ == "__main__":
    files = tcx.corpus("all")
    jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    with open(sys.argv[2], "w") as o, ThreadPoolExecutor(jobs) as ex:
        for r in ex.map(one, files):
            o.write(json.dumps(r) + "\n"); o.flush()
