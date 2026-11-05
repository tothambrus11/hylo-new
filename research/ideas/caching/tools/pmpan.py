# Analyze pmp.sh output: inclusive percentages over samples of the busiest thread.
# usage: pmpan.py pmp.txt map.tsv [PATTERN ...]   (patterns match demangled names)
import sys, re, collections
txt = open(sys.argv[1]).read().split("=== END")
dm = {}
for line in open(sys.argv[2]):
    a, b = line.rstrip("\n").split("\t", 1); dm[a] = b
samples = []
for s in txt:
    best = None
    for th in s.split("\nThread ")[0:]:
        fr = re.findall(r"^#\d+\s+(?:0x[0-9a-f]+ in )?(\S+)", th, re.M)
        names = [dm.get(f, f) for f in fr]
        if any("FrontEnd" in f or "Typer" in n or "Parser" in n for f, n in zip(fr, names)):
            best = names; break
    if best is not None: samples.append(best)
N = len(samples)
print("samples", N)
pats = sys.argv[3:]
def has(st, p): return any(p in n for n in st)
for p in pats:
    if "|" in p and p.count(">") == 1:
        pass
    if " < " in p:   # A < B : samples with A that have B above it (as a caller)
        a, b = p.split(" < ")
        sa = [st for st in samples if has(st, a)]
        sb = [st for st in sa if any(b in n for n in st[min(i for i, n in enumerate(st) if a in n):])]
        print(f"{100*len(sa)/N:6.1f}% {a}   of which {100*len(sb)/N:6.1f}% called from {b}")
    elif " > " in p:   # A > B : fraction of samples with A that also have B below it
        a, b = p.split(" > ")
        sa = [st for st in samples if has(st, a)]
        sb = []
        for st in sa:
            ia = max(i for i, n in enumerate(st) if a in n)
            if any(b in n for n in st[:ia]): sb.append(st)
        print(f"{100*len(sa)/N:6.1f}% {a}   of which {100*len(sb)/N:6.1f}% under {b}")
    else:
        c = sum(1 for st in samples if has(st, p))
        print(f"{100*c/N:6.1f}% {p}")
