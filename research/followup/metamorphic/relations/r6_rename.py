"""Relation 6: consistently renaming a declaration does not change the verdict.

Every identifier token with the old name is replaced, so the result is alpha-equivalent as long
as the new name is fresh and the old name does not also denote something of the standard library
(names that the standard library declares, selects as a member or uses as a label are never
renamed; neither are `main`, `Self` and the like).

Kinds of variants:
- one:     one declared name (type, trait, alias, associated type, function, named given or
           generic parameter) gets the prefix `Zq`;
- all:     every such name gets the prefix `Zq` (the relative alphabetical order is kept);
- reverse: every such name gets a new name such that the alphabetical order of the names is
           reversed, which would expose a dependence on the order of names."""
from common import Variant, stdlib_names


def declared_names(F):
    names = []
    for d in F.all_decls():
        if d.name and d.kind in ("struct", "enum", "trait", "type", "fun", "given"): names.append(d.name)
        if d.clause:
            for a, b in d.clause.params:
                if F.toks[a].kind == "name": names.append(F.toks[a].text)
    std = stdlib_names()
    used = {t.text for t in F.toks}
    out = []
    for n in names:
        if n in std or n in out or n.startswith("`") or n == "_": continue
        if "Zq" + n in used: continue
        out.append(n)
    return out


def variants(F, rng):
    names = declared_names(F)
    if not names: return []
    out = []
    pick = list(names); rng.shuffle(pick)
    ones = [Variant("one:" + n, "%s renamed Zq%s" % (n, n), rename={n: "Zq" + n}, kind="one") for n in pick[:6]]
    if len(names) > 1:
        out.append(Variant("all", "every declared name gets the prefix Zq",
                           rename={n: "Zq" + n for n in names}, kind="all"))
        srt = sorted(names)
        # Upper-case initial for names that had one (type names), lower-case otherwise.
        m = {}
        for i, n in enumerate(srt):
            tag = "%03d" % (len(srt) - 1 - i)
            m[n] = ("Rq" if n[0].isupper() else "rq") + tag + n
        out.append(Variant("reverse", "every declared name renamed so that alphabetical order is reversed",
                           rename=m, kind="reverse"))
    return out[::-1] + ones
