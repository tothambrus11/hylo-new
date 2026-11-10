Programs: 801; skipped: {'syntax error in the original': 32, 'slow': 4, 'large': 5}; re-printed program differs from the original: 0 (verdict), 0 (verdict or messages).

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

Groups of violations (same relation, kind, verdicts and error messages with the names blanked), with what FIX and base
give for the members that were run under them (`same`: the same pair of verdicts as FULL; otherwise the pair):

| Relation | Kind | FULL: original -> variant | Error of the rejected side | Variants | Programs | FIX | base |
|---|---|---|---|---:|---:|---|---|
| r1 | permute | accept -> reject | type '_' has no static member '_' | 19 | 1 | same: 19 | not run |
| r1 | permute | reject -> accept | definition of '_' refers to itself | 16 | 1 | same: 16 | not run |
| r1 | permute | reject -> accept | type '_' has no static member '_' | 47 | 5 | same: 47 | not run |
| r2 | reqs | accept -> reject | implicit resolution is too complex: more than 100000 candidate derivations; conside | 1 | 1 | same: 1 | timeout -> timeout: 1 |
| r2 | reqs | accept -> reject | type '_' has no static member '_' | 81 | 37 | same: 81 | accept -> crash:-6: 1, accept -> timeout: 4, same: 55 |
| r2 | reqs | reject -> accept | cannot pass value of type '_' to parameter '_' | 1 | 1 | same: 1 | same: 1 |
| r2 | reqs-dep | accept -> reject | implicit resolution is too complex: more than 100000 candidate derivations; conside | 1 | 1 | same: 1 | timeout -> timeout: 1 |
| r4 | taut-app | accept -> reject | no coercion from '_' to '_' | 2 | 1 | same: 2 | accept -> timeout: 1 |
| r4 | taut-assoc | accept -> reject | type '_' has no static member '_' | 16 | 16 | same: 16 | reject -> reject: 2, same: 12 |
| r4 | taut-ground | accept -> reject | no coercion from '_' to '_' | 2 | 1 | same: 2 | not run |
| r4 | taut-ground | reject -> accept | ambiguous use of '_' | 4 | 2 | same: 4 | same: 4 |
| r4 | taut-ground | reject -> accept | no coercion from '_' to '_' | 4 | 2 | same: 4 | same: 4 |
| r4 | taut-param | accept -> reject | T expects 1 type argument(s) | 1 | 1 | same: 1 | same: 1 |
| r4 | taut-param | accept -> reject | implicit resolution is too complex: more than 100000 candidate derivations; conside | 3 | 1 | same: 3 | timeout -> crash:-6: 1, timeout -> timeout: 2 |
| r4 | taut-param | accept -> reject | no coercion from '_' to '_' | 3 | 3 | same: 3 | accept -> timeout: 1, same: 2 |
| r4 | unused-param | accept -> reject | not enough context to infer a type | 90 | 84 | same: 28 | same: 12 |
| r5 | expand | reject -> accept | definition of '_' refers to itself | 1 | 1 | same: 1 | same: 1 |
| r5 | expand | reject -> accept | type '_' has no static member '_' | 2 | 2 | same: 2 | same: 2 |
| r5 | expand-drop | reject -> accept | definition of '_' refers to itself | 1 | 1 | same: 1 | same: 1 |
| r5 | expand-drop | reject -> accept | type '_' has no static member '_' | 2 | 2 | same: 2 | same: 2 |
| r5 | intro-all | accept -> reject | cannot pass value of type '_' to parameter '_' | 1 | 1 | same: 1 | same: 1 |
| r5 | intro-all | accept -> reject | definition of '_' refers to itself | 1 | 1 | same: 1 | same: 1 |
| r5 | intro-all | reject -> accept | circular extension: the extendee of this extension depends on a lookup of '_', whic | 5 | 5 | same: 5 | accept -> reject: 5 |
| r5 | intro-all-top | accept -> reject | cannot pass value of type '_' to parameter '_' | 1 | 1 | same: 1 | same: 1 |
| r5 | intro-all-top | accept -> reject | definition of '_' refers to itself | 16 | 12 | same: 16 | same: 8 |
| r5 | intro-all-top | accept -> reject | type '_' has no static member '_' | 4 | 4 | same: 4 | same: 4 |
| r5 | intro-generic | accept -> reject | cannot pass value of type '_' to parameter '_' | 1 | 1 | same: 1 | same: 1 |
| r5 | intro-generic | accept -> reject | cannot pass value of type '_' to parameter '_'; no coercion from '_' to '_'; no conversion from '_' to '_'; type '_' has no member '_' | 1 | 1 | same: 1 | same: 1 |
| r5 | intro-generic | accept -> reject | no coercion from '_' to '_' | 15 | 15 | same: 15 | accept -> timeout: 1, reject -> reject: 1, same: 9 |
| r5 | intro-generic | accept -> reject | type '_' has no member '_' | 6 | 6 | same: 6 | same: 6 |
| r5 | intro-generic | accept -> reject | type '_' has no static member '_' | 2 | 2 | same: 2 | same: 2 |
| r5 | intro-generic | reject -> accept | cannot pass value of type '_' to parameter '_' | 2 | 2 | same: 2 | crash:-11 -> accept: 2 |
| r7 | dup | accept -> reject | implicit resolution is too complex: more than 100000 candidate derivations; conside | 1 | 1 | same: 1 | timeout -> timeout: 1 |
| r7 | dup-sym | accept -> reject | implicit resolution is too complex: more than 100000 candidate derivations; conside | 2 | 1 | same: 2 | timeout -> timeout: 2 |
| r7 | dup-sym | accept -> reject | no coercion from '_' to '_' | 1 | 1 | same: 1 | same: 1 |
| r7 | dup-sym | reject -> accept | no coercion from '_' to '_' | 1 | 1 | same: 1 | same: 1 |
| r7 | sym | accept -> reject | no coercion from '_' to '_' | 2 | 1 | same: 2 | same: 2 |
| r7 | sym | reject -> accept | no coercion from '_' to '_' | 3 | 2 | same: 3 | same: 3 |
| r8 | conf | accept -> reject | no coercion from '_' to '_' | 1 | 1 | same: 1 | not run |
| r8 | conf | reject -> accept | no coercion from '_' to '_' | 7 | 7 | same: 7 | crash:-11 -> accept: 6 |

