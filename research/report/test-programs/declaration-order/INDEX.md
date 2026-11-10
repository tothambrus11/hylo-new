# Test programs: declaration order

Verdicts of the existing implementation, of the techniques with the fixes for problems 1 to 4 only, and of the recommended configuration of the report, with a 30 s limit (recommended configuration: 60 s).

| Program | Existing | Fixes 1–4 | Recommended | First error (recommended) |
|---|---|---|---|---|
| `amb_direct.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `amb_e1first.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `amb_e2first.hylo` | accepted | rejected | rejected | expression does not denote a type |
| `amb_e2first_use.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `amb_viaalias_direct.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `n01_noext_member.hylo` | rejected | accepted | accepted |  |
| `n05_givenonly.hylo` | rejected | accepted | accepted |  |
| `n05_nogiven.hylo` | rejected | accepted | accepted |  |
| `v2_noearly.hylo` | rejected | rejected | accepted |  |
| `amb0.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `amb1.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `amb2.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `amb3.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `amb4.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `amb5.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `casc1.hylo` | rejected | accepted | accepted |  |
| `casc2.hylo` | rejected | accepted | accepted |  |
| `casc3.hylo` | accepted | accepted | accepted |  |
| `g1.hylo` | rejected | accepted | accepted |  |
| `g2.hylo` | rejected | accepted | accepted |  |
| `g3.hylo` | accepted | accepted | accepted |  |
| `g4.hylo` | rejected | accepted | accepted |  |
| `perf_g1.hylo` | rejected | accepted | accepted |  |
| `perf_g16.hylo` | rejected | accepted | accepted |  |
| `perf_g4.hylo` | rejected | accepted | accepted |  |
| `al1.hylo` | rejected | rejected | accepted |  |
| `al2.hylo` | accepted | accepted | accepted |  |
| `al3.hylo` | rejected | rejected | accepted |  |
| `ext-order-amb0.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb1.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb2.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb3.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `ext-order-amb4.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb5.hylo` | rejected | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb_direct.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `ext-order-amb_e1first.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `ext-order-amb_e2first.hylo` | accepted | rejected | rejected | expression does not denote a type |
| `ext-order-amb_e2first_use.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `ext-order-amb_viaalias_direct.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `g_dup0.hylo` | rejected | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `g_dup0_nouse.hylo` | accepted | accepted | accepted |  |
| `g_dup1.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `g_dup2.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `g_dup3.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `ge1.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `ge2.hylo` | rejected | rejected | rejected | ambiguous use of 'Y' |
| `ge3.hylo` | rejected | rejected | rejected | ambiguous use of 'Y' |
| `gx1.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `gx1_ctrl.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `gx1_use.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `gz0.hylo` | rejected | rejected | rejected | ambiguous use of 'Y' |
| `gz1.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `gz1b.hylo` | rejected | rejected | rejected | cannot pass value of type 'U' to parameter '#!' |
| `gz1c.hylo` | rejected | rejected | rejected | cannot pass value of type 'U' to parameter '#!' |
| `gz2.hylo` | rejected | rejected | rejected | ambiguous use of 'Y' |
| `gz3.hylo` | rejected | rejected | rejected | ambiguous use of 'Y' |
| `gz4.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `pc1_selfapply.hylo` | rejected | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `pc1_selfapply_nouse.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `r1_alias.hylo` | rejected | rejected | rejected | type 'B' has no static member 'Foo' |
| `r1_nested.hylo` | accepted | accepted | accepted |  |
| `r1_selfname.hylo` | accepted | accepted | accepted |  |
| `r1_selfname_fun.hylo` | accepted | accepted | accepted |  |
| `r2_where_assoc.hylo` | accepted | accepted | accepted |  |
| `r2_where_assoc_ctrl.hylo` | accepted | accepted | accepted |  |
| `r2_where_assoc_fun.hylo` | accepted | accepted | accepted |  |
| `r2_where_trait.hylo` | rejected | rejected | rejected | expected '{' |
| `red1.hylo` | accepted | accepted | accepted |  |
| `red2.hylo` | accepted | accepted | accepted |  |
| `red3.hylo` | rejected | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `gvalid.hylo` | accepted | accepted | accepted |  |
| `gx1_swap.hylo` | accepted | rejected | rejected | the type of this declaration depends on a name lookup or an implicit resolution that it changes; no stable interpretation was found |
| `r2_bare.hylo` | accepted | rejected | accepted |  |
| `n04-order-a.hylo` | accepted | rejected | accepted |  |
| `n04-order-b.hylo` | accepted | rejected | accepted |  |
| `v4-swapped.hylo` | rejected | rejected | accepted |  |
| `v4-use-first.hylo` | accepted | rejected | accepted |  |
| `names-casc1.hylo` | rejected | accepted | accepted |  |
| `names-casc2.hylo` | rejected | accepted | accepted |  |
| `names-casc3.hylo` | accepted | accepted | accepted |  |
| `names-g1.hylo` | rejected | accepted | accepted |  |
| `names-g2.hylo` | rejected | accepted | accepted |  |
| `names-g3.hylo` | accepted | accepted | accepted |  |
| `names-g4.hylo` | rejected | accepted | accepted |  |
| `names-n01_alias_cycle.hylo` | rejected | accepted | accepted |  |
| `names-n02_reverse_poison_noeffect.hylo` | accepted | rejected | accepted |  |
| `names-n03_reverse_poison.hylo` | accepted | rejected | accepted |  |
| `names-n04_reverse_poison_min.hylo` | accepted | rejected | accepted |  |
| `names-n05_spurious_cycle_conformance.hylo` | rejected | accepted | accepted |  |
| `names-n06_diag_ambiguous.hylo` | rejected | rejected | rejected | type 'A' has no member 'h' |
| `names-n07_bad_extendee.hylo` | rejected | rejected | rejected | undefined symbol 'Undefined' |
| `names-n08_conditional_ext.hylo` | rejected | rejected | rejected | type 'Box<J>' has no member 'onlyP' |
| `names-n09_kinds.hylo` | rejected | rejected | rejected | no candidate matches the argument list |
| `names-n10_trait_ext.hylo` | rejected | rejected | rejected | no implementation of associated type requirement 'X' |
| `names-n11_poison_via_summon.hylo` | accepted | rejected | accepted |  |
| `names-n12_poison_via_summon_noearly.hylo` | accepted | rejected | accepted |  |
| `names-n13_typevar_in_diag.hylo` | rejected | rejected | rejected | consecutive statements on the same line must be separated by ';' |
| `names-n14_typevar_in_diag2.hylo` | rejected | rejected | rejected | no coercion from '{#!, Bool}' to 'Int' |
| `names-n15_local_extension.hylo` | rejected | rejected | rejected | undefined symbol 'Nope' |
| `names-n16_cycle_via_where.hylo` | rejected | rejected | rejected | type 'Inner' has no member 'f' |
| `names-n17_alias_cycle_generic.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `names-n18_summon_cache_refinement.hylo` | rejected | rejected | rejected | no given instance of 'P<A>' in this scope |
| `names-n19_summon_cache_refinement_ctrl.hylo` | rejected | rejected | rejected | no given instance of 'P<A>' in this scope |
| `names-t01_ext_order.hylo` | rejected | accepted | accepted |  |
| `names-t02_names_worse.hylo` | rejected | rejected | accepted |  |
| `names-t03_names_worse.hylo` | accepted | rejected | accepted |  |
| `names-t04_init_ops_subscript.hylo` | rejected | rejected | rejected | no candidate matches the argument list |
| `names-t05_conf_in_ext.hylo` | rejected | rejected | rejected | unused value of type 'Int' |
| `names-t06_ambiguous_notfound.hylo` | rejected | rejected | rejected | type 'A' has no static member 'nope' |
| `names-t07_conditional_ext.hylo` | rejected | rejected | rejected | type 'G<Bool>' has no member 'onlyR' |
| `names-t08_local_ext.hylo` | accepted | accepted | accepted |  |
| `names-t09_cycle_extendee.hylo` | rejected | rejected | accepted |  |
| `names-t10_alias_extendee.hylo` | rejected | rejected | rejected | type 'S<Bool>' has no member 'only' |
| `names-t11_static_meta.hylo` | accepted | accepted | accepted |  |
| `names-t12_self_ext.hylo` | accepted | accepted | accepted |  |
| `names-verify-names-2-v01_ext_declares_foo.hylo` | rejected | rejected | accepted |  |
| `names-verify-names-2-v02_ext_before_alias.hylo` | accepted | accepted | accepted |  |
| `names-verify-names-2-v03_direct_control.hylo` | accepted | accepted | accepted |  |
| `names-verify-names-2-v04_use_before.hylo` | accepted | accepted | accepted |  |
| `names-verify-names-2-v05_true_cycle.hylo` | rejected | rejected | rejected | definition of 'X' refers to itself |
| `names-verify-names-2-v06_member_of_ext_alias.hylo` | rejected | accepted | accepted |  |
| `names-verify-names-2-v07_ext_of_alias_member.hylo` | accepted | accepted | accepted |  |
| `names-verify-names-2-v08_two_aliases.hylo` | rejected | accepted | accepted |  |
| `names-verify-names-1-v1_noearly.hylo` | accepted | rejected | accepted |  |
| `names-verify-names-1-v2_swapped.hylo` | rejected | rejected | accepted |  |
| `names-verify-names-1-v3_nouse.hylo` | accepted | rejected | accepted |  |
| `names-verify-names-1-v4_noC.hylo` | accepted | rejected | accepted |  |
| `names-verify-names-1-v5_early_other.hylo` | accepted | rejected | accepted |  |
| `names-verify-names-1-v6_summon_swapped.hylo` | rejected | rejected | accepted |  |
