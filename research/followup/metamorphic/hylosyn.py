"""A small lexer and declaration-structure parser for Hylo, sufficient to split a file into
declarations, to find the members of a type body, and to find context clauses
(`<T, U where R1, R2>`). It never re-prints tokens: every transformation is expressed as edits of
the original text, so whitespace-sensitive syntax (operators) is preserved."""
import re

KEYWORDS = {"auto", "break", "case", "continue", "else", "enum", "extension", "false", "fun",
            "given", "if", "import", "infix", "init", "inout", "let", "match", "module",
            "postfix", "prefix", "public", "return", "set", "sink", "static", "struct",
            "subscript", "trait", "true", "type", "var", "where", "while", "yield"}
BINDING_INTRODUCERS = {"inout", "let", "set", "sink", "var"}
MODIFIERS = {"static", "module", "public"}
INTRODUCERS = {"case", "enum", "extension", "fun", "given", "import", "struct", "subscript",
               "trait", "type", "init"} | BINDING_INTRODUCERS
OPCHARS = "<>=+-*/%&|!?^~"
OPEN = {"(": ")", "[": "]", "{": "}"}
CLOSE = {")", "]", "}"}


class Tok:
    __slots__ = ("kind", "text", "start", "end", "nl")

    def __init__(self, kind, text, start, end, nl):
        self.kind, self.text, self.start, self.end, self.nl = kind, text, start, end, nl

    def __repr__(self):
        return "%s:%r" % (self.kind, self.text)


def lex(src):
    """Returns the significant tokens of `src`. `nl` is true iff a newline (or the start of the
    file) separates the token from the previous one. Kinds: name, kw, num, str, pound, op, punct."""
    toks, i, n, nl = [], 0, len(src), True
    while i < n:
        c = src[i]
        if c.isspace():
            if c == "\n": nl = True
            i += 1; continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j): depth += 1; j += 2
                elif src.startswith("*/", j): depth -= 1; j += 2
                else: j += 1
            if "\n" in src[i:j]: nl = True
            i = j; continue
        s = i
        if c.isdigit() or (c == "-" and i + 1 < n and src[i + 1].isdigit()):
            m = re.compile(r"-?(0x[0-9a-fA-F_]+|0o[0-7_]+|0b[01_]+|[0-9][0-9_]*(\.[0-9][0-9_]*)?([eE][+-]?[0-9][0-9_]*)?)").match(src, i)
            i = m.end(); kind = "num"
        elif c == '"':
            i += 1; esc = False
            while i < n:
                if not esc and src[i] == '"': i += 1; break
                if src[i] == "\\": esc = not esc
                else: esc = False
                i += 1
            kind = "str"
        elif c.isalpha() or c == "_":
            while i < n and (src[i].isalnum() or src[i] == "_"): i += 1
            w = src[s:i]
            if w == "as":
                if i < n and src[i] in "!*": i += 1
                kind = "op"
            else:
                kind = "kw" if w in KEYWORDS else "name"
        elif c == "`":
            j = src.find("`", i + 1)
            i = n if j < 0 else j + 1; kind = "name"
        elif c == "#":
            i += 1
            while i < n and (src[i].isalnum() or src[i] == "_"): i += 1
            kind = "pound"
        elif c in "<>":
            i += 1; kind = "punct"
        elif c == "*":
            i += 1; kind = "op"
        elif c in OPCHARS:
            while i < n and src[i] in OPCHARS: i += 1
            kind = "op"
        elif c == ":":
            i += 2 if src.startswith("::", i) else 1; kind = "punct"
        elif c == ".":
            i += 3 if src.startswith("...", i) else 1; kind = "punct"
        else:
            i += 1; kind = "punct"
        toks.append(Tok(kind, src[s:i], s, i, nl)); nl = False
    return toks


class Clause:
    """A context clause `< params [where reqs] >`. `lt` and `gt` are token indices; `params` and
    `reqs` are lists of (first token index, one past the last token index); `where` is the index
    of the `where` token or None."""

    def __init__(self, lt, gt, params, where, reqs):
        self.lt, self.gt, self.params, self.where, self.reqs = lt, gt, params, where, reqs


class Decl:
    def __init__(self):
        self.t0 = self.t1 = 0      # token range [t0, t1), prologue included
        self.intro = 0             # index of the introducer token
        self.kind = None           # text of the introducer ("fun", "struct", "let", ...)
        self.name = None           # declared identifier, if simple
        self.name_tok = None
        self.clause = None         # Clause or None
        self.body = None           # (index of '{', index of '}') of the body, or None
        self.members = None        # [Decl] for type bodies
        self.parent = None


def match_close(toks, i, end):
    """Index of the token closing the bracket opened at `i` (one of ( [ {), or `end`."""
    depth = 0
    for k in range(i, end):
        t = toks[k].text
        if toks[k].kind == "punct":
            if t in OPEN: depth += 1
            elif t in CLOSE:
                depth -= 1
                if depth == 0: return k
    return end


