# Metamorphic testing of the type checker

## What was asked

Apply, systematically, eight transformations that should not change whether a program type-checks, and compare the verdicts. Each of them had exposed a defect once when applied by hand. For every change of verdict: reduce the program, check that the transformed program is a correct instance of the relation, and decide whether the change is legitimate in this language or a defect, and in which configuration.

## Summary

- The tool checked 15,206 variants of 760 programs under FULL. The verdict changed for 370 variants. They reduce to eleven causes: eight defects (D1 to D8 below) and three changes that are legitimate in this language (L1 to L3).
- **No violation is specific to the optimizations.** Every verdict change under FULL also occurs under FIX. FULL and FIX never differed on the variants that were run under both.
- **Most defects are in the existing checker** and are untouched by the fixes: the left-to-right reading of where clauses (D3), ambiguity decided by derivation length (D2, D4, D5), opaque generic aliases (D7), cycles through an alias (D1, D8).
- **Three effects come from the fixes**: the resource bound makes acceptance depend on the order of requirements (D6); the rule against circular extensions is avoided by naming the extended type through an alias (D8); the occurs check does not look under a generic alias (D7).
- Relations 3 (order of members) and 6 (renaming) never changed a verdict. Relation 8 (unrelated declaration) changed it only where a call leaves a type argument to be inferred from the conformances in scope (L3).
- Declaration order: the same seven programs as in the pilot, and no other, among 727 programs. Relation 5 produced 16 more order-dependent programs, by introducing an alias. All of them are cycles through a type alias or through a given; cycles through extensions only are handled.

## What was done

`metamorphic.py` generates the variants of a program for one relation, type-checks the original and each variant with `tc-bench` (one process at a time, 60 s limit), and records one row per variant. A verdict is `accept`, `reject`, `crash:<code>` or `timeout`. A row is a *violation* when the verdict of the variant differs from the verdict of the original. When the verdicts agree but the sets of error messages differ (source positions removed), the row is marked `messages_differ`.

Every transformation edits the original text; nothing is re-printed from a syntax tree, so comments, whitespace and operator spacing are preserved. `hylosyn.py` is a lexer that follows the compiler's lexer, plus a parser of the declaration structure (declarations, type bodies, context clauses).

| File | Content |
|---|---|
| `metamorphic.py` | driver: `baseline`, `run`, `attribute`, `show` |
| `relations/r1_*.py` … `r8_*.py` | one module per relation; the docstring of each defines its variants |
| `hylosyn.py`, `common.py` | lexer and declaration parser; running `tc-bench`, cache, corpus |
| `reduce.py`, `reduce_all.py` | reduction of one violation; grouping and reduction of all of them |
| `report.py`, `causes.py`, `r1list.py` | the tables of this document, from the raw rows: per relation and per group; per cause; the order-dependent programs |
| `shapes.py`, `shapes/` | order test of ten hand-written programs, one per shape of dependency cycle |
| `tc.sh` | `./tc.sh (base\|FIX\|FULL) file.hylo` prints the diagnostics of one program |
| `data/baseline-FULL.jsonl` | original and re-printed verdict of each program |
| `data/rows-FULL.jsonl`, `rows-FIX.jsonl`, `rows-base.jsonl` | one row per variant |
| `data/done-FULL.jsonl` | one row per (program, relation): makes `run` restartable |
| `data/cache.jsonl` | every type-checker result, keyed by the hash of the program text |
| `data/summary.md` | output of `report.py`, including the list of all violating variants |
| `violations/<relation>/<program>--<variant>/` | `a.hylo` (reduced original), `b.hylo` (reduced variant), `info.json` (verdicts under the three configurations) |
| `violations/index.jsonl` | the violations grouped by signature, with the members of each group |

To reproduce a finding: `./tc.sh FULL violations/r7/e01-orient-amb--sym-2-2/a.hylo`, then the same with `b.hylo`, and with `base` or `FIX`.

### Programs

801 `.hylo` files: 538 test programs of the report, 204 compiler tests (123 positive, 81 negative) and 59 workloads. 723 of them are distinct texts. 41 are skipped: 32 have a syntax error in the original (transforming them is meaningless), 5 are larger than 20 kB (`builtins.hylo`, `members.hylo`, `members-big.hylo`, `breadth40.hylo`, `breadth80.hylo`) and 4 take more than 5 s under FULL. 760 programs remain.

### The relations

