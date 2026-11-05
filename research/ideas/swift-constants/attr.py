#!/usr/bin/env python3
"""attr.py PKL [--under S] [--top N] [--depth K] [--cat C]
Attribute leaf runtime cost (by category) to nearest application frame(s).
PKL is a pickle of demangled stacks (leaf first) made by ideas/algorithmic/callers.py."""
import sys, pickle, re, collections
stacks = pickle.load(open(sys.argv[1], "rb"))
args = sys.argv[2:]; under=None; top=20; depth=1; only=None
while args:
    a=args.pop(0)
    if a=="--under": under=args.pop(0)
    elif a=="--top": top=int(args.pop(0))
    elif a=="--depth": depth=int(args.pop(0))
    elif a=="--cat": only=args.pop(0)
def category(n):
    if any(k in n for k in ("swift_retain","swift_release","bridgeObjectRe","doDecrementSlow","swift_isUniquelyReferenced","swift_unknownObject")): return "retain/release"
    if any(k in n for k in ("dynamicCast","tryCast","conformsToProtocol","ConformanceCache","ExistentialTypeMetadata","getWitnessTable","ConformanceCacheKey","_conformsTo")): return "cast/conformance"
    if "TupleCache" in n or "getTupleTypeMetadata" in n: return "tuple-metadata"
    if any(k in n for k in ("GenericMetadata","GenericCacheEntry","getCache","MetadataCache","instantiateConcreteType","MetadataWaitQueue","hash_combine","hash_short","AtomicWaitQueue","swift_checkMetadataState","getSingletonMetadata","TaggedMetadataAllocator")): return "generic-metadata"
    if "Hasher" in n or "_hash(" in n or "hashValue" in n or "hash(into" in n: return "hashing"
    if "String" in n or "getBinaryProperties" in n or "_stringCompare" in n or "Unicode" in n: return "string"
    if any(k in n for k in ("swift_allocObject","malloc","free","deallocating","swift_slowAlloc","swift_slowDealloc","_int_","swift_deallocObject","0x")): return "alloc/libc"
    if any(k in n for k in ("initializeWithCopy","destroy","assignWithCopy","assignWithTake","initializeWithTake","outlined","value witness","initializeBufferWithCopy")): return "value-witness"
    if n.startswith("_ZN") or n.startswith("_ZL") or n.startswith("swift_"): return "other-runtime"
    return None
GENERIC = re.compile(r"^(specialized |generic specialization <.*> of )?(Swift\.)?(Sequence|Collection|Array|ContiguousArray|Dictionary|Set|_Native|__Raw|Slice|IndexingIterator|Optional|LazyFilter|Flatten|Range|ArraySlice|BidirectionalCollection|RangeReplaceable|MutableCollection|_ArrayBuffer|_ContiguousArrayBuffer|Hasher|String|Substring|partial apply|closure|reabstraction thunk|protocol witness|thunk|implicit closure|merged|outlined|__swift|value witness|initializeWithCopy|assignWithCopy|destroy|_init|swift_|_swift|_ZN|_ZL|0x|\?|_stringCompare|static String|static Hasher|_StringGuts|_SmallString|_copySequence|_allocateUninitialized|default argument)")
def is_app(n): return not GENERIC.match(n) and category(n) is None
N=len(stacks); used=0
tot=collections.Counter(); by=collections.defaultdict(collections.Counter); appself=collections.Counter()
for st in stacks:
    if under and not any(under in n for n in st): continue
    used+=1
    c=category(st[0])
    if c is None:
        c = "generic-in-binary" if GENERIC.match(st[0]) else "app-self"
    if only and c!=only: continue
    tot[c]+=1
    apps=[n for n in st if is_app(n)]
    key="  <=  ".join(a[:110] for a in apps[:depth]) if apps else "?"
    by[c][key]+=1
print(f"samples {used}/{N}" + (f" under '{under}'" if under else ""))
for c,k in tot.most_common():
    print(f"\n== {c}: {100*k/used:.2f}% of considered ({100*k/N:.2f}% of all)")
    for a,v in by[c].most_common(top): print(f"  {100*v/N:6.2f}%  {a}")
