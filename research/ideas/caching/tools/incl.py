import pickle, sys
stacks = pickle.load(open(sys.argv[1], "rb")); N = len(stacks)
for p in sys.argv[2:]:
    c = sum(1 for st in stacks if any(p in n for n in st))
    s = sum(1 for st in stacks if p in st[0])
    print(f"{100*c/N:6.2f}% incl {100*s/N:6.2f}% self  {p}")