1. **Order of top-level declarations.** The reversal, the rotation by one, then other permutations.
2. **Order of requirements and of generic parameters.** `reqs`: a permutation of the requirements after `where`. `reqs-dep`: a permutation that keeps every requirement mentioning a projection `T.X` after the requirements that preceded it. `params`: a permutation of the generic parameters, only for conformances, extensions and functions never applied to explicit type arguments. `swap-names`: two generic parameters exchange their names throughout the declaration.
3. **Order of members** of a struct, enum, trait, extension or conformance body. Stored properties and enum cases keep their relative order.
4. **Tautology or unused parameter.** `X == X` added to the where clause of a function, conformance or extension, as the last or as the first requirement, where X is a generic parameter (`taut-param`), an associated type `T.X` (`taut-assoc`), a type application of the head such as `Box<T>` (`taut-app`) or a non-generic struct (`taut-ground`; a declaration without a context clause gets `<where A == A>`). `unused-param`: an extra generic parameter that nothing mentions.
5. **Type alias.** `intro-all`: every occurrence, in a type position, of a closed type expression (`A`, `Box<A>`, `A.Me`) is replaced by a new alias declared at the end of the file (`intro-all-top`: at the beginning; `intro-one`: only the first occurrence). `intro-generic`: `type Alq<T> = Box<T>` is declared and applications `Box<...>` are spelled `Alq<...>`. `expand`: every use of an existing non-generic alias is replaced by its definition (`expand-drop`: and the alias is removed).
6. **Renaming.** Every identifier token with the old name is replaced. `reverse`: every declared name gets a new name such that the alphabetical order of the names is reversed. `all`: every declared name gets a prefix. `one`: one name does. Names that the standard library declares or uses as labels are never renamed.
7. **Forms of an equality.** `sym`: `B == A` for `A == B`. `dup`: `A == B, A == B`. `dup-sym`: `A == B, B == A`.
8. **Unrelated declaration.** `conf`: a new struct and its conformance to an existing trait of the file (only traits without requirements other than associated types), added at the end. `struct-top`: a new struct at the beginning. `trait`: a new empty trait at the end (run for the programs that have no suitable trait for `conf`). Further kinds (`gconf`, a generic conformance of a new generic struct; a new extension; the same at the other end of the file) are implemented but were not run, for lack of machine time.

Each relation lists its variants in a fixed priority order and the driver checks the first *n* of them: 23 permutations for the 129 programs of the declaration-order set and 2 for the others (the pilot found nothing there with 24); 8 for relation 2 plus every `reqs-dep` variant, 6 for relations 3, 4 and 7, 8 for relation 5, 2 for relations 6 and 8. The random choices are seeded by the program text, so a run is reproducible.

### Validation of the declaration splitter

The pilot's splitter worked on lines and brace counts. The new one works on tokens: a declaration starts at an annotation, a modifier or an introducer, and ends at the closing brace of its body, at a `;`, or where the next declaration starts on a new line. It handles multi-line heads, modifiers on their own line, tuple types written with braces in a head (`given {Void, Void} is P {`), access effects after a parameter list (`fun f() inout -> T`) and `memberwise init`.

Three checks:
- the re-printed file (the identity permutation) has the same token sequence as the original, for all 796 files that are not too large;
- the re-printed file gets the same verdict and the same messages as the original under FULL, for all 796;
- no variant of any relation introduced a syntax error (the driver marks such a variant `invalid`; there are none among 15,206).

The eleven false reports of the pilot are gone: outside the declaration-order set, no program changes its verdict under relation 1 (two permutations each).

## Results

| Relation | Programs with a variant | Variants | Invalid variants | Programs with a verdict change | Variants with a verdict change | Programs with only messages changed | Variants with only messages changed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 order of top-level declarations | 727 | 3782 | 0 | 7 | 82 | 39 | 372 |
| 2 order of requirements and generic parameters | 341 | 1787 | 0 | 39 | 84 | 109 | 216 |
| 3 order of members | 120 | 197 | 0 | 0 | 0 | 0 | 0 |
| 4 tautology or unused parameter | 648 | 3087 | 0 | 105 | 125 | 128 | 271 |
| 5 type alias | 410 | 1790 | 0 | 47 | 61 | 142 | 379 |
| 6 renaming | 727 | 1424 | 0 | 0 | 0 | 0 | 0 |
| 7 forms of an equality | 314 | 1619 | 0 | 4 | 10 | 33 | 81 |
| 8 unrelated declaration | 760 | 1520 | 0 | 8 | 8 | 0 | 0 |

