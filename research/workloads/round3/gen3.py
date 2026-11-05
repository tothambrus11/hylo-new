"""Generators for the round-3 workloads: transitive equalities, associated-type equality,
refinement (nested given) chains and wide nested givens. Usage: python3 gen3.py KIND N > out.hylo"""
import sys

def trans(n, neg=False, use_assoc=True):
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i} == T{i+1}" for i in range(n))
    conf = "T0 is P" + (f", T{n} is P" if neg else "")
    body = [] if neg else [f"  g<T{n}>()"]
    if use_assoc: body.append("  check<T0.X>(x)")
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun g<V where V is P>() {{}}
fun f<{ps} where {eqs}, {conf}>(x: T{n}.X) {{
{chr(10).join(body)}
}}
"""

def transconf(n):
    # Conformance through an equality chain only (no associated type).
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i} == T{i+1}" for i in range(n))
    return f"""trait P {{}}
fun g<V where V is P>() {{}}
fun f<{ps} where {eqs}, T0 is P>() {{ g<T{n}>() }}
"""

def refine(n):
    ls = ["trait P {}", "trait Q1 refines P {}"] + [f"trait Q{i} refines Q{i-1} {{}}" for i in range(2, n + 1)]
    return "\n".join(ls) + f"\nfun use<T>(x: T) {{}}\nfun f<T is Q{n}>() {{ use(summon[P<T>]) }}\n"

def nestwide(n):
    # n traits, each declaring a nested given; the user needs all of them.
    ls = ["trait P {}"]
    for i in range(n):
        ls.append(f"struct S{i} {{}}")
        ls.append(f"trait R{i} {{ given S{i} is P }}")
    bounds = " & ".join(f"R{i}" for i in range(n))
    uses = "\n".join(f"  use(summon[P<S{i}>])" for i in range(n))
    return "\n".join(ls) + f"\nfun use<T>(x: T) {{}}\nfun f<T is {bounds}>() {{\n{uses}\n}}\n"

def assoceq(n):
    # Associated-type equality across n conformance-carrying parameters, all equal.
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i}.X == T{i+1}.X" for i in range(n))
    confs = ", ".join(f"T{i} is P" for i in range(n + 1))
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun f<{ps} where {confs}, {eqs}>(x: T{n}.X) {{
  check<T0.X>(x)
}}
"""

def assocneg(n):
    # Like assoceq but with the middle link missing: must be rejected.
    ps = ", ".join(f"T{i}" for i in range(n + 1))
    eqs = ", ".join(f"T{i}.X == T{i+1}.X" for i in range(n) if i != n // 2)
    confs = ", ".join(f"T{i} is P" for i in range(n + 1))
    return f"""trait P {{ type X }}
fun check<T>(x: T) {{}}
fun f<{ps} where {confs}{', ' + eqs if eqs else ''}>(x: T{n}.X) {{
  check<T0.X>(x)
}}
"""

K = {"trans": trans, "transneg": lambda n: trans(n, neg=True), "transconf": transconf,
     "refine": refine, "nestwide": nestwide, "assoceq": assoceq, "assocneg": assocneg}
print(K[sys.argv[1]](int(sys.argv[2])), end="")
