# Implicit resolution for a fragment of Hylo: a specification

This document states, as inference rules, what implicit resolution should accept for a small, well-defined fragment of Hylo. It is written to be an *independent* source of expected verdicts: the rules are derived from the language's documented behaviour, from the compiler's own tests, and from what a sound type checker must do. They are not a transcription of the implementation.

Where the intended semantics could not be established from those sources, the text says **[GUESS n]** and the point is repeated in section 9, "Open questions for the language designers". A reader who disagrees with a guess can change one rule; `reference.py` follows this document rule by rule, and each rule is named in its comments.

## 1. Sources

| Source | What it establishes |
|---|---|
| `Tests/CompilerTests/positive/equality.hylo` | reflexivity, symmetry and transitivity of `==` |
| `positive/conformance-via-equivalence.hylo` | a conformance of `T` is a conformance of `U` when `T == U` |
| `positive/associated-type-equality.hylo` | `T.X` through a declared conformance reduces to its definition; `U.X` is `T.X` when `T == U` and only `T` has a conformance; equalities between associated types can be required |
| `negative/associated-type-inequality.hylo` | associated types through two different conformances are different, even on equal types |
| `positive/coercion-derivability-cache.hylo` | a premise `Box<T> == V` of a conformance is checked in the scope of use; congruence under `Pair<_, _>` |
| `research/report/techniques/eqsolve.md` | the implementation's equality theory has no injectivity |
| first principles | soundness with respect to the model of section 6; invariance under renaming, declaration order, requirement order and the orientation of `==` |

## 2. The fragment

### 2.1 Types

```
A, B ::= T                    generic parameter of the enclosing function (rigid)
       | S<A1, ..., An>       nominal type of arity n >= 0 (a struct)
       | {A1, ..., An}        tuple type, n >= 2 (optional part of the fragment)
       | A.X                  associated type X of a trait P, on A (section 5)
```

A parameter is *rigid*: inside the function it stands for one unknown type, and it is never instantiated by resolution.

### 2.2 Declarations

```
trait P { type X }                         a trait, with at most one associated type
struct S<E1, ..., En> { ... }              a nominal type
given <a1, ..., ak where R1, ..., Rm> => H is P { type X = E }      a conformance declaration
```

In a conformance declaration, `a1..ak` are its parameters, `H` its head type, and each premise `R` is `A is Q` or `A == B`. The fragment requires that:

- every parameter occurs in `H` (so that matching `H` determines the instance);
- no two declarations have the same trait and the same head constructor (no overlap between declarations);
- `E` contains no associated type.

A declaration with `k = 0` and `m = 0` is *ground*; with `k > 0` and `m = 0`, *generic*; with `m > 0`, *conditional*. The head may be a bare parameter: `given <a where a is Q> => a is P`.

### 2.3 Scopes and goals

A *query* is a generic function with parameters and a where clause, whose body states one goal:

```
fun q<T1, ..., Tn where R1, ..., Rm>() { ... goal ... }
R ::= A is P | A == B
```

The *scope* Γ of the body consists of the conformance declarations of the program and the requirements `R1..Rm`. There are three kinds of goals:

| Goal | Source form | Read as |
|---|---|---|
| conformance | `need<A>()` where `fun need<W where W is P>()` | find a witness of `P<A>` |
| equality | `needEq<A, B>()` where `fun needEq<X, Y where X == Y>()` | prove `A == B` |
| coercion | `check<B>(x)` with `x: A`, where `fun check<X>(x: X)` | use a value of type `A` where `B` is expected |

Not in the fragment: inferred type arguments, givens declared inside functions, equality givens with parameters or premises, trait refinement, extensions, overloading, existential types, and the ranking of derivations beyond section 4.3.

## 3. Equality

The judgment `Γ ⊢ A == B` is defined by five rules.

