# Soundness review — partial results (workflow run wf_3f983407-510)

The review workflow was interrupted twice (machine crash / session end). Completed agents so far:

## Reviewer verdict: **unsound** (topic: names)

### Soundness argument

The candidate computation itself does not change. In resolve(_:declaredIn:applyingTo:in:statically:) (Typer.swift ~4678-4705), the flag skips extension e exactly when `declarations(lexicallyIn: e)[n.identifier] == nil`. In that case the inner loop `for m in declarations(lexicallyIn: e)[n.identifier] ?? []` would have run zero times. Both sites use the same memoised table and the same key (n.identifier). The table only ever gets entries appended, so it is never present-but-empty. Program.declarations(lexicallyIn:) comes purely from scoping (scopeToDeclarations) and cannot change during typing, so building the tables early cannot leave them stale. So for a given Typer state, the set and order of NameResolutionCandidates is identical, for every kind of member: operators (key is the identifier, notation is ignored on both paths), labelled names, init, subscripts, static members, bundles, generic parameters (filtered after lookup on both paths), and members reached through traits or conformances (those go through resolve(inheritedMemberOf:), which already filters by name). A member can't be found through an extension unless it is lexically declared in it, because the baseline loop iterates exactly that table.

The REPORT's claim that "`applies` only fills a cache" is false, and that is where soundness breaks. applies(e, to: q) also:
- forces extendeeType(e), which evaluates e's extendee under `ignoring(e)` and memoises the result permanently, including an `.error` computed while a cycle was cut or while another extension was on the stack;
- in its slow path, runs matching and summon over all visible givens, which forces and memoises declaredType of conformances and given heads (e.g. `given A.Inner.Foo is P`) and fills scopeToSummoned.

The typer's cycle handling is order-dependent: the inner cyclic reference reports "refers to itself" and returns .error, and the outer call memoises the poisoned value. Removing these forced evaluations therefore changes the order in which extendees and given heads are first computed, which changes the results. Confirmed with the oracle in both directions:
- (a) the baseline reports a spurious cycle and breaks an extension, and names fixes it;
- (b) the baseline accepts a valid program and names rejects it with 2 errors.

Precondition for any divergence: a dependency cycle between an extension's extendee (or a conformance head) and a qualified member lookup, through an extension whose evaluation the baseline forced as a side effect. With no such cycle, names is dump-identical on everything tested (stdlib, all 192 tests, 15 targeted programs here). Another side effect of applies, fresh() calls and type-store insertions, shifts raw type identities (seen as `(erased: 1108)` vs `(erased: 780)` in builtin references) and variable numbering. The oracle normalises the identities. Relative order of variables is kept, and no dump or diagnostic in the corpus prints a type variable. So I found no visible effect from that.

### names-1 — names rejects programs the baseline accepts: skipping applies() changes when extendee and given types are first memoised (cycle poisoning)

*severity:* major, *kind:* unsound

**Evidence**

Repro /home/hylo/hylo-tc/research/review/names/n04_reverse_poison_min.hylo:
  struct A { struct Inner {} }
  struct C { type Foo = Bool }
  fun early(i: C.Foo) {}
  extension A.Inner.Foo { type Inner = Bool }   // E2
  extension A.Inner { type Foo = Int }          // E1
  fun use(x: Int.Inner) {}
The baseline has no diagnostics. With names (also names,index and names,unify,index,absmodel,loopcheck) the oracle shows MISMATCH: 0:13 '-> Foo' becomes '#!', 0:23 '-> Inner' becomes '#!', and two new errors appear: '6.19-22: error: type 'Inner' has no static member 'Foo'' and '9.16-21: error: type 'Int' has no static member 'Inner''.
Mechanism: the baseline's lookup of C.Foo calls applies(E2, C) first, in source order. That computes extendeeType(E2)=Int in a clean context. Under names, E2 is skipped because it does not declare Foo, so the first evaluation of E2's extendee happens inside extendeeType(E1). E1 is then on the stack and ignored, so A.Inner.Foo is not found and the .error is memoised for E2 (Typer.swift extendeeType ~1749-1770: setType(u) is called even when u is a cycle-truncated error).
Second repro, through summon rather than the extendee: /home/hylo/hylo-tc/research/review/names/n12_poison_via_summon_noearly.hylo (and n11 with an extra early lookup). Here applies(<T where T is P> T, C) in the baseline forces declaredType(given A.Inner.Foo is P) early. Under names it is first computed while E1 is ignored and memoised as error. Same two extra errors.
Also independently found by the earlier run: t03_names_worse.hylo.
Oracle outputs: /home/hylo/hylo-tc/research/review/names/oracle_all.txt and oracle_n11_n17.txt.

