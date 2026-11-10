# Test programs: declaration order

Verdicts of the existing implementation ("Old") and of the revised implementation with all techniques enabled ("New"), with a 30 s limit. Each difference is an ill-typed program that is now rejected, an abnormal termination or timeout that is now resolved, or a case discussed in the accompanying documents.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `amb_direct.hylo` | rejected | rejected | expression does not denote a type |
| `amb_e1first.hylo` | rejected | rejected | expression does not denote a type |
| `amb_e2first.hylo` | accepted | rejected | expression does not denote a type |
| `amb_e2first_use.hylo` | rejected | rejected | expression does not denote a type |
| `amb_viaalias_direct.hylo` | rejected | rejected | expression does not denote a type |
| `n01_noext_member.hylo` | rejected | accepted |  |
| `n05_givenonly.hylo` | rejected | accepted |  |
| `n05_nogiven.hylo` | rejected | accepted |  |
| `v2_noearly.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `amb0.hylo` | rejected | rejected | ambiguous use of 'Me' |
| `amb1.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `amb2.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `amb3.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Me', which this extension |
| `amb4.hylo` | rejected | rejected | ambiguous use of 'Me' |
| `amb5.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `casc1.hylo` | rejected | accepted |  |
| `casc2.hylo` | rejected | accepted |  |
| `casc3.hylo` | accepted | accepted |  |
| `g1.hylo` | rejected | accepted |  |
| `g2.hylo` | rejected | accepted |  |
| `g3.hylo` | accepted | accepted |  |
| `g4.hylo` | rejected | accepted |  |
| `perf_g1.hylo` | rejected | accepted |  |
| `perf_g16.hylo` | rejected | accepted |  |
| `perf_g4.hylo` | rejected | accepted |  |
| `al1.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `al2.hylo` | accepted | accepted |  |
| `al3.hylo` | rejected | rejected | type 'X' has no static member 'Me' |
| `ext-order-amb0.hylo` | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb1.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `ext-order-amb2.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `ext-order-amb3.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Me', which this extension |
| `ext-order-amb4.hylo` | rejected | rejected | ambiguous use of 'Me' |
| `ext-order-amb5.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `ext-order-amb_direct.hylo` | rejected | rejected | expression does not denote a type |
| `ext-order-amb_e1first.hylo` | rejected | rejected | expression does not denote a type |
| `ext-order-amb_e2first.hylo` | accepted | rejected | expression does not denote a type |
| `ext-order-amb_e2first_use.hylo` | rejected | rejected | expression does not denote a type |
| `ext-order-amb_viaalias_direct.hylo` | rejected | rejected | expression does not denote a type |
| `g_dup0.hylo` | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `g_dup0_nouse.hylo` | accepted | accepted |  |
| `g_dup1.hylo` | rejected | rejected | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satis |
| `g_dup2.hylo` | rejected | rejected | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satis |
| `g_dup3.hylo` | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `ge1.hylo` | accepted | rejected | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satis |
| `ge2.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `ge3.hylo` | rejected | rejected | ambiguous use of 'Y' |
| `gx1.hylo` | accepted | rejected | circular given: the type of this given depends on an implicit resolution of 'P<A>' that it may satis |
| `gx1_ctrl.hylo` | rejected | rejected | expression does not denote a type |
| `gx1_use.hylo` | rejected | rejected | circular given: the type of this given depends on an implicit resolution of 'P<A>' that it may satis |
| `gz0.hylo` | rejected | rejected | ambiguous use of 'Y' |
| `gz1.hylo` | accepted | rejected | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satis |
| `gz1b.hylo` | rejected | rejected | ambiguous use of 'Y' |
| `gz1c.hylo` | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `gz2.hylo` | rejected | rejected | definition of 'Z' refers to itself |
| `gz3.hylo` | rejected | rejected | definition of 'Z' refers to itself |
| `gz4.hylo` | rejected | rejected | definition of 'Z' refers to itself |
| `pc1_selfapply.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `pc1_selfapply_nouse.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `r1_alias.hylo` | rejected | rejected | type 'B' has no static member 'Foo' |
| `r1_nested.hylo` | accepted | accepted |  |
| `r1_selfname.hylo` | accepted | accepted |  |
| `r1_selfname_fun.hylo` | accepted | accepted |  |
| `r2_where_assoc.hylo` | accepted | accepted |  |
| `r2_where_assoc_ctrl.hylo` | accepted | accepted |  |
| `r2_where_assoc_fun.hylo` | accepted | accepted |  |
| `r2_where_trait.hylo` | rejected | rejected | expected '{' |
| `red1.hylo` | accepted | accepted |  |
| `red2.hylo` | accepted | accepted |  |
| `red3.hylo` | rejected | rejected | no coercion from 'P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `gvalid.hylo` | accepted | accepted |  |
| `gx1_swap.hylo` | accepted | rejected | circular given: the type of this given depends on an implicit resolution of 'P<A>' that it may satis |
| `r2_bare.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Element', which this exte |
| `n04-order-a.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `n04-order-b.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `v4-swapped.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `v4-use-first.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-casc1.hylo` | rejected | accepted |  |
| `names-casc2.hylo` | rejected | accepted |  |
| `names-casc3.hylo` | accepted | accepted |  |
| `names-g1.hylo` | rejected | accepted |  |
| `names-g2.hylo` | rejected | accepted |  |
| `names-g3.hylo` | accepted | accepted |  |
| `names-g4.hylo` | rejected | accepted |  |
| `names-n01_alias_cycle.hylo` | rejected | accepted |  |
| `names-n02_reverse_poison_noeffect.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-n03_reverse_poison.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `names-n04_reverse_poison_min.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `names-n05_spurious_cycle_conformance.hylo` | rejected | accepted |  |
| `names-n06_diag_ambiguous.hylo` | rejected | rejected | type 'A' has no member 'h' |
| `names-n07_bad_extendee.hylo` | rejected | rejected | undefined symbol 'Undefined' |
| `names-n08_conditional_ext.hylo` | rejected | rejected | type 'Box<J>' has no member 'onlyP' |
| `names-n09_kinds.hylo` | rejected | rejected | no candidate matches the argument list |
| `names-n10_trait_ext.hylo` | rejected | rejected | no implementation of associated type requirement 'X' |
| `names-n11_poison_via_summon.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `names-n12_poison_via_summon_noearly.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `names-n13_typevar_in_diag.hylo` | rejected | rejected | consecutive statements on the same line must be separated by ';' |
| `names-n14_typevar_in_diag2.hylo` | rejected | rejected | no coercion from '{#!, Bool}' to 'Int' |
| `names-n15_local_extension.hylo` | rejected | rejected | undefined symbol 'Nope' |
| `names-n16_cycle_via_where.hylo` | rejected | rejected | type 'Inner' has no member 'f' |
| `names-n17_alias_cycle_generic.hylo` | rejected | rejected | expression does not denote a type |
| `names-n18_summon_cache_refinement.hylo` | rejected | rejected | no given instance of 'P<A>' in this scope |
| `names-n19_summon_cache_refinement_ctrl.hylo` | rejected | rejected | no given instance of 'P<A>' in this scope |
| `names-t01_ext_order.hylo` | rejected | accepted |  |
| `names-t02_names_worse.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'V', which this extension  |
| `names-t03_names_worse.hylo` | accepted | rejected | type 'B' has no static member 'V' |
| `names-t04_init_ops_subscript.hylo` | rejected | rejected | no candidate matches the argument list |
| `names-t05_conf_in_ext.hylo` | rejected | rejected | unused value of type 'Int' |
| `names-t06_ambiguous_notfound.hylo` | rejected | rejected | type 'A' has no static member 'nope' |
| `names-t07_conditional_ext.hylo` | rejected | rejected | type 'G<Bool>' has no member 'onlyR' |
| `names-t08_local_ext.hylo` | accepted | accepted |  |
| `names-t09_cycle_extendee.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Y', which this extension  |
| `names-t10_alias_extendee.hylo` | rejected | rejected | type 'S<Bool>' has no member 'only' |
| `names-t11_static_meta.hylo` | accepted | accepted |  |
| `names-t12_self_ext.hylo` | accepted | accepted |  |
| `names-verify-names-2-v01_ext_declares_foo.hylo` | rejected | rejected | type 'Int' has no member 'g' |
| `names-verify-names-2-v02_ext_before_alias.hylo` | accepted | accepted |  |
| `names-verify-names-2-v03_direct_control.hylo` | accepted | accepted |  |
| `names-verify-names-2-v04_use_before.hylo` | accepted | accepted |  |
| `names-verify-names-2-v05_true_cycle.hylo` | rejected | rejected | definition of 'X' refers to itself |
| `names-verify-names-2-v06_member_of_ext_alias.hylo` | rejected | accepted |  |
| `names-verify-names-2-v07_ext_of_alias_member.hylo` | accepted | accepted |  |
| `names-verify-names-2-v08_two_aliases.hylo` | rejected | accepted |  |
| `names-verify-names-1-v1_noearly.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-verify-names-1-v2_swapped.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-verify-names-1-v3_nouse.hylo` | accepted | rejected | type 'Inner' has no static member 'Foo' |
| `names-verify-names-1-v4_noC.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-verify-names-1-v5_early_other.hylo` | accepted | rejected | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extensio |
| `names-verify-names-1-v6_summon_swapped.hylo` | rejected | rejected | type 'Inner' has no static member 'Foo' |