```
                                Γ ⊢ A == B              Γ ⊢ A == B    Γ ⊢ B == C
REFL  ─────────────       SYM  ────────────      TRANS ──────────────────────────
       Γ ⊢ A == A               Γ ⊢ B == A                     Γ ⊢ A == C

       (A == B) is a requirement of Γ               Γ ⊢ A1 == B1   ...   Γ ⊢ An == Bn
FACT  ────────────────────────────────      CONG  ─────────────────────────────────────────
              Γ ⊢ A == B                           Γ ⊢ S<A1, ..., An> == S<B1, ..., Bn>
```

- `CONG` also applies to tuples of the same length: `{A1, ..., An} == {B1, ..., Bn}`.
- In `FACT`, the requirement is taken after its associated types have been given their meaning (section 5).
- The rules are symmetric by construction: the direction in which a requirement is written, and the order of the requirements, cannot matter.

**There is no injectivity rule.** `Box<A> == Box<B>` does not give `A == B`, and there is no conflict rule either: `Box<A> == Pair<B, C>` gives nothing more than itself. This choice mirrors the implementation (`eqsolve.md`: "The search uses no injectivity rule"). **[GUESS 1]** Section 6 explains what the choice costs, and it is the first open question.

**Deciding it.** All terms are closed, since parameters are rigid, so the theory is that of ground equations with uninterpreted constructors. It is decided by congruence closure. `reference.py` uses the textbook algorithm without optimization (class `EGraph`).

**Coercion and equality goals.** The fragment has no subtyping, so:

```
        Γ ⊢ A == B                              Γ ⊢ A == B
EQ-GOAL ──────────────────────      COERCE ─────────────────────────────────────────
        needEq<A, B>() is accepted          a value of type A is accepted where B is expected
```

Both goals are accepted *exactly* when `A == B` is derivable. In particular an equality goal and a coercion between the same two types must have the same verdict.

**[GUESS 2]** A tuple is a constructor of fixed arity. The implementation represents `{A, B, C}` as a list, `A` followed by `{B, C}`, so its congruence also derives `{A, B, C} == {A, D, E}` from `{B, C} == {D, E}`. That conclusion holds in every model of section 6, but it is not derivable here.

## 4. Conformance

### 4.1 Rules

The judgment `Γ ⊢ d : P<A>` reads "`d` is a derivation of the conformance of `A` to `P`".

```
      (A is P) is requirement number i of Γ        Γ ⊢ A == B
REQ  ────────────────────────────────────────────────────────────
                       Γ ⊢ req(i) : P<B>


      declaration number j is   given <a where R1, ..., Rm> => H is P
      σ maps the parameters a to types          Γ ⊢ Hσ == B
      for each premise (A' is Q):    Γ ⊢ dk : Q<A'σ>
      for each premise (L == R):     Γ ⊢ Lσ == Rσ
DECL ───────────────────────────────────────────────────────────────────
                       Γ ⊢ decl(j, σ, d1, ..., dm') : P<B>
```

Three points deserve attention.

1. **A witness is transported along equalities.** Both rules conclude for any `B` equal to the type the given speaks about. This is `conformance-via-equivalence.hylo`: from `T == U` and `T is P`, the call `g<U>()` is accepted.
2. **Matching is modulo equality.** `DECL` does not ask that `H` match `B` syntactically, only that some instance of `H` be equal to `B`. With `given <a where a is P> => Box<a> is P`, the requirements `Box<T> == U` and `T is P` give `U is P`: take `σ(a) = T`, and `Box<T> == U` is a fact. A checker that only decomposes `B` structurally cannot find this derivation. **[GUESS 3]** The language's tests do not include such a case, but rule 1 implies it: `Box<T> is P` is derivable, and `Box<T> == U`.
3. **Premises are goals in the same scope.** A premise `a is Q` instantiated to `T` may itself be satisfied through an equality (`T == U`, `U is Q`).

### 4.2 When two derivations are the same

Derivations are compared *up to the equality theory*: the proofs of the `==` premises are irrelevant, and two instances `σ`, `σ'` of a declaration are the same if `Γ ⊢ σ(a) == σ'(a)` for every parameter. So `decl(j, σ, d...)` and `decl(j', σ', d'...)` are the same derivation iff `j = j'`, `σ` and `σ'` are equal in this sense, and the premise derivations are pairwise the same; and `req(i)` is the same as `req(i')` iff `i = i'`.

