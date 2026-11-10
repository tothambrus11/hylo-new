#!/usr/bin/env python3
"""Writes the reviewer's attack programs tests/a*.hylo, in the format of make_tests.py: what is
expected once the change is in, why, and what the binary does today (base and FULL).

  python3 scripts/review_tests.py      writes the tests (runs base and FULL for each one)
  python3 scripts/review_check.py a    re-runs them and compares with the comments

Sequential: one tc-bench process at a time.
"""
import os

from make_tests import ROOT, wrap, run, describe, CONFIGS

FORCING = '''fun test(b: B) { let y = f(b).m() }
struct A { public memberwise init }
%s
%s
%s
extension X {
  type Me = Int
  public fun m(q: Int) -> Int { q }
}
extension A { type Me = B }
type X = A.Me
public fun main() {}
'''
B_PLAIN = 'struct B { public memberwise init }'
B_WITH_M = 'struct B {\n  public memberwise init\n  public fun m() -> X { B() }\n}'
C_PLAIN = 'struct C { public memberwise init }\nextension C { public fun m() -> Int { 0 } }'
C_WITH_M = ('struct C {\n  public memberwise init\n  public fun m() -> X { B() }\n}\n'
            'extension B { public fun m() -> Int { 0 } }')
F_WRONG_FIRST = 'fun f(x: A) -> C { C() }\nfun f(x: B) -> B { x }'
F_RIGHT_FIRST = 'fun f(x: B) -> B { x }\nfun f(x: A) -> C { C() }'

BASE_ONLY = '''fun test(b: B) { let y = f(b).m() }
struct A { public memberwise init }
struct B {
  public memberwise init
  public fun m() -> X { B() }
}
struct C { public memberwise init }
extension C { public fun m() -> Int { 0 } }
%s
extension X { type Me = Int }
extension A { type Me = B }
type X = A.Me
public fun main() {}
'''

LOOKAHEAD = '''fun test() { let y = %s }
trait P { type E }
struct A { public memberwise init }
struct Foo<T> { public memberwise init }
given A is P { type E = Int }
struct B { public memberwise init }
struct C { public memberwise init }
struct K {
  public memberwise init
  public fun m() -> X { 0 }
}
struct K2 {
  public memberwise init
  public fun m() -> Bool { true }
}
fun h() -> C { C() }
fun h() -> B { B() }
fun k() -> K { K() }
fun k() -> K2 { K2() }
fun two(x: B, y: Int) -> Int { y }
fun two1(x: B) -> Int { 0 }
fun pair(x: Int, y: Int) -> Int { y }
type X = A.E
given Foo<X> is P { type E = Bool }
public fun main() {}
'''

THREE = '''struct A0 { public memberwise init }
struct A1 { public memberwise init }
trait P { fun m(x: A0) -> Int }
struct S {
  public memberwise init
  public fun m(x: A0) -> Int { 0 }
}
extension S { public fun m(x: A1) -> Int { 1 } }
given S is P {}
public fun main() {
  let s = S()
  let r = s.m(%s())
}
'''

OVER_ERRORS = '''struct A0 { public memberwise init }
struct A1 { public memberwise init }
struct A2 { public memberwise init }
fun f(x: A0) -> A0 { x }
fun f(x: A1) -> A1 { x }
fun f(x: A2) -> A2 { x }
trait Stepper { fun step(x: A2) -> Self }
struct C {
  public memberwise init
  public fun step(x: A2) -> C { C() }
}
given C is Stepper {}
public fun main() {
  let c = C()
  let d = c.step(f(A2())).step(f(A2())).step(f(A2()))
}
'''

A2 = ('Attack on assumption A2 (DESIGN.md 5.5), which the design does NOT withstand. ')

