"""Relation 4: adding a requirement that is trivially true, or a generic parameter that is not
used, does not change the verdict.

Kinds of variants, for functions, conformances and extensions:
- taut-param:  `T == T` for a generic parameter T of the declaration;
- taut-assoc:  `T.X == T.X` where the declaration requires `T is P` and P declares `type X`;
- taut-app:    `Box<T> == Box<T>` for a type application written in the head of the declaration;
- taut-ground: `A == A` for a non-generic struct mentioned in the head (also on declarations that
               have no context clause, which then get `<where A == A>`);
each as the last and as the first requirement;
- unused-param: an extra generic parameter that nothing mentions. Only for conformances,
  extensions, and functions that are never applied to explicit type arguments."""
from common import Variant, fresh, by_kind
from hylosyn import match_angle
from relations.r2_permute_requirements import explicitly_applied


def file_types(F):
    """Names of the top-level structs and enums, with their number of generic parameters, and
    {trait name: [associated type names]}."""
    types, traits = {}, {}
    for d in F.decls:
        if d.kind in ("struct", "enum") and d.name:
            types[d.name] = len(d.clause.params) if d.clause else 0
        if d.kind == "trait" and d.name:
            traits[d.name] = [m.name for m in (d.members or [])
                              if m.kind == "type" and m.name and F.toks[m.t1 - 1].text == m.name]
    return types, traits


def head_end(F, d):
    return d.body[0] if d.body else d.t1


def clause_site(F, d):
    """Token index before which a new clause `<...>` goes, and the text to add after it."""
    k = d.intro + 1
    if d.kind == "fun":
        if d.name_tok is None: return None
        k = d.name_tok + 1
        if k < d.t1 and F.toks[k].text == "[": return None
        return k, "", False
    if d.kind == "given":
        if k < d.t1 and F.toks[k].text in ("let", "var", "inout", "sink", "set"): return None
        if d.name_tok is not None: k = d.name_tok + 2
        # A conformance needs `is`; a given binding (`given T = e`) is left alone.
        if not any(t.kind == "name" and t.text == "is" for t in F.toks[k:head_end(F, d)]): return None
        return k, " =>", True
    if d.kind == "extension":
        # `extension T: P { }` is sugar that admits no clause.
        if any(t.text == ":" for t in F.toks[k:head_end(F, d)]): return None
        return k, "", True
    return None


def add_requirement(F, d, req, first):
    """An edit adding the requirement text `req` to `d`, or None."""
    c = d.clause
    if c is not None:
        if c.where is not None and c.reqs:
            if first: return (F.toks[c.where].end, F.toks[c.where].end, " " + req + ",")
            e = F.toks[c.reqs[-1][1] - 1].end
            return (e, e, ", " + req)
        if c.where is not None: return None
        e = F.toks[c.gt].start
        return (e, e, " where " + req)
    site = clause_site(F, d)
    if site is None: return None
    k, after, space = site
    if k >= d.t1: return None
    p = F.toks[k].start
    if space or F.src[F.toks[k - 1].end:p] != "":
        return (p, p, "<where " + req + ">" + after + " ")
    return (p, p, "<where " + req + ">" + after)


def candidates(F, d, types, traits):
    """[(kind, type expression text)] of the types for which a tautology is added."""
    out, c = [], d.clause
    params = []
    if c is not None:
        for a, b in c.params:
            if F.toks[a].kind == "name" and not any(F.toks[k].text == ":" for k in range(a, b)):
                params.append(F.toks[a].text)
                out.append(("taut-param", F.toks[a].text))
        # Conformance requirements `T is P`, inline or after `where`.
        for a, b in list(c.params) + list(c.reqs):
            for k in range(a + 1, b):
                if F.toks[k].kind == "name" and F.toks[k].text == "is":
                    lhs = F.text(a, k)
                    for j in range(k + 1, b):
                        if F.toks[j].kind == "name" and F.toks[j].text in traits and F.toks[j - 1].text in ("is", "&"):
                            for x in traits[F.toks[j].text]:
                                out.append(("taut-assoc", "%s.%s" % (lhs, x)))
                    break
    # Type applications and ground structs in the head.
    he = head_end(F, d)
    k = d.intro + 1
    while k < he:
        t = F.toks[k]
        if t.kind == "name" and t.text in types and F.toks[k - 1].text != ".":
            if types[t.text] > 0 and k + 1 < he and F.toks[k + 1].text == "<":
                g = match_angle(F.toks, k + 1, he)
                if g is not None:
                    txt = F.text(k, g + 1)
                    if "_" not in [x.text for x in F.toks[k:g + 1]]: out.append(("taut-app", txt))
            elif types[t.text] == 0:
                out.append(("taut-ground", t.text))
        k += 1
    seen, uniq = set(), []
    for x in out:
        if x not in seen: seen.add(x); uniq.append(x)
    return uniq


def variants(F, rng):
    types, traits = file_types(F)
    out = []
    for di, d in enumerate(F.all_decls()):
        if d.kind not in ("fun", "given", "extension"): continue
        if d.clause is None and clause_site(F, d) is None: continue
        label = "%s %s" % (d.kind, d.name or F.text(d.intro + 1, min(d.intro + 6, head_end(F, d))))
        for ci, (kind, ty) in enumerate(candidates(F, d, types, traits)):
            for first in (False, True):
                e = add_requirement(F, d, "%s == %s" % (ty, ty), first)
                if e is None: continue
                if first and (d.clause is None or not d.clause.reqs): continue
                out.append(Variant("%s:%d:%d:%s" % (kind, di, ci, "first" if first else "last"),
                                   "`%s == %s` added %s to `%s`" % (ty, ty, "first" if first else "last", label),
                                   repl=F.edited_pieces([e]), kind=kind))
        c = d.clause
        if c is not None and c.params and (d.kind in ("given", "extension") or not explicitly_applied(F, d)):
            z = fresh(F, "Zq")
            e = F.toks[c.params[-1][1] - 1].end
            out.append(Variant("unused-param:%d" % di, "unused generic parameter %s added to `%s`" % (z, label),
                               repl=F.edited_pieces([(e, e, ", " + z)]), kind="unused-param"))
    rng.shuffle(out)
    last = [v for v in out if not v.vid.endswith(":first")]
    return by_kind(last, ["taut-assoc", "taut-app", "taut-param", "unused-param", "taut-ground"]) \
        + by_kind([v for v in out if v.vid.endswith(":first")])