**Suggested fix**

The root cause is the baseline's order-dependent memoisation of results computed under a cut cycle or under ignoring(). Only fixing that makes names sound by construction.
Options:
(1) Do not memoise extendeeType or declaredType results when a cycle was detected underneath. Track a 'cycle-hit' flag and only cache when it is clear, as is already done with hasImplicitOnStack for summon.
(2) Bind all extension extendees in a dedicated pre-pass with a defined rule (e.g. extendee lookup sees only native members), independent of lookup order.
A cheaper partial mitigation, calling `_ = extendeeType(e)` before the skip check, would restore n04 but not n11/n12, which go through summon. It would also re-introduce the spurious baseline cycles of names-2. At minimum, correct REPORT §5.1 ('applies only fills a cache' is wrong) and list this exception.

### names-2 — Baseline reports spurious 'refers to itself' cycles through unrelated extensions; names removes them (elaboration and diagnostics differ, baseline is the broken side)

*severity:* minor, *kind:* baseline-bug

**Evidence**

Repro /home/hylo/hylo-tc/research/review/names/n01_alias_cycle.hylo:
  struct A { type Foo = Int }
  type X = A.Foo
  extension X { fun g() {} }
  fun h(x: Int) { x.g() }
The baseline gives 'error: definition of 'X' refers to itself' and 'type 'Int' has no member 'g''. Types 0:6..0:9 and 0:11/0:12 become '#!'. With names there are no diagnostics, 0:17 -> g, and the extension types as X.
Mechanism: while computing typealias X, the lookup of A.Foo calls applies(extension X, A). That evaluates the extendee X while X is on the stack: cycle, and the extension's extendee is memoised as error.
Same class: n05_spurious_cycle_conformance.hylo (the witness table for 'given X is P' changes from P<#!> to P<X>), n17_alias_cycle_generic.hylo (diagnostic-only: an extra 'definition of 'X' refers to itself'), and the earlier run's t01_ext_order.hylo. All are MISMATCH in the oracle for names alone and for names with the other flags.

**Suggested fix**

Call this out explicitly as a 'baseline broken' divergence in REPORT §5.1, with regression tests. The spurious cycle is a baseline bug, since `type X = A.Foo; extension X {...}` is a natural pattern. Names fixes it only incidentally: it still fails if the extension of X happens to declare Foo. The fix proposed in names-1 (no memoisation of cycle-truncated results) also addresses this.

### names-3 — names still pays an O(#visible extensions) scan per member lookup

*severity:* info, *kind:* perf

**Evidence**

tc-bench --count on research/workloads/members-big.hylo. Baseline user: names.appliesCalls=4008000, summon.matches=4262000. names user: appliesCalls=1000, names.skippedExtensions=4007000, summon.matches=14000. Each skip is a hash lookup in cache.scopeToLookupTable plus a copy-on-write OrderedDictionary return, and extensions(visibleFrom:) returns an array that is iterated in full. Stdlib: 7300 skipped vs 32 applies calls. Separately, when an extension is not skipped, declarations(lexicallyIn:) is looked up twice (in the guard and in the loop header).

**Suggested fix**

Implement the inverted index the report already proposes (identifier -> [extension] per module or per visible-extension set, cached with scopeToExtensions) to make lookups O(hits). Note that this has the same side-effect caveat as names-1. Also bind the lookup result once and reuse it in the loop.

### names-4 — REPORT claim 'semantics-preserving by construction' / 'applies only fills a cache' is incorrect

*severity:* minor, *kind:* claim

**Evidence**

REPORT.md §5.1 says: 'Semantics are unchanged by construction, since a skipped extension could not contribute candidates and `applies` only fills a cache'. §7 says: 'Land names (5 lines, semantics-preserving by construction)'. applies() (Typer.swift ~4944-4975) also calls extendeeType(d), which memoises the type of d with possible cycle errors and diagnostics. Its slow path calls formThread and takeSummonResults, which memoise declaredType of givens and fill scopeToSummoned. Counterexamples: names-1 and names-2.

**Suggested fix**

Reword: 'candidate sets are identical for a given typer state; divergence is possible only when the skipped applies() would have been the first to force an extendee or given type that participates in a cyclic dependency (see review/names tests)'.

### Checked OK

- Candidate generation: the skip predicate is exactly 'loop body iterates zero times' (same memoised table, same key n.identifier, table entries never empty), so for a fixed typer state the candidate sets and their order are identical
- Operators (infix+), argument-label overloads f(a:)/f(b:), static members, init in an extension, subscripts, unapplied S.f(a:): n09_kinds.hylo and t04_init_ops_subscript.hylo are dump-identical
- Ambiguity and not-found diagnostics across several extensions ("ambiguous use of 'f'", "has no member 'h'"): n06_diag_ambiguous.hylo and t06_ambiguous_notfound.hylo are identical. Diagnostics don't list candidates from skipped extensions
- Erroneous extendees (undefined symbol, missing member) emit the same diagnostics, because every extension is still checked in check(): n07_bad_extendee.hylo is identical
- Local or nested extensions (in a function body, in a struct body): n15_local_extension.hylo and t08_local_ext.hylo are identical
- Conditional extensions with where clauses, conditional conformances, universal <T is Q> T extensions: n08_conditional_ext.hylo and t07_conditional_ext.hylo are identical
- Trait extensions, associated types, Self in extensions, aliases as extendees: n10_trait_ext.hylo, t05_conf_in_ext.hylo, t10_alias_extendee.hylo, t11_static_meta.hylo and t12_self_ext.hylo are identical
- Where-clause that mentions a member only another extension declares: n16_cycle_via_where.hylo is identical
- Summon-cache warming through applies with refinement (Q refines P): n18/n19 are identical
- Type-variable numbering and type-store IDs shift with names (fresh() is called less often), but relative variable order is kept (SubstitutionTable sorts by bits, the counter is monotonic) and no dump or diagnostic in the 279 cached baseline dumps prints a type variable. n13/n14 have identical diagnostics
- Staleness of lookup tables built early: Program.declarations(lexicallyIn:) is fixed after scoping, so no invalidation issue
- Interaction with index/unify/absmodel/loopcheck: the same set of files differs under names alone and under every combination with names; no extra mismatches from combining

### Tests written

- `/home/hylo/hylo-tc/research/review/names/n01_alias_cycle.hylo`
- `/home/hylo/hylo-tc/research/review/names/n02_reverse_poison_noeffect.hylo`
- `/home/hylo/hylo-tc/research/review/names/n03_reverse_poison.hylo`
- `/home/hylo/hylo-tc/research/review/names/n04_reverse_poison_min.hylo`
- `/home/hylo/hylo-tc/research/review/names/n05_spurious_cycle_conformance.hylo`
- `/home/hylo/hylo-tc/research/review/names/n06_diag_ambiguous.hylo`
- `/home/hylo/hylo-tc/research/review/names/n07_bad_extendee.hylo`
- `/home/hylo/hylo-tc/research/review/names/n08_conditional_ext.hylo`
- `/home/hylo/hylo-tc/research/review/names/n09_kinds.hylo`
- `/home/hylo/hylo-tc/research/review/names/n10_trait_ext.hylo`
- `/home/hylo/hylo-tc/research/review/names/n11_poison_via_summon.hylo`
- `/home/hylo/hylo-tc/research/review/names/n12_poison_via_summon_noearly.hylo`
- `/home/hylo/hylo-tc/research/review/names/n13_typevar_in_diag.hylo`
- `/home/hylo/hylo-tc/research/review/names/n14_typevar_in_diag2.hylo`
- `/home/hylo/hylo-tc/research/review/names/n15_local_extension.hylo`
- `/home/hylo/hylo-tc/research/review/names/n16_cycle_via_where.hylo`
- `/home/hylo/hylo-tc/research/review/names/n17_alias_cycle_generic.hylo`
- `/home/hylo/hylo-tc/research/review/names/n18_summon_cache_refinement.hylo`
- `/home/hylo/hylo-tc/research/review/names/n19_summon_cache_refinement_ctrl.hylo`
- `/home/hylo/hylo-tc/research/review/names/oracle_all.txt`
- `/home/hylo/hylo-tc/research/review/names/oracle_n11_n17.txt`
- `/home/hylo/hylo-tc/research/review/names/oracle_n13_n19.txt`
- `(earlier run in the same dir: t01_ext_order..t12_self_ext.hylo, oracle_t01_t03.txt)`

### Redundancy notes

names and index target different costs. names removes almost all applies() calls (stdlib 7332 -> 32; members-big user 4.0M -> 1000), and with them the summon.matches spent inside applies' matching (stdlib 41452 -> 20052). index speeds up summon over givens. With names on, little of index's benefit comes from extension matching, so their gains add up rather than overlap. The applies memo (scopeToExtensionApplies) gets far fewer hits under names, which is expected and harmless. names is also consistent with the trait path: lookup(_:memberOfTraitVisibleFrom:) already filtered by name before summoning. The remaining overhead is the per-lookup linear scan over visible extensions (4.0M skip checks on members-big). The inverted index proposed in the report would remove it, but would inherit the same side-effect caveat (names-1).

## Adversarial verification: confirmed=True, severity=minor, reproduced=True

I tried to refute this and could not.

Code: in Typer.swift, the `names` change at line 4683 skips `applies(e, to: q, in:)` for any extension that declares no member named `n`. `applies` (lines 4944-4975) is not a pure cache filler. Before it ever touches the cache, it unconditionally calls `extendeeType(d)` (lines 1749-1771). `extendeeType`:
(a) evaluates the extendee type ascription while `d` is inserted in `declarationsOnStack`, under `ignoring(d, ...)`;
(b) memoises the result for good with `program[d.module].setType(u, for: d)`;
(c) on re-entry reports "declaration refers to itself" and returns `.error`.
Also, the member loop in `resolve(_:declaredIn:...)` skips any extension that is on `declarationsOnStack`. So a skipped `applies` changes the order in which extendee and alias types are first forced, and therefore which lookups run while a declaration is on the stack. Those order-dependent results, including errors, are memoised. The slow path (`formThread`, `takeSummonResults`) can also force and memoise given types. So "a skipped extension could not contribute candidates and `applies` only fills a cache" is false. The candidate set is the same only for a fixed typer state, and skipping `applies` changes that state.

Oracle re-run (saved in /home/hylo/hylo-tc/research/review/names/verify-names-4/oracle_rerun.txt): `names` 0/3 identical and `names,index` 0/3 identical; `index` alone 3/3 identical. Files tested:
- /home/hylo/hylo-tc/research/review/names/n01_alias_cycle.hylo: the baseline reports a spurious "definition of 'X' refers to itself" plus "type 'Int' has no member 'g'". `names` types the program cleanly. Here the baseline is the broken one.
- /home/hylo/hylo-tc/research/review/names/n05_spurious_cycle_conformance.hylo: the baseline gives `#!` (error) types and `names` gives X. Again the baseline is broken.
- /home/hylo/hylo-tc/research/review/names/n04_reverse_poison_min.hylo: the baseline accepts the program with 0 diagnostics (`Int.Inner` resolves to Inner; checked in the raw dump base_n04.txt). With `names` it has 2 new errors: "6.19-22: type 'Inner' has no static member 'Foo'" and "9.16-21: type 'Int' has no static member 'Inner'" (names_n04.txt). Here `names` is strictly worse on a program the baseline accepts.

So the divergence goes both ways. It is not limited to cases where the baseline is broken, and the "semantics-preserving by construction" wording in §5.1 and §7 (the "Land names" recommendation) is wrong under the task's definition of sound. The suggested rewording is close, but too narrow and too soft. It says divergence happens only when the skipped `applies` would have been first to force a type "that participates in a cyclic dependency". In n04 there is no real cycle in the program's semantics: the only cycle comes from the typer's evaluation order, and the baseline resolves it. Severity is minor because this finding is about the wording; the unsoundness itself is the substance of names-1 and names-2. It does matter to the landing recommendation, though.

**Recommended fix**

1) REPORT §5.1 should say: "For a fixed typer state, skipping an extension that declares no member `n` removes no candidate. But `applies` is not side-effect free: it forces and permanently memoises `extendeeType(e)`, plus given types on the slow path. Those computations run under `declarationsOnStack`/`ignoring`, so their results (including cycle errors and failed member lookups) depend on evaluation order. With `names` the order changes, so the elaboration and diagnostics can differ when extendees or aliases depend on members declared in other extensions. n01/n05: names removes spurious cycle errors the baseline reports. n04: names rejects a program the baseline accepts. names is therefore not sound by the review definition. It is sound on all 192 tests plus the workloads." §7 should drop "by construction" and say "dump-identical on the test corpus; known order-dependent divergence on mutually dependent extension and alias programs (review/names)".

