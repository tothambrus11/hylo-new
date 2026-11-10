#!/usr/bin/env python3
"""An executable model of how declared types are computed, for a small subset of Hylo.

usage: model.py FILE.hylo [--fix K] [--max N]

The model covers what the order-dependence problem needs and nothing else: structs (possibly
generic, with member aliases and nested structs), traits with associated types, type aliases,
extensions (of a type expression, or of a type parameter constrained by one trait), non-generic
givens (at the top level or in a function body), and functions whose parameters have type
expressions. Types are names applied to arguments; aliases are transparent.

It implements two semantics.

  ondemand  The existing checker, without the extorder and givencheck fixes ("base"): the type
            of a declaration is computed on demand and memoized; the declaration is hidden from
            lookups meanwhile; a member lookup evaluates the extendee of every extension that is
            not hidden; a resolution evaluates the type of every given that is not hidden.

  checked   The same with an approximation of extorder and givencheck: a lookup ignores the
            extensions that do not declare the name; every hidden extension or given that a
            lookup or resolution skipped is checked at the end, and the program is rejected if
            one of them applies to the type looked into or matches the goal.

  rounds    The proposed design: the signatures of extensions and givens are computed in rounds;
            in a round, lookups and resolutions read these signatures from the previous round's
            table only; rounds repeat until the table is stable (or a bound is hit: rejected).

For FILE, prints the verdict of `rounds` (which cannot depend on the order, by construction; the
script checks it anyway) and the number of permutations of the top-level declarations that
`ondemand` accepts. The permutations are those of orders.py with the same options.
"""
import hashlib, itertools, math, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orders

ERR = ("err",)

# --- Parsing ------------------------------------------------------------------------------------

TOKEN = re.compile(r"\s*(//[^\n]*|[A-Za-z_][A-Za-z_0-9]*|==|->|[{}()<>,.:=@&\[\]]|\d+|\S)")

def tokens(text):
    out, i = [], 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if not m: break
        i = m.end()
        if not m.group(1).startswith("//"): out.append(m.group(1))
    return out

class Parser:
    def __init__(self, text): self.t, self.i = tokens(text), 0
    def peek(self, k=0): return self.t[self.i + k] if self.i + k < len(self.t) else None
    def take(self, x=None):
        v = self.peek()
        if x is not None and v != x: raise SyntaxError(f"expected {x}, found {v} at {self.i}")
        self.i += 1; return v
    def expr(self):
        e = self.primary()
        while self.peek() == ".":
            self.take(); e = ("member", e, self.take())
        return e
    def primary(self):
        n = self.take()
        if self.peek() == "<":
            self.take(); args = [self.expr()]
            while self.peek() == ",": self.take(); args.append(self.expr())
            self.take(">"); return ("app", n, tuple(args))
        return ("name", n)
    def skip_block(self):
        self.take("{"); d = 1
        while d: d += {"{": 1, "}": -1}.get(self.take(), 0)
    def members(self, owner):
        """Parses `{ ... }`, returning {name: declaration} for the member types."""
        ms = {}
        self.take("{")
        while self.peek() != "}":
            if self.peek() == "public": self.take()
            k = self.take()
            if k == "type":
                n = self.take()
                if self.peek() == "=": self.take(); ms[n] = {"kind": "alias", "name": n, "rhs": self.expr(), "owner": owner}
                else: ms[n] = {"kind": "assoc", "name": n}
            elif k == "struct":
                n = self.take(); self.skip_block(); ms[n] = {"kind": "struct", "name": owner["name"] + "." + n, "members": {}, "params": 0}
            elif k == "fun":
                while self.peek() != "{" : self.take()
                self.skip_block()
            else: raise SyntaxError(f"unsupported member {k}")
        self.take("}")
        return ms
    def generic_clause(self):
        """Parses `<T where T is P>` or `<T>`, returning (parameters, [(parameter, trait)])."""
        ps, ws = [], []
        if self.peek() != "<": return ps, ws
        self.take("<")
        while self.peek() not in ("where", ">"):
            ps.append(self.take())
            if self.peek() == ",": self.take()
        if self.peek() == "where":
            self.take()
            while True:
                t = self.take(); self.take("is"); ws.append((t, self.take()))
                if self.peek() == ",": self.take()
                else: break
        self.take(">")
        return ps, ws
    def declaration(self, level, scope):
        k = self.take()
        if k == "public": k = self.take()
        if k == "trait":
            d = {"kind": "trait", "name": self.take()}; d["members"] = self.members(d); return d
        if k == "struct":
            n = self.take(); ps, _ = self.generic_clause()
            d = {"kind": "struct", "name": n, "params": len(ps)}; d["members"] = self.members(d); return d
        if k == "type":
            n = self.take(); self.take("="); return {"kind": "alias", "name": n, "rhs": self.expr(), "owner": None}
        if k == "extension":
            ps, ws = self.generic_clause()
            d = {"kind": "ext", "params": ps, "where": ws, "extendee": self.expr(), "name": f"extension@{self.i}"}
            d["members"] = self.members(d); return d
        if k == "given":
            s = self.expr(); self.take("is")
            d = {"kind": "given", "subject": s, "trait": self.take(), "level": level, "scope": scope, "name": f"given@{self.i}"}
            d["members"] = self.members(d); return d
        if k == "fun":
            n = self.take(); ps, _ = self.generic_clause()
            d = {"kind": "fun", "name": n, "tparams": ps, "params": [], "body": []}
            self.take("(")
            while self.peek() != ")":
                self.take(); self.take(":")
                if self.peek() in ("sink", "let", "inout", "set"): self.take()
                d["params"].append(self.expr())
                if self.peek() == ",": self.take()
            self.take(")")
            self.take("{")
            while self.peek() != "}":
                if self.peek() == "given": d["body"].append(self.declaration(level + 1, d))
                elif self.peek() == "let":
                    self.take(); self.take(); self.take(":"); t = self.expr(); self.take("="); d["body"].append({"kind": "let", "type": t, "value": self.take()})
                else:  # A statement that the model ignores.
                    self.take()
                    if self.peek() == "(":
                        depth = 0
                        while True:
                            depth += {"(": 1, ")": -1}.get(self.take(), 0)
                            if depth == 0: break
            self.take("}")
            return d
        raise SyntaxError(f"unsupported declaration {k}")

