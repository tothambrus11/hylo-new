# Attack on `sigrounds` (signatures computed in rounds)

## What was asked

`sigrounds` computes the signatures of the extensions, conformances and given bindings of a module in rounds, each round reading these signatures from the table of the previous round, until the table is stable. Its intended property is that the verdict does not depend on the order of declarations. It was implemented from `../design-order/DESIGN.md` and had only been tested by its author. The task was to find programs on which it is wrong: an ill-typed program accepted, a well-typed program newly rejected, a verdict that depends on an order that should not matter, a self-check violation, or a program of the intended shape that is still rejected.

## What was done

- The implementation was read (`Typer.settleSignatures`, `signatureRound`, `isVisible`, the extension loop, `applies`, `declaredType(of: Given)`, the hook in `declaredType(of: BindingDeclaration.ID)`, `typeOfSelf(in:)`, `summon`), together with the design and its review (section 9), to list what the mechanism assumes.
- 104 programs were written or copied into `p/` (8 are copies of design tests, prefix `k`; 12 are the permutations of one where clause, `w01`). Each was run on binary `eq22-554540c3a507` under base, FULL, FULL+`sigrounds`, NEW without `sigrounds` (NOSIG), NEW and NEW+`selfcheck`, and under NEW with one of `memberskip`, `index`, `absmodel`, `extorder`, `givencheck` removed.
- 35 programs were type-checked in permuted orders of their top-level declarations (up to 120 orders each), and 8 in permuted orders of the declarations of a function body.
- Chains of dependent declarations were generated up to 32 nodes to measure rounds and resolution work.

Everything is reproducible: `run.py` (one program, several configurations), `ord.py` (top-level orders), `localord.py` (orders inside a function body), `cost.py` (generated chains), `tabulate.py` (writes `RESULTS.md`). Raw results are in `results.jsonl`, `orders.jsonl`, `localorders.jsonl` and `cost.jsonl`. `RESULTS.md` has one row per program with its verdict in each configuration and what it tests.

The design document was revised while this work was under way. Its second version records three defects of the implemented ("first") design and proposes corrections R1 (inferred givens and named requirements are not in the table), R2 (the signature of an enclosing function, extension or conformance is computed before a node declared inside it) and R3 (self-check in every round). None is in the binary. For each finding below, the text says whether the corrections would remove it; that part is reasoning, not measurement.

## Findings

| # | Kind | Program (control) | base | FULL | NEW | Removed by R1–R3? |
|---|---|---|---|---|---|---|
| 1 | REGRESSION and ORDER | `p/a06-…` / `p/a06b-…`, `p/a05-…` / `p/a05b-…` | accept, every order | accept, every order | **accept or reject, by order** | no |
| 2 | ORDER | `p/a01-…` / `p/a01b-…`, `p/a02-…` / `p/a02b-…` | by order | by order | **by order, opposite to FULL** | no |
| 3 | VIOLATION | `p/t03-…` (`p/t03c-…`), `p/t02-…`; also the accepting orders of 1 and 2 | reject | reject | reject, self-check violation | no |
| 4 | UNSOUND (a rule is bypassed; known cause, new shape) | `p/e01-…` (`p/e01c-…`), `p/e02-…` (`p/e02c-…`) | reject | reject | **accept** | yes (R1) |
| 5 | CRASH, REGRESSION (known) | `p/k24-…`, `p/k23-…` | crash, accept | accept, accept | **crash**, **reject** | yes (R1) |
| 6 | COST | `cost/given-*.hylo`, `cost/mixed-*.hylo` | – | – | rounds = nodes + 1; work quadratic | no |
| 7 | QUESTION | `p/h01-…` / `p/h02-…` | reject | reject | accept / reject | no |
| 8 | UNSOUND, outside the mechanism | `p/q04-…` (`p/q04c-…`), `p/q03-…` (`p/q03c-…`) | accept | accept | accept | – |
| 9 | INCOMPLETE | `p/h02-…`, `p/a08-…`, `p/c02-…` | reject | reject | reject | no |