**[GUESS 4]** This is the coarsest identity under which the associated types of section 5 are well defined. Note that without injectivity two instances can differ although their heads are equal: with `Box<A> == Box<B>`, the instances `a := A` and `a := B` of `Box<a> is P` are two derivations of `P<Box<A>>`.

### 4.3 Acceptance of a conformance goal

```
CONF-GOAL    need<A>() is accepted   iff   P<A> has a derivation and one of them is selected
```

- **No derivation:** rejected. This case is unambiguous.
- **Exactly one derivation:** accepted. This case is unambiguous.
- **Several derivations:** the outcome depends on a *ranking* of derivations. **[GUESS 5]** This specification does not define the ranking. It only assumes that the ranking is invariant under the symmetries of the rules: renaming parameters, reordering requirements and declarations, and swapping the two sides of an equality requirement. Consequently, when a symmetry of the problem exchanges two derivations and fixes the goal, no ranking can separate them, and the goal must be rejected as ambiguous. Example (`e01b-both-direct.hylo`):

  ```hylo
  fun f<A, B, C where B is P, C is P, B == A, C == A>() { g<A>() }   // ambiguous: B and C play the same role
  ```

  `reference.py` reports the number of distinct derivations (up to 3). `fuzz.py` builds problems of this symmetric shape on purpose (kind `twin`), and for them the expected verdict is "rejected".

For information, the existing implementation ranks by the number of search steps and then by a sum of lexical-scope offsets, and reports a tie as an error. The number of steps depends on the orientation of equalities (using `A == C` backwards costs a symmetry step), which is how `e01-orient-amb.hylo`, the program above with `A == C` in place of `C == A`, comes to be accepted.

## 5. Associated types

### 5.1 An associated type belongs to a witness

A trait `P` with `type X` gives every *derivation* `d` of a conformance to `P` an associated type, written `X(d)`. The type on which `d` witnesses the conformance is not part of `X(d)`.

```
          Γ ⊢ decl(j, σ, d...) : P<B>     declaration j defines  type X = E
PROJ-DECL ──────────────────────────────────────────────────────────────────
                          Γ ⊢ X(decl(j, σ, d...)) == Eσ

PROJ-REQ  X(req(i)) is an atom: a type about which nothing is known but the requirements of Γ.
```

- `PROJ-DECL`: with `given A is P { type X = B }`, `X(decl) == B`; with `given <a> => Box<a> is P { type X = a }`, the associated type of the instance `a := T` is `T`.
- `PROJ-REQ`: for `T is P` in a where clause, `X(req)` is opaque. It is equal to itself, and to whatever the where clause equates it with (`T.X == U`), through `FACT`.
- **No other rule.** In particular there is no rule concluding `X(d) == X(d')` for two different derivations, *even when they witness the conformance of equal types*. This is `associated-type-inequality.hylo`:

  ```hylo
  fun f0<T, U where T == U, T is P, U is P>(x: U.X) { check<T.X>(x) }   // rejected
  ```

  The function receives two conformances, and nothing says that they agree. The rule is also what makes scoped conformances sound: two witnesses of `P<A>` may come from two different declarations.
- By section 4.2, the same derivation always has the same associated type, whatever the type it is used at: with `T == U` and only `T is P`, both `T.X` and `U.X` are `X(req)` (`associated-type-equality.hylo`, function `f1`).

### 5.2 The meaning of `A.X` in source

```
       P is the trait declaring X      d = select(Γ, P<A>)
PROJ  ─────────────────────────────────────────────────────
                    A.X  denotes  X(d)
```

where `select(Γ, P<A>)` is:

- the derivation of `P<A>`, if there is exactly one;
- **[GUESS 6] (rule DIRECT)** if there are several, the requirement `A is P` written on exactly the type `A`, if there is exactly one such requirement;
- otherwise undefined, and `A.X` *denotes no type*: a goal that mentions it is rejected.

