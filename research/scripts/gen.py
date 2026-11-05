#!/usr/bin/env python3
"""Synthetic Hylo workloads stressing implicit resolution, overloading, and name lookup."""
import sys, os

def chain(d):
    """W1: resolution through a chain of conditional conformances of depth d."""
    t = "Z"
    for _ in range(d): t = f"S<{t}>"
    return f"""trait P {{}}
struct S<T> {{}}
struct Z {{}}
given Z is P {{}}
given <T where T is P> => S<T> is P {{}}
fun need<where {t} is P>() {{}}
public fun main() {{ need() }}
"""

def breadth(n_traits, n_types, n_queries):
    """W2: many unrelated givens in scope; a few queries."""
    out = []
    for i in range(n_traits): out.append(f"trait P{i} {{}}")
    for j in range(n_types): out.append(f"struct A{j} {{}}")
    for i in range(n_traits):
        for j in range(n_types): out.append(f"given A{j} is P{i} {{}}")
    for q in range(n_queries):
        i, j = q % n_traits, (q * 7) % n_types
        out.append(f"fun need{q}<where A{j} is P{i}>() {{}}")
    out.append("public fun main() {")
    for q in range(n_queries): out.append(f"  need{q}()")
    out.append("}")
    return "\n".join(out) + "\n"

def diverge(kind, n_queries=1):
    """W3: queries that must fail; the search diverges (intro.md examples)."""
    if kind == "loop":     # g: forall T. P T => P T ; x : P Int ; query P Bool
        rules = "given <T where T is P> => T is P {}\ngiven Xi is P {}"
    elif kind == "grow":   # forall T. P (S T) => P T : terms grow without bound
        rules = "given <T where S<T> is P> => T is P {}\ngiven Xi is P {}"
    elif kind == "dead":   # no base case at all: Bool and Int depend on each other
        rules = "given <where Yb is P> => Xi is P {}\ngiven <where Xi is P> => Yb is P {}"
    out = ["trait P {}", "struct S<T> {}", "struct Yb {}", "struct Xi {}", rules]
    for q in range(n_queries): out.append(f"fun need{q}<where Yb is P>() {{}}")
    out.append("public fun main() {")
    for q in range(n_queries): out.append(f"  need{q}()")
    out.append("}")
    return "\n".join(out) + "\n"

def overloads(k, n):
    """W4: one expression with n independent calls to an overload set of size k."""
    out = []
    for i in range(k): out.append(f"struct A{i} {{ public memberwise init }}")
    for i in range(k): out.append(f"fun f(x: A{i}) -> A{i} {{ x }}")
    params = ", ".join(f"x{j}: A{j % k}" for j in range(n))
    out.append(f"fun g({params}) {{}}")
    args = ", ".join(f"f(A{j % k}())" for j in range(n))
    out.append(f"public fun main() {{ g({args}) }}")
    return "\n".join(out) + "\n"

def overloads_ret(k, n):
    """W4b: overloads disambiguated only by return type (needs the outer call's context)."""
    out = []
    for i in range(k): out.append(f"struct A{i} {{ public memberwise init }}")
    for i in range(k): out.append(f"fun h() -> A{i} {{ A{i}() }}")
    params = ", ".join(f"x{j}: A{j % k}" for j in range(n))
    out.append(f"fun g({params}) {{}}")
    args = ", ".join("h()" for j in range(n))
    out.append(f"public fun main() {{ g({args}) }}")
    return "\n".join(out) + "\n"

def members(n_types, n_ext, n_uses):
    """W5: member lookup through many extensions."""
    out = []
    for j in range(n_types): out.append(f"struct T{j} {{ public memberwise init }}")
    for e in range(n_ext):
        j = e % n_types
        out.append(f"extension T{j} {{ fun m{e}() {{}} }}")
    out.append("public fun main() {")
    for u in range(n_uses):
        e = (u * 13) % n_ext
        out.append(f"  T{e % n_types}().m{e}()")
    out.append("}")
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    kind, *a = sys.argv[1:]
    a = [x if not x.lstrip('-').isdigit() else int(x) for x in a]
    print({"chain": chain, "breadth": breadth, "diverge": diverge, "overloads": overloads,
           "overloads_ret": overloads_ret, "members": members}[kind](*a), end="")
