# Count calls of CALLEE (mangled symbol) split by the function containing the return address.
# env: GDBC_CALLEE=sym  GDBC_RANGES=file with "start size name" lines (from nm -S)  GDBC_OUT=json
import gdb, os, json, bisect, collections
callee = os.environ["GDBC_CALLEE"]
rng = []
for l in open(os.environ["GDBC_RANGES"]):
    p = l.split()
    if len(p) >= 4 and p[2] in "tT": rng.append((int(p[0], 16), int(p[1], 16), p[3]))
rng.sort(); starts = [r[0] for r in rng]
base = None; cnt = collections.Counter()
class BP(gdb.Breakpoint):
    def stop(self):
        global base
        f = gdb.selected_frame()
        rsp = int(f.read_register("rsp"))
        ret = int(gdb.parse_and_eval(f"*(unsigned long*){rsp}"))
        if base is None:
            a = [r for r in rng if r[2] == callee][0][0]
            m = gdb.execute("info proc mappings", to_string=True)
            exe = os.path.realpath(gdb.current_progspace().filename)
            base = min(int(l.split()[0], 16) for l in m.splitlines() if l.strip().endswith(exe))
            print("base", hex(base))
        x = ret - base; i = bisect.bisect_right(starts, x) - 1
        cnt[rng[i][2] if i >= 0 and x < rng[i][0] + rng[i][1] else "?"] += 1
        return False
gdb.execute("set pagination off")
b = BP("'" + callee + "'", internal=True); b.silent = True
gdb.execute("run")
json.dump(cnt.most_common(), open(os.environ.get("GDBC_OUT", "callers.json"), "w"))
for k, v in cnt.most_common(12): print(v, k[:150])
