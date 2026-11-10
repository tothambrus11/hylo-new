# Test programs: unsimplified projections

Verdicts of the existing implementation, of the techniques with the fixes for problems 1 to 4 only, and of the recommended configuration of the report, with a 30 s limit (recommended configuration: 60 s).

| Program | Existing | Fixes 1–4 | Recommended | First error (recommended) |
|---|---|---|---|---|
| `min.hylo` | timeout | rejected | accepted |  |
| `v2-swapped.hylo` | rejected | rejected | rejected | type 'T' has no static member 'X' |
| `v3-param.hylo` | rejected | rejected | accepted |  |
| `v4-plaineq.hylo` | accepted | accepted | accepted |  |
| `v5-generic.hylo` | accepted | accepted | accepted |  |
| `v6-refl.hylo` | accepted | accepted | accepted |  |
| `v7-ret.hylo` | rejected | rejected | accepted |  |
| `v8-proj.hylo` | accepted | accepted | accepted |  |
| `t1.hylo` | timeout | rejected | accepted |  |
| `t10-wrongx.hylo` | rejected | rejected | rejected | cannot pass value of type 'B' to parameter 'X' |
| `t11-generic-conf.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `t12-assoc-in-body-generic.hylo` | rejected | rejected | accepted |  |
| `t13-generic-conf-const.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `t14-generic-conf-call.hylo` | accepted | accepted | accepted |  |
| `t2-swapped.hylo` | rejected | rejected | rejected | type 'T' has no static member 'X' |
| `t3-param.hylo` | rejected | rejected | accepted |  |
| `t4-generic-caller.hylo` | accepted | accepted | accepted |  |
| `t5-concrete-x.hylo` | accepted | accepted | accepted |  |
| `t6-ret.hylo` | rejected | rejected | accepted |  |
| `t7-cond-direct.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `t8-cond-call.hylo` | timeout | rejected | accepted |  |
| `t9-two-conf.hylo` | accepted | accepted | accepted |  |
| `j1-box-nongeneric.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `j2-generic-conf-alias.hylo` | rejected | rejected | rejected | expected declaration |