def parse(text):
    p, ds = Parser(text), []
    while p.peek() is not None: ds.append(p.declaration(0, None))
    return ds

# --- Evaluation ---------------------------------------------------------------------------------

class Checker:
    """Computes declared types; `table` is None for the on-demand semantics, and the signatures
    of the previous round for the round semantics."""

    def __init__(self, decls, table=None, checked=False):
        self.decls, self.table, self.checked, self.skips = decls, table, checked, []
        self.errors, self.memo, self.stack = [], {}, []
        self.hidden_candidate_seen = False
        self.types = {n: {"kind": "struct", "name": n, "members": {}, "params": 0} for n in ("Int", "Bool", "Void")}
        self.exts, self.traits, self.top_givens = [], {}, []
        for d in decls:
            if d["kind"] in ("struct", "alias"): self.types[d["name"]] = d
            if d["kind"] == "struct":
                for m in d["members"].values():
                    if m["kind"] == "struct": self.types[m["name"]] = m
            if d["kind"] == "trait": self.traits[d["name"]] = d
            if d["kind"] == "ext": self.exts.append(d)
            if d["kind"] == "given": self.top_givens.append(d)

    def error(self, m):
        self.errors.append(m); return ERR

    def has_error(self, t):
        return t == ERR or (t[0] == "nom" and any(self.has_error(a) for a in t[2]))

    # Signatures of nodes: hard (computed now) and soft (as a lookup or resolution sees them).

    def node(self, d, compute):
        """The signature of `d`, computed now if needed."""
        k = id(d)
        if k in self.memo: return self.memo[k]
        if k in self.stack: return self.error(f"{d['name']} refers to itself")
        self.stack.append(k)
        t = compute()
        self.stack.pop()
        self.memo[k] = t
        return t

    def alias(self, d):
        return self.node(d, lambda: self.eval(d["rhs"], d.get("owner")))

    def extendee(self, d):
        return self.node(d, lambda: self.eval(d["extendee"], d))

    def given(self, d):
        return self.node(d, lambda: self.eval(d["subject"], d["scope"]))

    def soft(self, d, compute, query=None):
        """The signature of the extension or given `d` as a candidate, or None if it is hidden."""
        if self.table is not None:
            t = self.table.get(id(d))
            if t is None: self.hidden_candidate_seen = True
            return t
        if id(d) in self.stack:
            self.skips.append((d, query)); return None
        t = compute(d)
        return None if self.has_error(t) else t

    # Type expressions.

    def eval(self, e, scope):
        if e[0] == "name":
            n = e[1]
            if scope and scope.get("kind") == "ext" and n in scope["params"]: return ("gp", n)
            if scope and scope.get("kind") == "fun" and n in scope["tparams"]: return ("gp", n)
            d = self.types.get(n)
            if d is None: return self.error(f"undefined {n}")
            if d["kind"] == "alias": return self.alias(d)
            return ("nom", d["name"], ())
        if e[0] == "app":
            return ("nom", e[1], tuple(self.eval(a, scope) for a in e[2]))
        q = self.eval(e[1], scope)
        if self.has_error(q): return ERR
        cs = self.lookup(e[2], q, scope)
        if len(cs) == 1: return cs[0]
        return self.error(f"no member {e[2]}" if not cs else f"ambiguous {e[2]}")

    def lookup(self, n, q, scope):
        cs = []
        if q[0] == "nom":
            m = self.types[q[1]]["members"].get(n)
            if m: cs.append(self.alias(m) if m["kind"] == "alias" else ("nom", m["name"], ()))
        for e in self.exts:
            if (self.table is not None or self.checked) and n not in e["members"]: continue
            u = self.soft(e, self.extendee, q)
            if u is None or not self.applies(e, u, q, scope): continue
            if n in e["members"]: cs.append(self.alias(e["members"][n]))
        for p in self.traits.values():
            if n not in p["members"]: continue
            for g in self.summon(p["name"], q, scope):
                m = g["members"].get(n)
                cs.append(self.alias(m) if m else ERR)
        return cs

    def applies(self, e, u, q, scope):
        if u[0] == "gp":
            return all(len(self.summon(p, q, scope)) == 1 for (_, p) in e["where"])
        return u == q

    def summon(self, p, q, scope):
        """The givens of `p` for `q` in the innermost scope that has one."""
        levels = []
        s = scope
        while s is not None and s.get("kind") != "fun": s = s.get("scope") if s.get("kind") == "given" else None
        if s is not None: levels.append([d for d in s["body"] if d["kind"] == "given"])
        levels.append(self.top_givens)
        found = []
        for gs in levels:
            ms = []
            for g in gs:
                if g["trait"] != p and self.table is not None: continue
                t = self.soft(g, self.given, (p, q))
                if t is not None and g["trait"] == p and t == q: ms.append(g)
            found.append(ms)
        for ms in found:
            if ms: return ms
        return []

    # Checking.

    def check(self, d):
        k = d["kind"]
        if k == "alias": self.alias(d)
        elif k == "struct":
            for m in d["members"].values():
                if m["kind"] == "alias": self.alias(m)
        elif k == "ext":
            self.extendee(d)
            for m in d["members"].values(): self.alias(m)
        elif k == "given":
            self.given(d)
            for m in d["members"].values(): self.alias(m)
        elif k == "fun":
            for e in d["params"]: self.eval(e, d)
            for s in d["body"]:
                if s["kind"] == "given": self.check(s)
                else:
                    t = self.eval(s["type"], d)
                    if s["value"] == "true" and t != ("nom", "Bool", ()) and not self.has_error(t):
                        self.error("expected Bool")