Rule DIRECT is forced by the negative test above. There `P<T>` has two derivations, `req(T is P)` and `req(U is P)` transported along `T == U`, yet the test's comment and its expected diagnostic treat `T.X` as "the associated type of `T`'s conformance". Some preference for the requirement stated on `T` itself is therefore part of the language. Its exact extent is open: section 9, question 4.

A consequence worth stating: with `given S is P { type X = Bool }`, the function `f<T where T == S, T is P>` has `T.X` opaque, not `Bool`. The requirement `T is P` is a second witness, and the caller may pass any conformance of `S`.

### 5.3 The where clause

The requirements of a where clause may mention associated types whose meaning depends on other requirements of the same clause (`T == U, T is P, U.X == V`). **[GUESS 7] (rule SCOPE)** The scope is built in stages: a requirement enters the scope as soon as every `A.X` it mentions denotes a type in the scope built so far; this is repeated until all requirements have entered. The where clause is well formed only if all requirements enter, and if every `A.X` denotes the same type in the final scope as at the stage at which it was given its meaning. `reference.py` answers "unspecified" otherwise, and the generator discards such problems.

### 5.4 `Self.X` inside a trait

Inside `trait P { type X ... }`, `Self` is a rigid parameter and the scope contains the requirement `Self is P`, the trait's own witness; `X` and `Self.X` denote `X(self)` by rule DIRECT. Under the rules above, a method

```hylo
trait P { type X
  fun f<T where T == Self, T is P>() { needEq<Self.X, T.X>() } }
```

is **rejected**: `T is P` is a second witness, exactly as in `associated-type-inequality.hylo` with `Self` in place of `U`. **[GUESS 8]** The implementation disagrees: its unifier lets `Self.X` match any `T.X` with `T == Self`, and the equality procedure of `eqsolve` equates them when the scope has exactly one other conformance of a type equal to `Self`. That rule is not derivable from the others, and it is not monotone in the scope (adding the requirement `U is P` with `U == Self` withdraws the equality). This specification keeps the uniform rule; the programs `v-abs-*.hylo` and `abs-trans-*.hylo` of the test programs are where the two differ (README, "Self.X").

The fragment tested by `fuzz.py` has no trait bodies; this rule is covered by hand-written cases only.

## 6. The model, and what "unsound" means

The rules are meant to be sound for the following model. A type is a finite tree built from nominal types and tuples. A function may be called with any assignment of types to its parameters, and of witnesses to its conformance requirements, that satisfies its where clause. A goal is *valid* if it holds for every such call.

In this model constructors are free, so three more principles hold that section 3 does not have:

```
       Γ ⊢ S<A1..An> == S<B1..Bn>              Γ ⊢ S<...> == S'<...>   S ≠ S'          Γ ⊢ T == S<... T ...>
INJ   ─────────────────────────────  CONFLICT ──────────────────────────────  OCCURS ─────────────────────────
              Γ ⊢ Ai == Bi                          Γ ⊢ anything                         Γ ⊢ anything
```

The last two say that a where clause without any solution makes the function uncallable, so that every goal in its body is vacuously valid.

Validity in the model is decidable for the fragment: unify the equality requirements, treating parameters and opaque associated types as variables; if there is no unifier the scope is *vacuous*; otherwise apply the unifier everywhere and decide the goal syntactically (`reference.semantic`). This gives three grades for a goal:

| Grade | Meaning | A checker that accepts it is |
|---|---|---|
| derivable | derivable by sections 3 to 5 | correct |
| valid, not derivable | needs INJ, or the scope is vacuous | not unsound, but beyond this specification (question 1) |
| invalid | false for some call | **unsound** |

The converse classification for rejections: rejecting a goal that has exactly one derivation is an *incompleteness* with respect to this specification.

## 7. What a verdict means, in terms of the reference

`reference.answer(world, query)` returns:

