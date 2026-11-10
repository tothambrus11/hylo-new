# Test programs: abstract model

Verdicts of the existing implementation ("Old") and of the revised implementation with all techniques enabled ("New"), with a 30 s limit. Each difference is an ill-typed program that is now rejected, an abnormal termination or timeout that is now resolved, or a case discussed in the accompanying documents.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `aq1-premise-instance.hylo` | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq2-congruent-instance.hylo` | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq3-generic-instance.hylo` | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq4-ground-using.hylo` | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `probe1.hylo` | accepted | accepted |  |
| `probe2.hylo` | rejected | rejected | no coercion from 'Q<Opt<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
