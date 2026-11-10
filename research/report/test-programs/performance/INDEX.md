# Test programs: performance

Verdicts of the old checker and of the new one with all techniques enabled (30 s limit). A difference is either an ill-typed program that is now rejected, a crash or timeout that now gets an answer, or a case discussed in the reports.

| Program | Old | New | First error (new) |
|---|---|---|---|
| `cc-chain-k16-w10-m1.hylo` | timeout | accepted |  |
| `cc-chain-k16-w10-m8.hylo` | timeout | accepted |  |
| `cc-chain-k24-w10-m1.hylo` | timeout | accepted |  |
| `cc-chain-k4-w10-m1.hylo` | accepted | accepted |  |
| `cc-chain-k8-w10-m1.hylo` | accepted | accepted |  |
| `cc-deep-10-1.hylo` | accepted | accepted |  |
| `cc-deep-20-1.hylo` | accepted | accepted |  |
| `cc-deep-40-1.hylo` | accepted | accepted |  |
| `cc-deep-40-m10.hylo` | timeout | accepted |  |
| `cc-deep-40-m30.hylo` | timeout | accepted |  |
| `cc-deep-60-m30.hylo` | timeout | accepted |  |
| `cc-deep-80-m1.hylo` | accepted | accepted |  |
| `cc-goals-m10.hylo` | rejected | accepted |  |
| `cc-goals-m20.hylo` | rejected | accepted |  |
| `cc-goals-m30.hylo` | rejected | accepted |  |
| `cc-goals-m36.hylo` | rejected | accepted |  |
| `cc-refl-k12-w10-m8.hylo` | accepted | accepted |  |
| `cc-refl-k16-w10-m1.hylo` | accepted | accepted |  |
| `cc-refl-k16-w10-m4.hylo` | accepted | accepted |  |
| `cc-refl-k4-w10-m1.hylo` | accepted | accepted |  |
| `cc-refl-k8-w10-m1.hylo` | accepted | accepted |  |
| `div-eq-b2-0.hylo` | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-b2-1.hylo` | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-b3-0.hylo` | timeout | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-b3-1.hylo` | timeout | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-ovl-b2-0.hylo` | accepted | accepted |  |
| `div-eq-ovl-b2-1.hylo` | accepted | accepted |  |
| `div-eq-ovl-b3-0.hylo` | timeout | accepted |  |
| `div-eq-ovl-b3-1.hylo` | timeout | accepted |  |
| `div-trunc-b1.hylo` | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-trunc-b2.hylo` | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-trunc-b3.hylo` | timeout | rejected | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit |
| `div-trunc-b4.hylo` | timeout | rejected | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit |
| `div-valid-b3-d4.hylo` | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-valid-b3-d5.hylo` | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-valid-b4-d4.hylo` | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `extchain-16.hylo` | rejected | accepted |  |
| `extchain-24.hylo` | rejected | accepted |  |
| `extchain-8.hylo` | rejected | accepted |  |
| `extsame-16.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Y', which this extension  |
| `extsame-8.hylo` | rejected | rejected | circular extension: the extendee of this extension depends on a lookup of 'Y', which this extension  |
| `occurs-dag-12.hylo` | accepted | accepted |  |
| `occurs-dag-16.hylo` | accepted | accepted |  |
| `occurs-dag-18.hylo` | accepted | accepted |  |
| `occurs-dag-8.hylo` | accepted | accepted |  |
| `occurs-only-18.hylo` | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-only-22.hylo` | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-only-24.hylo` | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-valid-20.hylo` | accepted | accepted |  |
| `occurs-valid-22.hylo` | accepted | accepted |  |
| `occurs-valid-24.hylo` | accepted | accepted |  |
| `open-neg-0.hylo` | timeout | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Vo |
| `open-neg-1.hylo` | timeout | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Vo |
| `open-neg-2.hylo` | timeout | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Vo |
| `open-pos-1.hylo` | accepted | accepted |  |
| `open-pos-chain-2.hylo` | accepted | accepted |  |
| `open-pos-chain-3.hylo` | accepted | accepted |  |
| `open-pos-chain-4.hylo` | accepted | accepted |  |
| `open-wide-1.hylo` | accepted | accepted |  |
| `open-wide-2.hylo` | accepted | accepted |  |
| `open-wide-3.hylo` | accepted | accepted |  |
| `open-wide-4.hylo` | timeout | accepted |  |
| `ovl-ret-12.hylo` | timeout | timeout |  |
| `ovl-ret-4.hylo` | accepted | accepted |  |
| `ovl-ret-8.hylo` | accepted | accepted |  |
| `ovl-ret-9.hylo` | accepted | accepted |  |
| `pending-var-2.hylo` | accepted | accepted |  |
| `pending-var-3.hylo` | rejected | accepted |  |
| `pending-var-4.hylo` | accepted | accepted |  |
| `pending-var2-3.hylo` | accepted | accepted |  |
| `pending-var2-5.hylo` | accepted | accepted |  |
| `poison-a-3.hylo` | rejected | rejected | declaration is not allowed here |
| `poison-b-3.hylo` | rejected | rejected | declaration is not allowed here |
| `poison-trans-2.hylo` | rejected | rejected | expected 'is' |
| `poison-trans-3.hylo` | rejected | rejected | expected 'is' |
| `poison-trans-4.hylo` | rejected | rejected | expected 'is' |
