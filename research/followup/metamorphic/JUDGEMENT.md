# Judgement of the metamorphic testing campaign

This file is the independent check of the claims made in `README.md`. Each claim was re-run under the three configurations (base = the existing checker, FIX, FULL), the correct verdict was decided from the meaning of the program, and for each confirmed defect the likely cause was located in `/home/user/hylo-impl/Sources/FrontEnd` (read only).

## Result

- **Every observation reproduces.** All 134 reduced programs in `violations/` were re-run under base, FIX and FULL (402 runs, `judge/all-violations.txt`). The 348 verdicts recorded in the `info.json` files are the same, except five base runs that the campaign recorded as a timeout and that ended here with an abort at the memory limit. Both mean "no verdict".
- **The classification is too generous in four places and too mild in one.** Of the eight claimed defects, five are confirmed (D1, D2, D5, D7, and the resource-bound half of D6), one is the same defect as another (D8 is D1 plus a gap in the `extorder` check), and three are not defects of the implementation: D3 is a deliberate rule, D4 follows from the ranking rule that a positive compiler test relies on, and the depth-bound half of D6 is the known bound.
- **D7 is worse than reported.** Through a type alias of a generic type, the checker accepts a call that passes a value of the wrong type (`judge/progs/alias-args-lost.hylo`), in the three configurations. The README attributed the one unsound case it saw to the occurs check; that explanation is wrong.
- **No finding is specific to the optimizations** (FULL against FIX). This holds for every variant attributed to a defect. It was not tested in the other direction: FIX was run only on variants where FULL had already changed its verdict.
- The three legitimate changes (L1, L2, L3) are correctly classified.

## Verdict on each claim

"In base" says whether the existing checker shows the same pair of verdicts.

| Claim | Campaign's class | Judge's verdict | Affected | In base |
|---|---|---|---|---|
| D1. Declaration order decides the verdict when a cycle passes through a type alias or a given | defect | **Confirmed** | base, FIX, FULL | yes. On the reduced `n12` pair only FIX and FULL depend on the order |
| D2. The orientation of an equality decides between two derivations | defect | **Confirmed** | base, FIX, FULL | yes |
| D3. A where clause is read left to right (97 variants) | language decision | **Not a defect**: deliberate, stated in a comment of `initializeContext` | – | – |
| D3, the case `v-abs-9` | defect | **Open question**, not a separate defect | base, FIX, FULL | yes |
| D4. A trivially true premise hides an ambiguity | defect | **Open question** about the ranking rule; the behaviour follows from "the smallest derivation wins", which `nullary-conformance.hylo` requires | base, FIX, FULL | yes |
| D5. The position of a tautology in the callee decides the verdict of a call | defect | **Confirmed** | base, FIX, FULL | yes |
| D6, depth bound (`chain8`, 5 variants) | defect of the bounds | **Not a new defect**: the known bound of 10 steps; open question whether it belongs to the language | base, FIX, FULL | yes |
| D6, resource bound (`open-wide-4`, 8 variants) | defect of the bounds | **Confirmed** | FIX, FULL | no: base gives no verdict on either program (timeout or memory) |
| D7. Generic type aliases are not transparent | defect | **Confirmed**, with a wrong cause for the unsound case and a stronger unsound case found here | base, FIX, FULL | yes |
| D8. A type alias changes the handling of cyclic lookups | defect | **Confirmed, but not distinct from D1**; one part is a gap of `extorder` | first part: base, FIX, FULL; second part: FIX, FULL | first part yes; second part no (base differs the other way) |
| L1. An unused generic parameter cannot be inferred | legitimate | **Not a defect** | – | – |
| L2. `T == T` for a type constructor is ill-kinded | legitimate | **Not a defect** (artefact of the generator) | – | – |
| L3. An open type argument is inferred from the conformances in scope | legitimate | **Not a defect** (the behaviour is required by `nullary-conformance.hylo`) | – | – |

