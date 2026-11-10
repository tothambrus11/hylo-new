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