2) To make `names` truly order-independent, fix the root cause instead of the flag. Stop memoising type or lookup results computed while a declaration they depend on is on `declarationsOnStack`, so a provisional cycle-broken result is never persisted. Alternatively, force `extendeeType` for every extension of the module in source order in a pre-pass before any member lookup; this is cheap, one evaluation per extension. With either change the baseline and `names` no longer depend on lookup order, and the skip in `resolve(_:declaredIn:...)` becomes a pure filter. Then re-check n01, n03, n04, n05, n11, n16 and n17 with the oracle.

## Adversarial verification: confirmed=True, severity=minor, reproduced=True

I tried to refute the finding and could not. Every part of it held up when re-run.

1) Oracle re-run. Command: semtest --configs "names;index;unify;names,index,unify,absmodel,loopcheck" on n01, n05, n17 and t01. names alone matched 0/4. The all-flags config without solver also matched 0/4. index and unify alone matched 4/4. The diffs are the ones claimed:
- n01: the baseline types 0:6-0:9 and 0:11/0:12 as '#!' and emits "definition of 'X' refers to itself" (5.6-7) and "type 'Int' has no member 'g'". names gives Metatype<X>, 0:17 -> g, and no diagnostics.
- n05: the witness/conformance type is P<#!> in the baseline and P<X> with names.
- n17: the only difference is the extra cycle diagnostic.
- t01: 0:12 -> V and 0:20 -> hello appear only with names.

