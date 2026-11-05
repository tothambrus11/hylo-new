#!/usr/bin/env python3
"""Dump symbolized, demangled stacks of a perf.data once (pickle), then query them.

usage: stacks.py PERF DATA OUT.pkl                      # build
       stacks.py --q OUT.pkl REGEX [--callers|--callees] [N]
--callers: for samples containing a frame matching REGEX (outermost match), share by immediate caller.
--callees: share by immediate callee of the outermost match (or 'self').
default: inclusive % of REGEX and of REGEX-but-not-under-another-REGEX-frame.
"""
import sys, subprocess, re, collections, pickle, bisect, os
if sys.argv[1] != "--q":
    perf, data, outp = sys.argv[1:4]
    sys.argv = [sys.argv[0], perf, data]
    # reuse perfsym's symbolization
    src = open("/home/hylo/hylo-tc/research/scripts/perfsym.py").read()
    src = src.split("self_c, incl_c")[0]
    g = {"__name__": "x"}; exec(src, g)
    out = g["out"]; resolve = g["resolve"]
    stacks = []; cur = []
    for line in out.splitlines():
        s = line.strip()
        if not s:
            if cur: stacks.append(tuple(cur))
            cur = []; continue
        m = re.match(r"^([0-9a-f]+)\s", s)
        if m and "PERF_RECORD" not in s: cur.append(resolve(int(m.group(1), 16)))
    if cur: stacks.append(tuple(cur))
    names = sorted({n for st in stacks for n in st})
    dm = dict(zip(names, subprocess.run(["swift", "demangle", "--simplified", "--compact"],
        input="\n".join(n.split(":", 1)[1] if ":" in n else n for n in names), capture_output=True, text=True).stdout.splitlines()))
    stacks = [tuple(dm.get(n, n) for n in st) for st in stacks]
    pickle.dump(stacks, open(outp, "wb")); print(len(stacks), "stacks"); sys.exit()
pk, rx = sys.argv[2], re.compile(sys.argv[3])
mode = sys.argv[4] if len(sys.argv) > 4 else ""
N = int(sys.argv[5]) if len(sys.argv) > 5 else 25
stacks = pickle.load(open(pk, "rb")); T = len(stacks)
c = collections.Counter(); hit = 0
for st in stacks:
    idx = [i for i, f in enumerate(st) if rx.search(f)]
    if not idx: continue
    hit += 1
    o = idx[-1]  # outermost (stack[0] is leaf)
    if mode == "--callers": c[st[o + 1] if o + 1 < len(st) else "<root>"] += 1
    elif mode == "--callees": c[st[o - 1] if o > 0 else "<self>"] += 1
print(f"{100*hit/T:.2f}% of {T} samples match {rx.pattern}")
for k, v in c.most_common(N): print(f"{100*v/T:6.2f}%  {k[:160]}")
