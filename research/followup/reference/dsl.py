"""A compact text notation for abstract problems, used for the hand-written cases.

    trait P X            trait P with the associated type X
    trait Q              trait Q without associated type
    struct A             nominal type of arity 0
    struct Box 1         nominal type of arity 1
    given A is P = B                       conformance, with `type X = B`
    given [T: T is Q] Box<T> is Q          generic or conditional conformance
    query [T U: T == U, T is P] U is P     conformance goal
    query [T U: T == U] T == U             equality goal
    query [T U: T == U] T -> U             coercion goal
    ... # expect: D                        the verdict expected by hand: D(erivable),
                                           U(nderivable), I(ll-formed goal), ? (unspecified)

Types: `T`, `A`, `Box<T>`, `{T, U}`, `T.X` (X is looked up among the traits' associated types).
"""

import re


class Parser:
    def __init__(self, world, params):
        self.world = world
        self.params = params

    def parse(self, s):
        self.toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[<>{},.]", s)
        self.i = 0
        t = self.type()
        assert self.i == len(self.toks), "trailing tokens in type: " + s
        return t

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, x=None):
        t = self.toks[self.i]
        assert x is None or t == x, "expected %s, found %s" % (x, t)
        self.i += 1
        return t

    def list(self, close):
        xs = [self.type()]
        while self.peek() == ",":
            self.eat()
            xs.append(self.type())
        self.eat(close)
        return tuple(xs)

    def type(self):
        if self.peek() == "{":
            self.eat()
            xs = self.list("}")
            t = ("app", "{%d}" % len(xs), xs)
        else:
            n = self.eat()
            if n in self.params:
                t = ("var", n)
            else:
                assert n in self.world["structs"], "unknown type " + n
                args = ()
                if self.peek() == "<":
                    self.eat()
                    args = self.list(">")
                assert len(args) == self.world["structs"][n], "arity of " + n
                t = ("app", n, args)
        while self.peek() == ".":
            self.eat()
            x = self.eat()
            traits = [p for p, a in self.world["traits"].items() if a == x]
            assert len(traits) == 1, "unknown associated type " + x
            t = ("proj", t, traits[0])
        return t


def split_top(s, sep):
    """Splits `s` at the occurrences of `sep` that are not nested in brackets."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(s):
        ch = s[i]
        if ch in "<{":
            depth += 1
        elif ch in ">}" and not (ch == ">" and i > 0 and s[i - 1] == "-"):
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            out.append(cur)
            cur = ""
            i += len(sep)
            continue
        cur += ch
        i += 1
    out.append(cur)
    return [x.strip() for x in out]


def requirement(p, s):
    if "==" in s:
        a, b = split_top(s, "==")
        return ("eq", p.parse(a), p.parse(b))
    a, b = s.rsplit(" is ", 1)
    return ("conf", p.parse(a), b.strip())


def context(world, s):
    """Parses `[T U: reqs] rest` and returns (params, reqs, parser, rest)."""
    params, reqs = [], []
    m = re.match(r"\s*\[([^\]]*)\]\s*(.*)$", s)
    p = Parser(world, params)
    if m:
        head, s = m.group(1), m.group(2)
        ps, _, rs = head.partition(":")
        params.extend(ps.split())
        if rs.strip():
            reqs = [requirement(p, r) for r in split_top(rs, ",")]
    return params, reqs, p, s


def parse(text):
    """Returns (world, expectations) where expectations[i] is the hand verdict of query i."""
    world = {"traits": {}, "structs": {}, "confs": [], "queries": []}
    expect = []
    for raw in text.strip().splitlines():
        line, _, comment = raw.partition("#")
        line = line.strip()
        if not line:
            continue
        kind, _, rest = line.partition(" ")
        if kind == "trait":
            xs = rest.split()
            world["traits"][xs[0]] = xs[1] if len(xs) > 1 else None
        elif kind == "struct":
            xs = rest.split()
            world["structs"][xs[0]] = int(xs[1]) if len(xs) > 1 else 0
        elif kind == "given":
            params, premises, p, rest = context(world, rest)
            impl = None
            if " = " in rest:
                rest, impl = rest.rsplit(" = ", 1)
                impl = p.parse(impl)
            t, trait = rest.rsplit(" is ", 1)
            world["confs"].append({"params": params, "premises": premises, "type": p.parse(t),
                                   "trait": trait.strip(), "impl": impl})
        elif kind == "query":
            params, reqs, p, rest = context(world, rest)
            if "->" in rest:
                a, b = split_top(rest, "->")
                goal = ("coerce", p.parse(a), p.parse(b))
            else:
                goal = requirement(p, rest)
            world["queries"].append({"params": params, "reqs": reqs, "goal": goal})
            m = re.search(r"expect:\s*(\S+)", comment)
            expect.append(m.group(1) if m else None)
        else:
            raise ValueError("unknown line: " + raw)
    return world, expect