| Relation | Kind of variant | Variants | Verdict changes | Message-only changes |
|---|---|---:|---:|---:|
| r1 | permute | 3782 | 82 | 372 |
| r2 | params | 490 | 0 | 6 |
| r2 | reqs | 579 | 83 | 102 |
| r2 | reqs-dep | 263 | 1 | 7 |
| r2 | swap-names | 455 | 0 | 101 |
| r3 | members | 197 | 0 | 0 |
| r4 | taut-app | 258 | 2 | 14 |
| r4 | taut-assoc | 360 | 16 | 44 |
| r4 | taut-ground | 537 | 10 | 63 |
| r4 | taut-param | 1316 | 7 | 109 |
| r4 | unused-param | 616 | 90 | 41 |
| r5 | expand | 68 | 3 | 23 |
| r5 | expand-drop | 68 | 3 | 21 |
| r5 | intro-all | 610 | 7 | 115 |
| r5 | intro-all-top | 601 | 21 | 174 |
| r5 | intro-generic | 158 | 27 | 32 |
| r5 | intro-one | 285 | 0 | 14 |
| r6 | all | 697 | 0 | 0 |
| r6 | one | 30 | 0 | 0 |
| r6 | reverse | 697 | 0 | 0 |
| r7 | dup | 538 | 1 | 29 |
| r7 | dup-sym | 540 | 4 | 28 |
| r7 | sym | 541 | 5 | 24 |
| r8 | conf | 332 | 8 | 0 |
| r8 | struct-top | 760 | 0 | 0 |
| r8 | trait | 428 | 0 | 0 |

A program counts under "only messages changed" when none of its variants changes the verdict and at least one changes the set of messages. Most of these changes are inherent to the transformation, because messages print types and requirements as written (`(X ~ Y)` becomes `(Y ~ X)`), or name the alias. The ones that reveal something are mentioned under the defects.

### Causes

| | Cause | Relations | Variants | Programs | base | FIX | FULL | Class |
|---|---|---|---:|---:|---|---|---|---|
| D1 | Cycle through a type alias, or through a given and extensions: the verdict depends on declaration order | 1, 5 | 102 | 22 | yes | yes | yes | defect |
| D2 | The orientation of an equality decides between two derivations | 7 | 7 | 3 | yes | yes | yes | defect |
| D3 | A where clause is read from left to right | 2, 4 | 98 | 50 | yes | yes | yes | language decision; one case is a defect |
| D4 | A trivially true premise hides an ambiguity between two conformances | 4 | 8 | 4 | yes | yes | yes | defect |
| D5 | The position of a tautology in the callee decides the verdict of a call | 4 | 2 | 2 | yes | yes | yes | defect |
| D6 | The depth bound and the resource bound: one more step or another order exhausts them | 2, 4, 7 | 13 | 2 | partly | yes | yes | defect of the bounds |
| D7 | Generic type aliases are not transparent | 5 | 29 | 27 | yes | yes | yes | defect |
| D8 | A type alias changes the handling of cyclic lookups | 5 | 12 | 9 | yes, differently | yes | yes | defect |
| L1 | An unused generic parameter cannot be inferred | 4 | 90 | 84 | yes | yes | yes | legitimate |
| L2 | `T == T` for a type constructor `T :: * -> *` is ill-kinded | 4 | 1 | 1 | yes | yes | yes | legitimate |
| L3 | A type argument left open is inferred from the conformances in scope | 8 | 8 | 8 | yes (or crash) | yes | yes | legitimate |

The counts are produced by `causes.py`, which assigns each violating variant to a cause by relation, kind of variant, verdicts and messages.

`data/summary.md` gives, for each group of violations, how many of its members were run under FIX and base and what they gave. FIX agrees with FULL on every one of the 396 variants run under both. The existing checker differs from FULL on some members by not terminating (timeout) or by crashing, and in D8.

## The defects

### D1. Declaration order: cycles through an alias or a given (relation 1 and relation 5; base, FIX, FULL)

Relation 1 found the seven programs of the pilot and no other: 82 of 3,782 permutations change the verdict, all in the declaration-order set. Relation 5 adds 20 variants (16 programs) in which a new alias declared first is rejected and the same alias declared last is accepted; for three of them the two placements are stored as `b.hylo` (alias first) and `c.hylo` (alias last) in `violations/r5/r1_selfname--intro-all-top-1/`, `r1_selfname_fun--intro-all-top-0/` and `red2--intro-all-top-0/`.

To group them, ten small programs were written, one per shape of cycle (`shapes/`), and checked in 24 orders each: the original and 23 permutations, which is every order for the programs of four declarations (`shapes.py`, `shapes/results.jsonl`). The three configurations give the same counts for every one of them.

