| Program | Step | Expected, design as revised | Observed: first version (FULL + `premsubst` / NEW) | Currently (base / FULL) |
|---|---|---|---|---|
| `s1-gain-conformance-generic` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-conformance-two` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-chain` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-middle` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-extension` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-given` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-static-method` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-equal-parameters` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-extension-concrete` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-conformance-concrete` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-equality-concrete` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-given-concrete` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-open-variable-a` | 3 | accepted | accepted / accepted | timeout / rejected |
| `s1-gain-open-variable-b` | 3 | accepted | accepted / accepted | rejected / rejected |
| `s1-gain-nested-dependent-given` | 3 | accepted with `assocsubst`, `premsubst.stuck=0`; rejected without | rejected / accepted | rejected / rejected |
| `s1-keep-equality-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted | accepted / accepted |
| `s1-keep-extension-generic` | 2 | accepted, `eqsolve.premises=0` | accepted / accepted | accepted / accepted |
| `s1-keep-recursion` | 2, 5 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-extension-sibling` | 2, 5 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-result-type` | 2 | accepted, same witness | accepted / accepted | accepted / accepted |
| `s1-keep-hypothesis` | 2 | accepted, trace identical | accepted / accepted | accepted / accepted |
| `s1-reject-missing-requirement` | 2 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-concrete-mismatch` | 3 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-given-concrete` | 3 | rejected | rejected / rejected | rejected / rejected |
| `s1-reject-ambiguous-both` | 3 | rejected (two results) | rejected / rejected | rejected / rejected |
| `s1-reject-duplicate-requirement` | – | rejected where the clause is declared | rejected / rejected | rejected / rejected |
| `s1-reject-cyclic-definition` | 3 | rejected at the conformance, terminates | rejected / rejected | rejected / rejected |
| `s1-reject-capture-control` | – | rejected | rejected / rejected | rejected / rejected |
| `s1-attack-capture-recursion` | 5 | **rejected** | accepted / accepted | rejected / rejected |
| `s1-attack-capture-recursion-generic` | 5 | **rejected**, also with `assocsubst` | rejected / accepted | rejected / rejected |
| `s1-attack-method` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-initializer` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-trait-requirement` | 6 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-coerced-witness` | 7 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-attack-coerced-witness-own-projection` | 7 | **accepted** | rejected / rejected | rejected / rejected |
| `s1-reject-other-conformance` | 7, 8 | rejected with `premcommit`; accepted with step 7 alone | rejected / rejected | rejected / rejected |
| `s1-attack-other-conformance-equality` | 7, 8 | rejected with `premcommit`; accepted with step 7 alone | rejected / rejected | accepted / rejected |
| `s1-attack-shadowed-requirement` | 8 | rejected with `premcommit`; accepted without | accepted / accepted | rejected / rejected |
| `s1-attack-shadowed-local-given` | 8 | rejected with `premcommit`; accepted without | accepted / accepted | rejected / rejected |
| `s1-attack-nonminimal-witness` | 8 | rejected with `premcommit`; accepted without, given `assocsubst` | rejected / accepted | rejected / rejected |
| `s1-open-ambiguous-dependency` | 8 | rejected with `premcommit`; accepted without; question 4 | accepted / accepted | rejected / rejected |
| `s1-attack-shadowed-result-type` | 8 | rejected with `premcommit`; accepted without, given `headsubst` | rejected / accepted | rejected / rejected |
| `s1-attack-shadowed-result-type-own` | – | rejected | rejected / rejected | rejected / rejected |
| `s1-attack-where-order-a` | 2 | accepted | accepted / accepted | rejected / rejected |
| `s1-attack-where-order-b` | 2 | rejected by the bound (`summon.depthExhausted=1`); accepted under a height bound | rejected / rejected | rejected / rejected |
| `s1-open-parameter-type` | – | rejected by `premsubst`; accepted with `headsubst` | rejected / accepted | rejected / rejected |
