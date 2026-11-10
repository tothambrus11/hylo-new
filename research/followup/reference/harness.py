"""Runs the compiler on a printed problem and attributes the verdicts to the queries."""
import os

import tc
import to_hylo

TIMEOUT = {"base": 20, "FIX": 60, "FULL": 60}


def run_world(world, path, configs=("base", "FIX", "FULL"), only=None, timeouts=TIMEOUT):
    """Prints `world` to `path`, runs each configuration, and returns

        {config: {"status": "ok" | "crash" | "timeout" | "invalid", "code": exit code,
                  "verdicts": {query index: "accept" | "reject"}, "messages": {query: text}}}

    "invalid" means that a diagnostic was reported outside the query functions, or that the
    program does not parse: a defect of the printer or of the generator, never a finding.
    """
    text, where = to_hylo.program(world, only)
    with open(path, "w") as f:
        f.write(text)
    out = {}
    for c in configs:
        r = tc.run(path, c, timeout=timeouts.get(c, 60))
        res = {"status": r["status"], "code": r["code"], "verdicts": {}, "messages": {}}
        if r["status"] == "ok":
            rejected = {}
            for line, msg in r["diags"]:
                if line not in where or "expected" in msg or "not a valid identifier" in msg:
                    res["status"] = "invalid"
                    res["messages"][-1] = "%d: %s" % (line, msg)
                else:
                    i = where[line]
                    rejected[i] = (rejected[i] + " | " + msg) if i in rejected else msg
            if r["n"] != len(r["diags"]):
                res["status"] = "invalid"
                res["messages"][-1] = "diagnostic count mismatch"
            for i in where.values():
                res["verdicts"][i] = "reject" if i in rejected else "accept"
            res["messages"].update(rejected)
        out[c] = res
    return out


def classify(ref, verdict):
    """Compares one compiler verdict with the reference answer `ref` (reference.answer).

    Returns one of: agree, UNSOUND (accepted, underivable even with injectivity),
    BEYOND-SPEC (accepted, underivable in the specification but valid with injectivity or
    vacuous), INCOMPLETE (rejected, one derivation), MULTI-accept / MULTI-reject (several
    derivations: the specification leaves the ranking open), ILLFORMED-accept, skip.
    """
    v = ref["verdict"]
    if v == "unspecified":
        return "skip"
    if v == "illformed-goal":
        return "agree" if verdict == "reject" else "ILLFORMED-accept"
    if v == "underivable":
        if verdict == "reject":
            return "agree"
        return "UNSOUND" if ref["sem"] == "invalid" else "BEYOND-SPEC"
    if ref["count"] is not None and ref["count"] >= 2:
        return "MULTI-" + verdict
    return "agree" if verdict == "accept" else "INCOMPLETE"


def renamed(world, prefix):
    """A copy of `world` whose traits, structs and associated types are prefixed, so that several
    worlds can be printed in one program without interacting."""
    def ty(t):
        if t[0] == "app":
            h = t[1] if t[1].startswith("{") else prefix + t[1]
            return ("app", h, tuple(ty(a) for a in t[2]))
        if t[0] == "proj":
            return ("proj", ty(t[1]), prefix + t[2])
        return t

    def req(r):
        if r[0] == "conf":
            return ("conf", ty(r[1]), prefix + r[2])
        return (r[0], ty(r[1]), ty(r[2]))

    return {
        "traits": {prefix + t: (prefix + x if x else None) for t, x in world["traits"].items()},
        "structs": {prefix + s: n for s, n in world["structs"].items()},
        "confs": [{"params": c["params"], "premises": [req(p) for p in c["premises"]],
                   "type": ty(c["type"]), "trait": prefix + c["trait"],
                   "impl": ty(c["impl"]) if c["impl"] is not None else None}
                  for c in world["confs"]],
        "queries": [{"params": q["params"], "reqs": [req(r) for r in q["reqs"]],
                     "goal": req(q["goal"])} for q in world["queries"]],
    }


def run_batch(worlds, path, config, timeout=60):
    """Prints several worlds in one program (with disjoint names) and runs `config` once.
    Returns one result per world, shaped as in `run_world`, or None if the run as a whole
    failed (crash, timeout, or a diagnostic outside the query functions)."""
    lines = []
    where = {}
    ws = [renamed(w, "W%d" % k) for k, w in enumerate(worlds)]
    for w in ws:
        lines.extend(to_hylo.declarations(w))
    lines.extend(to_hylo.HELPERS)
    for k, w in enumerate(ws):
        for i, q in enumerate(w["queries"]):
            lines.append(to_hylo.query_line(w, i, q, prefix="w%dq" % k))
            where[len(lines)] = (k, i)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    r = tc.run(path, config, timeout=timeout)
    if r["status"] != "ok" or r["n"] != len(r["diags"]):
        return None
    out = [{"status": "ok", "code": 0, "verdicts": {i: "accept" for i in range(len(w["queries"]))},
            "messages": {}} for w in worlds]
    for line, msg in r["diags"]:
        if line not in where or "expected" in msg or "not a valid identifier" in msg:
            return None
        k, i = where[line]
        out[k]["verdicts"][i] = "reject"
        out[k]["messages"][i] = (out[k]["messages"][i] + " | " + msg) if i in out[k]["messages"] else msg
    return out
