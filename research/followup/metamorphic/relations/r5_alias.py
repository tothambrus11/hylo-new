"""Relation 5: a type alias is transparent. Naming a type expression with a new alias, or
replacing an alias by its definition, does not change the verdict.

Kinds of variants:
- intro-all:   every occurrence, in a type position, of a closed type expression (`A`, `Box<A>`,
               `A.Me`) is replaced by a new alias `type Alq = <expression>` declared at the end
               of the file (`intro-all-top`: at the beginning);
- intro-one:   only the first occurrence is replaced;
- intro-generic: `type Alq<T> = Box<T>` is declared and every application `Box<...>` in a type
               position is spelled `Alq<...>`;
- expand:      every use of a non-generic top-level alias is replaced by its definition; the alias
               declaration stays (`expand-drop`: it is removed).

A "type position" is recognised from the preceding token: after `:` in a declaration head,
`->`, `==`, `where`, `given`, `=>`, `extension`, `=` of an alias definition, `&`... and as an
argument between angle brackets. Occurrences in function bodies are only replaced between angle
brackets. A closed expression mentions no generic parameter of the file and no `Self`."""
from common import Variant, fresh, by_kind
from hylosyn import match_angle
from relations.r4_tautology import file_types


def generic_names(F):
    names = set()
    for d in F.all_decls():
        if d.clause:
            for a, b in d.clause.params: names.add(F.toks[a].text)
    return names


def body_ranges(F):
    """Token ranges of function bodies (where expressions, not types, are the rule)."""
    out = []
    for d in F.all_decls():
        if d.kind in ("fun", "subscript", "init") and d.body: out.append(d.body)
    return out


def angle_depth_map(F):
    """For each token, true iff it is directly inside a `<...>` argument or parameter list."""
    n = len(F.toks)
    inside = [False] * n
    k = 0
    while k < n:
        t = F.toks[k]
        if t.kind == "punct" and t.text == "<" and k and (F.toks[k - 1].kind == "name" or F.toks[k - 1].text in ("given", "extension", "init")):
            g = match_angle(F.toks, k, n)
            if g is not None:
                depth = 0
                for j in range(k + 1, g):
                    x = F.toks[j]
                    if x.kind == "punct" and x.text in "<([{": depth += 1
                    elif x.kind == "punct" and x.text in ">)]}": depth -= 1
                    elif depth == 0: inside[j] = True
                    if x.kind == "punct" and x.text == "<" and depth == 1: pass
        k += 1
    return inside


def type_position(F, k, bodies, inside):
    """True iff the expression starting at token `k` is in a type position."""
    prev = F.toks[k - 1] if k else None
    if prev is None: return False
    in_body = any(a < k < b for a, b in bodies)
    if prev.text == "<" or (prev.text == "," and inside[k]) :
        # An argument of a type application or of an explicit instantiation.
        return k >= 2 and (F.toks[k - 2].kind == "name" or prev.text == ",") and (inside[k] or prev.text == "<")
    if in_body: return False
    if prev.text in ("->", "==", "where", "given", "=>", "extension", "&"): return True
    if prev.kind == "name" and prev.text == "is": return False     # a trait, not a type
    if prev.text == "=":
        # The definition of an alias: `type X = ...`.
        j = k - 2
        while j >= 0 and F.toks[j].text not in ("type", "let", "var", "{", "}", ";", "("): j -= 1
        return j >= 0 and F.toks[j].text == "type"
    if prev.text == ":":
        # A parameter or binding annotation; not an argument label inside a call.
        return k >= 2 and F.toks[k - 2].kind == "name"
    if prev.text in ("let", "inout", "sink", "set") and k >= 2 and F.toks[k - 2].text == ":": return True
    return False


def closed_expressions(F, types, generics, bodies, inside):
    """{expression text: [(first token, one past last token)]} of the closed type expressions in
    type positions. An application or a member path is one expression."""
    occ = {}
    n = len(F.toks)
    k = 0
    while k < n:
        t = F.toks[k]
        if not (t.kind == "name" and t.text in types and (k == 0 or F.toks[k - 1].text != ".")):
            k += 1; continue
        # Extent: Name [<...>] (. Name [<...>])*
        e = k + 1
        ok = True
        if types[t.text] > 0:
            if e < n and F.toks[e].text == "<":
                g = match_angle(F.toks, e, n)
                if g is None: ok = False
                else: e = g + 1
            else: ok = False
        spans = [(k, e)] if ok else []
        while ok and e + 1 < n and F.toks[e].text == "." and F.toks[e + 1].kind == "name" \
                and not (e + 2 < n and F.toks[e + 2].text in ("(", "<")) and F.toks[e + 1].text[0].isupper():
            e += 2; spans.append((k, e))
        for a, b in spans:
            names = [x.text for x in F.toks[a:b] if x.kind in ("name", "kw")]
            if any(x in generics or x in ("Self", "_") for x in names): continue
            if any(x.kind not in ("name", "punct") or (x.kind == "punct" and x.text not in "<>,.") for x in F.toks[a:b]): continue
            if not type_position(F, a, bodies, inside): continue
            # The declared name of a struct is not a use.
            if F.toks[a - 1].text in ("struct", "enum", "trait", "type"): continue
            if b < n and F.toks[b].text == "(": continue                 # a constructor call
            occ.setdefault(F.text(a, b), []).append((a, b))
        k += 1
    return occ


