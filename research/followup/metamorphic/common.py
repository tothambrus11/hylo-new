"""Shared machinery: running the type checker (one process at a time, cached), the corpus, and
the representation of a metamorphic variant."""
import fcntl, hashlib, json, os, re, subprocess, time
from hylosyn import File, lex

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # .../hylo-new
BINARY = os.path.join(ROOT, "research", "exp", "bin", "eq9-723cc0e6b0f8", "tc-bench")
STDLIB = os.path.join(os.path.dirname(BINARY), "Hylo_StandardLibrary.resources")
FIX = "occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
CONFIGS = {"base": "", "FIX": FIX,
           "FULL": FIX + ",symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"}
CORPUS = [("test-programs", os.path.join(ROOT, "research", "report", "test-programs")),
          ("compiler-positive", os.path.join(ROOT, "Tests", "CompilerTests", "positive")),
          ("compiler-negative", os.path.join(ROOT, "Tests", "CompilerTests", "negative")),
          ("workloads", os.path.join(ROOT, "research", "workloads"))]
MAX_BYTES = 20000       # larger files are skipped ("skip the largest files")
TMP = os.environ.get("MM_TMP", "/tmp/claude-0/-home-user-hylo-new/fd857f11-b63a-5859-949e-90078fb8fdea/scratchpad/mm")
CACHE = os.path.join(HERE, "data", "cache.jsonl")
LOCK = os.path.join(HERE, "data", ".tc-bench.lock")

_cache = None


def rel(path):
    return os.path.relpath(path, ROOT)


def corpus():
    """[(group, path)] of every program, in a fixed order."""
    out = []
    for g, r in CORPUS:
        for d, _, fs in sorted(os.walk(r)):
            for f in sorted(fs):
                if f.endswith(".hylo"):
                    p = os.path.join(d, f)
                    grp = g + "/" + os.path.basename(d) if g == "test-programs" else g
                    out.append((grp, p))
    return out


def _load_cache():
    global _cache
    if _cache is None:
        _cache = {}
        if os.path.exists(CACHE):
            for l in open(CACHE):
                try: r = json.loads(l)
                except ValueError: continue
                _cache[(r["sha"], r["config"])] = r
    return _cache


def check(text, config="FULL", timeout=60, refresh=False):
    """Type-checks `text` under `config`. Returns {verdict, errors, syntax, ms}: verdict is one of
    accept, reject, crash:<code>, timeout; errors is the sorted list of diagnostics with source
    positions removed; syntax is true iff a diagnostic comes from the parser."""
    os.makedirs(TMP, exist_ok=True); os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    sha = hashlib.sha1(text.encode()).hexdigest()
    c = _load_cache()
    if not refresh and (sha, config) in c:
        r = c[(sha, config)]; r["syntax"] = is_syntax(r["errors"])
        return r
    path = os.path.join(TMP, "p%d.hylo" % os.getpid())
    with open(path, "w") as f: f.write(text)
    with open(LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)        # at most one tc-bench process at a time
        t0 = time.time()
        try:
            p = subprocess.run(["timeout", str(timeout), BINARY, path],
                               env=dict(os.environ, HYLO_TC_EXPERIMENTS=CONFIGS[config]),
                               capture_output=True, text=True, errors="replace")
            rc, out = p.returncode, p.stdout
        finally:
            ms = int((time.time() - t0) * 1000)
            fcntl.flock(lock, fcntl.LOCK_UN)
    errs = []
    for l in out.splitlines():
        m = re.match(r"^\s*.*?\.hylo:\d+\.\d+(?:-\d+(?:\.\d+)?)?: (error|warning|note): (.*)$", l)
        if m: errs.append(m.group(1) + ": " + m.group(2))
    errs.sort()
    if rc == 124: verdict = "timeout"
    elif rc != 0: verdict = "crash:%d" % rc
    elif "diagnostics:" not in out: verdict = "crash:noout"
    else: verdict = "reject" if any(e.startswith("error") for e in errs) else "accept"
    r = {"sha": sha, "config": config, "verdict": verdict, "errors": errs, "syntax": is_syntax(errs), "ms": ms}
    c[(sha, config)] = r
    with open(CACHE, "a") as f: f.write(json.dumps(r) + "\n")
    return r


