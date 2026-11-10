### Problems and queries checked

| Kind | Problems | Queries | base: problems / queries | FIX: problems / queries | FULL: problems / queries |
|---|---:|---:|---:|---:|---:|
| conf | 500 | 3000 | 120 / 720 | 500 / 3000 | 500 / 3000 |
| eq-param | 550 | 3300 | 5 / 30 | 550 / 3300 | 550 / 3300 |
| eq-app | 550 | 3300 | 5 / 30 | 550 / 3300 | 550 / 3300 |
| chain | 450 | 2700 | 5 / 30 | 450 / 2700 | 450 / 2700 |
| cond | 500 | 3000 | 5 / 30 | 500 / 3000 | 500 / 3000 |
| assoc | 650 | 3900 | 5 / 30 | 650 / 3900 | 650 / 3900 |
| blanket | 250 | 1500 | 5 / 30 | 250 / 1500 | 250 / 1500 |
| twin | 200 | 800 | 5 / 20 | 200 / 800 | 200 / 800 |
| total | 3650 | 21500 | 155 / 920 | 3650 / 21500 | 3650 / 21500 |

### Reference answers of the generated queries

| Reference answer | conf | eq-param | eq-app | chain | cond | assoc | blanket | twin | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| derivable, one derivation | 1472 | 1611 | 1614 | 1302 | 1322 | 1919 | 735 | 0 | 9975 |
| derivable, several derivations | 16 | 36 | 28 | 42 | 155 | 32 | 15 | 800 | 1124 |
| illformed-goal | 0 | 0 | 0 | 0 | 0 | 223 | 73 | 0 | 296 |
| underivable, invalid in the model | 1512 | 1653 | 1394 | 1309 | 1523 | 1632 | 604 | 0 | 9627 |
| underivable, scope has no solution | 0 | 0 | 123 | 7 | 0 | 94 | 73 | 0 | 297 |
| underivable, valid with injectivity | 0 | 0 | 141 | 40 | 0 | 0 | 0 | 0 | 181 |

### Classes by configuration

| Class | base | FIX | FULL |
|---|---:|---:|---:|
| AMBIGUITY-MISSED | 13 | 408 | 408 |
| BEYOND-SPEC | 0 | 12 | 12 |
| BUDGET-agree | 0 | 17 | 17 |
| ILLFORMED-accept | 0 | 6 | 6 |
| INCOMPLETE | 17 | 735 | 735 |
| MULTI-accept | 6 | 281 | 281 |
| MULTI-reject | 1 | 43 | 43 |
| TIMEOUT | 24 | 0 | 0 |
| UNSOUND | 4 | 43 | 43 |
| WHERE-ORDER | 1 | 87 | 87 |
| agree | 854 | 19868 | 19868 |

### Classes by kind (FIX / FULL)

| Class | conf | eq-param | eq-app | chain | cond | assoc | blanket | twin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AMBIGUITY-MISSED | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 408 / 408 |
| BEYOND-SPEC | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 12 / 12 | 0 / 0 |
| BUDGET-agree | 0 / 0 | 1 / 1 | 1 / 1 | 0 / 0 | 15 / 15 | 0 / 0 | 0 / 0 | 0 / 0 |
| ILLFORMED-accept | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 6 / 6 | 0 / 0 |
| INCOMPLETE | 0 / 0 | 0 / 0 | 318 / 318 | 123 / 123 | 0 / 0 | 35 / 35 | 259 / 259 | 0 / 0 |
| MULTI-accept | 16 / 16 | 30 / 30 | 21 / 21 | 39 / 39 | 137 / 137 | 26 / 26 | 12 / 12 | 0 / 0 |
| MULTI-reject | 0 / 0 | 6 / 6 | 7 / 7 | 3 / 3 | 18 / 18 | 6 / 6 | 3 / 3 | 0 / 0 |
| TIMEOUT | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| UNSOUND | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 43 / 43 | 0 / 0 |
| WHERE-ORDER | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 62 / 62 | 25 / 25 | 0 / 0 |
| agree | 2984 / 2984 | 3263 / 3263 | 2953 / 2953 | 2535 / 2535 | 2830 / 2830 | 3771 / 3771 | 1140 / 1140 | 392 / 392 |

### Goals with exactly one derivation: accepted / total, by size of the smallest derivation

