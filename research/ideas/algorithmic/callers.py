#!/usr/bin/env python3
"""Caller/callee breakdown for perf data: callers.py <perf> <data> <out.pickle-cache> pattern..."""
import sys, subprocess, bisect, re, collections, os, pickle
perf, data, cache = sys.argv[1], sys.argv[2], sys.argv[3]
pats = sys.argv[4:]
if os.path.exists(cache):
    stacks = pickle.load(open(cache, "rb"))
else:
    out = subprocess.run([perf, "script", "-i", data, "-F", "comm,ip,dso", "--show-mmap-events"],
                         capture_output=True, text=True).stdout
    maps = []
    for m in re.finditer(r"PERF_RECORD_MMAP2? \d+/\d+: \[0x([0-9a-f]+)\((0x[0-9a-f]+)\) @ (0x[0-9a-f]+|\d+)[^\]]*\]: [rwxp-]+ (\S+)", out):
        base, size, pgoff, path = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 0), m.group(4)
        maps.append((base, base + size, pgoff, path))
    syms = {}
    def symtab(path):
        if path in syms: return syms[path]
        try: r = subprocess.run(["nm", "--defined-only", "-n", path], capture_output=True, text=True).stdout
        except Exception: r = ""
        addrs, names = [], []
        for line in r.splitlines():
            p = line.split(None, 2)
            if len(p) == 3 and p[1] in "tTwW":
                addrs.append(int(p[0], 16)); names.append(p[2])
        seg = subprocess.run(["readelf", "-lW", path], capture_output=True, text=True).stdout
        delta = 0
        for l in seg.splitlines():
            f = l.split()
            if f and f[0] == "LOAD" and "E" in f[-2]:
                delta = int(f[2], 16) - int(f[1], 16)
        syms[path] = (addrs, names, delta); return syms[path]
    rc = {}
    def resolve(ip):
        if ip in rc: return rc[ip]
        r = "?"
        for (b, e, off, path) in maps:
            if b <= ip < e:
                addrs, names, delta = symtab(path)
                va = ip - b + off + delta
                i = bisect.bisect_right(addrs, va) - 1
                r = names[i] if i >= 0 else hex(va); break
        rc[ip] = r; return r
    stacks = []; cur = []
    for line in out.splitlines() + [""]:
        s = line.strip()
        if not s:
            if cur: stacks.append([resolve(ip) for ip in cur])
            cur = []; continue
        m = re.match(r"^([0-9a-f]+)\s", s)
        if m and "PERF_RECORD" not in s: cur.append(int(m.group(1), 16))
    allnames = sorted({n for st in stacks for n in st})
    dm = subprocess.run(["swift", "demangle", "--simplified"], input="\n".join(allnames), capture_output=True, text=True).stdout.splitlines()
    d = dict(zip(allnames, dm)) if len(dm) == len(allnames) else {n: n for n in allnames}
    stacks = [[d[n] for n in st] for st in stacks]
    pickle.dump(stacks, open(cache, "wb"))
N = len(stacks)
for p in pats:
    callers, callees = collections.Counter(), collections.Counter()
    hit = 0
    for st in stacks:
        idx = [i for i, n in enumerate(st) if p in n]
        if not idx: continue
        hit += 1
        i = idx[-1]  # outermost occurrence
        j = idx[0]
        callers[st[i+1] if i+1 < len(st) else "<root>"] += 1
        callees[st[j-1] if j > 0 else "<self>"] += 1
    print(f"=== {p}: {100*hit/N:.2f}% of {N}")
    print(" callers:")
    for k, v in callers.most_common(12): print(f"   {100*v/N:6.2f}% {k[:150]}")
    print(" callees:")
    for k, v in callees.most_common(15): print(f"   {100*v/N:6.2f}% {k[:150]}")