SYNTAX = re.compile(r"^error: (expected (?!value of type)|'unexpected context bound'|consecutive statements|unterminated"
                    r"|.* is not a valid identifier|.*requires whitespaces|.*cannot be separated|.*is not allowed here"
                    r"|duplicate modifier|extraneous whitespace)")


def is_syntax(errors):
    """True iff one of the diagnostics comes from the parser."""
    return any(SYNTAX.match(e) for e in errors)


class Variant:
    """A transformed program, described relative to the top-level pieces of a File:
    `order`: the indices of the pieces to print, in order (None = original order);
    `repl`: {piece index: replacement text} (an empty replacement deletes the piece);
    `pre`, `post`: declarations added before and after; `rename`: {old identifier: new}."""

    def __init__(self, vid, desc="", order=None, repl=None, pre=None, post=None, rename=None, kind=""):
        self.vid, self.desc, self.kind = vid, desc, kind or vid.split(":")[0]
        self.order, self.repl = order, repl or {}
        self.pre, self.post, self.rename = pre or [], post or [], rename

    def render(self, F, keep=None):
        idx = list(range(len(F.pieces))) if self.order is None else list(self.order)
        if keep is not None: idx = [i for i in idx if i in keep]
        ps = [self.repl.get(i, F.pieces[i]) for i in idx]
        text = F.render(self.pre + [p for p in ps if p.strip()] + self.post)
        if self.rename: text = rename_tokens(text, self.rename)
        return text

    def touched(self):
        return set(self.repl)


IDENTITY = Variant("identity")


def rename_tokens(text, mapping):
    """Replaces every identifier token whose text is a key of `mapping`."""
    out, pos = [], 0
    for t in lex(text):
        if t.kind == "name" and t.text in mapping:
            out.append(text[pos:t.start]); out.append(mapping[t.text]); pos = t.end
    out.append(text[pos:])
    return "".join(out)


_stdnames = None


def stdlib_names():
    """Identifiers that the standard library declares, uses as labels, or selects as members."""
    global _stdnames
    if _stdnames is None:
        names = set()
        for d, _, fs in os.walk(STDLIB):
            for f in fs:
                if not f.endswith(".hylo"): continue
                ts = lex(open(os.path.join(d, f)).read())
                for i, t in enumerate(ts):
                    if t.kind != "name": continue
                    prev = ts[i - 1].text if i else ""
                    nxt = ts[i + 1].text if i + 1 < len(ts) else ""
                    if prev in ("struct", "trait", "enum", "type", "fun", "subscript", "let", "var",
                                "case", ".", "infix", "prefix", "postfix", "import", "given") \
                            or (nxt == ":" and prev != "extension"):
                        names.add(t.text)
        _stdnames = names | {"Self", "self", "main", "Builtin", "Hylo", "is", "memberwise", "Int",
                             "Bool", "Void", "Never", "Metatype", "refines", "indirect", "new", "any"}
    return _stdnames


def fresh(F, base):
    """An identifier starting with `base` that occurs neither in the file nor in the stdlib."""
    used = {t.text for t in F.toks} | stdlib_names()
    n, k = base, 0
    while n in used:
        k += 1; n = "%s%d" % (base, k)
    return n


def same_messages(a, b, rename=None):
    """Compares two error lists, mapping renamed identifiers back."""
    if rename:
        inv = {v: k for k, v in rename.items()}
        b = sorted(re.sub(r"[A-Za-z_][A-Za-z_0-9]*", lambda m: inv.get(m.group(0), m.group(0)), e) for e in b)
    return list(a) == list(b)


def round_robin(groups):
    """Interleaves lists: the first element of each, then the second of each, and so on."""
    out, i = [], 0
    groups = [g for g in groups if g]
    while any(i < len(g) for g in groups):
        out += [g[i] for g in groups if i < len(g)]
        i += 1
    return out


def by_kind(variants, order=None):
    """Orders variants so that every prefix covers the kinds as evenly as possible."""
    groups = {}
    for v in variants: groups.setdefault(v.kind, []).append(v)
    keys = sorted(groups, key=lambda k: (order.index(k) if order and k in order else 99, k))
    return round_robin([groups[k] for k in keys])