2) Mechanism, checked in the code (Sources/FrontEnd/Typer/Typer.swift):
- declaredType(of: TypeAliasDeclaration) (l.1536-1563) puts X on declarationsOnStack and evaluates A.Foo.
- The member lookup reaches resolve(_:declaredIn:applyingTo:) (l.4677+). That loop skips only extensions that are themselves on the stack (l.4681), not extensions whose extendee is on the stack. It then calls applies(e, to: A) (l.4944).
- applies calls extendeeType(e) (l.1749) before any fast path.
- extendeeType evaluates the ascription X, which re-enters declaredType(of: X). The insert fails, so the cycle diagnostic is reported (l.1561) and .error comes back. extendeeType then memoises .error as the extension's type (setType at l.1762), so every later lookup through `extension X` fails.
- With names, l.4683 skips extensions with no member named Foo, so applies and extendeeType never run for `extension X` during alias evaluation.

3) Further evidence I wrote and ran (files in /home/hylo/hylo-tc/research/review/names/verify-names-2/, oracle output in oracle_v.txt):
- The baseline depends on declaration order, which shows the baseline is the broken side. v02_ext_before_alias.hylo and v04_use_before.hylo are n01 with `extension X` placed before `type X`. The baseline reports no diagnostics there and types g correctly, because the extension is already on declarationsOnStack and is skipped at l.4681. Only the order alias-then-extension triggers the spurious cycle.
- v01_ext_declares_foo.hylo adds `type Foo = Bool` to `extension X`. Both baseline and names still report the spurious "refers to itself" and "no member 'g'" (dump identical). So names removes the cycle only incidentally, as the finding says.
- More mismatches of the same class:
  - v06_member_of_ext_alias.hylo: Foo is declared in an extension of A. The baseline gives a cycle diagnostic and #!, names types it fine.
  - v08_two_aliases.hylo: two aliases, X's extension is poisoned in the baseline.
