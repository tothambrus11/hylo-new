import pickle, sys, collections
# usage: sub.py pickle TARGET [N]  -> inclusive breakdown of descendants of TARGET (outermost occurrence)
stacks = pickle.load(open(sys.argv[1], "rb")); N = len(stacks)
target = sys.argv[2]; top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
c = collections.Counter(); callers = collections.Counter(); hit = 0
for st in stacks:
    idx = [i for i, n in enumerate(st) if target in n]
    if not idx: continue
    hit += 1; i = idx[-1]
    callers[st[i+1] if i+1 < len(st) else "<root>"] += 1
    for n in set(st[:i]): c[n] += 1
print(f"{target}: {100*hit/N:.2f}% of {N}")
print(" callers:")
for k, v in callers.most_common(8): print(f"   {100*v/N:6.2f}% {k[:140]}")
print(" descendants (inclusive):")
for k, v in c.most_common(top): print(f"   {100*v/N:6.2f}% {k[:140]}")