## Confirmed defects

To reproduce: `./tc.sh (base|FIX|FULL) FILE`, from this directory.

### D1 (and D8). Declaration order decides the verdict when a cycle passes through an alias or a given

Reproduction, the three configurations: `violations/r1/al1--perm-0-2-1-4-3-5/a.hylo` is rejected (`definition of 'X' refers to itself`) and `b.hylo`, the same declarations with `extension X` before `type X`, is accepted. `violations/r5/red2--intro-all-top-0/b.hylo` (alias declared first) is rejected and `c.hylo` (alias declared last) is accepted. `violations/r1/names-verify-names-1-v6_summon_swapped--perm-0-2-1-4-3-5-6/a.hylo` is rejected and `b.hylo` accepted.

Correct verdict: the two orders must agree. In `al1` and `red2` the program has one consistent reading (`X` is `B`; the given `Alq is P` cannot provide `U is Q`), so the rejection is a false error. A language rule that forbids such cycles would reject both orders. No rule gives one verdict per order.

For base on the seven corpus programs I relied, like the campaign, on the pilot (`../permute-base.jsonl`); I checked that the seven are order-dependent there. The reduced pairs were re-run under base.

Cause. A cycle is noticed only when a declaration is entered a second time, by looking at `declarationsOnStack`, and each kind of declaration reacts differently. `declaredType(of: TypeAliasDeclaration.ID)` reports `definition of ... refers to itself` at once. `resolve(_:declaredIn:applyingTo:in:statically:)` skips an extension whose extended type is being computed, and `isVisible`/`notOnStack` skip a given whose type is being computed. Which of the three happens depends on which declaration of the cycle is typed first.

Two effects are specific to FIX and FULL, and both come from the fact that `noteExtensionCycle` and `popExtensionFrame` (flag `extorder`) only follow extension frames:
- `violations/r1/names-n12_poison_via_summon_noearly--perm-1-4-7-3-2-5-6-0/`: base accepts `a.hylo` and `b.hylo`; FIX and FULL reject `a.hylo` (`circular extension`) and accept `b.hylo`. When the given is typed first, the cycle is cut at the given, which is skipped silently, and no extension is ever re-entered.
- `violations/r5/names-verify-names-1-v4_noC--intro-all-0/`: FIX and FULL reject `a.hylo` as a circular extension and accept `b.hylo`, where the extended type is named through an alias. The lookup made while the alias is computed is recorded in the frame of the first extension only, and the memoized alias carries no trace of it. This is not a stable way round the rule: with the two extensions exchanged (`judge/progs/v4-alias-swapped.hylo`) the alias form is rejected with `definition of 'Alq' refers to itself`. So D8 is the order dependence of D1 seen through relation 5.

### D2. The orientation of an equality decides between two competing derivations

Reproduction, the three configurations: `violations/r7/e01-orient-amb--sym-2-2/a.hylo` (`where B is P, C is P, B == A, A == C`, then `g<A>()`) is accepted; `b.hylo` (`C == A` for `A == C`) is rejected.

Correct verdict: both must agree. `A is P` has two derivations that a symmetry of the program exchanges, so no ranking can prefer one; the program is ambiguous. The accepted spelling silently uses the conformance of `B`.

Cause. `takeSummonResultsUnchecked` advances all candidates one layer at a time and stops at the first layer in which one completes (`while done.isEmpty ...`). An equality used in the direction opposite to the one written needs the built-in symmetry given that `summon` adds, which costs one more layer. The trace (`judge/traces/`) shows `4 layers, 1 done` for `a.hylo` and `4 layers, 2 done, 2 minimal` for `b.hylo`: the second derivation is never seen in `a.hylo`. Under FIX and FULL the equality procedure reproduces the same ranking through its path cost.

### D5. The position of a tautology in the callee decides the verdict of a call

