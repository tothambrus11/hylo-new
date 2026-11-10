"""Split a hand-written probe into one file per query function (lines starting with 'fun q')."""
import sys, os
src = sys.argv[1]
lines = open(src).read().splitlines()
head = [l for l in lines if not l.startswith("fun q")]
qs = [l for l in lines if l.startswith("fun q")]
out = []
os.makedirs(sys.argv[2], exist_ok=True)
for i, q in enumerate(qs):
    p = os.path.join(sys.argv[2], os.path.basename(src).replace(".hylo", f"-q{i}.hylo"))
    open(p, "w").write("\n".join(head + [q]) + "\n")
    print(p)
