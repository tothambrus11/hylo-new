# Test programs: unsimplified projections

Verdicts of the old checker and of the new one with all techniques enabled (30 s limit). A difference is either an ill-typed program that is now rejected, a crash or timeout that now gets an answer, or a case discussed in the reports.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `min.hylo` | timeout | rejected | no coercion from '(P<A>, ((A::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v2-swapped.hylo` | rejected | rejected | type 'T' has no static member 'X' |
| `v3-param.hylo` | rejected | rejected | cannot pass value of type 'B' to parameter '(A::P).X' |
| `v4-plaineq.hylo` | accepted | accepted |  |
| `v5-generic.hylo` | accepted | accepted |  |
| `v6-refl.hylo` | accepted | accepted |  |
| `v7-ret.hylo` | rejected | rejected | no coercion from '(A::P).X' to 'B' |
| `v8-proj.hylo` | accepted | accepted |  |
| `t1.hylo` | timeout | rejected | no coercion from '(P<A>, ((A::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `t10-wrongx.hylo` | rejected | rejected | cannot pass value of type 'B' to parameter '(A::P).X' |
| `t11-generic-conf.hylo` | rejected | rejected | expression does not denote a type |
| `t12-assoc-in-body-generic.hylo` | rejected | rejected | cannot pass value of type '(U::P).X' to parameter '(U::P).X' |
| `t13-generic-conf-const.hylo` | rejected | rejected | expression does not denote a type |
| `t14-generic-conf-call.hylo` | accepted | accepted |  |
| `t2-swapped.hylo` | rejected | rejected | type 'T' has no static member 'X' |
| `t3-param.hylo` | rejected | rejected | cannot pass value of type 'B' to parameter '(A::P).X' |
| `t4-generic-caller.hylo` | accepted | accepted |  |
| `t5-concrete-x.hylo` | accepted | accepted |  |
| `t6-ret.hylo` | rejected | rejected | no coercion from '(A::P).X' to 'B' |
| `t7-cond-direct.hylo` | rejected | rejected | expression does not denote a type |
| `t8-cond-call.hylo` | timeout | rejected | no coercion from '(P<Box<B>>, ((Box<B>::P).X ~ B)) ==> [Void]() let -> Void' to '[Void]() let -> Voi |
| `t9-two-conf.hylo` | accepted | accepted |  |
| `j1-box-nongeneric.hylo` | rejected | rejected | expression does not denote a type |
| `j2-generic-conf-alias.hylo` | rejected | rejected | expected declaration |