| Shape of the dependency cycle | Accepted orders of 24 (base = FIX = FULL) | Corpus programs (accepted orders of the 24 tried, FULL and FIX) | Alias variants of relation 5 |
|---|---:|---|---:|
| alias and an extension of the alias (`shapes/alias-extension.hylo`) | 10 | `al1` (9), `al2` (5), `al3` (6), `names-verify-names-2-v01_ext_declares_foo` (16) | 13, and 3 where the alias is an argument of the extended type |
| the same, the extension declaring a function with the looked-up name (`alias-extension-function.hylo`) | 12 | | (`r1_selfname_fun`, counted above) |
| alias of an alias and an extension (`alias-alias-extension.hylo`) | 6 | | (`al2`, counted above) |
| alias and a given whose head is the alias (`alias-given.hylo`) | 9 | | 4 |
| given, conditional extension and extension (`given-extension.hylo`) | 9 | `names-n11_poison_via_summon` (12), `names-n12_poison_via_summon_noearly` (10), `names-verify-names-1-v6_summon_swapped` (10) | |
| alias, given, conditional extension and extension (`alias-given-extension.hylo`) | 7 | | |
| two extensions (`extension-extension.hylo`) | 24 | | |
| two givens (`given-given.hylo`), given and conditional given (`given-conditional-given.hylo`) | 24 | | |
| alias of an alias, no extension (`alias-alias.hylo`) | 24 | | |

So every order dependence found passes through a type alias or through a given. Cycles made of extensions only, and of givens only, are order-independent in the programs tried.

**Through an alias and an extension**, `violations/r1/al1--perm-0-2-1-4-3-5/` (base, FIX, FULL):

```hylo
struct A {}
struct B {}
extension A { type Me = B }
type X = A.Me
extension X { type Me = Int }     // a.hylo, this order: definition of 'X' refers to itself
```

`b.hylo` has `extension X` before `type X` and is accepted. Computing `X` looks `Me` up in `A`, which asks every extension whether it extends `A`, which needs the extended type of `extension X`. When checking starts at the alias, `X` is being computed at that moment and the error is reported. When it starts at the extension, the extension is hidden while its own extended type is computed, `X` is found without it, and no error is reported. `violations/r1/names-verify-names-2-v01_ext_declares_foo--perm-0-2-1-3/` is the same in four lines; `al2` and `al3` differ by the position of the declarations and of a use.

**Through an alias and a given**, `violations/r5/red2--intro-all-top-0/` (base, FIX, FULL; `b.hylo` rejected, `c.hylo` accepted):

```hylo
type Alq = U.O              // b.hylo: here; c.hylo: at the end
trait P { }
trait Q { type O }
struct T { }
struct U { }
given U is Q { type O = T }
given Alq is P { }
```

Finding `O` in `U` needs `U is Q`; the resolution enumerates the givens, among them `given Alq is P`, whose type needs `Alq`.

**Through a given and extensions**, `violations/r1/names-verify-names-1-v6_summon_swapped--perm-0-2-1-4-3-5-6/`:

```hylo
trait P {}
struct A {
  struct Inner {}
  fun m() {}
}
extension A.Inner { type Foo = Int }
given A.Inner.Foo is P {}
extension <T where T is P> T { type Inner = Bool }
```

This order (`a.hylo`) is rejected; with the given before `extension A.Inner` (`b.hylo`) it is accepted. The head of the given needs `Inner` in `A`; the conditional extension applies to `A` if `A is P`; that resolution considers the given, whose head is being computed. Under base the rejected order fails with `type 'Inner' has no static member 'Foo'`; under FIX and FULL it fails with `circular extension`. For the reduction of `n12` (`violations/r1/names-n12_poison_via_summon_noearly--perm-1-4-7-3-2-5-6-0/`) the existing checker accepts both orders and FIX and FULL reject one: on that pair the new rule creates the order dependence.

The cause is the one stated in section 2.4 of the plan: a cycle is noticed from the state of the evaluation stack, so the outcome depends on which declaration of the cycle is entered first. The fixes handle extensions; aliases and givens enter the same cycles and are not covered.

Messages only: in 39 more programs every order gives the same verdict but not the same messages.

### D2. The orientation of an equality decides between two derivations (relation 7; base, FIX, FULL)

`violations/r7/e01-orient-amb--sym-2-2/`

```hylo
trait P {}
fun g<V where V is P>() {}
fun f<A, B, C where B is P, C is P, B == A, A == C>() { g<A>() }   // a.hylo: accepted
fun f<A, B, C where B is P, C is P, B == A, C == A>() { g<A>() }   // b.hylo: rejected
```

