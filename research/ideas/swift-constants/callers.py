#!/usr/bin/env python3
"""Caller attribution for runtime hotspots in a perf profile (frame-pointer callchains).

usage: callers.py PERF DATA [--under REGEX] [--top N]

For every sample, the leaf "runtime" cost (libswiftCore / libc / runtime-ish frames and tc-bench
value-witness thunks) is attributed to the nearest *application* frame in tc-bench, and to the
nearest application frame matching nothing generic (Sequence/Collection/Array/Dictionary
helpers are skipped). Prints, per runtime category, the top attributed callers.
"""
import sys, subprocess, bisect, re, collections

perf, data = sys.argv[1], sys.argv[2]
under = None
top = 25
args = sys.argv[3:]
while args:
    a = args.pop(0)
    if a == "--under": under = re.compile(args.pop(0))
    elif a == "--top": top = int(args.pop(0))

out = subprocess.run([perf, "script", "-i", data, "-F", "comm,ip,dso", "--show-mmap-events"],
                     capture_output=True, text=True).stdout
maps = []
for m in re.finditer(r"PERF_RECORD_MMAP2? \d+/\d+: \[0x([0-9a-f]+)\((0x[0-9a-f]+)\) @ (0x[0-9a-f]+|\d+)[^\]]*\]: [rwxp-]+ (\S+)", out):
    base, size, pgoff, path = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 0), m.group(4)
    maps.append((base, base + size, pgoff, path))
syms = {}
def symtab(path):
    if path in syms: return syms[path]
    r = subprocess.run(["nm", "--defined-only", "-n", path], capture_output=True, text=True).stdout
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
    syms[path] = (addrs, names, delta)
    return syms[path]
cache = {}
def resolve(ip):
    if ip in cache: return cache[ip]
    r = ("?", "?")
    for (b, e, off, path) in maps:
        if b <= ip < e:
            addrs, names, delta = symtab(path)
            va = ip - b + off + delta
            i = bisect.bisect_right(addrs, va) - 1
            r = (path.split("/")[-1], names[i] if i >= 0 else hex(va))
            break
    cache[ip] = r
    return r

samples = []
cur = []
for line in out.splitlines():
    s = line.strip()
    if not s:
        if cur: samples.append(cur)
        cur = []; continue
    m = re.match(r"^([0-9a-f]+)\s", s)
    if m and "PERF_RECORD" not in s:
        cur.append(int(m.group(1), 16))
if cur: samples.append(cur)

allnames = set()
rs = []
for smp in samples:
    fr = [resolve(ip) for ip in smp]
    rs.append(fr)
    for d, n in fr: allnames.add(n)
allnames = sorted(allnames)
dm = dict(zip(allnames, subprocess.run(["swift", "demangle", "--simplified", "--compact"],
         input="\n".join(allnames), capture_output=True, text=True).stdout.splitlines()))

def category(dso, name):
    n = dm.get(name, name)
    if "swift_retain" in n or "swift_release" in n or "bridgeObjectRe" in n or "doDecrementSlow" in n or "swift_isUniquelyReferenced" in n: return "retain/release"
    if "dynamicCast" in n or "tryCast" in n or "conformsToProtocol" in n or "ConformanceCache" in n or "ExistentialTypeMetadata" in n or "getWitnessTable" in n: return "cast/conformance"
    if "TupleCache" in n or "getTupleTypeMetadata" in n: return "tuple-metadata"
    if "GenericMetadata" in n or "GenericCacheEntry" in n or "getCache" in n or "MetadataCache" in n or "instantiateConcreteType" in n or "MetadataWaitQueue" in n or "hash_combine" in n or "hash_short" in n: return "generic-metadata"
    if "Hasher" in n or "_hash(" in n: return "hashing"
    if "String" in n or "getBinaryProperties" in n or "_stringCompare" in n: return "string"
    if "swift_allocObject" in n or "malloc" in n or "free" in n or "deallocating" in n or dso.startswith("libc"): return "alloc/libc"
    if "initializeWithCopy" in n or "destroy" in n or "assignWithCopy" in n or "outlined" in n: return "value-witness"
    if dso.startswith("libswiftCore"): return "other-swiftCore"
    return None

GENERIC = re.compile(r"^(specialized )?(Sequence|Collection|Array|ContiguousArray|Dictionary|Set|_Native|__Raw|Slice|IndexingIterator|Optional|LazyFilter|FlattenSequence|Range|ArraySlice|BidirectionalCollection|RangeReplaceable|MutableCollection|_ArrayBuffer|_ContiguousArrayBuffer|OrderedDictionary|OrderedSet|Hasher|String|Substring|partial apply|closure|reabstraction thunk|protocol witness|thunk|implicit closure|merged|outlined|__swift|value witness|initializeWithCopy|assignWithCopy|destroy|_init|swift_)")

def is_app(dso, name):
    if dso != "tc-bench": return False
    n = dm.get(name, name)
    return not GENERIC.match(n) and category(dso, name) is None

cat_total = collections.Counter()
cat_callers = collections.defaultdict(collections.Counter)
cat_callers2 = collections.defaultdict(collections.Counter)
n_used = 0
for fr in rs:
    if under is not None and not any(under.search(dm.get(n, n)) for d, n in fr):
        continue
    n_used += 1
    d0, n0 = fr[0]
    c = category(d0, n0)
    if c is None:
        # leaf is app or generic code in tc-bench
        if d0 == "tc-bench" and GENERIC.match(dm.get(n0, n0)):
            c = "generic-stdlib-in-binary"
        else:
            continue
    cat_total[c] += 1
    apps = [dm.get(n, n) for d, n in fr if is_app(d, n)]
    a1 = apps[0] if apps else "?"
    a2 = (apps[0] + "  <=  " + apps[1]) if len(apps) > 1 else a1
    cat_callers[c][a1] += 1
    cat_callers2[c][a2] += 1

print(f"samples considered: {n_used} of {len(rs)}" + (f" (under /{under.pattern}/)" if under else ""))
for c, k in cat_total.most_common():
    print(f"\n== {c}: {100*k/n_used:.2f}% of considered samples")
    for a, v in cat_callers[c].most_common(top):
        print(f"  {100*v/n_used:6.2f}%  {a[:160]}")
print("\n\n######## two-level callers")
for c, k in cat_total.most_common(6):
    print(f"\n== {c}")
    for a, v in cat_callers2[c].most_common(top):
        print(f"  {100*v/n_used:6.2f}%  {a[:220]}")