Violating variants under FULL, with the verdicts original -> variant under each configuration:

| Relation | Program | Variant | FULL | FIX | base |
|---|---|---|---|---|---|
| r4 | Tests/CompilerTests/negative/use-before-declaration.hylo | unused-param:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/negative/use-before-init.hylo | unused-param:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/assignment.hylo | unused-param:2 | accept -> reject | accept -> reject | accept -> reject |
| r2 | Tests/CompilerTests/positive/associated-type-equality.hylo | reqs:7:3210 | accept -> reject | accept -> reject | accept -> reject |
| r5 | Tests/CompilerTests/positive/context-bound.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/enum-constructor.hylo | unused-param:4 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/existentialization-1.hylo | unused-param:2 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/existentialization-3.hylo | unused-param:13 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/existentialization-5.hylo | unused-param:14 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/generic-bundle.hylo | unused-param:4 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/generic-call-1.hylo | unused-param:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/generic-call-2.hylo | unused-param:8 | accept -> reject | accept -> reject | accept -> reject |
| r5 | Tests/CompilerTests/positive/generic-member.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | Tests/CompilerTests/positive/generic-member.hylo | intro-all:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | Tests/CompilerTests/positive/generic-member.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/higher-kinded.hylo | taut-param:4:0:last | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/higher-kinded.hylo | unused-param:4 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/implicit-qualification.hylo | unused-param:12 | accept -> reject | accept -> reject | accept -> reject |
| r5 | Tests/CompilerTests/positive/implicit-qualification.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/inlining-existentialized.hylo | unused-param:5 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/metatype.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/nested-given-1.hylo | unused-param:4 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/nullary-conformance.hylo | unused-param:2 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/nullary-conformance.hylo | unused-param:3 | accept -> reject | accept -> reject | not run |
| r8 | Tests/CompilerTests/positive/nullary-conformance.hylo | conf:0 | accept -> reject | accept -> reject | not run |
| r5 | Tests/CompilerTests/positive/overload-priority.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | Tests/CompilerTests/positive/refinement.hylo | unused-param:7 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/remote-binding.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/stored-binding.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | Tests/CompilerTests/positive/tuple-consing.hylo | unused-param:4 | accept -> reject | accept -> reject | not run |
| r5 | abstract-model/probe1.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> timeout |
| r4 | cycles-and-crashes/a2-arrow-env-generic.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a4-annot.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a4-annot.hylo | unused-param:1 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a4-env-var-goal.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a4-env-var-goal.hylo | unused-param:1 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a4-explicit.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a5-env-var-goal-ctrl.hylo | unused-param:0 | accept -> reject | accept -> reject | not run |
| r4 | cycles-and-crashes/a5-env-var-goal-ctrl.hylo | unused-param:1 | accept -> reject | not run | not run |
| r5 | cycles-and-crashes/b1c-method-cycle-ctrl.hylo | intro-generic:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r5 | cycles-and-crashes/b1d-method-env-cycle.hylo | intro-generic:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r8 | cycles-and-crashes/cyclic-query-segfault.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r4 | cycles-and-crashes/e2-abs-qual-distinct-conf.hylo | taut-assoc:2:1:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | cycles-and-crashes/e3-env-implicit.hylo | unused-param:0 | accept -> reject | not run | not run |
| r8 | cycles-and-crashes/n1-nested-occurs.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r8 | cycles-and-crashes/n1-nested.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r8 | cycles-and-crashes/n2-nested2.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r4 | cycles-and-crashes/o1-value-ctx.hylo | unused-param:2 | accept -> reject | not run | not run |
| r4 | cycles-and-crashes/o1-value-ctx.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | cycles-and-crashes/o1-value-ctx.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r8 | cycles-and-crashes/o2-toplevel-occurs.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r8 | cycles-and-crashes/o4-toplevel-occurs-full.hylo | conf:0 | reject -> accept | reject -> accept | crash:-11 -> accept |
| r4 | cycles-and-crashes/q2-open-eq-amb.hylo | unused-param:0 | accept -> reject | not run | not run |
| r8 | cycles-and-crashes/variant-swapped.hylo | conf:0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:0,2,1,4,3,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:0,2,4,1,3,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:0,4,5,2,3,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:1,0,4,5,2,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:1,2,0,4,3,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:1,2,4,5,3,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:2,4,0,3,5,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:4,0,1,2,5,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al1.hylo | perm:4,2,1,5,3,0 | reject -> accept | reject -> accept | not run |
| r5 | declaration-order/al1.hylo | expand-drop:0 | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/al1.hylo | expand:0 | reject -> accept | reject -> accept | reject -> accept |
| r1 | declaration-order/al2.hylo | perm:0,1,5,4,2,3 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:0,3,4,2,5,1 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:0,4,1,2,3,5 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:0,4,1,2,5,3 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:1,0,3,4,5,2 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:1,4,3,0,2,5 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:3,1,4,5,0,2 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:3,5,2,1,4,0 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:4,3,1,0,5,2 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:4,3,2,0,1,5 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,1,0,3,2,4 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,1,2,0,3,4 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,1,3,0,4,2 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,1,4,0,2,3 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,2,4,3,1,0 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,3,4,1,2,0 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,3,4,2,0,1 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,4,2,0,3,1 | accept -> reject | accept -> reject | not run |
| r1 | declaration-order/al2.hylo | perm:5,4,3,2,1,0 | accept -> reject | accept -> reject | not run |
| r5 | declaration-order/al2.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r1 | declaration-order/al3.hylo | perm:0,3,1,4,5,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al3.hylo | perm:3,4,0,5,1,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al3.hylo | perm:3,4,1,0,2,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al3.hylo | perm:3,4,5,0,2,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al3.hylo | perm:4,0,2,1,3,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/al3.hylo | perm:4,1,2,3,5,0 | reject -> accept | reject -> accept | not run |
| r5 | declaration-order/al3.hylo | expand-drop:0 | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/al3.hylo | expand:0 | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/g1.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/g2.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/g3.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/g4.hylo | unused-param:7 | accept -> reject | not run | not run |
| r4 | declaration-order/g_dup0.hylo | taut-ground:3:0:last | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/g_dup0.hylo | taut-ground:5:0:last | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/ge3.hylo | taut-ground:11:0:last | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/ge3.hylo | taut-ground:7:0:last | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/gvalid.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/gz0.hylo | taut-ground:4:0:last | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/gz0.hylo | taut-ground:6:0:last | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/n04-order-b.hylo | intro-all:2 | reject -> accept | reject -> accept | accept -> reject |
| r4 | declaration-order/names-g1.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/names-g2.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/names-g3.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/names-g4.hylo | unused-param:7 | accept -> reject | not run | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:3,8,7,5,6,4,0,2,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:5,2,6,1,3,4,0,8,7 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:5,8,3,7,0,2,4,1,6 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:5,8,6,1,4,7,0,2,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:6,3,2,7,5,4,0,8,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:6,3,8,7,1,0,4,2,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:6,5,0,2,1,7,4,8,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:6,8,0,5,1,2,3,7,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:8,5,0,3,6,2,4,1,7 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:8,6,3,5,7,0,1,2,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:8,7,3,1,4,6,2,5,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n11_poison_via_summon.hylo | perm:8,7,6,5,4,3,2,1,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:1,4,7,3,2,5,6,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:1,4,7,6,2,3,5,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:2,7,6,5,3,0,1,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:4,5,2,1,7,0,6,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:5,0,6,1,3,7,2,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:5,0,6,7,1,4,2,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:5,1,2,7,0,6,4,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:5,1,4,3,0,7,2,6 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:5,4,6,3,0,1,7,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-n12_poison_via_summon_noearly.hylo | perm:7,6,5,4,3,2,1,0 | reject -> accept | reject -> accept | not run |
| r5 | declaration-order/names-verify-names-1-v1_noearly.hylo | intro-all:0 | reject -> accept | reject -> accept | accept -> reject |
| r5 | declaration-order/names-verify-names-1-v4_noC.hylo | intro-all:0 | reject -> accept | reject -> accept | accept -> reject |
| r5 | declaration-order/names-verify-names-1-v5_early_other.hylo | intro-all:2 | reject -> accept | reject -> accept | accept -> reject |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:0,2,1,4,3,5,6 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:0,4,2,6,3,1,5 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:0,5,6,1,2,3,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:1,0,2,4,5,3,6 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:1,6,5,2,3,0,4 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:2,1,5,6,4,3,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:2,5,1,0,6,4,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:2,5,4,0,6,3,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:4,3,5,6,1,0,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-1-v6_summon_swapped.hylo | perm:6,5,4,3,2,1,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:0,2,1,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:0,2,3,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:0,3,1,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:0,3,2,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,0,1,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,0,3,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,1,0,3 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,1,3,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,3,0,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:2,3,1,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,0,1,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,0,2,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,1,0,2 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,1,2,0 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,2,0,1 | reject -> accept | reject -> accept | not run |
| r1 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | perm:3,2,1,0 | reject -> accept | reject -> accept | not run |
| r5 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | expand-drop:0 | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/names-verify-names-2-v01_ext_declares_foo.hylo | expand:0 | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/perf_g1.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/perf_g16.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | declaration-order/perf_g4.hylo | unused-param:5 | accept -> reject | not run | not run |
| r5 | declaration-order/r1_nested.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | declaration-order/r1_selfname.hylo | intro-all-top:1 | accept -> reject | accept -> reject | accept -> reject |
| r5 | declaration-order/r1_selfname_fun.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r2 | declaration-order/r2_where_assoc.hylo | reqs:4:10 | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/r2_where_assoc.hylo | taut-assoc:4:1:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | declaration-order/r2_where_assoc_ctrl.hylo | reqs:4:10 | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/r2_where_assoc_ctrl.hylo | taut-assoc:4:1:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/r2_where_assoc_fun.hylo | taut-assoc:5:1:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/red2.hylo | taut-assoc:12:1:first | accept -> reject | accept -> reject | accept -> reject |
| r5 | declaration-order/red2.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | declaration-order/red3.hylo | taut-ground:10:0:last | reject -> accept | reject -> accept | reject -> accept |
| r4 | declaration-order/red3.hylo | taut-ground:12:0:last | reject -> accept | reject -> accept | reject -> accept |
| r5 | declaration-order/v4-use-first.hylo | intro-all:0 | reject -> accept | reject -> accept | accept -> reject |
| r4 | equalities/a05-quantified.hylo | unused-param:2 | accept -> reject | not run | not run |
| r5 | equalities/a05-quantified.hylo | intro-generic:0 | accept -> reject | accept -> reject | reject -> reject |
| r4 | equalities/a07-open.hylo | unused-param:0 | accept -> reject | not run | not run |
| r2 | equalities/a08-assoc-generic.hylo | reqs:4:10 | accept -> reject | accept -> reject | accept -> crash:-6 |
| r2 | equalities/a08-assoc-generic.hylo | reqs:5:120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/a08-assoc-generic.hylo | reqs:5:210 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/a09-conf-via-eq.hylo | unused-param:4 | accept -> reject | not run | not run |
| r2 | equalities/absinst-ok.hylo | reqs:3:10 | accept -> reject | accept -> reject | accept -> timeout |
| r4 | equalities/absinst-ok.hylo | taut-assoc:3:1:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/absleak-0.hylo | taut-assoc:4:1:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-1.hylo | reqs:3:120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-1.hylo | reqs:3:210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-2.hylo | reqs:3:04213 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-2.hylo | reqs:3:12340 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-2.hylo | reqs:3:43210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-3.hylo | reqs:3:1234560 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-3.hylo | reqs:3:1235406 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-3.hylo | reqs:3:6543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-4.hylo | reqs:3:123456780 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-4.hylo | reqs:3:304682157 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-4.hylo | reqs:3:876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-5.hylo | reqs:3:109876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-5.hylo | reqs:3:123456789100 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-5.hylo | reqs:3:291054017368 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-6.hylo | reqs:3:1211109876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-6.hylo | reqs:3:1234567891011120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-6.hylo | reqs:3:9612832751141010 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-8.hylo | reqs:3:123456789101112131415160 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-8.hylo | reqs:3:161514131211109876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/assoceq-8.hylo | reqs:3:166871412152413119051031 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/ate-f1.hylo | taut-assoc:3:2:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/ate.hylo | reqs:7:3210 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/cong-0.hylo | taut-assoc:3:2:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/cong-1.hylo | reqs:3:120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/cong-1.hylo | reqs:3:210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/cong-2.hylo | reqs:3:120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/cong-2.hylo | reqs:3:210 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/decomp-1.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r7 | equalities/e01-orient-amb.hylo | dup-sym:2:3 | accept -> reject | accept -> reject | accept -> reject |
| r7 | equalities/e01-orient-amb.hylo | sym:2:2 | accept -> reject | accept -> reject | accept -> reject |
| r7 | equalities/e01-orient-amb.hylo | sym:2:3 | accept -> reject | accept -> reject | accept -> reject |
| r7 | equalities/e01b-both-direct.hylo | sym:2:2 | reject -> accept | reject -> accept | reject -> accept |
| r7 | equalities/e01b-both-direct.hylo | sym:2:3 | reject -> accept | reject -> accept | reject -> accept |
| r4 | equalities/e02-penalty.hylo | unused-param:3 | accept -> reject | not run | not run |
| r4 | equalities/e06-elab-change.hylo | taut-param:3:0:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/e09-trait-self-assoc.hylo | reqs:5:120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/e09-trait-self-assoc.hylo | reqs:5:210 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/eq-regress-judge-e06-elab-change.hylo | taut-param:3:0:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/eq-regress-judge-o2-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/eq-regress-judge-o2-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/eq-regress-judge-o2b-call-infer.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | equalities/eq-regress-judge-o2d-order.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/eq-regress-judge-o2d-order.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x01-ext-arg-member.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x01-ext-arg-member.hylo | intro-all-top:1 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x01-ext-arg-member.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x03-ext-nested-struct.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x06-nested-ext-no-alias.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eq-regress-judge-x10b-ext-where-assoc.hylo | reqs:6:10 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eq-regress-judge-x10b-ext-where-assoc.hylo | reqs:9:10 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/eq-regress-judge-x10b-ext-where-assoc.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eq-unsound-v-abs-7.hylo | reqs:3:210 | accept -> reject | accept -> reject | accept -> timeout |
| r2 | equalities/eqbug-5.hylo | reqs:5:034152 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqbug-5.hylo | reqs:5:123450 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqbug-5.hylo | reqs:5:543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-2.hylo | reqs:3:04213 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-2.hylo | reqs:3:12340 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-2.hylo | reqs:3:43210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-3.hylo | reqs:3:1234560 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-3.hylo | reqs:3:1235406 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-3.hylo | reqs:3:6543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-4.hylo | reqs:3:123456780 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-4.hylo | reqs:3:304682157 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-4.hylo | reqs:3:876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-5.hylo | reqs:3:109876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-5.hylo | reqs:3:123456789100 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-5.hylo | reqs:3:291054017368 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-6.hylo | reqs:3:1211109876543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-6.hylo | reqs:3:1234567891011120 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/eqchain-fix-assoceq-6.hylo | reqs:3:9612832751141010 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/extwhere-3.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | equalities/extwhere-3.hylo | unused-param:6 | accept -> reject | not run | not run |
| r4 | equalities/mirror-0.hylo | taut-assoc:4:2:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o1-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o1-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o2-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o2-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o2b-call-infer.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | equalities/o2d-order.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o2d-order.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o3-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o3-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o4-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o4-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/o5-open-chain.hylo | unused-param:3 | accept -> reject | not run | not run |
| r5 | equalities/o5-open-chain.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/open-1.hylo | unused-param:0 | accept -> reject | not run | not run |
| r4 | equalities/open-2.hylo | unused-param:0 | accept -> reject | not run | not run |
| r4 | equalities/open-3.hylo | unused-param:2 | accept -> reject | not run | not run |
| r4 | equalities/open-4.hylo | unused-param:0 | accept -> reject | not run | not run |
| r4 | equalities/openchain-4.hylo | unused-param:0 | accept -> reject | not run | not run |
| r4 | equalities/openchain-5.hylo | unused-param:0 | accept -> reject | not run | not run |
| r7 | equalities/pen-ref-2.hylo | dup-sym:6:0 | reject -> accept | reject -> accept | reject -> accept |
| r7 | equalities/pen-ref-2.hylo | sym:6:0 | reject -> accept | reject -> accept | reject -> accept |
| r4 | equalities/v-abs-1.hylo | taut-assoc:3:1:first | accept -> reject | accept -> reject | reject -> reject |
| r4 | equalities/v-abs-2.hylo | taut-assoc:3:1:first | accept -> reject | accept -> reject | accept -> reject |
| r4 | equalities/v-abs-3.hylo | taut-assoc:3:1:first | accept -> reject | accept -> reject | reject -> reject |
| r2 | equalities/v-abs-7.hylo | reqs:3:210 | accept -> reject | accept -> reject | accept -> timeout |
| r2 | equalities/v-abs-9.hylo | reqs:3:021 | reject -> accept | reject -> accept | reject -> accept |
| r2 | equalities/v-chain3-assoc.hylo | reqs:3:1234560 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/v-chain3-assoc.hylo | reqs:3:2614035 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/v-chain3-assoc.hylo | reqs:3:6543210 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/v-congr-5.hylo | reqs:3:3210 | accept -> reject | accept -> reject | accept -> timeout |
| r4 | equalities/v-congr-6.hylo | taut-assoc:3:2:first | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/v-def-4.hylo | reqs:8:10 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x01-ext-arg-member.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/x01-ext-arg-member.hylo | intro-all-top:1 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x01-ext-arg-member.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/x02-ext-nested.hylo | intro-all-top:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/x03-ext-nested-struct.hylo | intro-all-top:0 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x05-alias-ext.hylo | intro-all-top:0 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x05-alias-ext.hylo | intro-all:0 | accept -> reject | accept -> reject | accept -> reject |
| r5 | equalities/x06-nested-ext-no-alias.hylo | intro-all-top:0 | accept -> reject | accept -> reject | not run |
| r4 | equalities/x07-given-arg-member.hylo | taut-assoc:8:1:first | accept -> reject | accept -> reject | not run |
| r4 | equalities/x07-given-arg-member.hylo | unused-param:8 | accept -> reject | not run | not run |
| r5 | equalities/x07-given-arg-member.hylo | intro-all-top:0 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x07-given-arg-member.hylo | intro-all-top:1 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x07-given-arg-member.hylo | intro-generic:0 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x08-ext-arg-member-reordered.hylo | intro-all-top:0 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x08-ext-arg-member-reordered.hylo | intro-all-top:1 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x08-ext-arg-member-reordered.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r2 | equalities/x10b-ext-where-assoc.hylo | reqs:6:10 | accept -> reject | accept -> reject | not run |
| r2 | equalities/x10b-ext-where-assoc.hylo | reqs:9:10 | accept -> reject | accept -> reject | not run |
| r5 | equalities/x10b-ext-where-assoc.hylo | intro-generic:0 | accept -> reject | accept -> reject | accept -> reject |
| r4 | performance/occurs-dag-12.hylo | unused-param:6 | accept -> reject | not run | not run |
| r4 | performance/occurs-dag-16.hylo | unused-param:6 | accept -> reject | not run | not run |
| r4 | performance/occurs-dag-18.hylo | unused-param:6 | accept -> reject | not run | not run |
| r4 | performance/occurs-dag-8.hylo | unused-param:5 | accept -> reject | not run | not run |
| r4 | performance/open-pos-1.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-pos-chain-2.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-pos-chain-3.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-pos-chain-4.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-wide-1.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-wide-2.hylo | unused-param:1 | accept -> reject | not run | not run |
| r4 | performance/open-wide-3.hylo | unused-param:1 | accept -> reject | not run | not run |
| r2 | performance/open-wide-4.hylo | reqs-dep:1:76543210 | accept -> reject | accept -> reject | timeout -> timeout |
| r2 | performance/open-wide-4.hylo | reqs:1:76543210 | accept -> reject | accept -> reject | timeout -> timeout |
| r4 | performance/open-wide-4.hylo | taut-param:1:0:last | accept -> reject | accept -> reject | timeout -> timeout |
| r4 | performance/open-wide-4.hylo | taut-param:1:2:last | accept -> reject | accept -> reject | timeout -> timeout |
| r4 | performance/open-wide-4.hylo | taut-param:1:3:last | accept -> reject | accept -> reject | timeout -> crash:-6 |
| r4 | performance/open-wide-4.hylo | unused-param:1 | accept -> reject | not run | not run |
| r7 | performance/open-wide-4.hylo | dup-sym:1:3 | accept -> reject | accept -> reject | timeout -> timeout |
| r7 | performance/open-wide-4.hylo | dup-sym:1:5 | accept -> reject | accept -> reject | timeout -> timeout |
| r7 | performance/open-wide-4.hylo | dup:1:3 | accept -> reject | accept -> reject | timeout -> timeout |
| r5 | unsimplified-projections/t14-generic-conf-call.hylo | intro-generic:0 | accept -> reject | accept -> reject | not run |
| r2 | unsimplified-projections/t4-generic-caller.hylo | reqs:4:10 | accept -> reject | accept -> reject | not run |
| r2 | unsimplified-projections/t4-generic-caller.hylo | reqs:5:10 | accept -> reject | accept -> reject | not run |
| r2 | unsimplified-projections/v5-generic.hylo | reqs:7:10 | accept -> reject | accept -> reject | not run |
| r2 | unsimplified-projections/v5-generic.hylo | reqs:8:10 | accept -> reject | accept -> reject | not run |
| r2 | unsimplified-projections/v6-refl.hylo | reqs:7:10 | accept -> reject | accept -> reject | not run |
| r4 | unsimplified-projections/v6-refl.hylo | taut-assoc:7:1:first | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/chain3.hylo | unused-param:4 | accept -> reject | not run | not run |
| r5 | research/workloads/chain3.hylo | intro-generic:0 | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/chain8.hylo | taut-app:4:1:last | accept -> reject | accept -> reject | accept -> timeout |
| r4 | research/workloads/chain8.hylo | taut-app:5:4:last | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/chain8.hylo | taut-ground:3:0:last | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/chain8.hylo | taut-ground:5:8:last | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/chain8.hylo | taut-param:4:0:last | accept -> reject | accept -> reject | accept -> timeout |
| r4 | research/workloads/chain8.hylo | unused-param:4 | accept -> reject | not run | not run |
| r5 | research/workloads/chain8.hylo | intro-generic:0 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-2.hylo | reqs:3:04213 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-2.hylo | reqs:3:12340 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-2.hylo | reqs:3:43210 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-3.hylo | reqs:3:1234560 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-3.hylo | reqs:3:1235406 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-3.hylo | reqs:3:6543210 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-5.hylo | reqs:3:109876543210 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-5.hylo | reqs:3:123456789100 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-5.hylo | reqs:3:291054017368 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-8.hylo | reqs:3:123456789101112131415160 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-8.hylo | reqs:3:161514131211109876543210 | accept -> reject | accept -> reject | not run |
| r2 | research/workloads/round3/assoceq-8.hylo | reqs:3:166871412152413119051031 | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/round3/nestwide-2.hylo | unused-param:7 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/nestwide-3.hylo | unused-param:10 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/nestwide-5.hylo | unused-param:16 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/nestwide-8.hylo | unused-param:25 | accept -> reject | not run | not run |
| r2 | research/workloads/round3/orig-assoc-eq.hylo | reqs:7:3210 | accept -> reject | accept -> reject | not run |
| r4 | research/workloads/round3/orig-nested-1.hylo | unused-param:4 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/refine-2.hylo | unused-param:3 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/refine-3.hylo | unused-param:4 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/refine-5.hylo | unused-param:6 | accept -> reject | not run | not run |
| r4 | research/workloads/round3/refine-8.hylo | unused-param:9 | accept -> reject | not run | not run |

Under FIX (only the programs with a FULL violation were run): 396 variants, 308 verdict changes in 137 programs.
Under base (only the programs with a FULL violation were run): 172 variants, 160 verdict changes in 103 programs.
