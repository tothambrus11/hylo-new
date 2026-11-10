# Test programs: abstract model

Verdicts of the existing implementation, of the techniques with the fixes for problems 1 to 4 only, and of the recommended configuration of the report, with a 30 s limit (recommended configuration: 60 s).

| Program | Existing | Fixes 1–4 | Recommended | First error (recommended) |
|---|---|---|---|---|
| `aq1-premise-instance.hylo` | rejected | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq2-congruent-instance.hylo` | rejected | rejected | rejected | no coercion from 'P<Y> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq3-generic-instance.hylo` | rejected | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `aq4-ground-using.hylo` | rejected | rejected | rejected | no coercion from 'P<Wrap<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `probe1.hylo` | accepted | accepted | accepted |  |
| `probe2.hylo` | rejected | rejected | rejected | no coercion from 'Q<Opt<Y>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
