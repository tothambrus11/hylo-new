# Test programs: cycles and crashes

Verdicts of the existing implementation ("Old") and of the revised implementation with all techniques enabled ("New"), with a 30 s limit. Each difference is an ill-typed program that is now rejected, an abnormal termination or timeout that is now resolved, or a case discussed in the accompanying documents.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `variant-swapped.hylo` | crash | rejected | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `b1-arrow.hylo` | rejected | rejected | not enough context to infer a type |
| `b10-arrow-let.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '{[Void](let #!) let -> B, #!}' |
| `b11-bundle-tuple.hylo` | crash | rejected | no coercion from 'B' to '{T, B}' |
| `b2-bundle.hylo` | rejected | rejected | no coercion from 'B' to '{T, B}' |
| `b3-bundle-direct.hylo` | rejected | rejected | no coercion from 'B' to '{T, B}' |
| `b4-bundle-inst.hylo` | rejected | rejected | no coercion from 'B' to '{T, B}' |
| `b5-arrow-inst.hylo` | rejected | rejected | not enough context to infer a type |
| `b6-bundle-inst2.hylo` | rejected | rejected | no coercion from 'B' to '{T, B}' |
| `b7-bundle-selfapp.hylo` | rejected | rejected | not enough context to infer a type |
| `b8-arrow-selfapp.hylo` | rejected | rejected | not enough context to infer a type |
| `b9-bundle-let.hylo` | rejected | rejected | no coercion from 'B' to '{T, B}' |
| `c1-cycle-plus-coercion.hylo` | rejected | rejected | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c2-control.hylo` | rejected | rejected | not enough context to infer a type |
| `c3-accept-change.hylo` | rejected | rejected | no coercion from 'R<Z> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c4-control.hylo` | rejected | rejected | not enough context to infer a type |
| `c5-order1.hylo` | rejected | rejected | no coercion from 'R<Z> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c5-order2.hylo` | rejected | rejected | no coercion from 'R<Z> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `dag12.hylo` | rejected | rejected | no coercion from '<T> [Void](let T, let T) let -> Void' to '[Void](let {#!, #!}, let {#!, #!}) let - |
| `dag14.hylo` | rejected | rejected | no coercion from '<T> [Void](let T, let T) let -> Void' to '[Void](let {#!, #!}, let {#!, #!}) let - |
| `dag8.hylo` | rejected | rejected | no coercion from '<T> [Void](let T, let T) let -> Void' to '[Void](let {#!, #!}, let {#!, #!}) let - |
| `e1-env-capture.hylo` | rejected | rejected | no coercion from '<T> [Void](let T, let T) let -> Void' to '[Void](let [{#!}]() let -> Void, let [{# |
| `e2-env-capture-ctl.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '[Void]() let -> #!' |
| `e3-env-implicit.hylo` | accepted | accepted |  |
| `n1-nested.hylo` | crash | rejected | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `n2-nested2.hylo` | crash | rejected | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `s1-selfapp.hylo` | rejected | rejected | not enough context to infer a type |
| `s2-tuple.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '{#!, #!}' |
| `s3-generic.hylo` | crash | rejected | cannot pass value of type '#!' to parameter 'S<#!>' |
| `s4-check.hylo` | crash | rejected | cannot pass value of type 'S<#!>' to parameter 'S<S<#!>>' |
| `t1-assign.hylo` | rejected | rejected | not enough context to infer a type |
| `t2-assign-only.hylo` | rejected | rejected | not enough context to infer a type |
| `t3-assign-ctl.hylo` | rejected | rejected | no coercion from 'S<Void>' to 'Void' |
| `v1.hylo` | crash | rejected | cannot pass value of type '#!' to parameter 'S<#!>' |
| `v2.hylo` | crash | rejected | cannot pass value of type '#!' to parameter 'S<#!>' |
| `v3.hylo` | crash | rejected | cannot pass value of type 'S<#!>' to parameter '#!' |
| `v4.hylo` | crash | rejected | cannot pass value of type '#!' to parameter 'S<S<#!>>' |
| `v5.hylo` | rejected | rejected | not enough context to infer a type |
| `v6.hylo` | rejected | rejected | not enough context to infer a type |
| `v7.hylo` | rejected | rejected | not enough context to infer a type |
| `a1-arrow-env-cycle.hylo` | crash | rejected | cannot pass value of type '[#!](let Void) let -> Void' to parameter '#!' |
| `a1b-arrow-input-cycle.hylo` | crash | rejected | cannot pass value of type '[Void](let #!) let -> Void' to parameter '#!' |
| `a2-arrow-env-generic.hylo` | accepted | accepted |  |
| `a3-arrow-env-eq.hylo` | timeout | rejected | no coercion from '<X, Y> (X ~ Y) ==> [Void](let X, let Y) let -> Void' to '[Void](let [E](let Void)  |
| `a4-env-var-goal.hylo` | accepted | accepted |  |
| `a5-env-var-goal-ctrl.hylo` | accepted | accepted |  |
| `b1-bundle-cycle.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '[auto Box<#!>](auto #!) auto -> Void { let, inout }' |
| `b1c-method-cycle-ctrl.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '[let Box<#!>](let #!) let -> Void' |
| `b1d-method-env-cycle.hylo` | crash | rejected | cannot pass value of type '#!' to parameter '[let Box<#!>]() let -> Void' |
| `b2-bundle-cycle-free.hylo` | rejected | rejected | not enough context to infer a type |
| `c1-empty-where.hylo` | rejected | rejected | expected expression |
| `c2-eq-in-given.hylo` | timeout | rejected | no coercion from '(A ~ B) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `e1-sym-proof.hylo` | accepted | accepted |  |
| `e2-abs-qual-distinct-conf.hylo` | accepted | accepted |  |
| `e3-abs-qual-ctrl.hylo` | rejected | rejected | no coercion from '(U::P).X' to '(T::P).X' |
| `o1-value-ctx.hylo` | accepted | accepted |  |
| `o2-toplevel-occurs.hylo` | crash | rejected | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `o3-toplevel-occurs-ctrl.hylo` | rejected | rejected | no coercion from 'P<C<Void>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `o4-toplevel-occurs-full.hylo` | crash | rejected | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `o5-assign-occurs.hylo` | rejected | rejected | not enough context to infer a type |
| `o6-return-occurs.hylo` | rejected | rejected | not enough context to infer a type |
| `o7-assign-occurs-bound.hylo` | rejected | rejected | cannot pass value of type '#!' to parameter 'A' |
| `o8-assign-ctrl.hylo` | rejected | rejected | no coercion from 'Box<A>' to 'A' |
| `o9-assign-mk.hylo` | rejected | rejected | cannot pass value of type '#!' to parameter 'A' |
| `p1-deep-100.hylo` | rejected | accepted |  |
| `p1-deep-25.hylo` | rejected | accepted |  |
| `p1-deep-50.hylo` | rejected | accepted |  |
| `p2-alias-deep.hylo` | rejected | accepted |  |
| `p3-alias-deep256.hylo` | rejected | accepted |  |
| `q1-open-eq.hylo` | accepted | rejected | cannot pass value of type 'A' to parameter 'D' |
| `q2-open-eq-amb.hylo` | rejected | accepted |  |
| `r1-bundle-eq.hylo` | rejected | rejected | no coercion from 'Void' to '{T, Void}' |
| `r2-bundle-eq-neg.hylo` | timeout | rejected | no coercion from 'Void' to '{T, Void}' |
| `r3-arrow-eq.hylo` | timeout | rejected | no coercion from '([Void](x: let A) let -> Void ~ [Void](y: let B) let -> Void) ==> [Void]() let ->  |
| `x1-extorder-after.hylo` | rejected | rejected | no coercion from 'A' to '#!' |
| `x2-extorder-self.hylo` | rejected | rejected | definition of 'Me' refers to itself |
| `a4-annot.hylo` | accepted | accepted |  |
| `a4-explicit.hylo` | accepted | accepted |  |
| `n1-nested-occurs.hylo` | crash | rejected | no coercion from '<T> P<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `cyclic-query-segfault.hylo` | crash | rejected | no coercion from '<T> R<T> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