def match_angle(toks, i, end):
    """Index of the `>` closing the `<` at `i` in a type-level context, or None."""
    depth, k = 0, i
    while k < end:
        t = toks[k]
        if t.kind == "punct":
            if t.text == "<": depth += 1
            elif t.text == ">":
                depth -= 1
                if depth == 0: return k
            elif t.text in OPEN:
                k = match_close(toks, k, end)
            elif t.text in CLOSE: return None
        k += 1
    return None


def split_commas(toks, a, b):
    """Splits the token range [a, b) at commas that are not nested in brackets or angles."""
    parts, depth, s, k = [], 0, a, a
    while k < b:
        t = toks[k]
        if t.kind == "punct":
            if t.text in OPEN:
                k = match_close(toks, k, b)
            elif t.text == "<": depth += 1
            elif t.text == ">": depth -= 1
            elif t.text == "," and depth == 0:
                parts.append((s, k)); s = k + 1
        k += 1
    if s < b: parts.append((s, b))
    return parts


def parse_clause(toks, lt, end):
    gt = match_angle(toks, lt, end)
    if gt is None: return None
    where, depth, k = None, 0, lt + 1
    while k < gt:
        t = toks[k]
        if t.kind == "punct" and t.text in OPEN: k = match_close(toks, k, gt)
        elif t.kind == "punct" and t.text == "<": depth += 1
        elif t.kind == "punct" and t.text == ">": depth -= 1
        elif t.kind == "kw" and t.text == "where" and depth == 0: where = k; break
        k += 1
    params = split_commas(toks, lt + 1, where if where is not None else gt)
    reqs = split_commas(toks, where + 1, gt) if where is not None else []
    return Clause(lt, gt, params, where, reqs)


def _is_head(toks, k, end):
    """True iff token `k` can begin a declaration."""
    t = toks[k]
    if t.kind == "punct": return t.text == "@"
    if t.kind == "kw":
        if t.text in MODIFIERS: return True
        if t.text == "init": return k == 0 or toks[k - 1].text not in (".", "memberwise")
        return t.text in INTRODUCERS
    if t.kind == "name" and t.text in ("memberwise", "indirect"):
        return k + 1 < end and toks[k + 1].kind == "kw" and toks[k + 1].text in ("init", "case", "enum", "struct")
    return False


def _completes(t):
    """True iff a declaration may end with token `t`."""
    if t.kind in ("name", "num", "str", "pound"): return t.text != "is"
    if t.kind == "kw": return t.text in ("true", "false", "init", "auto") or t.text in BINDING_INTRODUCERS
    if t.kind == "punct": return t.text in (")", "]", "}", ">")
    return False


def parse_decls(toks, i, end, parent=None):
    """Parses the declarations in the token range [i, end)."""
    out = []
    while i < end:
        if toks[i].text == ";" and toks[i].kind == "punct": i += 1; continue
        d = Decl(); d.t0 = i; d.parent = parent
        k = i
        # Prologue: annotations and modifiers.
        while k < end:
            t = toks[k]
            if t.kind == "punct" and t.text == "@":
                k += 2
                if k < end and toks[k].text == "(" and toks[k].start == toks[k - 1].end:
                    k = match_close(toks, k, end) + 1
            elif t.kind == "kw" and t.text in MODIFIERS: k += 1
            elif t.kind == "name" and t.text in ("memberwise", "indirect") and _is_head(toks, k, end): k += 1
            else: break
        if k >= end:
            d.t1 = end; d.kind = "?"; out.append(d); break
        d.intro = k; d.kind = toks[k].text
        braced = d.kind in ("struct", "enum", "trait", "extension", "given", "fun", "subscript", "init")
        if d.kind == "given" and k + 1 < end and toks[k + 1].text in BINDING_INTRODUCERS:
            braced = False; k += 1
        # Find the end of the declaration.
        j, e = k + 1, None
        while j < end:
            t = toks[j]
            if t.kind == "punct" and t.text == ";": e = j; break
            if t.kind == "punct" and t.text in CLOSE: e = j; break
            if t.kind == "punct" and t.text in OPEN:
                c = match_close(toks, j, end)
                if t.text == "{" and braced:
                    nxt = c + 1
                    cont = (nxt < end and not toks[nxt].nl and not _is_head(toks, nxt, end)
                            and toks[nxt].text not in (";", "}", ")", "]"))
                    if not cont:
                        d.body = (j, c); e = min(c + 1, end); break
                j = min(c + 1, end); continue
            if _is_head(toks, j, end) and _completes(toks[j - 1]):
                if t.text in BINDING_INTRODUCERS and not t.nl and toks[j - 1].text == ")":
                    j += 1; continue      # an access effect, as in `fun f() inout -> T`
                if t.nl or toks[j - 1].text == "}":
                    e = j; break
            j += 1
        d.t1 = end if e is None else min(e, end)
        _describe(toks, d)
        out.append(d)
        i = d.t1
        if i == d.t0: i += 1    # stray closing bracket: skip it
    return out


