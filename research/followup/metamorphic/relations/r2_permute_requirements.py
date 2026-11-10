"""Relation 2: the order of the requirements of a where clause does not matter, and neither does
the order or the naming of generic parameters where no use site depends on it.

Kinds of variants:
- reqs: the requirements after `where` are reversed, rotated or shuffled;
- reqs-dep: a reordering that keeps every requirement that mentions a projection (`T.X`) after
  the requirements that preceded it: the requirements without a projection come first, in
  reverse order, and the others follow in their original order. (The checker reads a where
  clause from left to right and rejects `T.X` before `T is P`; this kind looks past that rule.)
- params: the generic parameters are listed in another order. Only for conformances (`given`),
  extensions, and functions that are never applied to explicit type arguments in the file, where
  the order of the parameters is unobservable;
- swap-names: two generic parameters exchange their names throughout the declaration (a pure
  alpha-renaming; the positions of the parameters do not change)."""
from common import Variant, by_kind


def explicitly_applied(F, d):
    """True iff the function `d` may be applied to explicit type arguments somewhere."""
    if d.name is None: return True
    for i, t in enumerate(F.toks):
        if t.kind == "name" and t.text == d.name and i != d.name_tok:
            if i + 1 < len(F.toks) and F.toks[i + 1].text == "<": return True
    return False


def reorder(F, parts, perm):
    """An edit replacing the comma-separated `parts` by their permutation."""
    texts = [F.text(a, b) for a, b in parts]
    s, e = F.toks[parts[0][0]].start, F.toks[parts[-1][1] - 1].end
    return (s, e, ", ".join(texts[i] for i in perm))


def perms_of(n, rng, limit=3):
    out = [list(reversed(range(n)))]
    if n > 2:
        out.append(list(range(1, n)) + [0])
        p = list(range(n)); rng.shuffle(p)
        if p not in out and p != list(range(n)): out.append(p)
    return out[:limit]


def variants(F, rng):
    out = []
    for di, d in enumerate(F.all_decls()):
        c = d.clause
        if c is None: continue
        label = "%s %s" % (d.kind, d.name or F.text(d.intro, min(d.intro + 6, d.t1)))
        if len(c.reqs) >= 2:
            for p in perms_of(len(c.reqs), rng):
                out.append(Variant("reqs:%d:%s" % (di, "".join(map(str, p))), "requirements of `%s` in order %s" % (label, p),
                                   repl=F.edited_pieces([reorder(F, c.reqs, p)]), kind="reqs"))
            plain = [i for i, (a, b) in enumerate(c.reqs) if not any(F.toks[k].text == "." for k in range(a, b))]
            proj = [i for i in range(len(c.reqs)) if i not in plain]
            p = plain[::-1] + proj
            if p != list(range(len(c.reqs))):
                out.append(Variant("reqs-dep:%d:%s" % (di, "".join(map(str, p))), "requirements of `%s` in order %s" % (label, p),
                                   repl=F.edited_pieces([reorder(F, c.reqs, p)]), kind="reqs-dep"))
        if len(c.params) >= 2:
            ok = d.kind in ("given", "extension") or (d.kind == "fun" and not explicitly_applied(F, d))
            if ok:
                for p in perms_of(len(c.params), rng, 2):
                    out.append(Variant("params:%d:%s" % (di, "".join(map(str, p))), "generic parameters of `%s` in order %s" % (label, p),
                                       repl=F.edited_pieces([reorder(F, c.params, p)]), kind="params"))
            # Exchange the names of the first two parameters throughout the declaration.
            a, b = F.toks[c.params[0][0]].text, F.toks[c.params[1][0]].text
            if a != b and F.toks[c.params[0][0]].kind == "name" and F.toks[c.params[1][0]].kind == "name":
                edits = []
                for k in range(d.t0, d.t1):
                    t = F.toks[k]
                    if t.kind == "name" and t.text in (a, b) and F.toks[k - 1].text != ".":
                        edits.append((t.start, t.end, b if t.text == a else a))
                out.append(Variant("swap-names:%d" % di, "parameters %s and %s of `%s` exchange their names" % (a, b, label),
                                   repl=F.edited_pieces(edits), kind="swap-names"))
    return by_kind(out, ["reqs", "swap-names", "params", "reqs-dep"])
