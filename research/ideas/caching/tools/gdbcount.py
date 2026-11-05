# gdb -batch --readnever -x gdbcount.py --args tc-bench.real file.hylo
# Counts calls of selected Typer functions on the frozen binary and the number of distinct
# argument tuples (raw register values; equal values imply equal arguments, so the distinct
# counts are upper bounds and the derived hit rates lower bounds).
import gdb, collections, os, json
FUNCS = {
 "memberOf": ("$s8FrontEnd5TyperV7resolve_8memberOf11visibleFromSayAA23NameResolutionCandidateVGAA0I0V_AA15AnyTypeIdentityVAA05ScopeN0VtF", ["rdi","rsi","rdx","rcx","r8","r9"]),
 "lookupUnqualified": ("$s8FrontEnd5TyperV6lookup33_A3D88A7B549457189E34B3066F923C6ALL_13unqualifiedIn09containedN0SayAA19DeclarationIdentityVGAA4NameV_AA05ScopeQ0VANSgtF", ["rdi","rsi","rdx","rcx","r8","r9"]),
 "resolveUnqualified": ("$s8FrontEnd5TyperV7resolve33_A3D88A7B549457189E34B3066F923C6ALL_13unqualifiedInSayAA23NameResolutionCandidateVGAA0O0V_AA13ScopeIdentityVtF", ["rdi","rsi","rdx","rcx","r8"]),
 "traitLookup": ("$s8FrontEnd5TyperV6lookup33_A3D88A7B549457189E34B3066F923C6ALL_24memberOfTraitVisibleFromSayAA22ConcreteSyntaxIdentityVyAA0O11DeclarationVG7concept_SayAA0uT0VG7memberstGAA4NameV_AA05ScopeT0VtF", ["rdi","rsi","rdx","rcx","r8"]),
 "inherited": ("$s8FrontEnd5TyperV7resolve33_A3D88A7B549457189E34B3066F923C6ALL_17inheritedMemberOf11visibleFrom10staticallySayAA23NameResolutionCandidateVGAA0S0V_AA15AnyTypeIdentityVAA05ScopeX0VSbtF", ["rdi","rsi","rdx","rcx","r8","r9"]),
 "native": ("$s8FrontEnd5TyperV7resolve33_A3D88A7B549457189E34B3066F923C6ALL_14nativeMemberOf10staticallySayAA23NameResolutionCandidateVGAA0Q0V_AA15AnyTypeIdentityVSbtF", ["rdi","rsi","rdx","rcx","r8","r9"]),
 "canDeriveCoercions": ("$s8FrontEnd5TyperV18canDeriveCoercions33_A3D88A7B549457189E34B3066F923C6ALL__2in5whereSbAA15AnyTypeIdentityV_AiA05ScopeS0VAC16ResolutionThreadAELLV11EnvironmentVtF", ["rdi","rsi","rdx"]),
 "canDeriveCoercion": ("$s8FrontEnd5TyperV17canDeriveCoercion33_A3D88A7B549457189E34B3066F923C6ALL_8applyings5UInt8V9Utilities4PairVyAA15AnyTypeIdentityVAMG_AA5GivenOtF", ["rdi","rsi","rdx","rcx"]),
 "givensVisible": ("$s8FrontEnd5TyperV6givens11visibleFromSaySayAA5GivenOGGAA13ScopeIdentityV_tF", ["rdi"]),
 "summon": ("$s8FrontEnd5TyperV6summon_2inSayAC12SummonResultVGAA15AnyTypeIdentityV_AA05ScopeJ0VtF", ["rdi","rsi"]),
 "expression": ("$s8FrontEnd5TyperV10expression33_A3D88A7B549457189E34B3066F923C6ALL11referringToAA17WitnessExpressionVAA5GivenO_tF", ["rdi","rsi","rdx"]),
 "applies": ("$s8FrontEnd5TyperV7applies33_A3D88A7B549457189E34B3066F923C6ALL_2to2inAC12SummonResultVSgAA22ConcreteSyntaxIdentityVyAA20ExtensionDeclarationVG_AA07AnyTypeS0VAA05ScopeS0VtF", ["rdi","rsi","rdx"]),
}
extra = os.environ.get("GDBCOUNT_EXTRA")  # name=symbol:regs;...
if extra:
    for item in extra.split(";"):
        k, v = item.split("=", 1); s, r = v.split(":"); FUNCS[k] = (s, r.split(","))
calls = collections.Counter(); keys = collections.defaultdict(collections.Counter)
class BP(gdb.Breakpoint):
    def __init__(self, name, sym, regs):
        super().__init__(sym, internal=True); self.n = name; self.regs = regs; self.silent = True
    def stop(self):
        f = gdb.selected_frame()
        k = tuple(int(f.read_register(r)) & 0xffffffffffffffff for r in self.regs)
        calls[self.n] += 1; keys[self.n][k] += 1
        return False
gdb.execute("set pagination off"); gdb.execute("set confirm off")
gdb.execute("set breakpoint pending on")
sel = os.environ.get("GDBCOUNT_ONLY")
for n, (s, r) in FUNCS.items():
    if sel and n not in sel.split(","): continue
    BP(n, "'" + s + "'", r)
gdb.execute("run")
out = {n: {"calls": calls[n], "distinct": len(keys[n]),
           "top": sorted(keys[n].values(), reverse=True)[:5],
           "keys": [[list(k), c] for k, c in keys[n].items()]} for n in calls}
p = os.environ.get("GDBCOUNT_OUT", "gdbcount.json")
json.dump(out, open(p, "w"), indent=1)
for n in sorted(out): print(f"{n:20s} calls={out[n]['calls']:8d} distinct={out[n]['distinct']:7d} top={out[n]['top']}")
