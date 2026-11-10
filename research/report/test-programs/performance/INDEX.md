# Test programs: performance

Verdicts of the existing implementation, of the techniques with the fixes for problems 1 to 4 only, and of the recommended configuration of the report, with a 30 s limit (recommended configuration: 60 s).

| Program | Existing | Fixes 1–4 | Recommended | First error (recommended) |
|---|---|---|---|---|
| `cc-chain-k16-w10-m1.hylo` | timeout | accepted | accepted |  |
| `cc-chain-k16-w10-m8.hylo` | timeout | accepted | accepted |  |
| `cc-chain-k24-w10-m1.hylo` | timeout | accepted | accepted |  |
| `cc-chain-k4-w10-m1.hylo` | accepted | accepted | accepted |  |
| `cc-chain-k8-w10-m1.hylo` | accepted | accepted | accepted |  |
| `cc-deep-10-1.hylo` | accepted | accepted | accepted |  |
| `cc-deep-20-1.hylo` | accepted | accepted | accepted |  |
| `cc-deep-40-1.hylo` | accepted | accepted | accepted |  |
| `cc-deep-40-m10.hylo` | timeout | accepted | accepted |  |
| `cc-deep-40-m30.hylo` | timeout | accepted | accepted |  |
| `cc-deep-60-m30.hylo` | timeout | accepted | accepted |  |
| `cc-deep-80-m1.hylo` | accepted | accepted | accepted |  |
| `cc-goals-m10.hylo` | rejected | accepted | accepted |  |
| `cc-goals-m20.hylo` | rejected | accepted | accepted |  |
| `cc-goals-m30.hylo` | rejected | accepted | accepted |  |
| `cc-goals-m36.hylo` | rejected | accepted | accepted |  |
| `cc-refl-k12-w10-m8.hylo` | accepted | accepted | accepted |  |
| `cc-refl-k16-w10-m1.hylo` | accepted | accepted | accepted |  |
| `cc-refl-k16-w10-m4.hylo` | accepted | accepted | accepted |  |
| `cc-refl-k4-w10-m1.hylo` | accepted | accepted | accepted |  |
| `cc-refl-k8-w10-m1.hylo` | accepted | accepted | accepted |  |
| `div-eq-b2-0.hylo` | rejected | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-b2-1.hylo` | rejected | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-b3-0.hylo` | timeout | rejected | rejected | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type arguments or annotations |
| `div-eq-b3-1.hylo` | timeout | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-eq-ovl-b2-0.hylo` | accepted | accepted | accepted |  |
| `div-eq-ovl-b2-1.hylo` | accepted | accepted | accepted |  |
| `div-eq-ovl-b3-0.hylo` | timeout | accepted | accepted |  |
| `div-eq-ovl-b3-1.hylo` | timeout | accepted | accepted |  |
| `div-trunc-b1.hylo` | rejected | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-trunc-b2.hylo` | rejected | rejected | rejected | no coercion from 'P<Yb> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-trunc-b3.hylo` | timeout | rejected | rejected | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type arguments or annotations |
| `div-trunc-b4.hylo` | timeout | rejected | rejected | implicit resolution is too complex: more than 100000 candidate derivations; consider adding explicit type arguments or annotations |
| `div-valid-b3-d4.hylo` | rejected | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-valid-b3-d5.hylo` | rejected | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `div-valid-b4-d4.hylo` | rejected | rejected | rejected | no coercion from 'P<Xi> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `extchain-16.hylo` | rejected | accepted | accepted |  |
| `extchain-24.hylo` | rejected | accepted | accepted |  |
| `extchain-8.hylo` | rejected | accepted | accepted |  |
| `extsame-16.hylo` | rejected | rejected | accepted |  |
| `extsame-8.hylo` | rejected | rejected | accepted |  |
| `occurs-dag-12.hylo` | accepted | accepted | accepted |  |
| `occurs-dag-16.hylo` | accepted | accepted | accepted |  |
| `occurs-dag-18.hylo` | accepted | accepted | accepted |  |
| `occurs-dag-8.hylo` | accepted | accepted | accepted |  |
| `occurs-only-18.hylo` | rejected | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-only-22.hylo` | rejected | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-only-24.hylo` | rejected | rejected | rejected | no coercion from 'Q<Bar> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `occurs-valid-20.hylo` | accepted | accepted | accepted |  |
| `occurs-valid-22.hylo` | accepted | accepted | accepted |  |
| `occurs-valid-24.hylo` | accepted | accepted | accepted |  |
| `open-neg-0.hylo` | timeout | rejected | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| `open-neg-1.hylo` | timeout | rejected | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| `open-neg-2.hylo` | timeout | rejected | rejected | no coercion from '<T, U> (Q<U>, (T ~ U)) ==> [Void](let T) let -> Void' to '[Void](let A0) let -> Void' |
| `open-pos-1.hylo` | accepted | accepted | accepted |  |
| `open-pos-chain-2.hylo` | accepted | accepted | accepted |  |
| `open-pos-chain-3.hylo` | accepted | accepted | accepted |  |
| `open-pos-chain-4.hylo` | accepted | accepted | accepted |  |
| `open-wide-1.hylo` | accepted | accepted | accepted |  |
| `open-wide-2.hylo` | accepted | accepted | accepted |  |
| `open-wide-3.hylo` | accepted | accepted | accepted |  |
| `open-wide-4.hylo` | timeout | accepted | accepted |  |
| `ovl-ret-12.hylo` | timeout | timeout | accepted |  |
| `ovl-ret-4.hylo` | accepted | accepted | accepted |  |
| `ovl-ret-8.hylo` | accepted | accepted | accepted |  |
| `ovl-ret-9.hylo` | accepted | accepted | accepted |  |
| `pending-var-2.hylo` | accepted | accepted | accepted |  |
| `pending-var-3.hylo` | rejected | accepted | accepted |  |
| `pending-var-4.hylo` | accepted | accepted | accepted |  |
| `pending-var2-3.hylo` | accepted | accepted | accepted |  |
| `pending-var2-5.hylo` | accepted | accepted | accepted |  |
| `poison-a-3.hylo` | rejected | rejected | rejected | declaration is not allowed here |
| `poison-b-3.hylo` | rejected | rejected | rejected | declaration is not allowed here |
| `poison-trans-2.hylo` | rejected | rejected | rejected | expected 'is' |
| `poison-trans-3.hylo` | rejected | rejected | rejected | expected 'is' |
| `poison-trans-4.hylo` | rejected | rejected | rejected | expected 'is' |