Reproduction, the three configurations: `violations/r4/hand-tautology-position/`. With `fun g<V where V is P>()` (`a.hylo`) or `<V where V is P, V == V>` (`c.hylo`) the call `g<A>()` is rejected, because `A is P` has two derivations. With `<V where V == V, V is P>` (`b.hylo`) it is accepted.

Correct verdict: the three must agree; `V == V` says nothing.

Cause. In `summon(_:in:where:then:penalties:ancestors:)` the penalty of a candidate is the index of its group of givens, and the groups start with one group per premise of the thread that is still pending (`environment.givens.reversed()`). `threadContinuation` discharges the premises of a callee from the last to the first. With `V == V` written first, `A ~ A` is still pending while `A is P` is proved, every step of that proof costs one more, and the derivation with three steps gets a larger penalty than the one with two. The trace of `b.hylo` shows `5 layers, 2 done, 1 minimal`; the trace of `a.hylo` shows `3 layers, 2 done, 2 minimal`. The penalty therefore measures the position of an unrelated requirement.

### D6, resource bound. The order of requirements decides whether the bound is hit

Reproduction, FIX and FULL: `violations/r2/open-wide-4--reqs-1-76543210/a.hylo` is accepted; `b.hylo`, the same eight requirements reversed, is rejected with `implicit resolution is too complex: more than 100000 candidate derivations`. Under base both programs end without a verdict (timeout, or abort at the memory limit).

Correct verdict: accept both. With `HYLO_TC_BUDGET=3000000`, FULL accepts `b.hylo` (206,750 candidate matches), so the rejection comes from the bound alone.

Cause. `takeSummonResultsUnchecked` gives up when the frontier holds more than `budgetLimit` threads and calls `reportResolutionBudgetExhausted`. The size of the frontier depends on the order in which `formThread` assumes the premises of `pick`, hence on the order of the requirements. The bound replaces a search that did not end, so base is not better; but under FIX and FULL a correct program is accepted or rejected according to its spelling.

### D7. Aliases of generic types are not transparent, and can accept an ill-typed call

Reproduction, the three configurations, each `a.hylo` accepted and `b.hylo` rejected: `violations/r5/hand-generic-alias-given-head/`, `hand-generic-alias-extension-head/`, `hand-generic-alias-receiver/`, `hand-alias-method-call/`. Generic aliases are a supported feature (`Tests/CompilerTests/negative/invalid-alias.hylo` expects `X<Void>` to accept `()`), so the accepted side is the correct one.

Unsound direction, found by the judge, the three configurations: `judge/progs/alias-args-lost.hylo`.

```hylo
struct K {}
struct A<U> {
  public fun f(x: U) {}
  public fun g() -> U { self.g() }
}
type AV = A<Void>
type AK = A<K>
fun use(a: AV, b: AK) { a.f(b.g()) }     // accepted: passes a K where a Void is expected
```

Without the aliases (`judge/progs/alias-args-ctrl.hylo`) the call is rejected with `cannot pass value of type 'K' to parameter 'Void'`. A generic alias behaves the same (`judge/progs/generic-alias-args-lost.hylo`).

Two causes.
- `resolve(_:nativeMemberOf:statically:)` finds the members of the aliased struct through `declarations(nativeMembersOf:)`, which looks through aliases, but substitutes the type arguments only when the receiver is itself a `TypeApplication` of the struct. Through `type Alq = A<Void>` the member keeps the parameter `U` of the struct; through `G<Void>` the arguments of the alias are substituted for the parameter of the struct, which changes nothing. Hence `cannot pass value of type 'Void' to parameter 'U'`, and the acceptance above, where both sides are `U`.
- `TypeStore.unifiable` replaces a bare `TypeAlias` by its definition but compares an application of a generic alias structurally: the alias constructor is unified with its unapplied definition, so `AB<T>` never matches `Box<A>`. This is what the head of a given, the head of an extension (through `applies`) and a receiver of type `AB<A>` run into. `dealiased` does expand such applications, which is why passing a `Box<A>` where an `AB<A>` is expected works (`judge/progs/galias-coercion.hylo`). One symptom is not explained by this: `need<AB<A>>()` fails against `given <T> => AB<T> is P {}` although a direct resolution of `P<AB<A>>` succeeds in the trace (`judge/progs/galias-goal-spelled.hylo`).