### 1. A member that needs `Self`, named by the where clause of its extension: FULL accepts every order, NEW half of them

```hylo
trait Q {}
trait R {}
struct A {}
given A is Q {}
extension <where LA is Q> A { type LA = Self }
given A.LA is R {}
```

`p/a06` is this program; `p/a06b` has the last two lines swapped. `p/a05` and `p/a05b` are the same with the requirement `Foo<LA> is Q` and a given for every `Foo<U>`.

| | base | FULL | FULL+`sigrounds` | NOSIG | NEW | NEW+`selfcheck` |
|---|---|---|---|---|---|---|
| `a06` (extension first) | accept | accept | accept | accept | accept | accept, VIOLATION |
| `a06b` (given first) | accept | accept | **reject** | accept | **reject** | reject |
| 60 orders of the 6 declarations | 60 accept | 60 accept | | | 31 accept, 29 reject | 31 accept with VIOLATION, 29 reject |

The rejection is "the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found" (twice) and "type 'A' has no static member 'LA'". The single flag is responsible: FULL+`sigrounds` rejects, NEW without it accepts. For `a05`: FULL accepts 40 of 40 orders, NEW 17 of 40.

The program is well-typed in the sense of the existing checker, in every order: `LA` is `A`, `A is Q` holds, the last given is `A is R`.

Cause. There are two ways into the pair (extension, `LA`), and they do not compute the same thing.

- Entered at the extension (by the driver): the where clause names `LA`; `LA` is `Self`; `typeOfSelf(in: ExtensionDeclaration.ID)` sees that the extension is on the stack and evaluates the extendee expression directly. No error.
- Entered at `LA`: in a round where the table already has the extension, the lookup `A.LA` made by the given selects the member through the table and types it before the extension's signature was computed in this round. `Self` then calls `extendeeType`, whose where clause demands `LA`, which is on the stack: "definition of 'LA' refers to itself". The extension gets an erroneous signature and leaves the table; in the next round it is back; the table oscillates.

Which way is taken is the order of the nodes in the syntax, that is the order of the declarations. On-demand evaluation always enters at the extension, because a member is only reached after its extension was forced; the table removes that guarantee. The design saw this for requirements (assumption A3, case (i), "open in principle for a member of an extension or conformance selected through the table, where no program is known"; section 3.6: "I could not construct such a program at top level"). The attempts described there make the where clause select the member through a lookup, which needs the extension to be in the table already. Here the where clause names the member lexically, so the extension enters the table in round 1.

This program does not use the hook of section 3.6 at all (`sigrounds.ownerFirst` is absent): the dependence of the member on its owner is `Self`, not a requirement. R1 does not apply (no inferred given, no named requirement), R2 does not apply (the given that enters `LA` is at top level and has no enclosing owner), R3 only detects it.

### 2. The same through the hook: extension and conformance whose where clause names a member that needs a requirement

```hylo
trait P { type X }
trait Q {}
trait R {}
struct A {}
struct Box<T> {}
struct Foo<T> {}
given A is P { type X = Int }
given <U> => Foo<U> is Q {}
type BA = Box<A>
extension <T where T is P, Foo<LA> is Q> Box<T> { type LA = T.X }
given BA.LA is R {}
```

`p/a01` (above) and `p/a01b` (last two lines swapped); `p/a02`, `p/a02b` are the same with `given <T where T is P, Foo<Y> is Q> => Box<T> is S { type Y = T.X }` and `given BA.Y is R {}`.

| | base | FULL | NEW | NEW+`selfcheck` |
|---|---|---|---|---|
| `a01` (extension first) | reject | reject ("circular extension") | accept | accept, VIOLATION |
| `a01b` (given first) | accept | accept | reject ("no stable interpretation") | reject |
| 120 orders of the last 5 declarations | | 60 reject, 60 accept | 60 accept, 60 reject | |
| `a02`, 30 orders | | | 16 accept, 14 reject | |

