# Test programs: abstract model

Verdicts of the old checker and of the new one with all techniques enabled (30 s limit). A difference is either an ill-typed program that is now rejected, a crash or timeout that now gets an answer, or a case discussed in the reports.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `aq1-premise-instance.hylo` | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq2-congruent-instance.hylo` | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq3-generic-instance.hylo` | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq4-ground-using.hylo` | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `probe1.hylo` | accepted | accepted |  |
| `probe2.hylo` | rejected | rejected | no coercion from 'Q<Opt<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
