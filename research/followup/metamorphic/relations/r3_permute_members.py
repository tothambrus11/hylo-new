"""Relation 3: the order of the members of a struct, enum, trait, extension or conformance body
does not matter.

Stored properties keep their relative order (it determines the memberwise initializer), and so do
enum cases; every other member moves freely."""
from common import Variant, round_robin

FIXED = ("let", "var", "inout", "sink", "set", "case")


def member_texts(F, d):
    lb, rb = d.body
    texts, prev = [], F.toks[lb].end
    for m in d.members:
        e = F.toks[m.t1 - 1].end
        # Keep a comment that follows the member on its line.
        nl = F.src.find("\n", e)
        tail = F.src[e:nl] if nl >= 0 else ""
        if tail.strip().startswith("//") and nl <= F.toks[rb].start: e = nl
        t = F.src[prev:e]
        lines = [l for l in t.split("\n")]
        while lines and lines[0].strip() in ("", ";"): lines.pop(0)
        t = "\n".join(lines).strip()
        if t.startswith(";"): t = t[1:].strip()
        texts.append(t); prev = e
    return texts


def variants(F, rng):
    groups = []
    for di, d in enumerate(F.all_decls()):
        out = []; groups.append(out)
        if not d.members or len(d.members) < 2 or d.body is None: continue
        texts = member_texts(F, d)
        fixed = [i for i, m in enumerate(d.members) if m.kind in FIXED and "static" not in [t.text for t in F.toks[m.t0:m.intro]]]
        n = len(texts)
        perms = [list(reversed(range(n)))]
        for _ in range(2):
            p = list(range(n)); rng.shuffle(p); perms.append(p)
        seen = set()
        for p in perms:
            # Put the order-sensitive members back in their original relative order.
            slots = [k for k, i in enumerate(p) if i in fixed]
            q = list(p)
            for k, i in zip(slots, fixed): q[k] = i
            if q == list(range(n)) or tuple(q) in seen: continue
            seen.add(tuple(q))
            lb, rb = d.body
            line_start = F.src.rfind("\n", 0, F.toks[d.t0].start) + 1
            ind = F.src[line_start:F.toks[d.t0].start]
            ind = ind if not ind.strip() else ""
            body = "{\n" + "".join(ind + "  " + texts[i] + "\n" for i in q) + ind + "}"
            label = "%s %s" % (d.kind, d.name or F.text(d.intro + 1, min(d.intro + 5, lb)))
            out.append(Variant("members:%d:%s" % (di, ",".join(map(str, q))), "members of `%s` in order %s" % (label, q),
                               repl=F.edited_pieces([(F.toks[lb].start, F.toks[rb].end, body)]), kind="members"))
    rng.shuffle(groups)
    return round_robin(groups)
