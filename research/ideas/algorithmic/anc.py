import pickle, sys, collections
stacks = pickle.load(open(sys.argv[1], "rb")); N = len(stacks)
target = sys.argv[2]; probes = sys.argv[3:]
hit = [st for st in stacks if any(target in n for n in st)]
print(f"{target}: {100*len(hit)/N:.2f}%")
for p in probes:
    c = sum(1 for st in hit if any(p in n for n in st))
    print(f"  with ancestor/desc '{p}': {100*c/N:.2f}%")