TESTS = [
    ('a01-forcing-accepted',
     'with `twins` alone: as today (accepted). With `cleanfirst`: REJECTED, "definition of \'X\' '
     'refers to itself", in base and in FULL: a known change of verdict',
     A2 + 'The candidate f(x: A), declared first, fails at its argument. Today its fork goes on '
     'and looks `m` up in C, which computes the extended type of `extension X` before anything '
     'else needs the alias X; that order is accepted. `cleanfirst` cancels the fork at the '
     'failed argument, so the first lookup is `m` in B, whose member B.m mentions X in its '
     'signature: the alias is entered first and the checker reports a self-reference. a02 is '
     'the same program with the two `f` swapped; there the existing solver cancels the fork '
     'itself, and shows the verdict that a01 gets with `cleanfirst`.',
     FORCING % (B_WITH_M, C_PLAIN, F_WRONG_FIRST)),
    ('a02-forcing-accepted-swapped',
     'as today with every flag (rejected)',
     'a01 with the two candidates of `f` swapped. The right candidate is found first, the '
     'existing solver cancels the other fork at its first error, and the lookup of `m` in C '
     'is never made. Shows that the verdict of a01 depends on a lookup made in a fork whose '
     'result is discarded.',
     FORCING % (B_WITH_M, C_PLAIN, F_RIGHT_FIRST)),
    ('a03-forcing-rejected',
     'with `twins` alone: as today (rejected). With `cleanfirst`: ACCEPTED, in base and in '
     'FULL: a known change of verdict',
     A2 + 'The mirror image of a01: the discarded fork looks `m` up in C, and C.m mentions the '
     'alias X in its signature, so the alias is entered first and the self-reference is '
     'reported, although that fork contributes nothing to the solution. `cleanfirst` cancels '
     'the fork before the lookup. a04 shows the verdict without that lookup.',
     FORCING % (B_PLAIN, C_WITH_M, F_WRONG_FIRST)),
    ('a04-forcing-rejected-swapped',
     'as today with every flag (accepted)',
     'a03 with the two candidates of `f` swapped: the discarded fork is cancelled by the '
     'existing solver before it looks `m` up in C.',
     FORCING % (B_PLAIN, C_WITH_M, F_RIGHT_FIRST)),
    ('a05-forcing-base-only',
     'with `twins` alone: as today. With `cleanfirst`: base becomes REJECTED (as a06); FULL is '
     'unchanged (rejected in both orders, because `extorder` reports the cycle whichever '
     'declaration is entered first)',
     A2 + 'As a01, but `extension X` does not declare `m`. Without `extorder` a member lookup '
     'evaluates every extension, so the discarded fork still decides which declaration is '
     'entered first.',
     BASE_ONLY % F_WRONG_FIRST),
    ('a06-forcing-base-only-swapped',
     'as today with every flag',
     'a05 with the two candidates of `f` swapped.',
     BASE_ONLY % F_RIGHT_FIRST),
    ('a07-lookahead-forcing',
     'with `twins` and with `cleanfirst`: as today (rejected). With `lookahead`: ACCEPTED, in '
     'base and in FULL: a known change of verdict',
     A2 + 'This program has no cyclic definition (X is Int). Today, in the fork of h -> C, the '
     'lookup of `m` in K comes before the failing argument of `two`: K.m mentions the alias X, '
     'the alias is entered first, its definition needs `A is P`, which enumerates the given '
     '`Foo<X> is P`, and the checker reports a self-reference. The look-ahead asks '
     '`coerced(C, B)` when the set of `k` is popped, before that lookup; the coercion '
     'enumerates the givens first, which computes X in the accepting order. a08 has the same '
     'goals with the failing coercion placed before the lookup, and is accepted today.',
     LOOKAHEAD % 'two(h(), k().m())'),
    ('a08-lookahead-forcing-early',
     'as today with every flag (accepted)',
     'a07 written so that the argument that cannot be coerced is checked before `m` is looked '
     'up in K, which is the order of Typer queries that `lookahead` produces for a07.',
     LOOKAHEAD % 'pair(two1(h()), k().m())'),
    ('a09-twin-separated',
     'as today (accepted, the extension member is chosen); solver.forks=3 and '
     'solver.twinsReused=0 with `twins` alone; solver.forks=2 with `twins,cleanfirst`',
     'Three candidates in the order member, extension member, trait requirement; the first '
     'and the third have the same type and both fail at the argument. With `twins` alone the '
     'third must not reuse the first: the first was explored under best = worst and ran to a '
     'solution with one diagnostic; under best = 0 the fork is cancelled (rule T1 needs the '
     'same bound, rule T4 an exploration without any failure). A reuse would put a solution '
     'with a diagnostic in `viable`.',
     THREE % 'A1'),
    ('a10-twin-spotless',
     'as today (accepted, and the same declaration bound to `m`: compare the dump of step 0); '
     'solver.forks=2 and solver.twinsReused=1 with `twins` alone',
     'As a09 with the argument that the two candidates of the same type accept. The member is '
     'explored under best = worst without any failure, so its result holds under any bound '
     '(rule T4); the requirement reuses it although best is now 0. Checks that the rebinding '
     'keeps the choice between member and requirement.',
     THREE % 'A0'),
    ('a11-twins-over-errors',
     'as today (accepted); solver.forks at most 84 with `twins` alone and 12 with '
     '`twins,cleanfirst` (model)',
     'Method chain (member and requirement of the same type) whose arguments are overloaded '
     'calls with the right candidate declared last. The exploration of the first candidate of '
     'each `step` contains failed goals, so rule T4 does not apply to it and only T1 fires '
     '(deeper, where best is already 0). The model of the existing solver predicts the '
     '136 forks and 51 sets of the binary.',
     OVER_ERRORS),
]


def main():
    scratch = os.path.join(ROOT, 'results', 'scratch')
    os.makedirs(scratch, exist_ok=True)
    for name, expected, reason, body in TESTS:
        header = wrap('// expected after the change:', expected) + wrap('// reason:', reason)
        placeholder = '// currently (base): ?\n// currently (FULL): ?\n'
        tmp = os.path.join(scratch, name + '.hylo')
        open(tmp, 'w').write(header + placeholder + body)
        lines = ''
        for config in CONFIGS:
            r = run(tmp, config, 120)
            lines += '// currently (%s): %s\n' % (config, describe(r))
        assert lines.count('\n') == 2, name
        open(os.path.join(ROOT, 'tests', name + '.hylo'), 'w').write(header + lines + body)
        print(name, '|', lines.replace('\n', ' | '))


if __name__ == '__main__':
    main()