Entered at the owner, the where clause demands `LA` after its first requirement is typed and `T.X` resolves. Entered at `LA` through the table, the resolution inside `LA` asks for an untyped requirement, the hook computes the owner's signature, and the where clause demands `LA`, which is on the stack. FULL is order-dependent on this program too, in the opposite direction, so this is not a regression; it is a program on which `sigrounds` does not deliver order independence. It is the top-level form of the design's attack 3 (`tests/27`, `28`, reproduced here as `p/k27`, `p/k27b`, `p/k28`: 12 of 24 orders), without a local given, an inferred given or a function, and R2 does not cover it.

The requirement that names the member must be provable without knowing the member (here a given for every `Foo<U>`), or the member must not depend on a type parameter (finding 1). With `LA is Q` and `LA = T.X` the extension is never found to apply, in any order and any configuration (`p/a08`, finding 9).

Direction for a correction of 1 and 2 (not tested): when a lookup or a witness selects a member of an extension or conformance through the table and the owner is not on the stack, compute the owner's signature before typing the member. The member is then always first demanded by its owner's where clause, as in the existing checker. This does not make "a member typed in the middle of its owner's where clause" independent of the entry point when two owners select each other's members; the rule that would is to reject a where clause that demands a declaration of the body it governs, which changes `a06` and `tests/27` from accepted to rejected and is a language decision.

### 3. The self-check reports a violation on ill-typed programs with a cycle that two nodes read

```hylo
trait P {}
type X = Y
type Y = X
given X is P {}
given Y is P {}
```

`p/t03`: rejected by every configuration, as it must be. NEW+`selfcheck` prints `[selfcheck] VIOLATION: sigrounds: the stable round reports other diagnostics in reverse order` in 120 of 120 orders. The alias that is blamed ("definition of 'X' refers to itself" or "… 'Y' …") is the one entered first, and under NEW that is decided by the order of the two givens (60 orders each); under FULL by the order of the two aliases. The control `p/t03c` (one given) has no violation. `p/t02` shows the same with two named givens that select a member through each other by name (`given wa: wb.X is P`, `given wb: wa.X is P`): one outcome in 24 orders, a violation in each, and both diagnostics are attached to whichever given the driver enters first.

The verdict does not vary; this is question 7 of the design (which declaration of a cycle is blamed). It matters because the design makes "no self-check violation outside the kind of section 3.6" the acceptance condition of the mechanism: as implemented, the self-check fails that condition on any ill-typed program with a cycle of aliases that two signatures read. Either the comparison must ignore which member of a cycle is blamed, or the cycle must be reported at every member.

The accepting orders of findings 1 and 2 print `sigrounds: the stable round computes another table in reverse order`. Their rejecting orders print nothing, because the self-check only runs on a stable round (R3 would change that).

### 4. A named requirement used before it is introduced, at top level (known cause, new shape)

```hylo
trait P { type X }
trait Q {}
struct Box<T> {}
extension <T where T.X is Q, let u: P<T>> Box<T> { fun g() {} }
```

`p/e01`: base and FULL reject ("type 'T' has no static member 'X'"), FULL+`sigrounds` and NEW accept, in 24 of 24 orders. `p/e02` is the same for a conformance (30 of 30). The twins with an unnamed second requirement (`p/e01c`, `p/e02c`) are rejected by NEW, and so is the same where clause on a function (`p/e03`).

In terms of the language: the first requirement selects `T.X` when no `P<T>` has been introduced; the rule that a requirement only sees the requirements before it rejects the program, and NEW applies that rule to the unnamed twin. No value of a wrong type can flow: the extension and the conformance are unusable, a call is rejected whether or not `A.X is Q` holds (`p/e05`, `p/e05c`, `p/e06`, `p/e06c`). Whether the rule stays is question 6 of the design; NEW is inconsistent under either answer.