def soft_nodes(decls):
    for d in decls:
        if d["kind"] in ("ext", "given"): yield d
        if d["kind"] == "fun": yield from (s for s in d["body"] if s["kind"] == "given")

def ondemand(decls, checked=False):
    c = Checker(decls, checked=checked)
    for d in decls: c.check(d)
    if checked:
        for (d, query) in c.skips:
            t = c.memo.get(id(d))
            if t is None or c.has_error(t): continue
            if d["kind"] == "ext" and (t == query or t[0] == "gp"):
                c.error(f"circular extension {d['name']}")
            if d["kind"] == "given" and (d["trait"], t) == query:
                c.error(f"circular given {d['name']}")
    return ("reject" if c.errors else "accept"), c.errors

def rounds(decls, with_state=False):
    """Returns (verdict, errors, number of rounds), followed by the final checker if `with_state`."""
    nodes = list(soft_nodes(decls))
    table, seen, k = {}, [], 0
    while True:
        k += 1
        c = Checker(decls, table)
        nxt = {}
        for n in nodes:
            t = c.extendee(n) if n["kind"] == "ext" else c.given(n)
            if not c.has_error(t): nxt[id(n)] = t
        if nxt == table or (k == 1 and not c.hidden_candidate_seen):
            c.table = nxt
            for d in decls: c.check(d)
            r = ("reject" if c.errors else "accept"), c.errors, k
            return r + (c,) if with_state else r
        if nxt in seen or k > len(nodes) + 2:
            r = "reject", ["no stable interpretation of the signatures"], k
            return r + (c,) if with_state else r
        seen.append(table); table = nxt

def permutations(path, k, fix, nmax):
    head = tuple(range(min(fix, k)))
    if math.factorial(k - len(head)) <= nmax:
        return [head + q for q in itertools.permutations(range(len(head), k))]
    rng = random.Random(int(hashlib.sha1(os.path.basename(path).encode()).hexdigest()[:8], 16))
    perms = [tuple(range(k)), head + tuple(reversed(range(len(head), k)))]
    while len(perms) < nmax:
        p = list(range(len(head), k)); rng.shuffle(p); perms.append(head + tuple(p))
    return perms

def run(path, fix=0, nmax=720):
    header, chunks = orders.split(open(path).read())
    ps = permutations(path, len(chunks), fix, nmax)
    acc, accc, verdicts, nrounds = 0, 0, set(), set()
    for p in ps:
        ds = parse("\n".join(chunks[i] for i in p))
        if ondemand(ds)[0] == "accept": acc += 1
        ds = parse("\n".join(chunks[i] for i in p))
        if ondemand(ds, True)[0] == "accept": accc += 1
        ds = parse("\n".join(chunks[i] for i in p))
        v, _, k = rounds(ds)
        verdicts.add(v); nrounds.add(k)
    return {"file": os.path.basename(path), "perms": len(ps), "ondemand_accept": acc, "checked_accept": accc,
            "rounds_verdicts": sorted(verdicts), "rounds": sorted(nrounds)}

if __name__ == "__main__":
    a = sys.argv[1:]
    fix, nmax = 0, 720
    if "--fix" in a: i = a.index("--fix"); fix = int(a[i + 1]); del a[i:i + 2]
    if "--max" in a: i = a.index("--max"); nmax = int(a[i + 1]); del a[i:i + 2]
    print(run(a[0], fix, nmax))
