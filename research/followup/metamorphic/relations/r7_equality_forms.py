"""Relation 7: an equality requirement may be stated twice, or in the symmetric form.

Kinds of variants, for each requirement `A == B` of a where clause:
- sym:     `B == A` in its place;
- dup:     `A == B, A == B`;
- dup-sym: `A == B, B == A`."""
from common import Variant, by_kind


def variants(F, rng):
    out = []
    for di, d in enumerate(F.all_decls()):
        c = d.clause
        if c is None: continue
        for ri, (a, b) in enumerate(c.reqs):
            depth, eq = 0, None
            for k in range(a, b):
                t = F.toks[k]
                if t.kind == "punct" and t.text in "<([{": depth += 1
                elif t.kind == "punct" and t.text in ">)]}": depth -= 1
                elif t.kind == "op" and t.text == "==" and depth == 0: eq = k; break
            if eq is None or eq == a or eq + 1 >= b: continue
            lhs, rhs = F.text(a, eq), F.text(eq + 1, b)
            s, e = F.toks[a].start, F.toks[b - 1].end
            label = "%s %s" % (d.kind, d.name or F.text(d.intro + 1, min(d.intro + 5, d.t1)))
            for kind, text in (("sym", "%s == %s" % (rhs, lhs)),
                               ("dup", "%s == %s, %s == %s" % (lhs, rhs, lhs, rhs)),
                               ("dup-sym", "%s == %s, %s == %s" % (lhs, rhs, rhs, lhs))):
                out.append(Variant("%s:%d:%d" % (kind, di, ri), "`%s == %s` of `%s` becomes `%s`" % (lhs, rhs, label, text),
                                   repl=F.edited_pieces([(s, e, text)]), kind=kind))
    rng.shuffle(out)
    return by_kind(out, ["sym", "dup-sym", "dup"])