This is the design's defect E1 (`tests/25`, here `p/k25`): a named requirement has `role == .given`, is put in the table, and is read from it while an earlier requirement is typed. `tests/25` needs a given in the body of a function to make the function's signature be computed during the rounds; for an extension or a conformance nothing else is needed. R1 removes it.

### 5. The known defects of the first design are in this binary

- `p/k24` (copy of `tests/24`, a given inferred from a variable bound by a `match` pattern): NEW crashes (exit code -4), FULL accepts. base crashes too.
- `p/k23` (copy of `tests/23`, a given inferred from a lambda parameter): base and FULL accept, NEW rejects.
- `p/k25`, `p/k27`, `p/k27b`, `p/k28`: as recorded in section 9.3 of the design.

Other givens without a written type were tried (from a local binding, a parameter, `self`, a generic call, a conditional expression, a global binding, a call through `headsubst`: `p/b01`, `b02`, `b04`, `b08`, `f01`, `f04`, `f05`): none is rejected by NEW. One new consequence of treating them as nodes: `p/s01`, `given let w = make()` where `make` needs a given of the type of `w`, is accepted by NEW (the initializer is resolved with `w` itself, read from the table) and rejected by base and FULL. With the type written (`p/s02`) every configuration accepts it, so the existing checker does not forbid a given that initializes itself either. R1 removes both effects.

### 6. Cost: rounds equal to the length of the longest chain, paid by the whole module

Counters of the user module; times are indicative only (other jobs were running).

| Program | Configuration | Verdict | Rounds | `summon.calls` | `summon.matches` | `type.user` |
|---|---|---|---|---|---|---|
| chain of 4 givens | FULL / NEW | reject / accept | – / 5 | 6 / 32 | 221 / 1,172 | 19 ms / 174 ms |
| chain of 8 givens | FULL / NEW | reject / accept | – / 9 | 10 / 116 | 384 / 4,468 | 31 ms / 641 ms |
| chain of 12 givens | FULL / NEW | reject / accept | – / 13 | 14 / 248 | 559 / 10,036 | 71 ms / 1.5 s |
| chain of 16 givens | FULL / NEW | reject / accept | – / 17 | 18 / 428 | 746 / 18,164 | 80 ms / 2.6 s |
| chain of 32 givens | FULL / NEW | reject / accept | – / 33 | 34 / 1,628 | 1,614 / 82,036 | 153 ms / 11.9 s |
| 32 generic conformances and one dependency of depth 1 (`wide`) | FULL / NEW | accept / accept | – / 3 | 34 / 102 | 2,903 / 9,237 | 0.55 s / 1.8 s |
| the chain of 8 with 32 unrelated generic conformances (`mixed`) | FULL / NEW | reject / accept | – / 9 | 42 / 404 | 3,546 / 37,402 | 0.59 s / 7.7 s |
| chain of 32 extensions (`ext`) | FULL / NEW | accept / accept | – / 33 | 0 / 0 | 31 / 496 | 5 ms / 55 ms |

- A chain of `n` givens takes `n + 1` rounds, and `summon.matches` is multiplied by about 4 to 4.5 each time `n` doubles: quadratic, as the design says, and slightly more. FULL rejects these chains, so its counters are those of a failing run; the fair comparison is `n` signature computations against `n (n + 1)`.
- The number of rounds is set by the deepest chain of the module and every round recomputes every signature. One chain of 8 givens multiplies the resolution work of 32 unrelated conformances by 10 (`mixed`: 37,402 matches against 3,546).
- A module with one dependency of depth 1 takes 3 rounds; the signature phase costs 3.2 times as many matches (`wide`).
- A program that does not stabilize pays the same: the unstable pair of `tests/29` with a chain of 32 extensions hanging on it takes 34 rounds before it is reported (`flip`).
- The index of givens is unavailable during the rounds (`index.unavailable` 36,286 in `mixed-32`), which is why each match costs as much as in FULL.