`A is P` has two derivations, from `B is P` and from `C is P`. They use different conformances, so the call is ambiguous whatever the spelling. The checker reports the ambiguity only when `A` is on the same side of both equalities (`B == A, C == A` or `A == B, A == C`; all eight combinations of orientation and order were tried by hand). With `B == A, A == C` or `A == B, C == A` it accepts and silently uses one of the two conformances. The trace shows why: using an equality in the direction opposite to the one written takes one more step, the search stops at the first depth at which a derivation exists, and the other derivation is never seen. The same happens when the symmetric form is added next to the original one (`dup-sym`: `B == A, A == C, C == A` is rejected, `violations/r7/e01-orient-amb--dup-sym-2-3/`).

`violations/r7/pen-ref-2--sym-6-0/` is the same effect with a refinement chain: `where W == V, W is Q2` is rejected and `where V == W, W is Q2` is accepted.

Seven variants in three programs (`e01-orient-amb`, `e01b-both-direct`, `pen-ref-2`). The plain duplicate (`dup`) never changed a verdict except through the resource bound (D6).

### D3. A where clause is read from left to right (relations 2 and 4; base, FIX, FULL)

`violations/r2/cong-1--reqs-3-120/`

```hylo
trait P { type X }
fun f<T, U, V where T == U, T is P, V == U.X>(x: V) {}    // a.hylo: accepted
fun f<T, U, V where V == U.X, T is P, T == U>(x: V) {}    // b.hylo: type 'U' has no static member 'X'
```

A requirement sees only the requirements written before it. A projection `T.X` written before `T is P` (or before the equality that makes `T is P` derivable) is an error. This holds for functions, extensions and conformances, in the three configurations. It accounts for 81 of the 84 verdict changes of relation 2 (37 programs; the three others are the case below and the resource bound of D6, twice), and for the 16 verdict changes of `taut-assoc` in relation 4, which all come from `T.X == T.X` added as the *first* requirement (`violations/r4/e2-abs-qual-distinct-conf--taut-assoc-2-1-first/`); added last, it never changes a verdict (313 variants).

Classification: a language decision that is not written down. If requirements form a telescope, the rejection is intended, and relation 2 only holds for permutations that respect dependencies. The kind `reqs-dep` tests exactly those: 263 variants, one verdict change, which is the resource bound of D6 on `open-wide-4`.

One case is not a scoping error and changes the verdict in the other direction, `violations/r2/v-abs-9--reqs-3-021/`:

```hylo
fun check<T>(x: T) {}
trait P {
  type X
  fun f<T, U where T == Self, T is P, T.X == U>(x: U) { check<X>(x) }   // a.hylo: rejected
  fun f<T, U where T == Self, T.X == U, T is P>(x: U) { check<X>(x) }   // b.hylo: accepted
}
```

In `b`, `T.X` is resolved when `T is P` is not yet in scope, through `T == Self` and the conformance of `Self`, so `U == Self.X` holds. In `a`, `T.X` is resolved through the requirement `T is P`, a different conformance, and `U == Self.X` is not derivable. Both orders are valid telescopes; the meaning of `T.X` depends on the position of another requirement. This is a defect, in the three configurations. It is one face of the open question about `Self.X` in section 4.1 of the plan.

### D4. A trivially true premise hides an ambiguity (relation 4; base, FIX, FULL)

`violations/r4/g_dup0--taut-ground-3-0-last/`

```hylo
trait P { }
struct T {}
given T is P { }                        // a.hylo: rejected (two conformances of T to P)
given <where T == T> => T is P { }      // b.hylo, in place of the line above: accepted
given T is P { }
fun need<A where A is P>() {}
fun main2() { need<T>() }
```

Two conformances of the same type are reported as ambiguous only when their derivations have the same length. A premise that is trivially true makes one of them one step longer, and the checker then uses the other without a diagnostic. With the premise on both, the program is rejected again (checked by hand). `violations/r4/gz0--taut-ground-4-0-last/` shows the same for the lookup of an associated type (`ambiguous use of 'Y'` disappears). Eight variants in four programs of the declaration-order set (`g_dup0`, `ge3`, `gz0`, `red3`); 18 more variants lose an ambiguity message while staying rejected for another reason.

Classification: defect. A language may prefer an unconditional conformance to a conditional one, but here the premise is a tautology, and the preference decides which of two conflicting declarations is silently used.

### D5. The position of a tautology in the callee decides the verdict of a call (relation 4; base, FIX, FULL)

`violations/r4/hand-tautology-position/` (reduced by hand from `equalities/e06-elab-change.hylo`; the automatic reduction, which could not flatten the nested functions, is in `violations/r4/e06-elab-change--taut-param-3-0-first/`)

