#!/usr/bin/env python3
# Generate orderings of declarations to probe evaluation-order differences under `index`.
import itertools, os
D = os.path.dirname(os.path.abspath(__file__)) + "/perm"
head = """struct A { public memberwise init }
struct B { public memberwise init }
fun needA<where let a: A>() -> B { B() }
fun needB<where let b: B>() -> A { A() }
fun check<T>(x: T) {}
"""
parts = {
 "f": "fun f<T, U where T == U>(x: T) {\n  check<U>(x)\n}\n",
 "kg": "fun kg() {\n  let z = g\n}\n",
 "kh": "fun kh() {\n  let z = h\n}\n",
 "h": "given let h = needA()\n",
 "g": "given let g = needB()\n",
}
n = 0
for keys in [("f","kg","h","g"),("f","kh","h","g")]:
  for p in itertools.permutations(keys):
    if p.index("f") > min(p.index("h"), p.index("g")): continue
    name = "p_" + "_".join(p)
    open(f"{D}/{name}.hylo","w").write(head + "".join(parts[k] for k in p))
    n += 1
print(n)