### 7. Whether a reading is found depends on how many rounds a transient lasts

`p/h01` and `p/h02` differ in one name. In both, two local givens `g` (`A is P` with `E = Bool`, shadowing a top-level one) and `g2` (`A is Q`, but only when `A.E` is `Bool`) justify each other, and nothing else provides `A is Q` in the final table. A third local given `k` provides `A is Q` for a while: in `h01` it reads a type that changes one round later than in `h02`.

| | base | FULL | NEW | Rounds |
|---|---|---|---|---|
| `h01` (`k` provides `A is Q` in rounds 2 and 3) | reject | reject | **accept** | 5 |
| `h02` (`k` provides `A is Q` in round 2 only) | reject | reject | reject ("no stable interpretation") | 5 |

The table on which `h01` stabilizes is a stable table of `h02` as well; `h02` misses it because `g` and `g2` come up out of phase and the table oscillates. Both verdicts are the same in 30 orders of the top-level declarations and 24 orders of the local ones, so nothing here contradicts the claims of the design, which does not promise to find a reading. It shows what question 1 of the design means in practice: a reading in which two givens support each other is accepted when a signal that later disappears lasts two rounds, and not when it lasts one, and the length of that signal is the length of an unrelated chain of declarations.

### 8. A conformance satisfies the trait it refines with itself (outside the mechanism, in base too)

```hylo
trait Base { fun f() }
trait Derived refines Base { fun g() }
struct B { public memberwise init }
given B is Derived { public fun g() { self.f() } }
fun callBase<T where T is Base>(x: T) { x.f() }
fun callDerived<T where T is Derived>(x: T) { callBase(x) }
public fun main() { callDerived(B()) }
```

`p/q04` is accepted by every configuration. `B is Derived` requires `B is Base`, which nothing provides: `callBase` calls `Base.f` on a `B`, and no implementation of `f` for `B` exists. The control `p/q04c`, where the body of `g` is empty, is rejected ("no given instance of 'Base<B>' in this scope"). `p/q03` is the four-line form.

Cause: the design relies on the rule "a conformance cannot use itself to satisfy the traits it refines", which `check` enforces by putting the conformance on `declarationsOnStack` while the refinement is resolved. `summon(_:in:)` consults its cache before anything else and whatever is on the stack. The members are checked first; `self.f()` resolves `Base<B>` in the scope of the conformance, through the refinement applied to the conformance itself (the trace shows one derivation, through the nested given of `Derived`), and that answer is memoized; the refinement check then gets it from the cache (`summon.cacheHits=1`, 0 in the control). `sigrounds` neither causes nor worsens it: the rounds can only fill this cache from a member of the conformance, which the checks reach first anyway.

Also outside the mechanism: a member alias that the where clause of its extension demands is typed with the requirements typed so far. In `p/a03`, `type LA = T.X` under `where T is P, Foo<LA> is Q, T is P2` (both traits declare `X`) is accepted by every configuration in 30 of 30 orders, with `LA` meaning `P`'s `X`; without the middle requirement it is rejected as ambiguous (`p/a03c`). The existing checker behaves the same.

### 9. Programs of the intended shape that NEW still rejects

1. A program with a consistent reading that the iteration does not reach (`p/h02`, finding 7). By design.
2. A where clause that names a member alias defined through a type parameter (`extension <T where LA is Q> Box<T> { type LA = Self }` with `given Box<A> is Q`, `p/a08`, `p/a08b`): "type 'BA' has no static member 'LA'" in both orders and in every configuration. The premise is not proved through the alias. This is what keeps findings 1 and 2 away from generic code today; if it is repaired, their shape becomes more ordinary.
3. An alias through a generic conformance whose associated type is defined by an associated type of its parameter, used as the subject of a given (`p/c02`; through a refinement, `p/c10`; in a library-shaped program, `p/r03`). The rounds stabilize (3 rounds); the given is not found for `Int` because the projection is not reduced. Same verdict without `sigrounds`: this is shape 1 of the incompleteness reported in `../attack-assoc`, not a defect of the rounds.