| Conformance steps | Equalities needed | Congruence needed | base | FIX | FULL |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | no | 9 / 10 | 591 / 670 | 591 / 670 |
| 0 | 1 | no | 3 / 3 | 196 / 200 | 196 / 200 |
| 0 | 1 | yes | 10 / 21 | 2640 / 2888 | 2640 / 2888 |
| 0 | 2 | no | 3 / 3 | 126 / 126 | 126 / 126 |
| 0 | 2 | yes | 7 / 9 | 850 / 977 | 850 / 977 |
| 0 | ≥3 | no | 2 / 2 | 59 / 59 | 59 / 59 |
| 0 | ≥3 | yes | 2 / 2 | 224 / 255 | 224 / 255 |
| 1 | 0 | no | 301 / 301 | 1984 / 2005 | 1984 / 2005 |
| 1 | 1 | no | 5 / 6 | 527 / 563 | 527 / 563 |
| 1 | 1 | yes | 3 / 3 | 251 / 254 | 251 / 254 |
| 1 | 2 | no | 1 / 1 | 175 / 183 | 175 / 183 |
| 1 | 2 | yes |  | 52 / 79 | 52 / 79 |
| 1 | ≥3 | no | 1 / 1 | 28 / 28 | 28 / 28 |
| 1 | ≥3 | yes |  | 9 / 16 | 9 / 16 |
| 2 | 0 | no | 55 / 57 | 563 / 619 | 563 / 619 |
| 2 | 1 | no | 4 / 4 | 485 / 527 | 485 / 527 |
| 2 | 1 | yes |  | 18 / 18 | 18 / 18 |
| 2 | 2 | no | 1 / 1 | 108 / 117 | 108 / 117 |
| 2 | 2 | yes |  | 2 / 5 | 2 / 5 |
| 2 | ≥3 | no | 1 / 1 | 12 / 16 | 12 / 16 |
| 2 | ≥3 | yes |  | 0 / 5 | 0 / 5 |
| ≥3 | 0 | no | 8 / 8 | 133 / 144 | 133 / 144 |
| ≥3 | 1 | no | 1 / 1 | 92 / 102 | 92 / 102 |
| ≥3 | 1 | yes |  | 3 / 3 | 3 / 3 |
| ≥3 | 2 | no |  | 22 / 23 | 22 / 23 |
| ≥3 | 2 | yes |  | 0 / 2 | 0 / 2 |
| ≥3 | ≥3 | no |  | 3 / 3 | 3 / 3 |
| ≥3 | ≥3 | yes |  | 0 / 1 | 0 / 1 |

### Predicted cause of rejection (explain.py) against the verdict, goals with one derivation

| Predicted cause | FIX accepted | FIX rejected | FULL accepted | FULL rejected |
|---|---:|---:|---:|---:|
| none (predicted: accepted) | 8993 | 2 | 8993 | 2 |
| BLANKET | 157 | 256 | 157 | 256 |
| BLANKET+DECOMP | 3 | 2 | 3 | 2 |
| BLANKET+PREFILTER | 0 | 2 | 0 | 2 |
| DECL-HEAD | 0 | 30 | 0 | 30 |
| DECL-HEAD+DECOMP | 0 | 2 | 0 | 2 |
| DECOMP | 0 | 346 | 0 | 346 |
| PREFILTER | 0 | 95 | 0 | 95 |

### FIX against FULL, and base against FIX

| FIX verdict | FULL verdict | Queries |
|---|---:|---:|
| accept | accept | 9903 |
| reject | reject | 11597 |

| Reference | base verdict | FIX verdict | Queries |
|---|---:|---:|---:|
| derivable (one) | accept | accept | 417 |
| derivable (one) | reject | accept | 9 |
| derivable (one) | reject | reject | 9 |
| derivable (one) | timeout | accept | 2 |
| derivable (one) | timeout | reject | 2 |
| derivable (several) | accept | accept | 18 |
| derivable (several) | accept | reject | 1 |
| derivable (several) | reject | accept | 1 |
| derivable (several) | reject | reject | 7 |
| illformed-goal | reject | reject | 6 |
| underivable | accept | accept | 1 |
| underivable | accept | reject | 3 |
| underivable | reject | reject | 424 |
| underivable | timeout | reject | 20 |

### Batch runs confirmed alone

525 (problem, configuration) pairs with a disagreement in a batch were rerun alone; 525 gave the same verdicts for every query.