The README explained `violations/r5/b1d-method-env-cycle--intro-generic-0/` (rejected without the alias, accepted with it) by an occurs check that does not look under a generic alias. `occurs` in `TypeStore.swift` does visit the arguments of a type application and the definition of an alias. The acceptance comes from the first cause: the type of `mkbox(a).n` no longer mentions the type of `a`, so there is nothing for the check to find. Base confirms it: it overflows the stack on the cyclic binding of `a.hylo` and accepts `b.hylo` without a crash.

## Claims that are not defects, or that are open questions

**D3, left-to-right where clauses (97 variants).** `initializeContext` keeps the later requirements hidden while a requirement is typed, and its comment says so. A projection `U.X` written before the requirement that makes `U is P` derivable is an error by design. The README already calls this a language decision; it should not be counted among the defects. The README notes that the rule is not written down; I did not search the language documentation.

**D3, `violations/r2/v-abs-9--reqs-3-021/`.** Inside `trait P`, `where T == Self, T is P, T.X == U` makes `check<X>(x)` ill-typed and `where T == Self, T.X == U, T is P` makes it well-typed. Given the rule above the two programs are different: in the second, `T.X` is resolved when the only conformance of `T` is that of `Self`; in the first, the requirement `T is P` is in scope and is preferred, and its `X` is not `Self.X` because nothing says that two conformances of equal types coincide. Each verdict is right for its reading. What is open is the choice between the two conformances in the first program, which is the `Self.X` question of section 4.1 of the plan. It is not a new defect.

**D4, a tautological premise hides an ambiguity** (`violations/r4/g_dup0--taut-ground-3-0-last/`, `gz0--taut-ground-4-0-last/`). Reproduced in the three configurations, and with the premise on both conformances the ambiguity is reported again (`judge/progs/dup-both-premise.hylo`). The mechanism is the one of D2: the conformance without a premise completes one layer earlier. But here the two derivations really have different sizes, and "the smallest derivation wins" is a rule the language relies on: `Tests/CompilerTests/positive/nullary-conformance.hylo` has infinitely many derivations of `Int is P` and is accepted only because the smallest one is chosen (`judge/progs/nullary-smallest.hylo`, trace: `3 layers, 1 done`). Under that rule the accepted program is right. Whether a conformance with a satisfied premise should lose silently to a duplicate without one is a question for the designers of the ranking, not an implementation error.

**D6, depth bound** (`violations/r4/chain8--taut-ground-3-0-last/`). `chain8` needs nine steps and was written to sit at the bound of ten; one more step fails. With `HYLO_TC_MAXDEPTH=12` the variant is accepted in the three configurations. This is the known bound (`maxImplicitDepth`), already listed as an open question in the plan. The finding adds that the failure is reported as `no coercion`, with no mention of the bound.

**L1, L2, L3.** Reproduced (`violations/r4/use-before-init--unused-param-0/`, `higher-kinded--taut-param-4-0-last/`, `violations/r8/hand-open-goal/`). An uninferable parameter, an ill-kinded requirement produced by the generator, and the inference of an open argument from the only conformance in scope, which `nullary-conformance.hylo` requires. The transformations do not preserve the meaning in these cases.

## Coverage claims against the raw data

Checked from `data/rows-*.jsonl`, `data/baseline-FULL.jsonl` and `shapes/results.jsonl`:

- 15,206 distinct variants, 370 verdict changes, the per-relation and per-kind counts, the per-cause counts of `causes.py`, 0 invalid variants, 796 re-printed files with the same tokens and messages: all correct.
- FIX: 396 variants, the same pair of verdicts as FULL on all of them. They cover 308 of the 370 verdict changes: every variant attributed to D1–D8, L2 and L3, and 28 of the 90 of L1. The 62 not run are all L1.
- Base: 170 of the 370 verdict changes were run. For D1 in the corpus, 90 of 102 variants were not run under base (the pilot is the evidence). All reduced pairs were run under base by the campaign and again here.
- Declaration order: 124 programs of the declaration-order set were tested, not 129 (five have a syntax error); 114 of them with 23 permutations. Outside that set, 511 programs got two permutations, 92 one, and 33 none (a single declaration). "No other program among 727" therefore rests on the reversal and one rotation for most programs.
- The shape programs: counts confirmed. They are ten programs; "cycles through extensions only are handled" is true of the two shapes tried and of the corpus under FIX and FULL, not of base in general (the pilot counts 52 order-dependent programs under base).

What limits the statements of absence:

- **Half of the variants cannot show an accept-to-reject change.** 7,261 of the 15,206 variants have an original that is already rejected. For relation 3 only 141 variants have an accepted original; for relation 6, 773; for relation 8, 840.
- **Relation 3** (order of members): 197 variants of 120 programs, and 85 of these programs have a single variant. This is a small sample.
- **Relation 4**: a tautology was placed first in 179 variants and last in 2,292. D5 and the 16 changes of `taut-assoc` appear only with the tautology first, so the first position is where the effects are and it is the less tested one.
- **Relation 8**: the kinds `gconf` (a generic conformance), `ext` (a struct with an extension) and `conf-top` (a conformance placed first) were generated but never run. I ran them under FULL on 347 programs (the equalities and abstract-model sets and the positive compiler tests): 684 variants (`gconf` 156, `ext` 347, `conf-top` 181), two verdict changes, both on `nullary-conformance.hylo` and both instances of L3, and no change of messages elsewhere (`judge/r8-extra.jsonl`). The other program sets, and FIX and base, remain untested for these kinds.
- **FULL against FIX**: FIX was run only where FULL had changed its verdict, or on the seven order-dependent programs. A change of verdict that FIX shows and the optimizations hide could not be seen.
- **Relation 5** does not introduce aliases in local annotations or constructor calls, as the README says. Given D7, aliases of generic types in those positions are likely to fail too.
- One compiler test, `Tests/CompilerTests/negative/illegal-enum-case.hylo`, crashes `tc-bench` with signal 4 in the three configurations, in the original and in every variant. It is counted among the 760 programs and is not mentioned in the README. It is not a metamorphic finding.

## Corrections made to README.md

- The summary now states the judge's classification next to the campaign's, and points to this file.
- The sentence attributing the unsound case of D7 to the occurs check is replaced by the cause found here, and the stronger unsound program is added.
- "Every verdict change under FULL also occurs under FIX" is qualified (308 of 370 run; the rest are L1).
- D3 (`v-abs-9`), D4 and the depth bound of D6 are no longer called defects without qualification; D8 says that the alias form is itself order-dependent.
- The number of declaration-order programs tested (124) and the base outcome for `chain8--taut-app` are corrected, and the limits listed above are added to "What remains uncertain".

## Files of the judge

| File | Content |
|---|---|
| `judge/j.py` | runs programs under base, FIX and FULL, one process at a time; `-t` saves a trace, `-e NAME=VALUE` sets an environment variable |
| `judge/all-violations.txt` | the 402 re-runs of the reduced programs |
| `judge/results.jsonl` | every run made by the judge |
| `judge/progs/` | programs written by the judge |
| `judge/traces/` | resolution traces quoted above |
| `judge/r8extra.py`, `judge/r8-extra.jsonl` | the three kinds of relation 8 that had not been run, on a sample |