```hylo
trait P {}
trait Q {}
trait R {}
fun g<V where V is P>() {}             // a.hylo: the call below is rejected (two derivations of P<A>)
fun g<V where V == V, V is P>() {}     // b.hylo: accepted
fun g<V where V is P, V == V>() {}     // c.hylo: rejected
fun f<A, B where B == A, B is P, A is R>() {
  given <where A is Q> => A is P {}
  given <where A is R> => A is Q {}
  g<A>()
}
```

`P<A>` has a short derivation (from `B is P` and `B == A`) and a long one (through `Q` and `R`). The requirements of the callee are resolved together, and the depth at which the search stops depends on where the trivial goal `A ~ A` stands in the list. In `e06-elab-change.hylo` the effect goes the other way: the original is accepted and the variant with `V == V` first is rejected. Same root as D2 and D4: ambiguity is decided among the derivations found at the first successful depth, and that depth is not stable under transformations that do not change the meaning.

### D6. The depth bound and the resource bound make acceptance depend on spelling (relations 2, 4, 7)

Depth bound, `violations/r4/chain8--taut-ground-3-0-last/` (base, FIX, FULL):

```hylo
trait P {}
struct S<T> {}
struct Z {}
given Z is P {}                        // a.hylo: accepted
given <where Z == Z> => Z is P {}      // b.hylo, in place of the line above: rejected
given <T where T is P> => S<T> is P {}
fun need<where S<S<S<S<S<S<S<S<Z>>>>>>>> is P>() {}
public fun main() { need() }
```

The derivation of the goal has nine steps; the tautology adds a tenth and the search gives up at its depth limit. With the tautology on the generic conformance instead (`violations/r4/chain8--taut-app-4-1-last/`, `given <T where T is P, S<T> == S<T>> => ...`), FIX and FULL reject, and the existing checker does not terminate within 60 s.

Resource bound, `violations/r2/open-wide-4--reqs-1-76543210/` (FIX and FULL; the existing checker times out on both programs):

```hylo
trait Q {}
fun pick<T, U1, U2, U3, U4 where U1 is Q, T == U1, U2 is Q, T == U2, U3 is Q, T == U3, U4 is Q, T == U4>(x: T) {}   // a.hylo: accepted
fun pick<T, U1, U2, U3, U4 where T == U4, U4 is Q, T == U3, U3 is Q, T == U2, U2 is Q, T == U1, U1 is Q>(x: T) {}   // b.hylo: rejected
fun f<A0 where A0 is Q>(x: A0) { pick(x) }
```

`b` is rejected with `implicit resolution is too complex: more than 100000 candidate derivations`. On the same program, adding `U4 == U4` (`violations/r4/open-wide-4--taut-param-1-0-last/`), stating `T == U2` twice, or adding `U2 == T` next to it has the same effect: eight variants of `performance/open-wide-4.hylo` in all. Two more programs change only their messages in this way: `cycles-and-crashes/o4-toplevel-occurs-full.hylo` (requirements reversed) and `cycles-and-crashes/r1-bundle-eq.hylo` (`X == Y, Y == X`) get the "too complex" error in addition to their other errors.

Classification: defect of the bounds, for the configurations with `budget`. The bound turns a search that does not terminate into an error, which is its purpose, but whether a correct program is accepted then depends on the order in which its requirements are written. This supports section 4.1 of the plan: both bounds are language decisions.

### D7. Generic type aliases are not transparent (relation 5; base, FIX, FULL)

An application of a generic alias is not replaced by its definition in several places. Small programs written by hand after the automatic reductions (each directory holds `a.hylo`, accepted, and `b.hylo`, rejected, in the three configurations):

| Directory under `violations/r5/` | `b.hylo` differs from `a.hylo` by | Error |
|---|---|---|
| `hand-generic-alias-given-head` | `type AB<T> = Box<T>`; `given <T> => AB<T> is P {}` for `given <T> => Box<T> is P {}` | `no coercion from 'P<Box<A>> ==> ...'`: the conformance never applies, not even to a goal spelled `AB<A>` |
| `hand-generic-alias-extension-head` | `extension <T> AB<T> { fun first() {} }` for `extension <T> Box<T>` | `type 'Box<A>' has no member 'first'` |
| `hand-generic-alias-receiver` | `fun m(b: AB<A>) { b.first() }` for `b: Box<A>`, `first` declared in an extension of `Box<T>` | `type 'AB<A>' has no member 'first'` |
| `hand-alias-method-call` | `type Alq = A<Void>`; `fun use(a: Alq) { a.f(()) }` for `a: A<Void>`, `f(x: U)` a method of `struct A<U>` | `cannot pass value of type 'Void' to parameter 'U'` |