| Field | Meaning |
|---|---|
| `verdict` | `derivable`, `underivable`, `illformed-goal` (an `A.X` in the goal denotes no type), or `unspecified` (section 5.3, or the search bound was reached) |
| `count` | for a conformance goal, the number of distinct derivations (capped at 3) |
| `size` | the number of `REQ` and `DECL` steps in a smallest derivation |
| `eq_needed` | the smallest number of equality requirements that still make the goal derivable |
| `congruence` | whether `CONG` is necessary |
| `sem` | the grade of section 6: `valid`, `invalid` or `vacuous` |

Conformance derivations are searched exhaustively to height 12; a problem on which that bound is reached is reported `unspecified`, never `underivable`.

## 8. Properties that follow, usable as tests

1. **Symmetry.** Swapping the sides of any equality requirement, or permuting requirements, changes no verdict.
2. **Monotonicity of equality.** Adding a requirement never makes a derivable equality or coercion underivable. (It can make a conformance goal ambiguous, and it can change the meaning of an `A.X`.)
3. **Agreement of goals.** `needEq<A, B>()` and the coercion from `A` to `B` have the same verdict.
4. **Transport.** If `A == B` is derivable, then `P<A>` and `P<B>` have the same derivations.
5. **Conservativity.** Adding an unrelated equality (one whose sides share no parameter with the goal or with the requirements it uses) changes no verdict.

## 9. Open questions for the language designers

1. **Injectivity and uncallable functions (GUESS 1).** Should `Box<A> == Box<B>` give `A == B`? Every model says yes; the implementation and this specification say no. Should a where clause with no solution (`Box<A> == Pair<B, C>`, `T == Box<T>`) be an error at the declaration? Today it is accepted, and the body is checked as if it were callable.
2. **How complete must the checker be (GUESS 3)?** The rules derive `U is P` from `Box<T> == U`, `T is P` and the conditional conformance of `Box`, and `C` coerces to `Box<B>` from `Box<A> == C`, `A == B`. A checker that looks only at the syntactic parts of the goal rejects both. Is the checker required to accept everything derivable by congruence, or may it reject when the needed term is not written in the scope? If the latter, the language needs a rule stating which uses are accepted, because the current behaviour is not symmetric (README, incompleteness classes).
3. **Ranking and ambiguity (GUESS 5).** When a conformance goal has several derivations, which one is selected, and when is it an error? The specification needs a ranking that does not depend on the orientation of `==` or on the order of requirements.
4. **The preference for a requirement stated on the type itself (GUESS 6).** Is `T.X`, with `T == U, T is P, U is P`, the associated type of `T`'s requirement (as the negative test assumes), or ambiguous? Does the same preference apply to conformance goals (`need<T>()` in that scope), and does a requirement win over a declaration (`T == S, T is P`, with `given S is P`)?
5. **Identity of derivations (GUESS 4).** Are two instances of a generic conformance at equal types the same witness? At types whose equality is not derivable but whose heads are (`Box<A> == Box<B>`)?
6. **`Self.X` (GUESS 8).** Inside a trait, is `Self.X` equal to `T.X` when `T == Self` and `T is P`? The uniform answer is no. The implementation says yes in some scopes.
7. **Staging of the where clause (GUESS 7).** In which order do requirements acquire their meaning? May a requirement added later change the meaning of an `A.X` written earlier?
8. **Tuples (GUESS 2).** Is congruence on the tail of a tuple intended?
9. **The depth bound.** The implementation abandons a search after 10 steps. Is the bound part of the language? This specification has none; `fuzz.py` keeps derivations small so that the bound should not matter, and records the size.
10. **Where `A.X` is looked up.** `U.X` with `Box<T> == U` and a conformance of `Box` denotes a type by rule PROJ. The implementation reports "type 'U' has no static member 'X'": member lookup does not use resolution modulo equality. Which is intended?
11. **Coherence.** Is it intended that a declared conformance of `S` and a requirement `T is P` with `T == S` are unrelated (section 5.2, last paragraph)? It follows from scoped conformances, but it surprises: `T.X` is `Bool` without the requirement and opaque with it.
