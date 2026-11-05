import sys, pickle, re, collections
# attribute samples whose leaf matches LEAF to the nearest frame matching APP (tc-bench typer code)
pk, leaf = sys.argv[1], re.compile(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
skip = re.compile(r"^(specialized |merged |outlined |protocol witness|_|swift_|0x|<|static Array|Array|Dictionary|Set|Sequence|Collection|_Native|__Raw|Hasher|String|Optional|closure #\d+ in (Sequence|Array|Collection))|^\S+\.s |libswift|Lazy|Ordered|Stable|Contiguous|IndexingIterator|FlattenSequence|Chain2Sequence")
st = pickle.load(open(pk, "rb")); T = len(st); c = collections.Counter(); n = 0
for s in st:
    if not leaf.search(s[0]) and not any(leaf.search(f) for f in s[:4]): continue
    n += 1
    for f in s[1:]:
        if not skip.search(f) and not leaf.search(f): c[f] += 1; break
print(f"{100*n/T:.2f}% leaf {leaf.pattern}")
for k, v in c.most_common(N): print(f"{100*v/T:6.2f}%  {k[:140]}")