The last one involves a *non-generic* alias of a generic type: the type arguments are lost when a method is called through the alias (found on the compiler test `generic-member.hylo`, kinds `intro-all` and `intro-all-top`). Passing a `Box<A>` where an `AB<A>` is expected, and conversely, works; so does a non-generic alias in the head of a conformance or of an extension.

Automatic reductions of the same defect:
- `decomp-1--intro-generic-0`: with `where AlqBox<A> == AlqBox<B>`, a value of type `AlqBox<A>` cannot be passed as `AlqBox<B>`;
- `probe1--intro-generic-0`: `where Box<X> == AlqOpt<Y>` does not give `Box<X> ~ Opt<Y>` (the existing checker times out);
- `context-bound--intro-generic-0`: in `given <T is P> => AlqA<T> is P { fun f() { self.x.f() } }`, `self.x` no longer has a type that is `P`;
- `implicit-qualification--intro-generic-0`, `overload-priority--intro-generic-0`, `x01-ext-arg-member--intro-generic-0`: members of `extension AlqB<Void>` are not found;
- `chain3--intro-generic-0`, `o1-value-ctx--intro-generic-0`, `x07-given-arg-member--intro-generic-0`: conformances declared for an alias application are not found.

One case goes in the unsound direction, `violations/r5/b1d-method-env-cycle--intro-generic-0/`:

```hylo
struct Box<T> {
  fun n() -> Void {}
}
fun mkbox<T>(x: T) -> Box<T> { mkbox(x) }      // a.hylo: rejected under FIX and FULL, stack overflow under base
fun mkbox<T>(x: T) -> AlqBox<T> { mkbox(x) }   // b.hylo, with `type AlqBox<Tq0> = Box<Tq0>`: accepted
fun same<T>(x: T, y: T) {}
public fun main() {
  let f = fun[](a) { same(a, mkbox(a).n) }
}
```

`same(a, mkbox(a).n)` requires the type of `a` to contain itself. The occurs check added by `occurs` reports it, but not when the type variable is under an application of a generic alias: the program is then accepted with no diagnostic, in the three configurations.

`intro-generic` changed the verdict of 27 of its 158 variants (27 programs); the non-generic alias of a generic application adds 2 variants. The compiler tests `typealiases.hylo`, `chained-type-aliases.hylo` and `typealias-transparent.hylo` pass because they use aliases as annotations of values that are only passed around.

### D8. A type alias changes the handling of cyclic lookups (relation 5)

Extending a type through its alias is rejected when the definition of the alias contains a member lookup, `violations/r5/names-verify-names-2-v01_ext_declares_foo--expand-0/` (base, FIX, FULL):

```hylo
struct A {
  type Foo = Int
}
type X = A.Foo
extension X { type Foo = Bool }       // a.hylo: definition of 'X' refers to itself
extension A.Foo { type Foo = Bool }   // b.hylo, in place of the line above: accepted
```

Computing `X` looks `Foo` up in `A`; the lookup asks every extension whether it applies to `A`; the extension of `X` needs `X`, which is being computed. Written without the alias, the extension is the declaration being checked and is skipped. `al1--expand-0` is the same with the member declared in another extension. Six variants of `expand` and `expand-drop` in three programs.

The check for circular extensions added by `extorder` does not look through aliases, `violations/r5/names-verify-names-1-v4_noC--intro-all-0/`:

```hylo
struct A { struct Inner {} }
extension A.Inner.Foo { type Inner = Bool }    // a.hylo
extension A.Inner { type Foo = Int }
// b.hylo: `A.Inner` is written `Alq` in both extensions, and `type Alq = A.Inner` is added at the end
```

| Configuration | `a.hylo` | `b.hylo` |
|---|---|---|
| base | accepted | rejected: definition of 'Alq' refers to itself |
| FIX, FULL | rejected: circular extension | accepted |

So the rule that rejects `a` is avoided by naming the extended type through an alias (five programs). Whether `a` should be rejected at all is the open question "are cyclic extensions legal" of the plan; the point here is that the alias changes the answer, in opposite directions before and after the fix.

One more program gets a self-reference error from a new alias declared last (`violations/r5/x05-alias-ext--intro-all-0/`).

Finally, the position of the new alias matters: 20 variants with the alias declared first are rejected (`definition of 'Alq' refers to itself`) where the same program with the alias declared last is accepted. These are order dependences; they are counted under D1.

## Legitimate changes