- Controls that were identical: v03 (direct `extension Int`), v05 (a genuine X=Y=X cycle, same diagnostic in both), v07 (`extension A.Foo` with no alias).

4) The REPORT is wrong here. §5.1 says names is "semantics-preserving by construction ... `applies` only fills a cache". That is false: applies -> extendeeType has observable side effects (it reports diagnostics and memoises error extendee types). names is therefore not dump-identical to the baseline. The differences occur only where the baseline is broken (a spurious, order-dependent cycle), so under the stated soundness definition this is acceptable only if it is called out explicitly. The severity stays minor: names gives the better answer, but the report's soundness argument must be corrected.

**Recommended fix**

(a) Correct REPORT §5.1. Drop "semantics-preserving by construction / applies only fills a cache". Say instead that names is dump-identical except where the baseline reports a spurious, declaration-order-dependent cycle (alias X defined through a member lookup, plus a later `extension X`). In those cases names gives the correct result. Cite n01, n05, n17, t01 and v02/v04 (order dependence) as regression tests, and v01 as the case names does not fix.

(b) Fix the baseline bug itself, independently of names. In resolve(_:declaredIn:applyingTo:...), evaluating an extension's extendee for applicability should be speculative.
- If extendeeType(e) is not yet memoised and its evaluation hits a declaration already on declarationsOnStack, treat e as not applicable for this query (return no candidates).
- Do not report the cycle diagnostic and do not memoise .error for e.
- For example, add a `speculative: Bool` parameter, or a separate tryExtendeeType(e) -> AnyTypeIdentity?. It would run the evaluation with diagnostics buffered and, on a cycle, discard the buffer and skip setType (the same "do not memoise cycle-truncated results" rule proposed in names-1).
- The extension's extendee is then computed normally when the extension itself is checked, so it binds to Int and `x.g()` resolves.

