| File | Kind | Expected | Configuration | Verdict | `#!` in messages | `summon.calls` | `summon.matches` | `summon.layers` | `eqsolve.proved` | `eqsolve.refuted` | `eqmgu.solved` | type.user ms (indicative) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `rust-flatten.hylo` | benchmark | accepted | base | crash (stack overflow) | 0 | – | – | – | – | – | – | – |
| `rust-flatten.hylo` | benchmark | accepted | FIX | rejected (1) | 0 | 45 | 13841 | 56 | 3 | 0 | 142 | 588 |
| `rust-flatten.hylo` | benchmark | accepted | FULL | rejected (1) | 0 | 45 | 13841 | 56 | 3 | 0 | 142 | 418 |
| `generated/rust-flatten.neg.hylo` | false claims | 3 errors | base | crash (stack overflow) | 0 | – | – | – | – | – | – | – |
| `generated/rust-flatten.neg.hylo` | false claims | 3 errors | FIX | rejected (4) | 0 | 57 | 13844 | 59 | 3 | 6 | 142 | 646 |
| `generated/rust-flatten.neg.hylo` | false claims | 3 errors | FULL | rejected (4) | 0 | 57 | 13844 | 59 | 3 | 6 | 142 | 295 |
| `generated/rust-flatten.control.hylo` | control | 2 errors | base | crash (stack overflow) | 0 | – | – | – | – | – | – | – |
| `generated/rust-flatten.control.hylo` | control | 2 errors | FIX | rejected (3) | 0 | 47 | 13841 | 56 | 2 | 4 | 142 | 372 |
| `generated/rust-flatten.control.hylo` | control | 2 errors | FULL | rejected (3) | 0 | 47 | 13841 | 56 | 2 | 4 | 142 | 314 |
| `swift-collection-signature.hylo` | benchmark | accepted | base | accepted | 0 | 147 | 811287 | 879 | 0 | 0 | 0 | 46011 |
| `swift-collection-signature.hylo` | benchmark | accepted | FIX | accepted | 0 | 147 | 9501 | 144 | 14 | 8 | 0 | 849 |
| `swift-collection-signature.hylo` | benchmark | accepted | FULL | accepted | 0 | 147 | 9501 | 144 | 14 | 8 | 0 | 1010 |
| `generated/swift-collection-signature.neg.hylo` | false claims | 6 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-collection-signature.neg.hylo` | false claims | 6 errors | FIX | rejected (6) | 0 | 174 | 9693 | 152 | 14 | 20 | 0 | 574 |
| `generated/swift-collection-signature.neg.hylo` | false claims | 6 errors | FULL | rejected (6) | 0 | 174 | 9693 | 152 | 14 | 20 | 0 | 693 |
| `generated/swift-collection-signature.control.hylo` | control | 20 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-collection-signature.control.hylo` | control | 20 errors | FIX | rejected (20) | 0 | 167 | 9501 | 144 | 4 | 41 | 0 | 607 |
| `generated/swift-collection-signature.control.hylo` | control | 20 errors | FULL | rejected (20) | 0 | 167 | 9501 | 144 | 4 | 41 | 0 | 789 |
| `generated/swift-collection-signature.fn-one.hylo` | one function | accepted | base | accepted | 0 | 61 | 29870 | 364 | 0 | 0 | 0 | 1486 |
| `generated/swift-collection-signature.fn-one.hylo` | one function | accepted | FIX | accepted | 0 | 61 | 3104 | 56 | 8 | 2 | 0 | 379 |
| `generated/swift-collection-signature.fn-one.hylo` | one function | accepted | FULL | accepted | 0 | 61 | 3104 | 56 | 8 | 2 | 0 | 192 |
| `generated/swift-collection-signature.fn-two.hylo` | one function | accepted | base | accepted | 0 | 86 | 781417 | 515 | 0 | 0 | 0 | 33208 |
| `generated/swift-collection-signature.fn-two.hylo` | one function | accepted | FIX | accepted | 0 | 86 | 6397 | 88 | 6 | 6 | 0 | 616 |
| `generated/swift-collection-signature.fn-two.hylo` | one function | accepted | FULL | accepted | 0 | 86 | 6397 | 88 | 6 | 6 | 0 | 531 |
| `swift-string-protocol.hylo` | benchmark | accepted | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `swift-string-protocol.hylo` | benchmark | accepted | FIX | accepted | 0 | 161 | 10824 | 155 | 10 | 3 | 0 | 917 |
| `swift-string-protocol.hylo` | benchmark | accepted | FULL | accepted | 0 | 161 | 10749 | 154 | 10 | 3 | 0 | 1268 |
| `generated/swift-string-protocol.neg.hylo` | false claims | 5 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-string-protocol.neg.hylo` | false claims | 5 errors | FIX | rejected (5) | 0 | 190 | 11108 | 163 | 10 | 13 | 0 | 975 |
| `generated/swift-string-protocol.neg.hylo` | false claims | 5 errors | FULL | rejected (5) | 0 | 190 | 11033 | 162 | 10 | 13 | 0 | 1216 |
| `generated/swift-string-protocol.control.hylo` | control | 18 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-string-protocol.control.hylo` | control | 18 errors | FIX | rejected (18) | 0 | 179 | 10824 | 155 | 1 | 33 | 0 | 822 |
| `generated/swift-string-protocol.control.hylo` | control | 18 errors | FULL | rejected (18) | 0 | 179 | 10749 | 154 | 1 | 33 | 0 | 683 |
| `generated/swift-string-protocol.fn-overString.hylo` | one function | accepted | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-string-protocol.fn-overString.hylo` | one function | accepted | FIX | accepted | 0 | 141 | 9360 | 133 | 9 | 3 | 0 | 808 |
| `generated/swift-string-protocol.fn-overString.hylo` | one function | accepted | FULL | accepted | 0 | 141 | 9360 | 133 | 9 | 3 | 0 | 625 |
| `generated/swift-string-protocol.fn-decoding.hylo` | one function | accepted | base | accepted | 0 | 20 | 3731 | 78 | 0 | 0 | 0 | 228 |
| `generated/swift-string-protocol.fn-decoding.hylo` | one function | accepted | FIX | accepted | 0 | 20 | 1464 | 22 | 1 | 0 | 0 | 108 |
| `generated/swift-string-protocol.fn-decoding.hylo` | one function | accepted | FULL | accepted | 0 | 20 | 1389 | 21 | 1 | 0 | 0 | 120 |
| `swift-transitive-parameters.hylo` | benchmark | accepted | base | rejected (1) | 0 | 40 | 1549133 | 190 | 0 | 0 | 0 | 45341 |
| `swift-transitive-parameters.hylo` | benchmark | accepted | FIX | accepted | 0 | 39 | 2461 | 49 | 8 | 0 | 0 | 103 |
| `swift-transitive-parameters.hylo` | benchmark | accepted | FULL | accepted | 0 | 39 | 2236 | 46 | 8 | 0 | 0 | 92 |
| `generated/swift-transitive-parameters.neg.hylo` | false claims | 6 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-transitive-parameters.neg.hylo` | false claims | 6 errors | FIX | rejected (6) | 0 | 57 | 112196 | 1252 | 8 | 8 | 284 | 2304 |
| `generated/swift-transitive-parameters.neg.hylo` | false claims | 6 errors | FULL | rejected (6) | 0 | 57 | 111821 | 1247 | 8 | 8 | 284 | 1160 |
| `generated/swift-transitive-parameters.control.hylo` | control | 4 errors | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `generated/swift-transitive-parameters.control.hylo` | control | 4 errors | FIX | rejected (4) | 0 | 43 | 2461 | 49 | 6 | 8 | 0 | 94 |
| `generated/swift-transitive-parameters.control.hylo` | control | 4 errors | FULL | rejected (4) | 0 | 43 | 2236 | 46 | 6 | 8 | 0 | 108 |
| `generated/swift-transitive-parameters.fn-rangeSetInit.hylo` | one function | accepted | base | accepted | 0 | 21 | 33719 | 92 | 0 | 0 | 0 | 1174 |
| `generated/swift-transitive-parameters.fn-rangeSetInit.hylo` | one function | accepted | FIX | accepted | 0 | 21 | 1111 | 23 | 4 | 0 | 0 | 95 |
| `generated/swift-transitive-parameters.fn-rangeSetInit.hylo` | one function | accepted | FULL | accepted | 0 | 21 | 1036 | 22 | 4 | 0 | 0 | 85 |
| `generated/swift-transitive-parameters.fn-anyCollectionInit.hylo` | one function | accepted | base | accepted | 0 | 27 | 8978 | 99 | 0 | 0 | 0 | 390 |
| `generated/swift-transitive-parameters.fn-anyCollectionInit.hylo` | one function | accepted | FIX | accepted | 0 | 27 | 1110 | 21 | 3 | 0 | 0 | 93 |
| `generated/swift-transitive-parameters.fn-anyCollectionInit.hylo` | one function | accepted | FULL | accepted | 0 | 27 | 960 | 19 | 3 | 0 | 0 | 84 |
| `generated/swift-transitive-parameters.fn-chainUse.hylo` | one function | accepted | base | rejected (1) | 0 | 18 | 1508948 | 73 | 0 | 0 | 0 | 53709 |
| `generated/swift-transitive-parameters.fn-chainUse.hylo` | one function | accepted | FIX | accepted | 0 | 17 | 1256 | 19 | 1 | 0 | 0 | 61 |
| `generated/swift-transitive-parameters.fn-chainUse.hylo` | one function | accepted | FULL | accepted | 0 | 17 | 1256 | 19 | 1 | 0 | 0 | 54 |
| `gaps/associated-type-premise.hylo` | gap | see file | base | rejected (2) | 0 | 5 | 1047 | 24 | 0 | 0 | 0 | 71 |
| `gaps/associated-type-premise.hylo` | gap | see file | FIX | rejected (2) | 0 | 5 | 745 | 12 | 0 | 0 | 0 | 59 |
| `gaps/associated-type-premise.hylo` | gap | see file | FULL | rejected (2) | 0 | 5 | 173 | 12 | 0 | 0 | 0 | 17 |
| `gaps/equality-determined-parameter.hylo` | gap | see file | base | accepted | 0 | 2 | 807 | 18 | 0 | 0 | 0 | 66 |
| `gaps/equality-determined-parameter.hylo` | gap | see file | FIX | accepted | 0 | 2 | 291 | 6 | 0 | 0 | 1 | 19 |
| `gaps/equality-determined-parameter.hylo` | gap | see file | FULL | accepted | 0 | 2 | 291 | 6 | 0 | 0 | 1 | 22 |
| `gaps/error-type-accepted.hylo` | gap | see file | base | accepted | 0 | 2 | 440 | 14 | 0 | 0 | 0 | 47 |
| `gaps/error-type-accepted.hylo` | gap | see file | FIX | accepted | 0 | 2 | 144 | 2 | 0 | 0 | 0 | 10 |
| `gaps/error-type-accepted.hylo` | gap | see file | FULL | accepted | 0 | 2 | 2 | 2 | 0 | 0 | 0 | 2 |
| `gaps/generic-projection.hylo` | gap | see file | base | rejected (2) | 0 | 1 | 366 | 13 | 0 | 0 | 0 | 40 |
| `gaps/generic-projection.hylo` | gap | see file | FIX | rejected (2) | 0 | 1 | 218 | 7 | 0 | 0 | 0 | 16 |
| `gaps/generic-projection.hylo` | gap | see file | FULL | rejected (2) | 0 | 1 | 8 | 7 | 0 | 0 | 0 | 2 |
| `gaps/inherited-associated-type.hylo` | gap | see file | base | rejected (1) | 1 | 2 | 513 | 16 | 0 | 0 | 0 | 23 |
| `gaps/inherited-associated-type.hylo` | gap | see file | FIX | rejected (1) | 1 | 2 | 217 | 4 | 0 | 0 | 0 | 12 |
| `gaps/inherited-associated-type.hylo` | gap | see file | FULL | rejected (1) | 1 | 2 | 4 | 4 | 0 | 0 | 0 | 3 |
| `gaps/restated-conformance.hylo` | gap | see file | base | accepted | 0 | 13 | 30172 | 97 | 0 | 0 | 0 | 1124 |
| `gaps/restated-conformance.hylo` | gap | see file | FIX | rejected (1) | 0 | 14 | 882 | 13 | 0 | 2 | 0 | 93 |
| `gaps/restated-conformance.hylo` | gap | see file | FULL | rejected (1) | 0 | 14 | 882 | 13 | 0 | 2 | 0 | 70 |
| `gaps/trait-equality.hylo` | gap | see file | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `gaps/trait-equality.hylo` | gap | see file | FIX | rejected (2) | 0 | 7 | 365 | 6 | 0 | 2 | 0 | 15 |
| `gaps/trait-equality.hylo` | gap | see file | FULL | rejected (2) | 0 | 7 | 79 | 6 | 0 | 2 | 0 | 7 |
| `gaps/trait-given-not-used-for-lookup.hylo` | gap | see file | base | rejected (1) | 1 | 10 | 1692 | 48 | 0 | 0 | 0 | 79 |
| `gaps/trait-given-not-used-for-lookup.hylo` | gap | see file | FIX | rejected (1) | 1 | 10 | 798 | 12 | 0 | 0 | 0 | 38 |
| `gaps/trait-given-not-used-for-lookup.hylo` | gap | see file | FULL | rejected (1) | 1 | 10 | 443 | 12 | 0 | 0 | 0 | 36 |
| `gaps/two-equality-conditions.hylo` | gap | see file | base | timeout (60 s) | 0 | – | – | – | – | – | – | – |
| `gaps/two-equality-conditions.hylo` | gap | see file | FIX | rejected (1) | 0 | 29 | 14020 | 56 | 2 | 0 | 142 | 467 |
| `gaps/two-equality-conditions.hylo` | gap | see file | FULL | rejected (1) | 0 | 29 | 14020 | 56 | 2 | 0 | 142 | 223 |
| `gaps/unsatisfiable-conformance.hylo` | gap | see file | base | crash (stack overflow) | 0 | – | – | – | – | – | – | – |
| `gaps/unsatisfiable-conformance.hylo` | gap | see file | FIX | rejected (1) | 0 | 9 | 11322 | 26 | 0 | 0 | 142 | 395 |
| `gaps/unsatisfiable-conformance.hylo` | gap | see file | FULL | rejected (1) | 0 | 9 | 441 | 7 | 0 | 0 | 0 | 28 |
| `gaps/where-clause-order.hylo` | gap | see file | base | rejected (1) | 0 | 1 | 214 | 7 | 0 | 0 | 0 | 30 |
| `gaps/where-clause-order.hylo` | gap | see file | FIX | rejected (1) | 0 | 1 | 70 | 1 | 0 | 0 | 0 | 13 |
| `gaps/where-clause-order.hylo` | gap | see file | FULL | rejected (1) | 0 | 1 | 70 | 1 | 0 | 0 | 0 | 4 |