**L1. Unused generic parameter** (`unused-param`, 90 of 616 variants, 84 programs). `fun use<T, Zq>(x: T) {}` is accepted as a declaration, and each call that does not give `Zq` explicitly is rejected with `not enough context to infer a type` (`violations/r4/use-before-init--unused-param-0/`). The same holds for a conformance: `given <T, Zq where T is Q> => Box<T> is Q {}` is accepted, and rejected where the conformance is used (20 variants); it stays accepted when nothing uses it (11 variants). An unused parameter of an extension never changed a verdict (40 variants). The transformation is a correct instance of the relation as stated, but the relation does not hold in a language without defaulting of unconstrained type variables. One could argue that the declaration itself should be rejected.

**L2. Tautology on a type constructor.** `fun g<T :: * -> *, U where T == T>` is rejected with `T expects 1 type argument(s)` (`violations/r4/higher-kinded--taut-param-4-0-last/`). `T == T` is not a well-kinded requirement; the generator skips parameters with a `:` ascription but did not recognise `::`.

**L3. A type argument left open is inferred from the conformances in scope** (relation 8, kind `conf`). `violations/r8/hand-open-goal/`, written by hand after the eight violations:

```hylo
trait R {}
fun needR<T where T is R>() {}
public fun main() { needR() }     // a.hylo: rejected, no type is R
struct Nq {}                      // b.hylo adds these two lines: accepted, T is inferred to be Nq
given Nq is R {}
struct Mq {}                      // c.hylo adds these two as well: rejected again, T is ambiguous
given Mq is R {}
```

The call does not determine `T`, and resolution instantiates it with the only type that conforms. A new conformance is therefore never unrelated to such a call. Seven programs of the cycles-and-crashes set are rejected (under base, six of them overflow the stack) and become accepted when a new struct conforms to their trait; the compiler test `nullary-conformance.hylo` is accepted and becomes rejected, because the unconstrained parameter `T` of `given <T where T is P> => Int is P` then has two solutions. This is how the checker is meant to work, as that compiler test shows, so the relation does not hold for programs with open goals. It is still worth knowing that adding a conformance anywhere in a module can break or repair a call elsewhere. A new struct without a conformance never changed a verdict.

**An artefact that was removed.** Relation 6 first reported `Tests/CompilerTests/positive/integer-conversions.hylo`: its function `truncating_or_extending` has the name of an argument label of the standard library (`Int32(truncating_or_extending: x)`), and renaming every token with that text renamed the labels too. Argument labels of the standard library are now excluded from renaming, and the program was run again: no verdict change.

## Relations without violations

- **Relation 3, order of members:** 197 variants of 120 programs (every program with a type body of at least two members), no change of verdict or of messages.
- **Relation 6, renaming:** 1,424 variants of 727 programs, no change of verdict or of messages once renamed identifiers are mapped back in the messages. In particular the reversal of the alphabetical order of all declared names changes nothing: no result depends on the order of names.
- **Relation 8, unrelated declaration:** 1,520 variants of 760 programs: a new struct conforming to an existing trait (332 programs that have a suitable trait), a new struct at the beginning of the file (760), a new trait (428). The only verdict changes are those of L3.

## What remains uncertain

- **Coverage is bounded by machine time.** The machine was shared and each run took 0.3 to 2 s. Relation 1 checked 2 permutations per program outside the declaration-order set, relations 6 and 8 two variants per program. `MM_BUDGET="r1=23,r8=11" ./metamorphic.py run r1 r8` continues from the rows already recorded.
- **Attribution to base is partial.** FIX was run on at most 8 members of each group of violations (a group is a relation, a kind of variant, a pair of verdicts and a set of messages with the names blanked), and on every permutation of the seven order-dependent programs: 396 variants. The existing checker was run on 172 of them only, because it needs up to a minute on some and the machine was shared; the groups it was not run on are marked "not run" in `data/summary.md`. For those, the verdicts of the existing checker on the reduced pair are in `info.json`. For relation 1, the pilot (`../permute-base.jsonl`) already shows that the seven programs are order-dependent under the existing checker, which has 52 such programs in the declaration-order set; that run was not repeated.
- **Reduction is automatic only down to declarations, members, requirements and body lines.** The programs marked "by hand" were reduced further manually; the others may not be minimal.
- **D3 and the bounds of D6 are language decisions.** They are reported as defects of the relation, not necessarily of the implementation.
- **Type positions in relation 5 are recognised from the preceding token.** Occurrences in function bodies are replaced only between angle brackets, so aliases in local annotations and constructor calls (`Alq()`) are not tested.
- **Each expected verdict is the verdict of the original program.** A metamorphic test says that two programs should agree, not which of the two verdicts is right; where it matters, the text above says which one the reading of the program supports.
