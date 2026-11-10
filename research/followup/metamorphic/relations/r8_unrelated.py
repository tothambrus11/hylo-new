"""Relation 8: adding a declaration that nothing uses does not change the verdict.

Kinds of variants (each at the end of the file, and at the beginning for the `-top` kinds):
- struct:   a new empty struct;
- trait:    a new empty trait;
- gstruct:  a new generic struct `struct N<T> { }`;
- conf:     a new struct and its conformance to an existing trait of the file. Only traits whose
            body is empty or contains nothing but associated types, which the conformance defines
            as the new struct itself;
- gconf:    a new generic struct and `given <T> => N<T> is P { ... }`;
- ext:      a new struct and an extension of it with a member alias and a method."""
from common import Variant, fresh


def simple_traits(F):
    """[(name, [associated types])] of the non-generic traits that a new type can satisfy with
    associated types only."""
    out = []
    for d in F.decls:
        if d.kind != "trait" or not d.name or d.clause is not None or d.body is None: continue
        if any(t.kind == "name" and t.text == "refines" for t in F.toks[d.intro:d.body[0]]): continue
        ms = d.members or []
        if all(m.kind == "type" and m.name and m.t1 - m.intro == 2 for m in ms):
            out.append((d.name, [m.name for m in ms]))
    return out


def variants(F, rng):
    n, tr, g = fresh(F, "Nq"), fresh(F, "Trq"), fresh(F, "Gq")
    out = []
    def add(kind, decls, desc):
        out.append(Variant(kind, desc + ", added last", post=decls, kind=kind))
        out.append(Variant(kind + "-top", desc + ", added first", pre=decls, kind=kind + "-top"))
    add("struct", ["struct %s {}" % n], "new struct")
    add("trait", ["trait %s {}" % tr], "new trait")
    out.append(Variant("gstruct", "new generic struct, added last", post=["struct %s<Tq> {}" % g], kind="gstruct"))
    out.append(Variant("ext", "new struct with an extension, added last",
                       post=["struct %s {}" % n, "extension %s { type Mq = %s\n  fun mq() {} }" % (n, n)], kind="ext"))
    traits = simple_traits(F)
    rng.shuffle(traits)
    for i, (p, xs) in enumerate(traits[:2]):
        body = "{ " + "; ".join("type %s = %s" % (x, n) for x in xs) + " }" if xs else "{}"
        decls = ["struct %s {}" % n, "given %s is %s %s" % (n, p, body)]
        out.append(Variant("conf:%d" % i, "new struct conforming to %s, added last" % p, post=decls, kind="conf"))
        out.append(Variant("conf-top:%d" % i, "new struct conforming to %s, added first" % p, pre=decls, kind="conf-top"))
        if i == 0:
            gbody = "{ " + "; ".join("type %s = %s<Tq>" % (x, g) for x in xs) + " }" if xs else "{}"
            out.append(Variant("gconf:%d" % i, "new generic struct conforming to %s, added last" % p,
                               post=["struct %s<Tq> {}" % g, "given <Tq> => %s<Tq> is %s %s" % (g, p, gbody)], kind="gconf"))
    order = ["conf:0", "struct-top", "gconf:0", "trait", "ext", "conf-top:0", "struct", "gstruct",
             "trait-top", "conf:1", "conf-top:1"]
    return sorted(out, key=lambda v: order.index(v.vid) if v.vid in order else 99)
