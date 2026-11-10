"""Sampling profiler for tc-bench using gdb (no perf available on this machine).

usage: sample.py BINID FLAGS OUT.json [samples]
Runs standard-library type checking in a loop and takes stack samples with gdb. Reports, for each
function, the share of samples in which it is the innermost frame (self) and in which it appears
anywhere on the stack (inclusive). Only samples taken inside the type checker (a frame of
`Typer.apply` on the stack) are counted."""
import collections, json, os, re, subprocess, sys, time
RES = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(RES, "exp", "bin", sys.argv[1], "tc-bench.real")
flags, out = sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 150
p = subprocess.Popen([B, "--repeat", "100000", os.path.join(RES, "workloads/empty.hylo")],
                     env=dict(os.environ, HYLO_TC_EXPERIMENTS=flags), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
stacks = []
try:
    while len(stacks) < N and p.poll() is None:
        g = subprocess.run(["gdb", "-p", str(p.pid), "-batch", "-ex", "thread apply all bt 80"], capture_output=True, text=True, timeout=120)
        best = []
        for th in re.split(r"^Thread \d+.*$", g.stdout, flags=re.M):
            frames = re.findall(r"^#\d+\s+(?:0x[0-9a-f]+ in )?(\S+)", th, re.M)
            if any("FrontEnd" in f or "8FrontEnd" in f for f in frames) and len(frames) > len(best): best = frames
        if best: stacks.append(best)
        time.sleep(0.05)
finally:
    p.kill()
syms = sorted({f for s in stacks for f in s})
d = subprocess.run(["/opt/swift/usr/bin/swift-demangle", "--simplified"], input="\n".join(syms), capture_output=True, text=True).stdout.split("\n")
name = dict(zip(syms, d))
def short(f):
    n = name.get(f, f)
    n = re.sub(r"\(extension in \w+\):", "", n)
    n = re.sub(r"^(?:merged |function signature specialization <[^>]*> of |generic specialization <.*?> of |partial apply forwarder for |closure #\d+ .*? in )+", "", n)
    return n[:110]
typing = [s for s in stacks if any("Typer" in short(f) for f in s)]
self_, incl = collections.Counter(), collections.Counter()
for s in typing:
    self_[short(s[0])] += 1
    for n in {short(f) for f in s}: incl[n] += 1
json.dump({"samples": len(stacks), "typing": len(typing), "self": self_.most_common(60), "inclusive": incl.most_common(120)}, open(out, "w"), indent=1)
print(len(stacks), "samples,", len(typing), "in the type checker")
for n, c in incl.most_common(45): print(f"{100*c/max(1,len(typing)):5.1f}%  {n}")