## What held

- **Soft reads.** No place was found where a lookup or resolution computes or reads a node's signature outside the table during the rounds: conformances in a function body, in a lambda, in a struct, in an extension, in a trait (as a requirement and in a default method), in a method of a generic extension or conformance; the given a refinement desugars to; adjunct conformances; an extension of every type or of a constrained parameter; an extension declared in a function body; `Self` in the where clause of an extension; an extension of an unapplied generic type; a where clause that uses an alias defined through another conformance; chains of member aliases of extensions; a default argument (`c01`–`c11`, `m02`–`m04`, `k02`–`k04`, `l02`, `r01`, `r04`, `z01`, `d01`, `y01`, `y02`). Each is accepted with the same verdict in up to 30 orders of the top-level declarations, and `y01`, `y02`, `z01` in every order of their local declarations.
- **Order of requirements and of type parameters.** The 6 orders of three independent requirements, with the type parameters in either order (`w01`, 12 programs): all accepted.
- **Restore.** No diagnostic is reported twice or lost: an error in a signature, in a member read during the rounds or in an initializer is reported once in a program that needs three rounds (`g01`, `g03`, `b05`, `b06`), and an unstable table does not hide an unrelated error (`g02`). Apart from finding 3, the accepting orders of findings 1 and 2 and the known `k27`, `k27b` and `k28`, no self-check line "computes another table" or "reports other diagnostics" appeared in 104 programs.
- **Oscillation and cycles.** Programs without a stable table are rejected in every order with the same diagnostics (`r02`, `g02`, `k09`, `h02`, the `flip` chains); the round bound was never exceeded. A cycle through a conformance and `Self` is rejected identically from both sides (`a07`, `a07b`).
- **Other flags.** Removing `memberskip`, `index`, `absmodel`, `extorder` or `givencheck` from NEW changes no verdict and no diagnostic on the 104 programs (520 runs). `sigrounds.lateNodes` never appeared.
- **Messages.** In the permuted runs, programs with one verdict also have one set of diagnostics (positions aside), except `t03` (finding 3).
- **Named requirements used in the right order** are accepted without the double typing causing harm (`n01`–`n03`).

## What could not be tested

- The corrections R1, R2 and R3 are not in any binary. What is said about them above is read from the design.
- Several source files: the binary takes one program.
- An equality declared in a trait (`given let w: X == Int`) used by a signature: base crashes on the program written for it.
- Adjunct conformances with an associated type: base reports "no implementation of associated type requirement".
- A convergent program that needs more than `nodes + 2` rounds (question 2 of the design): none was built. `h01` shows that non-monotone programs exist, but a counter long enough needs more nodes than it gains rounds.
- The assertions (`declaration already initialized`, and those the design asks for A1, A4, A7): the binary does not stop on the double typing of `n01`, so it is assumed to be built without them.
- `orders.py` compares diagnostics without their positions. A difference in position only is seen by the self-check (finding 3) but not by the permutation runs.

## Files

| Path | Content |
|---|---|
| `p/` | The programs. The first comment of each says what it tests; a suffix `b` or `-swapped` is the same program in another order, `c` a control. |
| `RESULTS.md` | Verdict of every program in every configuration; the permutation runs; the cost table. |
| `results.jsonl`, `orders.jsonl`, `localorders.jsonl`, `cost.jsonl` | Raw results. |
| `run.py`, `tc.sh` | Run programs under named configurations (`tc.sh` prints every diagnostic of one run). |
| `ord.py` | Permutes top-level declarations through `../sigrounds/orders.py`, on binary `eq22`. |
| `localord.py` | Permutes the one-line declarations of a function body. |
| `cost.py`, `cost/` | Generated chains and their measurements. |
| `tabulate.py` | Writes `RESULTS.md`. |
| `scratch/ord/` | The copies of the programs that `orders.jsonl` refers to. |
