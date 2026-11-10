"""Mutation operators for Hylo sources.

Every operator works on the text of one file and yields *sites*: a character range and its replacement.
The operators are syntactic (no type information), so some mutants are equivalent (still accepted)
and a few are syntactically invalid; the runner classifies them from the checker's output.

Operators:
  del-given        delete a conformance declaration: a `given` declaration, one entry of a
                   `struct S is P & Q` list, or a `trait T refines U` clause
  del-where-req    delete one requirement of a generic clause (equalities, and conformance
                   requirements of declarations without a body)
  del-bound        delete a `T is P` requirement (in a where clause or as an inline bound `<T is P>`)
                   of a declaration that has a non-empty body
  repl-typearg     replace a type argument (`f<A>()`, `Box<A>`) or a type of a function signature
                   by another type in scope
  del-ext-member   delete one member of an extension or of a conformance declaration
  del-type-member  delete one member of a struct, enum or trait body
  swap-args        swap two arguments of a call
"""
import re

OPERATORS = ["del-given", "del-where-req", "del-bound", "repl-typearg", "del-ext-member",
             "del-type-member", "swap-args"]

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
MODS = r"(?:public|module|private|internal|static|sink|inout)"
BUILTIN_TYPES = ["Void", "Int", "Bool"]


def mask(text):
    """Returns `text` with comments and string literals replaced by spaces (same length)."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j): out[k] = " "
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n": out[k] = " "
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            for k in range(i + 1, min(j, n)): out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


OPEN = {"(": ")", "{": "}", "[": "]"}
CLOSE = {")", "}", "]"}


def match_close(code, i):
    """Index of the bracket closing the one at `i` (for (), {} and []), or None."""
    depth = 0
    for j in range(i, len(code)):
        c = code[j]
        if c in OPEN: depth += 1
        elif c in CLOSE:
            depth -= 1
            if depth == 0: return j
    return None


ANGLE_OK = re.compile(r"[A-Za-z0-9_ ,.:&{}()\[\]<>=\-\n]")


def match_angle(code, i):
    """If `code[i]` is `<` opening a generic list, the index of its closing `>`; otherwise None."""
    n = len(code)
    if code[i] != "<" or i + 1 >= n: return None
    nxt = code[i + 1]
    if not (nxt.isalpha() or nxt in "_{[("): return None
    # An operator name such as `infix<` or a comparison is not a generic list.
    k = i
    while k > 0 and code[k - 1] in "<>=!+-*/%&|^~": k -= 1
    if re.search(r"(?:infix|prefix|postfix)$", code[:k]): return None
    prev = code[i - 1] if i > 0 else " "
    if not (prev.isalnum() or prev in "_ ."): return None
    if prev == " ":
        # `given <T> => ...`, `extension <T> ...`, `given name: <T> => ...`
        if not re.search(r"(?:\bgiven|\bextension|\bgiven\s+" + IDENT + r"\s*:)\s*$", code[:i]): return None
    depth, other = 0, 0
    j = i
    while j < n:
        c = code[j]
        if not ANGLE_OK.match(c): return None
        if c == "<": depth += 1
        elif c == ">":
            if code[j - 1] in "-=":      # `->` or `=>`
                j += 1; continue
            depth -= 1
            if depth == 0: return j if other == 0 else None
        elif c in OPEN: other += 1
        elif c in CLOSE:
            other -= 1
            if other < 0: return None
        j += 1
    return None


def split_top(code, lo, hi, seps=(",",)):
    """Splits code[lo:hi] at top-level separators; returns a list of (start, end) ranges."""
    parts, depth, start, j = [], 0, lo, lo
    while j < hi:
        c = code[j]
        if c in OPEN: depth += 1
        elif c in CLOSE: depth -= 1
        elif c == "<":
            m = match_angle(code, j)
            if m is not None and m < hi:
                j = m + 1; continue
        elif depth == 0 and c in seps:
            parts.append((start, j)); start = j + 1
        j += 1
    parts.append((start, hi))
    return parts


def trim(code, a, b):
    while a < b and code[a].isspace(): a += 1
    while b > a and code[b - 1].isspace(): b -= 1
    return a, b


class Angle:
    """A generic list: either the parameters of a declaration or the arguments of an application."""
    def __init__(self, code, lo, hi):
        self.lo, self.hi = lo, hi                # positions of `<` and `>`
        before = code[:lo]
        m = re.search(r"(\b" + IDENT + r")?$", before)
        ident = m.group(1) if m else None
        self.is_params = False
        self.kind = None
        if ident is None:
            self.is_params = True                # after `given ` or `extension `
            self.kind = "extension" if re.search(r"\bextension\s*$", before) else "given"
        elif ident in ("init", "subscript"):
            self.is_params = True; self.kind = ident
        else:
            m2 = re.search(r"\b(fun|struct|enum|trait|type|typealias|subscript|property)\s+" + re.escape(ident) + r"$", before)
            if m2:
                self.is_params = True; self.kind = m2.group(1)
            elif re.search(r"\bfun\s+(?:infix|prefix|postfix)\S*\s*$", before):
                self.is_params = True; self.kind = "fun"
        self.params, self.reqs = [], []          # ranges
        self.where = None                        # range of the keyword `where` (with leading space)
        self.elements = []
        inner_lo, inner_hi = lo + 1, hi
        if self.is_params:
            m = None
            # top-level `where`
            depth = 0
            j = inner_lo
            wpos = None
            while j < inner_hi:
                c = code[j]
                if c in OPEN or c == "<": depth += 1
                elif c in CLOSE: depth -= 1
                elif c == ">" and code[j - 1] not in "-=": depth -= 1
                elif depth == 0 and code.startswith("where", j) and not (code[j - 1].isalnum() or code[j - 1] == "_") \
                        and not (code[j + 5].isalnum() or code[j + 5] == "_"):
                    wpos = j; break
                j += 1
            if wpos is None:
                plo, phi = inner_lo, inner_hi
            else:
                plo, phi = inner_lo, wpos
                self.where = (wpos, wpos + 5)
                self.reqs = [trim(code, a, b) for a, b in split_top(code, wpos + 5, inner_hi)]
                self.reqs = [r for r in self.reqs if r[0] < r[1]]
            self.params = [trim(code, a, b) for a, b in split_top(code, plo, phi)]
            self.params = [r for r in self.params if r[0] < r[1]]
        else:
            self.elements = [trim(code, a, b) for a, b in split_top(code, inner_lo, inner_hi)]
            self.elements = [r for r in self.elements if r[0] < r[1]]


def find_angles(code):
    out = []
    i = 0
    n = len(code)
    while i < n:
        if code[i] == "<":
            j = match_angle(code, i)
            if j is not None:
                out.append(Angle(code, i, j))
        i += 1
    return out


DECL_START = re.compile(r"\s*(?:@|\b(?:fun|given|struct|trait|extension|public|module|private|internal|type|static|init|let|var|enum|typealias|subscript|property|memberwise|case|namespace|import)\b|\})")


def body_after(code, pos):
    """The range (open, close) of the brace body of the declaration whose head ends at `pos`, or None."""
    n = len(code)
    j = pos
    depth = 0
    while j < n:
        c = code[j]
        if c == "{" and depth == 0:
            # A `{` directly after `:` or `->` or `(` is a tuple type, not a body.
            k = j - 1
            while k >= 0 and code[k] == " ": k -= 1
            if code[k] in ":,(<" or code[k - 1:k + 1] == "->" or code[k - 1:k + 1] == "=>" or code[k - 1:k + 1] == "==":
                m = match_close(code, j)
                if m is None: return None
                j = m + 1; continue
            m = match_close(code, j)
            return (j, m) if m is not None else None
        if c in "([": depth += 1
        elif c in ")]":
            depth -= 1
            if depth < 0: return None
        elif c == "}":
            return None
        elif c == "\n" and depth == 0 and DECL_START.match(code, j + 1):
            return None
        j += 1
    return None


def decl_scope(code, angle):
    """Extent over which the parameters of `angle` are in scope."""
    b = body_after(code, angle.hi + 1)
    if b: return (angle.lo, b[1] + 1)
    e = code.find("\n", angle.hi)
    return (angle.lo, len(code) if e < 0 else e)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def site(text, op, variant, a, b, repl, note=None):
    return {"op": op, "variant": variant, "start": a, "end": b, "repl": repl,
            "line": line_of(text, a), "orig": text[a:b][:120], "note": note}


def remove_list_item(code, items, k, lo_bound, hi_bound):
    """Range that removes items[k] and one adjacent comma from a comma-separated list."""
    a, b = items[k]
    if k + 1 < len(items):
        return a, items[k + 1][0]
    if k > 0:
        return items[k - 1][1], b
    return a, b


def is_conformance_req(code, r):
    s = code[r[0]:r[1]]
    return re.search(r"\sis\s", s) is not None and "==" not in s


def requirement_sites(text, code, angles):
    """Sites of del-where-req and del-bound."""
    out = []
    for A in angles:
        if not A.is_params: continue
        body = body_after(code, A.hi + 1)
        has_body = bool(body) and code[body[0] + 1:body[1]].strip() != ""
        # where-clause requirements
        for k, r in enumerate(A.reqs):
            conf = is_conformance_req(code, r)
            if len(A.reqs) > 1:
                a, b = remove_list_item(code, A.reqs, k, None, None)
                repl = ""
            elif A.params:
                # `<T where R>` -> `<T>`
                a, b = A.where[0], A.hi
                while a > A.lo + 1 and code[a - 1] == " ": a -= 1
                repl = ""
            else:
                # `<where R>` -> nothing; a following `=>` goes too
                a, b = A.lo, A.hi + 1
                m = re.match(r"\s*=>\s*", code[b:])
                if m: b += m.end()
                repl = ""
            op = "del-bound" if (conf and has_body) else "del-where-req"
            variant = ("where-is" if conf else "where-eq") + ("" if has_body else "-nobody")
            out.append(site(text, op, variant, a, b, repl, note=text[r[0]:r[1]]))
        # inline bounds `<T is P>`
        for p in A.params:
            s = code[p[0]:p[1]]
            m = re.match(r"(" + IDENT + r")(\s+is\s+.+)$", s, re.S)
            if not m: continue
            a = p[0] + m.start(2); b = p[1]
            op = "del-bound" if has_body else "del-where-req"
            out.append(site(text, op, "inline-is" + ("" if has_body else "-nobody"), a, b, "", note=s))
    return out


def given_sites(text, code):
    out = []
    # `given` declarations
    for m in re.finditer(r"(?:(?:public|module|private|internal)\s+)?\bgiven\b", code):
        j = m.end()
        end = None
        depth = 0
        hs = m.end()
        while j < len(code):
            c = code[j]
            if c == "<":
                k = match_angle(code, j)
                if k is not None:
                    if code[m.end():j].strip() == "" or re.match(r"\s*" + IDENT + r"\s*:\s*$", code[m.end():j]): hs = k + 1
                    j = k + 1; continue
            if c == "{":
                # tuple type in the head (`given {Void, Void} is P {`): not preceded by ` is X `
                head = code[hs:j]
                if not re.search(r"\sis\s", head):
                    k = match_close(code, j)
                    if k is None: break
                    j = k + 1; continue
                k = match_close(code, j)
                end = None if k is None else k + 1
                break
            if c == "}" or c == "\n":
                end = j
                while end > m.end() and code[end - 1] == " ": end -= 1
                break
            j += 1
        if end is None: continue
        head = code[hs:end]
        if not re.search(r"\sis\s", head): continue
        out.append(site(text, "del-given", "given", m.start(), end, "", note=text[m.start():end].split("{")[0].strip()[:100]))
    # conformance lists of type declarations, and trait refinements
    for m in re.finditer(r"\b(struct|enum)\s+" + IDENT, code):
        j = m.end()
        if j < len(code) and code[j] == "<":
            k = match_angle(code, j)
            if k is None: continue
            j = k + 1
        m2 = re.match(r"(\s+is\s+)([^{\n]+?)\s*\{", code[j:])
        if not m2: continue
        lo = j + m2.start(2); hi = j + m2.end(2)
        items = [trim(code, a, b) for a, b in split_top(code, lo, hi, seps=("&",))]
        for k, it in enumerate(items):
            if len(items) == 1:
                a, b = j, hi
            elif k + 1 < len(items):
                a, b = it[0], items[k + 1][0]
            else:
                a, b = items[k - 1][1], it[1]
            out.append(site(text, "del-given", "header", a, b, "", note=m.group(0) + " is " + text[it[0]:it[1]]))
    for m in re.finditer(r"\btrait\s+" + IDENT + r"(\s+refines\s+)([^{\n]+?)\s*\{", code):
        lo, hi = m.start(2), m.end(2)
        items = [trim(code, a, b) for a, b in split_top(code, lo, hi, seps=("&", ","))]
        for k, it in enumerate(items):
            if len(items) == 1:
                a, b = m.start(1), hi
            elif k + 1 < len(items):
                a, b = it[0], items[k + 1][0]
            else:
                a, b = items[k - 1][1], it[1]
            out.append(site(text, "del-given", "refines", a, b, "", note=text[m.start():m.end(2)]))
    return out


MEMBER_INTRO = re.compile(r"\b(fun|type|subscript|property|init|var|let|given|struct|enum|trait|typealias|memberwise|case)\b")
MEMBER_PREFIX = re.compile(r"(?:(?:@" + IDENT + r"(?:\([^)\n]*\))?|public|module|private|internal|static)\s+)+$")


def members(code, lo, hi):
    """Ranges of the member declarations in the body code[lo:hi] (lo/hi exclude the braces)."""
    starts = []
    depth = 0
    j = lo
    skip_until = lo
    while j < hi:
        c = code[j]
        if c in OPEN: depth += 1
        elif c in CLOSE: depth -= 1
        elif depth == 0 and j >= skip_until and (c.isalpha()) and not (code[j - 1].isalnum() or code[j - 1] in "_.@"):
            m = MEMBER_INTRO.match(code, j)
            if m:
                kw = m.group(1)
                start = j
                p = MEMBER_PREFIX.search(code[lo:j])
                if p: start = lo + p.start()
                starts.append((start, j, kw))
                skip_until = m.end()
                if kw == "memberwise":
                    m2 = re.match(r"\s+init\b", code[m.end():])
                    if m2: skip_until = m.end() + m2.end()
                # a declaration's own head may contain keywords (`type X = ...`); skip to end of line or body
                j = skip_until
                # skip the rest of the head until `{` at depth 0 or newline
                d2 = 0
                while j < hi:
                    c2 = code[j]
                    if c2 in "([": d2 += 1
                    elif c2 in ")]": d2 -= 1
                    elif c2 == "<":
                        k = match_angle(code, j)
                        if k is not None and k < hi: j = k + 1; continue
                    elif c2 == "{" and d2 == 0:
                        k = j - 1
                        while k >= 0 and code[k] == " ": k -= 1
                        if code[k] in ":,(<=" or code[k - 1:k + 1] == "->":
                            k2 = match_close(code, j)
                            if k2 is None: break
                            j = k2 + 1; continue
                        k2 = match_close(code, j)
                        if k2 is not None: j = k2 + 1
                        break
                    elif c2 == "\n" and d2 == 0:
                        break
                    elif c2 == "}" and d2 == 0:
                        break
                    j += 1
                starts[-1] = (start, j, kw)
                continue
        j += 1
    out = []
    for (start, end, kw) in starts:
        a, b = trim(code, start, min(end, hi))
        if a < b: out.append((a, b, kw))
    return out


def member_sites(text, code):
    out = []
    for m in re.finditer(r"\b(extension|given|struct|enum|trait)\b", code):
        kind = m.group(1)
        # locate the body
        j = m.end()
        body = None
        hs = m.end()
        while j < len(code):
            c = code[j]
            if c == "<":
                k = match_angle(code, j)
                if k is not None:
                    if code[m.end():j].strip() == "" or re.match(r"\s*" + IDENT + r"\s*:\s*$", code[m.end():j]): hs = k + 1
                    j = k + 1; continue
            if c == "{":
                head = code[hs:j]
                if kind == "given" and not re.search(r"\sis\s", head) or (kind == "extension" and head.strip() == "") \
                        or re.search(r"[,&]\s*$", head):
                    k = match_close(code, j)
                    if k is None: break
                    j = k + 1; continue
                k = match_close(code, j)
                if k is not None: body = (j, k)
                break
            if c == "}" or (c == "\n" and DECL_START.match(code, j + 1)):
                break
            j += 1
        if not body: continue
        for (a, b, kw) in members(code, body[0] + 1, body[1]):
            if kind in ("extension", "given"):
                op, variant = "del-ext-member", kind
            else:
                op, variant = "del-type-member", kind
            if kw in ("given", "struct", "enum", "trait"): continue   # nested declarations: other operators
            out.append(site(text, op, variant + ":" + kw, a, b, "", note=text[a:b].split("\n")[0][:100]))
    return out


def type_pool(code, extra):
    pool = []
    for m in re.finditer(r"^(?:public\s+)?(?:struct|enum)\s+(" + IDENT + r")\s*(<)?", code, re.M):
        if not m.group(2): pool.append(m.group(1))
    for t in extra:
        if t not in pool: pool.append(t)
    return pool


def typearg_sites(text, code, angles, rng, extra_types):
    out = []
    pool = type_pool(code, extra_types)
    scopes = []
    for A in angles:
        if A.is_params:
            names = []
            for p in A.params:
                m = re.match(IDENT, code[p[0]:p[1]])
                if m: names.append(m.group(0))
            scopes.append((decl_scope(code, A), names))

    def in_scope(pos):
        names = list(pool)
        for (lo, hi), ns in scopes:
            if lo <= pos < hi:
                for x in ns:
                    if x not in names: names.append(x)
        return names

    def pick(pos, orig):
        cands = [t for t in in_scope(pos) if t != orig.strip()]
        return rng.choice(cands) if cands else None

    for A in angles:
        if A.is_params: continue
        for e in A.elements:
            orig = text[e[0]:e[1]]
            r = pick(e[0], orig)
            if r is None: continue
            out.append(site(text, "repl-typearg", "typearg", e[0], e[1], r, note=text[max(0, A.lo - 12):A.hi + 1].replace("\n", " ")))
    # types in function signatures
    for m in re.finditer(r"\b(?:fun\s+(?:(?:infix|prefix|postfix)[^\s(A-Za-z0-9_]+|" + IDENT + r")|init)\s*", code):
        if code[m.start():m.end()].startswith("init") and re.search(r"memberwise\s+$", code[:m.start()]): continue
        j = m.end()
        if j < len(code) and code[j] == "<":
            k = match_angle(code, j)
            if k is None: continue
            j = k + 1
        if j >= len(code) or code[j] != "(": continue
        k = match_close(code, j)
        if k is None: continue
        for (a, b) in split_top(code, j + 1, k):
            s = code[a:b]
            mm = re.match(r"(\s*(?:" + IDENT + r"\s+)?" + IDENT + r"\s*:\s*(?:(?:sink|inout|let|set|lazy)\s+)?)(\S.*?)\s*$", s, re.S)
            if not mm: continue
            ta, tb = a + mm.start(2), a + mm.end(2)
            r = pick(ta, text[ta:tb])
            if r is None: continue
            out.append(site(text, "repl-typearg", "sigtype:param", ta, tb, r, note=text[m.start():k + 1].replace("\n", " ")[:100]))
        mm = re.match(r"\s*(?:(?:sink|inout|let|set|auto)\s+)?->\s*([^{\n]+?)\s*(?=\{|\n|$)", code[k + 1:])
        if mm:
            ta, tb = k + 1 + mm.start(1), k + 1 + mm.end(1)
            r = pick(ta, text[ta:tb])
            if r is not None:
                out.append(site(text, "repl-typearg", "sigtype:result", ta, tb, r, note=text[m.start():tb].replace("\n", " ")[:100]))
    return out


def swap_sites(text, code, rng):
    out = []
    for m in re.finditer(r"\(", code):
        j = m.start()
        if j == 0: continue
        prev = code[j - 1]
        if not (prev.isalnum() or prev in "_>)"): continue
        # find the head of the callee
        k = j
        if prev == ">":
            # skip a generic argument list backwards
            depth = 0
            while k > 0:
                k -= 1
                if code[k] == ">": depth += 1
                elif code[k] == "<":
                    depth -= 1
                    if depth == 0: break
            if k == 0: continue
        mm = re.search(r"(" + IDENT + r")$", code[:k])
        ident = mm.group(1) if mm else None
        if ident in ("init", "subscript", "fun", "if", "while", "for", "match", "return", "memberwise", "case", "inline", "where"):
            continue
        if ident and re.search(r"(?:\b(?:fun|subscript|case|property|struct|enum|trait|type)\s+|@)" + re.escape(ident) + r"$", code[:k]):
            continue
        if re.search(r"(?:infix|prefix|postfix)[^\s(]*\s*$", code[:j]): continue
        e = match_close(code, j)
        if e is None: continue
        args = [trim(code, a, b) for a, b in split_top(code, j + 1, e)]
        args = [a for a in args if a[0] < a[1]]
        if len(args) < 2: continue
        vals = []
        for (a, b) in args:
            lm = re.match(r"(" + IDENT + r")\s*:\s*(?!:)", code[a:b])
            va = a + lm.end() if lm else a
            vals.append((va, b))
        pairs = [(x, y) for x in range(len(vals)) for y in range(x + 1, len(vals))
                 if text[vals[x][0]:vals[x][1]] != text[vals[y][0]:vals[y][1]]]
        if not pairs: continue
        x, y = rng.choice(pairs)
        (a1, b1), (a2, b2) = vals[x], vals[y]
        repl = text[a2:b2] + text[b1:a2] + text[a1:b1]
        out.append(site(text, "swap-args", "call", a1, b2, repl, note=text[max(0, j - 20):e + 1].replace("\n", " ")[:120]))
    return out


def all_sites(text, rng, extra_types=BUILTIN_TYPES):
    code = mask(text)
    angles = find_angles(code)
    out = []
    out += given_sites(text, code)
    out += requirement_sites(text, code, angles)
    out += typearg_sites(text, code, angles, rng, extra_types)
    out += member_sites(text, code)
    out += swap_sites(text, code, rng)
    # drop duplicates (same resulting text)
    seen, uniq = set(), []
    for s in out:
        key = (s["start"], s["end"], s["repl"])
        if key in seen: continue
        seen.add(key); uniq.append(s)
    return uniq


def apply(text, s):
    return text[:s["start"]] + s["repl"] + text[s["end"]:]


if __name__ == "__main__":
    import random, sys
    text = open(sys.argv[1]).read()
    for s in all_sites(text, random.Random(1)):
        print(f'{s["op"]:16} {s["variant"]:18} L{s["line"]:<4} [{s["orig"]!r}] -> [{s["repl"]!r}]   // {s["note"]}')
