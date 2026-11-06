# Regression sweep: every program of both adversarial reviews, final configuration

Binary eq7-3bbd2b60cb89, 30 s timeout. FIX = occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget; FULL = FIX + symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo. Raw rows: regress-final.jsonl.

520 programs.

| outcome | baseline | FIX | FULL |
|---|---|---|---|
| accept | 233 | 250 | 252 |
| reject | 224 | 269 | 267 |
| timeout | 42 | 1 | 1 |
| OOM | 0 | 0 | 0 |
| crash | 21 | 0 | 0 |

## Programs on which the configurations differ

| program | baseline | FIX | FULL | first FIX/FULL error |
|---|---|---|---|---|
| review/cyclecut-cause/amb_e2first.hylo | accept | reject(2) | reject(2) | expression does not denote a type |
| review/cyclecut-cause/n01_noext_member.hylo | reject(1) | accept | accept |  |
| review/cyclecut-cause/n05_givenonly.hylo | reject(2) | accept | accept |  |
| review/cyclecut-cause/n05_nogiven.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/amb3.hylo | accept | reject(1) | reject(1) | circular extension: the extendee of this extension depends on a lookup of 'Me', which this extension may affec |
| review/cyclecut-fix/casc1.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/casc2.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/g1.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/g2.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/g4.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/perf_g1.hylo | reject(2) | accept | accept |  |
| review/cyclecut-fix/perf_g16.hylo | reject(17) | accept | accept |  |
| review/cyclecut-fix/perf_g4.hylo | reject(5) | accept | accept |  |
| review/eqchain-fix/assocneg-3.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(T3::P).X' to parameter '(T0::P).X' |
| review/eqchain-fix/assocneg-4.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(T4::P).X' to parameter '(T0::P).X' |
| review/eqchain-fix/assocneg-5.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(T5::P).X' to parameter '(T0::P).X' |
| review/eqchain-fix/assocneg-6.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(T6::P).X' to parameter '(T0::P).X' |
| review/eqchain-fix/assocneg-8.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(T8::P).X' to parameter '(T0::P).X' |
| review/eqchain-fix/eqbug1-plain.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| review/eqchain-fix/eqbug1-struct.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| review/eqsubst-cause/c01-single-eq-call.hylo | accept | reject(1) | reject(1) | no coercion from '(D ~ V) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c02-no-eq-call.hylo | timeout | reject(1) | reject(1) | no coercion from '(D ~ V) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c03-single-eq-given.hylo | accept | reject(1) | reject(1) | no coercion from 'P<D> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c04-single-assoc-call.hylo | accept | reject(1) | reject(1) | no coercion from '((D::P).X ~ (A::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c05-single-eq-both-unrelated.hylo | timeout | reject(1) | reject(1) | no coercion from '(D ~ E) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c06-single-eq-struct.hylo | accept | reject(1) | reject(1) | no coercion from '(Q ~ S) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-cause/c07-single-assoc-arg.hylo | accept | reject(1) | reject(1) | no coercion from '((D::P).X ~ (A::P).X) ==> [Void](let (D::P).X) let -> (A::P).X' to '[Void](let (D::P).X) let |
| review/eqsubst-cause/v02-params.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'D' to parameter 'A' |
| review/eqsubst-cause/v03-box.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'Box<(D::P).X>' to parameter 'Box<(A::P).X>' |
| review/eqsubst-cause/v04-boxside.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'D' to parameter 'A' |
| review/eqsubst-fix/n-nested-1.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'Box<(D::P).X>' to parameter 'Box<(A::P).X>' |
| review/eqsubst-fix/n-params-1.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'D' to parameter 'A' |
| review/eqsubst-fix/n-params-2.hylo | accept | reject(1) | reject(1) | no coercion from '(A ~ D) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-fix/n-params-3.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'Box<D>' to parameter 'Box<A>' |
| review/eqsubst-fix/n-three-1.hylo | accept | reject(1) | reject(1) | cannot pass value of type '(F::P).X' to parameter '(A::P).X' |
| review/eqsubst-fix/n-tuple-1.hylo | timeout | reject(1) | reject(1) | cannot pass value of type '{(D::P).X, (B::P).X}' to parameter '{(A::P).X, (A::P).X}' |
| review/eqsubst-fix/v-abs-1.hylo | reject(1) | accept | accept |  |
| review/eqsubst-fix/v-abs-3.hylo | reject(1) | accept | accept |  |
| review/eqsubst-fix/v-abs-4.hylo | reject(1) | accept | accept |  |
| review/eqsubst-fix/v-congr-1.hylo | timeout | reject(1) | reject(1) | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/eqsubst-fix/v-def-3.hylo | timeout | reject(1) | reject(1) | no coercion from '((T::P).X ~ Bool) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/occurs-cause/variant-swapped.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/occurs-fix/b10-arrow-let.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter '{[Void](let #!) let -> B, #!}' |
| review/occurs-fix/b11-bundle-tuple.hylo | crash(-11) | reject(2) | reject(2) | no coercion from 'B' to '{T, B}' |
| review/occurs-fix/e2-env-capture-ctl.hylo | crash(-11) | reject(2) | reject(2) | cannot pass value of type '#!' to parameter '[Void]() let -> #!' |
| review/occurs-fix/n1-nested.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/occurs-fix/n2-nested2.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/occurs-fix/s2-tuple.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter '{#!, #!}' |
| review/occurs-fix/s3-generic.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter 'S<#!>' |
| review/occurs-fix/s4-check.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type 'S<#!>' to parameter 'S<S<#!>>' |
| review/occurs-fix/v1.hylo | crash(-11) | reject(2) | reject(2) | cannot pass value of type '#!' to parameter 'S<#!>' |
| review/occurs-fix/v2.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter 'S<#!>' |
| review/occurs-fix/v3.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type 'S<#!>' to parameter '#!' |
| review/occurs-fix/v4.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter 'S<S<#!>>' |
| review/reqdep-cause/min.hylo | timeout | reject(1) | reject(1) | no coercion from '(P<A>, ((A::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/reqdep-fix/t1.hylo | timeout | reject(1) | reject(1) | no coercion from '(P<A>, ((A::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review/reqdep-fix/t8-cond-call.hylo | timeout | reject(1) | reject(1) | no coercion from '(P<Box<B>>, ((Box<B>::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/crash-paths-judge/n1-nested-occurs.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/crash-paths/a1-arrow-env-cycle.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '[#!](let Void) let -> Void' to parameter '#!' |
| review2/crash-paths/a1b-arrow-input-cycle.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '[Void](let #!) let -> Void' to parameter '#!' |
| review2/crash-paths/a3-arrow-env-eq.hylo | timeout | reject(1) | reject(1) | no coercion from '<X, Y> (X ~ Y) ==> [Void](let X, let Y) let -> Void' to '[Void](let [E](let Void) let -> Voi |
| review2/crash-paths/b1-bundle-cycle.hylo | crash(-11) | reject(2) | reject(2) | cannot pass value of type '#!' to parameter '[auto Box<#!>](auto #!) auto -> Void { let, inout }' |
| review2/crash-paths/b1c-method-cycle-ctrl.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter '[let Box<#!>](let #!) let -> Void' |
| review2/crash-paths/b1d-method-env-cycle.hylo | crash(-11) | reject(1) | reject(1) | cannot pass value of type '#!' to parameter '[let Box<#!>]() let -> Void' |
| review2/crash-paths/c2-eq-in-given.hylo | timeout | reject(2) | reject(2) | no coercion from '(A ~ B) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/crash-paths/o2-toplevel-occurs.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/crash-paths/o4-toplevel-occurs-full.hylo | crash(-11) | reject(1) | reject(1) | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/crash-paths/p1-deep-100.hylo | reject(1) | accept | accept |  |
| review2/crash-paths/p1-deep-25.hylo | reject(1) | accept | accept |  |
| review2/crash-paths/p1-deep-50.hylo | reject(1) | accept | accept |  |
| review2/crash-paths/p2-alias-deep.hylo | reject(1) | accept | accept |  |
| review2/crash-paths/p3-alias-deep256.hylo | reject(1) | accept | accept |  |
| review2/crash-paths/q1-open-eq.hylo | accept | reject(1) | reject(1) | cannot pass value of type 'A' to parameter 'D' |
| review2/crash-paths/q2-open-eq-amb.hylo | reject(2) | accept | accept |  |
| review2/crash-paths/r2-bundle-eq-neg.hylo | timeout | reject(2) | reject(2) | no coercion from 'Void' to '{T, Void}' |
| review2/crash-paths/r3-arrow-eq.hylo | timeout | reject(2) | reject(2) | no coercion from '([Void](x: let A) let -> Void ~ [Void](y: let B) let -> Void) ==> [Void]() let -> Void' to ' |
| review2/eq-regress-judge/p01-cc-big.hylo | timeout | accept | accept |  |
| review2/eq-regress-judge/p02-cc-big.hylo | timeout | accept | accept |  |
| review2/eq-regress/a05-quantified.hylo | reject(1) | accept | accept |  |
| review2/eq-regress/a06-tuple-arrow.hylo | reject(1) | accept | accept |  |
| review2/eq-regress/e08-shapes.hylo | timeout | accept | accept |  |
| review2/eq-regress/p01-cc-big.hylo | timeout | accept | accept |  |
| review2/eq-regress/p02-cc-big.hylo | timeout | accept | accept |  |
| review2/eq-regress/x10-ext-where-assoc.hylo | timeout | reject(1) | reject(1) | type 'Box<Bag>' has no member 'first' |
| review2/eq-unsound/abs-trans-2.hylo | accept | reject(1) | reject(1) | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/eq-unsound/abs-trans-3.hylo | accept | reject(1) | reject(1) | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let |
| review2/eq-unsound/abs-trans-4.hylo | timeout | reject(1) | reject(1) | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let |
| review2/eq-unsound/abs-trans-5.hylo | timeout | reject(1) | reject(1) | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let |
| review2/eq-unsound/absinst-0.hylo | accept | reject(1) | reject(1) | no coercion from '((V::P).X ~ Bool) ==> [let V]() let -> Void' to '[let V]() let -> Void' |
| review2/eq-unsound/absinst-1.hylo | accept | reject(1) | reject(1) | no coercion from '((V::P).X ~ Bool) ==> [let V]() let -> Void' to '[let V]() let -> Void' |
| review2/eq-unsound/absleak-3.hylo | timeout | reject(1) | reject(1) | no coercion from '(T::P).X' to '(U::P).X' |
| review2/eq-unsound/absleak-4.hylo | timeout | reject(1) | reject(1) | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/eq-unsound/nested-eq.hylo | timeout | reject(2) | reject(2) | expected 'is' |
| review2/eq-unsound/pen-ref-3.hylo | reject(2) | accept | accept |  |
| review2/eq-unsound/pend-1.hylo | timeout | reject(1) | reject(1) | no coercion from '<T> T ==> [Void](let Metatype<T>) let -> yield T' to '[Void](let Metatype<P<C>>) let -> yiel |
| review2/eq-unsound/pend-2.hylo | timeout | reject(1) | reject(1) | no coercion from '<T> T ==> [Void](let Metatype<T>) let -> yield T' to '[Void](let Metatype<P<C>>) let -> yiel |
| review2/eq-unsound/perf-alias-7.hylo | reject(1) | accept | accept |  |
| review2/eq-unsound/perf-alias.hylo | reject(1) | accept | accept |  |
| review2/eq-unsound/perf-deep-100.hylo | reject(1) | accept | accept |  |
| review2/eq-unsound/perf-deep-200.hylo | reject(1) | accept | accept |  |
| review2/eq-unsound/perf-deep-50.hylo | reject(1) | accept | accept |  |
| review2/ext-order-judge/gx1_swap.hylo | accept | reject(1) | reject(1) | circular given: the type of this given depends on an implicit resolution of 'P<A>' that it may satisfy |
| review2/ext-order-judge/r2_bare.hylo | accept | reject(1) | reject(1) | circular extension: the extendee of this extension depends on a lookup of 'Element', which this extension may  |
| review2/ext-order/amb3.hylo | accept | reject(1) | reject(1) | circular extension: the extendee of this extension depends on a lookup of 'Me', which this extension may affec |
| review2/ext-order/amb_e2first.hylo | accept | reject(2) | reject(2) | expression does not denote a type |
| review2/ext-order/ge1.hylo | accept | reject(1) | reject(1) | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satisfy |
| review2/ext-order/gx1.hylo | accept | reject(1) | reject(1) | circular given: the type of this given depends on an implicit resolution of 'P<A>' that it may satisfy |
| review2/ext-order/gz1.hylo | accept | reject(1) | reject(1) | circular given: the type of this given depends on an implicit resolution of 'P<T>' that it may satisfy |
| review2/ext-order/names/casc1.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/casc2.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/g1.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/g2.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/g4.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/n01_alias_cycle.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/n03_reverse_poison.hylo | accept | reject(3) | reject(3) | type 'Inner' has no static member 'Foo' |
| review2/ext-order/names/n04_reverse_poison_min.hylo | accept | reject(3) | reject(3) | type 'Inner' has no static member 'Foo' |
| review2/ext-order/names/n05_spurious_cycle_conformance.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/n11_poison_via_summon.hylo | accept | reject(3) | reject(3) | type 'Inner' has no static member 'Foo' |
| review2/ext-order/names/n12_poison_via_summon_noearly.hylo | accept | reject(3) | reject(3) | type 'Inner' has no static member 'Foo' |
| review2/ext-order/names/t01_ext_order.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/t03_names_worse.hylo | accept | reject(3) | reject(3) | type 'B' has no static member 'V' |
| review2/ext-order/names/verify-names-1/v3_nouse.hylo | accept | reject(2) | reject(2) | type 'Inner' has no static member 'Foo' |
| review2/ext-order/names/verify-names-2/v06_member_of_ext_alias.hylo | reject(2) | accept | accept |  |
| review2/ext-order/names/verify-names-2/v08_two_aliases.hylo | reject(2) | accept | accept |  |
| review2/ext-order/pc1_selfapply_nouse.hylo | accept | reject(1) | reject(1) | circular extension: the extendee of this extension depends on a lookup of 'Foo', which this extension may affe |
| review2/perf/cc-chain-k16-w10-m1.hylo | timeout | accept | accept |  |
| review2/perf/cc-chain-k16-w10-m8.hylo | timeout | accept | accept |  |
| review2/perf/cc-chain-k24-w10-m1.hylo | timeout | accept | accept |  |
| review2/perf/cc-deep-40-m10.hylo | timeout | accept | accept |  |
| review2/perf/cc-deep-40-m30.hylo | timeout | accept | accept |  |
| review2/perf/cc-deep-60-m30.hylo | timeout | accept | accept |  |
| review2/perf/cc-goals-m10.hylo | reject(10) | accept | accept |  |
| review2/perf/cc-goals-m20.hylo | reject(20) | accept | accept |  |
| review2/perf/cc-goals-m30.hylo | reject(30) | accept | accept |  |
| review2/perf/cc-goals-m36.hylo | reject(36) | accept | accept |  |
| review2/perf/div-eq-b3-0.hylo | timeout | reject(3) | reject(1) | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type argu |
| review2/perf/div-eq-b3-1.hylo | timeout | reject(2) | reject(1) | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| review2/perf/div-eq-ovl-b3-0.hylo | timeout | reject(2) | accept | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type argu |
| review2/perf/div-eq-ovl-b3-1.hylo | timeout | reject(1) | accept | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type argu |
| review2/perf/div-trunc-b3.hylo | timeout | reject(3) | reject(3) | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type argu |
| review2/perf/div-trunc-b4.hylo | timeout | reject(3) | reject(3) | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type argu |
| review2/perf/extchain-16.hylo | reject(15) | accept | accept |  |
| review2/perf/extchain-24.hylo | reject(23) | accept | accept |  |
| review2/perf/extchain-8.hylo | reject(7) | accept | accept |  |
| review2/perf/open-neg-0.hylo | timeout | reject(1) | reject(1) | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| review2/perf/open-neg-1.hylo | timeout | reject(1) | reject(1) | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| review2/perf/open-neg-2.hylo | timeout | reject(1) | reject(1) | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| review2/perf/open-wide-4.hylo | timeout | accept | accept |  |
| review2/perf/pending-var-3.hylo | reject(1) | accept | accept |  |

## FIX/FULL runs over 2 s

- review2/perf/div-eq-b3-0.hylo FIX: 3387 ms
- review2/perf/div-eq-b3-1.hylo FIX: 3253 ms
- review2/perf/div-eq-ovl-b3-0.hylo FIX: 3281 ms
- review2/perf/div-eq-ovl-b3-1.hylo FIX: 3385 ms
- review2/perf/div-trunc-b3.hylo FIX: 3392 ms
- review2/perf/div-trunc-b3.hylo FULL: 5980 ms
- review2/perf/div-trunc-b4.hylo FIX: 5739 ms
- review2/perf/div-trunc-b4.hylo FULL: 5241 ms
- review2/perf/occurs-dag-16.hylo FIX: 3032 ms
- review2/perf/occurs-dag-18.hylo FIX: 11927 ms
- review2/perf/ovl-ret-8.hylo FIX: 2462 ms
- review2/perf/ovl-ret-9.hylo FIX: 10380 ms
- review2/perf/ovl-ret-9.hylo FULL: 8960 ms
