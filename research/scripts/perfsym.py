#!/usr/bin/env python3
"""Symbolize `perf script` output (perf lacks libelf here) using nm, and aggregate self/inclusive time."""
import sys, subprocess, bisect, re, collections
perf, data = sys.argv[1], sys.argv[2]
top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
out = subprocess.run([perf, "script", "-i", data, "-F", "comm,ip,dso", "--show-mmap-events"],
                     capture_output=True, text=True).stdout
# mmap events: base address, pgoff, path
maps = []
for m in re.finditer(r"PERF_RECORD_MMAP2? \d+/\d+: \[0x([0-9a-f]+)\((0x[0-9a-f]+)\) @ (0x[0-9a-f]+|\d+)[^\]]*\]: [rwxp-]+ (\S+)", out):
    base, size, pgoff, path = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 0), m.group(4)
    maps.append((base, base + size, pgoff, path))
syms = {}
def symtab(path):
    if path in syms: return syms[path]
    try:
        r = subprocess.run(["nm", "--defined-only", "-n", path], capture_output=True, text=True).stdout
    except Exception:
        r = ""
    addrs, names = [], []
    for line in r.splitlines():
        p = line.split(None, 2)
        if len(p) == 3 and p[1] in "tTwW":
            addrs.append(int(p[0], 16)); names.append(p[2])
    # program header offset: vaddr - offset of the executable segment
    seg = subprocess.run(["readelf", "-lW", path], capture_output=True, text=True).stdout
    delta = 0
    for l in seg.splitlines():
        f = l.split()
        if f and f[0] == "LOAD" and "E" in f[-2]:
            delta = int(f[2], 16) - int(f[1], 16)  # vaddr - offset
    syms[path] = (addrs, names, delta)
    return syms[path]
def resolve(ip):
    for (b, e, off, path) in maps:
        if b <= ip < e:
            addrs, names, delta = symtab(path)
            va = ip - b + off + delta
            i = bisect.bisect_right(addrs, va) - 1
            name = names[i] if i >= 0 else hex(va)
            return path.split("/")[-1] + ":" + name
    return "?"
self_c, incl_c = collections.Counter(), collections.Counter()
samples = 0
cur = []
def flush():
    global samples
    if not cur: return
    samples += 1
    names = [resolve(ip) for ip in cur]
    self_c[names[0]] += 1
    for n in set(names): incl_c[n] += 1
for line in out.splitlines():
    s = line.strip()
    if not s:
        flush(); cur = []; continue
    m = re.match(r"^([0-9a-f]+)\s", s)
    if m and "PERF_RECORD" not in s:
        cur.append(int(m.group(1), 16))
flush()
names = sorted(set(self_c) | set(incl_c))
dm = dict(zip(names, subprocess.run(["swift", "demangle", "--simplified", "--compact"], input="\n".join(n.split(":",1)[1] for n in names), capture_output=True, text=True).stdout.splitlines()))
def show(c, title):
    print(f"== {title} ({samples} samples)")
    for n, k in c.most_common(top):
        print(f"{100*k/samples:6.2f}%  {n.split(':')[0][:14]:14} {dm.get(n, n)[:150]}")
show(self_c, "self")
show(incl_c, "inclusive")