def non_overlapping(spans):
    out, end = [], -1
    for a, b in sorted(spans):
        if a >= end: out.append((a, b)); end = b
    return out


def variants(F, rng):
    types, _ = file_types(F)
    generics = generic_names(F)
    bodies, inside = body_ranges(F), angle_depth_map(F)
    out = []
    occ = closed_expressions(F, types, generics, bodies, inside)
    # Prefer member paths and applications to plain names.
    exprs = sorted(occ, key=lambda e: (-(("." in e) + ("<" in e)), e))
    rng.shuffle(exprs)
    exprs.sort(key=lambda e: -(("." in e) + ("<" in e)))
    for ei, ex in enumerate(exprs[:3]):
        al = fresh(F, "Alq")
        decl = "type %s = %s" % (al, ex)
        spans = non_overlapping(occ[ex])
        edits = [(F.toks[a].start, F.toks[b - 1].end, al) for a, b in spans]
        out.append(Variant("intro-all:%d" % ei, "`%s` named %s everywhere (%d places), alias declared last" % (ex, al, len(spans)),
                           repl=F.edited_pieces(edits), post=[decl], kind="intro-all"))
        out.append(Variant("intro-all-top:%d" % ei, "`%s` named %s everywhere (%d places), alias declared first" % (ex, al, len(spans)),
                           repl=F.edited_pieces(edits), pre=[decl], kind="intro-all-top"))
        if len(spans) > 1:
            out.append(Variant("intro-one:%d" % ei, "first `%s` named %s, alias declared last" % (ex, al),
                               repl=F.edited_pieces(edits[:1]), post=[decl], kind="intro-one"))
    # A generic alias for a generic struct.
    gen = [n for n, k in sorted(types.items()) if k > 0]
    rng.shuffle(gen)
    for gi, g in enumerate(gen[:1]):
        spans = []
        for k, t in enumerate(F.toks):
            if t.kind == "name" and t.text == g and k + 1 < len(F.toks) and F.toks[k + 1].text == "<" \
                    and F.toks[k - 1].text not in (".", "struct", "enum") and type_position(F, k, bodies, inside):
                gt = match_angle(F.toks, k + 1, len(F.toks))
                if gt is not None and not (gt + 1 < len(F.toks) and F.toks[gt + 1].text == "("):
                    spans.append(k)
        if spans:
            al = fresh(F, "Alq" + g)
            ps = ["Tq%d" % i for i in range(types[g])]
            decl = "type %s<%s> = %s<%s>" % (al, ", ".join(ps), g, ", ".join(ps))
            edits = [(F.toks[k].start, F.toks[k].end, al) for k in spans]
            out.append(Variant("intro-generic:%d" % gi, "`%s<...>` spelled `%s<...>` (%d places), generic alias declared last" % (g, al, len(spans)),
                               repl=F.edited_pieces(edits), post=[decl], kind="intro-generic"))
    # Expansion of the existing non-generic top-level aliases.
    declared = {}
    for d in F.all_decls():
        if d.name: declared[d.name] = declared.get(d.name, 0) + 1
    xi = 0
    for pi, d in enumerate(F.decls):
        if d.kind != "type" or d.name is None or d.clause is not None: continue
        if declared.get(d.name) != 1 or d.name in generics: continue
        k = d.name_tok + 1
        if k >= d.t1 or F.toks[k].text != "=": continue
        body = F.toks[k + 1:d.t1]
        if not body or any(x.kind not in ("name", "punct") or (x.kind == "punct" and x.text not in "<>,.") for x in body): continue
        if d.name in [x.text for x in body]: continue          # a self-referential alias
        definition = F.text(k + 1, d.t1)
        uses = [j for j, t in enumerate(F.toks) if t.kind == "name" and t.text == d.name and j != d.name_tok
                and F.toks[j - 1].text != "." and not (j + 1 < len(F.toks) and F.toks[j + 1].text == ":")]
        if not uses: continue
        edits = [(F.toks[j].start, F.toks[j].end, definition) for j in uses]
        repl = F.edited_pieces(edits)
        out.append(Variant("expand:%d" % xi, "alias %s replaced by `%s` (%d places), declaration kept" % (d.name, definition, len(uses)),
                           repl=repl, kind="expand"))
        if pi not in repl:
            dropped = dict(repl); dropped[pi] = ""
            out.append(Variant("expand-drop:%d" % xi, "alias %s replaced by `%s` (%d places), declaration removed" % (d.name, definition, len(uses)),
                               repl=dropped, kind="expand-drop"))
        xi += 1
        if xi >= 3: break
    return by_kind(out, ["intro-all", "expand", "intro-generic", "intro-all-top", "expand-drop", "intro-one"])