def _describe(toks, d):
    k, end = d.intro + 1, d.t1
    hdr_end = d.body[0] if d.body else end
    kind = d.kind
    if kind in ("struct", "enum", "trait", "type", "fun", "subscript"):
        if k < end and toks[k].kind in ("name",) :
            d.name, d.name_tok = toks[k].text, k; k += 1
        elif kind == "fun" and k < end and toks[k].kind == "kw" and toks[k].text in ("infix", "prefix", "postfix"):
            return
    if kind == "given":
        if k + 1 < end and toks[k].kind == "name" and toks[k + 1].text == ":":
            d.name, d.name_tok = toks[k].text, k; k += 2
    if kind == "fun" and k < hdr_end and toks[k].text == "[":
        k = match_close(toks, k, hdr_end) + 1
    if kind in ("struct", "enum", "trait", "type", "fun", "subscript", "init", "given", "extension"):
        if k < hdr_end and toks[k].kind == "punct" and toks[k].text == "<":
            d.clause = parse_clause(toks, k, hdr_end)
    if d.body and kind in ("struct", "enum", "trait", "extension", "given"):
        d.members = parse_decls(toks, d.body[0] + 1, d.body[1], d)


class File:
    """A source file split into a header (leading `//!` lines), top-level declaration pieces and
    a trailer. `pieces[i]` is the text of declaration i with the comments that precede it."""

    def __init__(self, src):
        self.src = src
        self.toks = lex(src)
        self.decls = parse_decls(self.toks, 0, len(self.toks))
        self.spans = []           # (start, end) character span of each piece
        hdr_end = 0
        for m in re.finditer(r"[^\n]*\n?", src):
            l = m.group(0)
            if l.startswith("//!") or (not l.strip() and m.end() > m.start()): hdr_end = m.end()
            else: break
        if self.toks and hdr_end > self.toks[0].start: hdr_end = 0
        self.header = src[:hdr_end]
        prev = hdr_end
        for d in self.decls:
            e = self.toks[d.t1 - 1].end
            # A comment on the same line after the declaration belongs to it.
            m = re.compile(r"[ \t]*(//[^\n]*)?").match(src, e)
            nxt = self.toks[d.t1].start if d.t1 < len(self.toks) else len(src)
            if m and m.end() <= nxt and (m.end() == len(src) or src[m.end()] == "\n"): e = m.end()
            self.spans.append((prev, e)); prev = e
        self.trailer = src[prev:]
        self.pieces = [self._clean(src[a:b]) for a, b in self.spans]

    @staticmethod
    def _clean(piece):
        # Drops the separators (`;`, blank lines) left between two declarations.
        lines = piece.split("\n")
        while lines and lines[0].strip() in ("", ";"): lines.pop(0)
        if lines and lines[0].lstrip().startswith(";"): lines[0] = lines[0].lstrip()[1:].lstrip()
        return "\n".join(lines).rstrip()

    def top_index(self, pos):
        """Index of the top-level piece containing character offset `pos`."""
        for i, (a, b) in enumerate(self.spans):
            if a <= pos < b: return i
        return None

    def render(self, pieces=None):
        ps = self.pieces if pieces is None else pieces
        t = self.trailer.strip("\n")
        return self.header + "\n".join(ps) + "\n" + (t + "\n" if t.strip() else "")

    def edited_pieces(self, edits):
        """Applies character-level edits [(start, end, replacement)] (file coordinates, each
        inside one top-level piece) and returns {piece index: new piece text}."""
        by = {}
        for a, b, r in edits:
            i = self.top_index(a)
            assert i is not None and b <= self.spans[i][1], "edit outside a declaration"
            by.setdefault(i, []).append((a, b, r))
        out = {}
        for i, es in by.items():
            s0, s1 = self.spans[i]
            text, pos = [], s0
            for a, b, r in sorted(es):
                assert a >= pos, "overlapping edits"
                text.append(self.src[pos:a]); text.append(r); pos = b
            text.append(self.src[pos:s1])
            out[i] = self._clean("".join(text))
        return out

    def all_decls(self):
        """Every declaration, at any depth of type bodies, in source order."""
        out = []
        def walk(ds):
            for d in ds:
                out.append(d)
                if d.members: walk(d.members)
        walk(self.decls)
        return out

    def text(self, a, b):
        """Source text of the token range [a, b)."""
        return self.src[self.toks[a].start:self.toks[b - 1].end] if b > a else ""