A genuine cycle (e.g. v05, X=Y=X) is still reported when the alias itself is typed.

Keep names as the fast path on top of this. With (b) in place, names becomes truly semantics-preserving, since skipped extensions would then have had no side effects.

## Adversarial verification: confirmed=True, severity=major, reproduced=True

I could not refute the finding. I re-ran the oracle on the cited repros. With names, names,index and names,unify,index,absmodel,loopcheck, all four (n04, n11, n12, t03) give 0/4 identical. With unify,index,absmodel,loopcheck (no names), index alone, or unify alone, all four are identical, so names is the cause. Output: /home/hylo/hylo-tc/research/review/names/verify-names-1/oracle_cited.txt. For n04, the baseline has no user diagnostics. Under names it adds "6.19-22: error: type 'Inner' has no static member 'Foo'" and "9.16-21: error: type 'Int' has no static member 'Inner'", and 0:13 and 0:23 lose their bindings (they become #!).

Code check: the skip is at Typer.swift:4683 (`if TyperExperiments.names && declarations(lexicallyIn: e)[n.identifier] == nil { continue }`). It comes before `applies(e, to: q, in:)`, and applies() always calls `extendeeType(d)` first, at about line 4955. extendeeType (lines 1749-1771) runs the extendee under `ignoring(d)`, while the loop at 4681 filters out extensions on `declarationsOnStack`. It then calls `setType(u, for: d)` without conditions, even when u came from a lookup that silently skipped an on-stack extension. So applies() does more than fill a cache: it decides the order in which extendees are first evaluated and memoised. REPORT §5.1's claim "semantics are unchanged by construction ... applies only fills a cache" is wrong.

Mechanism, checked with variants in /home/hylo/hylo-tc/research/review/names/verify-names-1/ (outputs in oracle_variants.txt):
- v5_early_other: the early lookup uses a name no extension declares (C.Bar). names then skips both extensions in both runs, and the result is identical.
- v1_noearly and v4_noC: without the early lookup, the result is identical.
- v3_nouse: only the early lookup of C.Foo is needed to break it. Under names it adds the 6.19-22 error.
So the divergence comes from the lookup of C.Foo. The baseline calls applies(E2, C) and evaluates extendeeType(E2) cleanly (= Int). Under names, E2 is skipped, so E2's extendee is first evaluated inside extendeeType(E1): looking up Inner in A reaches E2, whose extendee A.Inner.Foo cannot see E1 because E1 is on the stack. .error is then memoised for E2.

Mitigating context: the baseline is itself order-dependent. Swapping the two extensions (v2_swapped.hylo), or reordering n12's declarations (v6_summon_swapped.hylo), makes the baseline produce the same two errors. names only changes which order wins. These are rare self-referential extension chains, not a crash or depth cap, so under the stated definition (identical diagnostics) this is a real unsoundness. It should be listed as an exception, not excused. Severity is major because valid programs the baseline accepts get rejected. In practice it is limited to extendees or given types that depend on members added by other extensions. I agree that the cheap mitigation of forcing `_ = extendeeType(e)` before the skip would not cover n11/n12. There the side effect is the summon inside applies' slow path (formThread/takeSummonResults forcing declaredType of `given A.Inner.Foo is P`).

**Recommended fix**

Fix the baseline's order-dependent memoisation, so that names becomes sound by construction instead of being made to replay the baseline's side effects.
1. Add a taint counter to Typer, e.g. `var cycleCuts = 0`. Increment it wherever an on-stack declaration is silently excluded:
   - the `where !declarationsOnStack.contains(.init(e))` filter in resolve(_:declaredIn:...) at Typer.swift:4681, when it actually excludes an e other than the outermost declaration being computed;
   - `notOnStack(g)` returning false during given collection;
   - the "declaration refers to itself" branch of extendeeType (and the analogous branches of declaredType).
2. In extendeeType, save `let c0 = cycleCuts` before evaluating, and call `program[d.module].setType(u, for: d)` only if `cycleCuts == c0`, or if the frame is the outermost one on declarationsOnStack, in which case its result is authoritative. Otherwise return u without memoising and leave cycleCuts raised, so that enclosing frames are also not memoised. Apply the same guard to memoising declaredType of givens and conformances.
3. Extend the existing `!hasImplicitOnStack()` guard on cache.scopeToExtensionApplies (line ~4972) to also require `cycleCuts == c0`.
Results computed under a cut are then recomputed once the cut is gone. For n04, E2 resolves to Int and E1 to A.Inner whatever the lookup order, which also fixes the baseline's own failures on v2_swapped and v6_summon_swapped. Recomputation only happens in cyclic cases, so the cost is negligible.
This changes baseline behaviour, so the dumps must be re-baselined.
Until then:
- Keep names, but correct REPORT §5.1: applies() has side effects (it evaluates and memoises extendee types and given declared types).
- List "programs whose extendee or given types depend on members added by other extensions" as a known divergence.
- Add n04, n12 and t03 as regression tests.
Forcing `_ = extendeeType(e)` before the skip is only a partial patch: it fixes n04 but not n11/n12, and per names-2 it reintroduces spurious cycles, so I do not recommend it.
