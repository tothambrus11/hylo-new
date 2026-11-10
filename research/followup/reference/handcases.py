"""Hand-written problems, with the verdict expected from the specification by reasoning.

Each case is (name, original program or None, text in the notation of dsl.py). When an original
program is named, the case transcribes it, and validate.py also checks that the compiler gives
the printed program and the original the same verdict. Expectations: D derivable, U underivable,
I ill-formed goal, D2 derivable in two or more ways, ? unspecified.
"""

EQ = "/home/user/hylo-new/research/report/test-programs/equalities/"
POS = "/home/user/hylo-new/Tests/CompilerTests/positive/"
NEG = "/home/user/hylo-new/Tests/CompilerTests/negative/"

CASES = [
    ("conf-basic", None, """
trait P
trait Q
struct A
struct B
struct Box 1
struct Pair 2
given A is P
given [T: T is P] Box<T> is P
given [T U: T is P, U is Q] Pair<T, U> is P
query [] Box<Box<A>> is P                      # expect: D
query [] Box<B> is P                           # expect: U
query [T: T is Q] Pair<A, T> is P              # expect: D
query [T: T is P] Pair<A, T> is P              # expect: U
query [T] Box<T> is P                          # expect: U
query [T: T is P] Box<Box<T>> is P             # expect: D
query [] A is Q                                # expect: U
"""),
    ("equality.hylo", POS + "equality.hylo", """
query [T] T == T                               # expect: D
query [T U: T == U] U == T                     # expect: D
query [T U V: T == U, U == V] T == V           # expect: D
"""),
    ("conformance-via-equivalence.hylo", POS + "conformance-via-equivalence.hylo", """
trait P
query [T U: T == U, T is P] U is P             # expect: D
"""),
    ("c01-single-eq-call", EQ + "c01-single-eq-call.hylo", """
query [V W D: V == W] D == V                   # expect: U
"""),
    ("n-params-2", EQ + "n-params-2.hylo", """
query [A B C D: A == B, C == D] A == D         # expect: U
"""),
    ("v02-params", EQ + "v02-params.hylo", """
query [A B C D: A == B, C == D] D -> A         # expect: U
"""),
    ("v07-samegiven", EQ + "v07-samegiven.hylo", """
query [A B C: A == B, A == C] C -> B           # expect: D
"""),
    ("v-chain3-mixed", EQ + "v-chain3-mixed.hylo", """
query [A B C D: A == B, C == B, C == D] D -> A # expect: D
"""),
    ("decomp-1", EQ + "decomp-1.hylo", """
struct Box 1
query [A B: Box<A> == Box<B>] Box<A> -> Box<B> # expect: D
"""),
    ("decomp-2", EQ + "decomp-2.hylo", """
trait P
struct Box 1
query [A B: Box<A> == Box<B>, Box<A> is P] Box<B> is P    # expect: D
"""),
    ("decomp-3", EQ + "decomp-3.hylo", """
struct Box 1
struct Pair 2
struct I
query [A B C: Box<A> == C] Pair<Box<A>, I> -> Pair<C, I>  # expect: D
"""),
    ("quant-2", EQ + "quant-2.hylo", """
struct Box 1
query [A B C: Box<A> == C, A == B] C -> Box<B>            # expect: D
"""),
    ("quant-2b", EQ + "quant-2b.hylo", """
struct Box 1
query [A C: Box<A> == C] C -> Box<A>                      # expect: D
"""),
    ("no-injectivity", None, """
struct Box 1
query [A B: Box<A> == Box<B>] A == B                      # expect: U
query [A B: Box<A> == Box<B>] A -> B                      # expect: U
query [A B: Box<A> == Box<B>] Box<Box<A>> == Box<Box<B>>  # expect: D
"""),
    ("transconf-3", EQ + "transconf-3.hylo", """
trait P
query [T0 T1 T2 T3: T0 == T1, T1 == T2, T2 == T3, T0 is P] T3 is P   # expect: D
"""),
    ("e01b-both-direct", EQ + "e01b-both-direct.hylo", """
trait P
query [A B C: B is P, C is P, B == A, C == A] A is P      # expect: D2
"""),
    ("e01-orient-amb", EQ + "e01-orient-amb.hylo", """
trait P
query [A B C: B is P, C is P, B == A, A == C] A is P      # expect: D2
"""),
    ("a05-quantified", EQ + "a05-quantified.hylo", """
trait P
struct Box 1
given [T] Box<T> is P
query [T U V: T == U, U == V] Box<V> is P                 # expect: D
query [T U V: T == U, U == V] Box<T> == Box<V>            # expect: D
query [T U V: T == U, U == V] V == T                      # expect: D
"""),
    ("a09-conf-via-eq", EQ + "a09-conf-via-eq.hylo", """
trait P
trait Q
given [T: T is P] T is Q
query [T U: T == U, T is P] U is P                        # expect: D
query [T U: T == U, T is P] U is Q                        # expect: D
query [T U V: T == U, V == U, T is P] V is P              # expect: D
query [T U V: T == U, V == U, T is P] V is Q              # expect: D
"""),
    ("a06-tuple", None, """
query [T U: T == U] {T, U} == {U, T}                      # expect: D
query [T U: T == U] {T, U} -> {U, T}                      # expect: D
query [T U] {T, U} == {U, T}                              # expect: U
query [T U V: {T, U} == V] {T, U} -> V                    # expect: D
"""),
    ("ematch", None, """
trait P
struct Box 1
given [T: T is P] Box<T> is P
query [T U: Box<T> == U, T is P] U is P                   # expect: D
query [T U: Box<T> == U] U is P                           # expect: U
query [T U V: Box<T> == U, V is P, V == T] U is P         # expect: D
query [T U: T == U, U is P] Box<T> is P                   # expect: D
query [T U: T == U, U is P] Box<Box<T>> is P              # expect: D
"""),
    ("premise-eq", None, """
trait P
struct A
struct Box 1
struct Pair 2
given [T U: T == U] Pair<T, U> is P
given [T: T == A] Box<T> is P
query [] Pair<A, A> is P                                  # expect: D
query [] Pair<A, Box<A>> is P                             # expect: U
query [T U: T == U] Pair<T, U> is P                       # expect: D
query [T U] Pair<T, U> is P                               # expect: U
query [T: T == A] Box<T> is P                             # expect: D
query [T] Box<T> is P                                     # expect: U
query [] Box<A> is P                                      # expect: D
"""),
    ("cong-0", EQ + "cong-0.hylo", """
trait P X
query [T U: T == U, T is P] U.X -> T.X                    # expect: D
"""),
    ("cong-1", EQ + "cong-1.hylo", """
trait P X
query [T U V: T == U, T is P, V == U.X] V -> T.X          # expect: D
"""),
    ("associated-type-inequality.hylo", NEG + "associated-type-inequality.hylo", """
trait P X
query [T U: T == U, T is P, U is P] U.X -> T.X            # expect: U
"""),
    ("associated-type-equality.hylo", None, """
trait P X
struct V
given V is P = V
query [T: T == V] T.X -> V                                # expect: D
query [T U: T == U, T is P] U.X -> T.X                    # expect: D
query [T U: T == U, T is P, U is P, T.X == U.X] U.X -> T.X    # expect: D
"""),
    ("assoceq-2", EQ + "assoceq-2.hylo", """
trait P X
query [T0 T1 T2: T0 is P, T1 is P, T2 is P, T0.X == T1.X, T1.X == T2.X] T2.X -> T0.X   # expect: D
"""),
    ("assocneg-3", EQ + "assocneg-3.hylo", """
trait P X
query [T0 T1 T2 T3: T0 is P, T1 is P, T2 is P, T3 is P, T0.X == T1.X, T2.X == T3.X] T3.X -> T0.X   # expect: U
"""),
    ("transneg-2", EQ + "transneg-2.hylo", """
trait P X
query [T0 T1 T2: T0 == T1, T1 == T2, T0 is P, T2 is P] T2.X -> T0.X     # expect: U
"""),
    ("v03-box", EQ + "v03-box.hylo", """
trait P X
struct Box 1
query [A B C D: A is P, B is P, C is P, D is P, A.X == B.X, C.X == D.X] Box<D.X> -> Box<A.X>   # expect: U
"""),
    ("v-def-1", EQ + "v-def-1.hylo", """
trait P X
struct S
struct Bo
given S is P = Bo
query [T: T == S] T.X == Bo                               # expect: D
"""),
    ("v-def-3", EQ + "v-def-3.hylo", """
trait P X
struct S
struct Bo
given S is P = Bo
query [T U: T == U, U == S, T is P] T.X == Bo             # expect: U
"""),
    ("v-congr-1", EQ + "v-congr-1.hylo", """
trait P X
query [T U: T == U, T is P, U is P] T.X == U.X            # expect: U
"""),
    ("quant-1", EQ + "quant-1.hylo", """
trait P X
struct Box 1
query [A B: A == B, A is P] Box<B.X> -> Box<A.X>          # expect: D
"""),
    ("a08-assoc-generic", None, """
trait P X
query [T U: T is P, T.X == U] T.X -> U                    # expect: D
query [T U: T is P, T.X == U] U -> T.X                    # expect: D
query [T U: T is P, T.X == U] T.X == U                    # expect: D
query [T U V: T is P, T.X == U, U == V] T.X -> V          # expect: D
query [T U: T is P] T.X -> U                              # expect: U
"""),
    ("assoc-decl", None, """
trait P X
trait Q
struct A
struct B
struct Box 1
given A is P = B
given [T] Box<T> is P = T
given B is Q
query [] A.X == B                                         # expect: D
query [] A.X is Q                                         # expect: D
query [T: T is P, T.X is Q] T.X is Q                      # expect: D
query [T U: T is P, U is P, T.X == U.X, T.X is Q] U.X is Q    # expect: D
query [T U: T is P, U is P, T.X is Q] U.X is Q            # expect: U
query [T: T == A] T.X == B                                # expect: D
query [T: T == A, T is P] T.X == B                        # expect: U
query [T U: T == Box<U>] T.X == U                         # expect: D
query [T U: Box<U> == T] T.X == U                         # expect: D
query [T U: T == Box<U>] T.X -> U                         # expect: D
query [T U] T.X == U                                      # expect: I
query [T U: T is P, U is P] T.X -> U.X                    # expect: U
query [T: T is P] T.X -> T.X                              # expect: D
"""),
    ("ambiguity", None, """
trait P
struct A
struct Box 1
given A is P
given [T] Box<T> is P
given Box<A> is P
query [T U: T is P, U is P, T == U] T is P                # expect: D2
query [T U V: T is P, U is P, T == V, U == V] V is P      # expect: D2
query [T U V: T is P, U is P, T == V, V == U] V is P      # expect: D2
query [T U V: T is P, U is P, V == T, V == U] V is P      # expect: D2
query [] Box<A> is P                                      # expect: D2
query [T] Box<T> is P                                     # expect: D
query [T: T == A, T is P] T is P                          # expect: D2
"""),
    ("goal-agreement", None, """
struct Box 1
query [A B C: Box<A> == C, A == B] C == Box<B>            # expect: D
query [A B C: Box<A> == C, A == B] C -> Box<B>            # expect: D
query [A B: Box<A> == Box<B>] Box<Box<A>> == Box<Box<B>>  # expect: D
query [A B: Box<A> == Box<B>] Box<Box<A>> -> Box<Box<B>>  # expect: D
"""),
    ("tuple-tail", None, """
query [A B C D E: {B, C} == {D, E}] {A, B, C} == {A, D, E}    # expect: U
query [A B C D E: {B, C} == {D, E}] {A, B, C} -> {A, D, E}    # expect: U
query [A B C D E: {B, C} == {D, E}] {B, C, A} == {D, E, A}    # expect: U
query [A B C D E: {B, C} == {D, E}] {A, {B, C}} == {A, {D, E}}    # expect: D
"""),
    ("blanket", None, """
trait Q
trait P X
struct S
struct R
given S is Q
given R is Q
given [A: A is Q] A is P = A
query [T U: T is Q, U is Q] T.X == U.X                    # expect: U
query [T U: T is Q, U is Q] T.X -> U.X                    # expect: U
query [] S.X -> R.X                                       # expect: U
query [T: T is Q] T.X == T                                # expect: D
query [] S.X == S                                         # expect: D
query [T: T is Q] T.X -> T.X                              # expect: D
"""),
    ("where-order", None, """
trait P X
struct S
query [T: T is P, T.X == S] T.X == S                      # expect: D
query [T: T.X == S, T is P] T.X == S                      # expect: D
query [T: T is P, T.X is P] T.X is P                      # expect: D
query [T: T.X is P, T is P] T.X is P                      # expect: D
"""),
    ("budget", None, """
trait P
struct S0
struct S1
struct S3 2
given S1 is P
given [A: A == S0, A is P] S3<S0, A> is P
query [T U: U == T] S3<U, S0> is P                        # expect: U
query [T U] S3<U, S0> is P                                # expect: U
query [] S3<S0, S0> is P                                  # expect: U
"""),
    ("proj-through-application", None, """
trait P X
struct S
struct Box 1
given [A] Box<A> is P = A
query [T U: T == Box<U>] T.X == U                         # expect: D
query [T: T == Box<S>] T.X == S                           # expect: D
query [T U: T == Box<U>] T is P                           # expect: D
"""),
]
