## Summary: growth of the primary counter / of the time

| Family | base | FIX | MIN5 | FULL |
|---|---|---|---|---|
| eqchain | n^3 exact / n^1.8 † | n^1 exact / undecided | n^3 exact / n^1.5 † | n^1 exact / undecided |
| eqchain-neg | n^3 exact / n^1.5 † ✗ | n^1 exact / undecided | n^3 exact / undecided † ✗ | n^1 exact / <20 ms |
| eqchain-goals | undecided / n^3.2 † | n^1 exact / undecided | undecided / undecided † | n^1 exact / undecided |
| assoceq | n^3 exact / undecided † | n^2 exact / undecided † | n^3 exact / undecided † | n^2 exact / n^2.0 † |
| assocneg | n^1.8 / n^1.8 † ✗ | n^2 exact / n^2.1 † | n^1.8 / n^1.9 † ✗ | n^2 exact / n^2.0 † |
| breadth-traits | n^1 exact / n^2.0 | n^1 exact / undecided | flat / n^1.2 | flat / n^0.7 |
| breadth-types | n^1 exact / n^2.2 | n^1 exact / n^2.6 | n^1 exact / n^1.0 | n^1 exact / n^1.3 |
| breadth-square | n^3 exact / undecided | n^3 exact / n^3.8 | n^2 exact / n^1.7 | n^2 exact / n^1.8 |
| div-branch | too few / too few † | too few / too few | – / – | – / – |

† the series ends with a timeout (or was stopped because a timeout was predicted); ‡ it ends with a crash; ✗ at some size the verdict differs from the intended one.

## Tables per family

### eqchain

Valid: conformance and associated type transported along n equality links. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 659 | 43.3 | 221 | 8.6 | 363 | 3.0 | 221 | 2.3 |
| 2 | 2,300 | 55.1 | 224 | 7.0 | 2,000 | 17.7 | 224 | 4.0 |
| 3 | 29,801 | 528 | 227 | 8.5 | 29,497 | 449 | 227 | 3.2 |
| 4 | 35,232 | 678 | 230 | 13.1 | 34,924 | 583 | 230 | 2.5 |
| 5 | 41,123 | 897 | 233 | 10.3 | 40,811 | 834 | 233 | 2.5 |
| 6 | 47,486 | 996 | 236 | 7.0 | 47,170 | 771 | 236 | 4.0 |
| 8 | 61,676 | 1,426 | 242 | 7.1 | 61,352 | 1,252 | 242 | 4.1 |
| 12 | 96,248 | 2,415 | 254 | 22.9 | 95,908 | 1,962 | 254 | 8.5 |
| 16 | 139,716 | 3,857 | 266 | 10.1 | 139,360 | 2,681 | 266 | 4.4 |
| 24 | 256,412 | 7,512 | 290 | 12.3 | 256,024 | 5,267 | 290 | 3.8 |
| 32 | 417,908 | 13,492 | 314 | 15.0 | 417,488 | 8,094 | 314 | 5.3 |
| 64 | not run |  | 410 | 13.9 | timeout | >20 s | 410 | 17.1 |
| 128 | not run |  | 602 | 21.1 | not run |  | 602 | 22.5 |
| 256 | not run |  | 986 | 41.8 | not run |  | 986 | 26.9 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2n^3 + 206n^2 + 3,915n + 16,148 (exact, n ≥ 3) | n^1.80 for n ≥ 3 (rms 0.04) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984) | – | stopped before n=64: predicted timeout: 13 s at n=32, power-law extrapolation gives 55 s at n=64 |
| FIX | 3n + 218 (exact) | undecided: n^1.5 (rms 0.10) or 1.01^n (rms 0.12) | n^0.44 (R² 0.956) / 1.01^n (R² 0.969) | – | completed |
| MIN5 | 2n^3 + 206n^2 + 3,911n + 15,856 (exact, n ≥ 3) | n^1.50 for n ≥ 3 (rms 0.07) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984) | – | timeout (>20 s) at n=64 |
| FULL | 3n + 218 (exact) | undecided: n^0.9 (rms 0.33) or 1.01^n (rms 0.49) | n^0.44 (R² 0.956) / 1.01^n (R² 0.969) | – | completed |

### eqchain-neg

Ill-typed: the chain of n links has its middle link missing, so T{n} is not P. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 143 | 29.8 | 143 | 10.1 | 3 | 3.1 | 1 | 4.3 |
| 2 | 145 | 56.6 | 145 | 11.9 | 145 | 3.0 | 145 | 5.3 |
| 3 | 45,728 (accepted!) | 993 | 149 | 12.7 | 45,728 (accepted!) | 620 | 149 | 4.8 |
| 4 | 57,443 (accepted!) | 976 | 151 | 12.8 | 57,443 (accepted!) | 822 | 151 | 4.5 |
| 5 | 17,426 (accepted!) | 340 | 153 | 17.8 | 17,426 (accepted!) | 237 | 153 | 4.7 |
| 6 | 20,369 (accepted!) | 365 | 155 | 10.6 | 20,369 (accepted!) | 234 | 155 | 4.5 |
| 8 | 26,969 (accepted!) | 712 | 159 | 17.4 | 26,969 (accepted!) | 493 | 159 | 6.1 |
| 12 | 43,193 (accepted!) | 1,228 | 167 | 14.0 | 43,193 (accepted!) | 621 | 167 | 4.5 |
| 16 | 63,769 (accepted!) | 1,649 | 175 | 14.7 | 63,769 (accepted!) | 998 | 175 | 5.7 |
| 24 | 119,513 (accepted!) | 2,722 | 191 | 17.4 | 119,513 (accepted!) | 2,334 | 191 | 6.3 |
| 32 | 197,273 (accepted!) | 5,482 | 207 | 16.2 | 197,273 (accepted!) | 4,121 | 207 | 5.0 |
| 64 | timeout | >20 s | 271 | 18.3 | timeout | >20 s | 271 | 7.6 |
| 128 | not run |  | 399 | 21.8 | not run |  | 399 | 11.2 |
| 256 | not run |  | 655 | 33.1 | not run |  | 655 | 14.8 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | n^1.50 for n ≥ 5 (rms 0.11) | n^1.36 (R² 0.991) / 1.09^n (R² 0.982) | – | timeout (>20 s) at n=64; verdict differs from the intended one at n=3..32 |
| FIX | 2n + 143 (exact, n ≥ 3) | undecided: n^1.4 (rms 0.07) or 1.01^n (rms 0.08) | n^0.44 (R² 0.956) / 1.01^n (R² 0.968) | – | completed |
| MIN5 | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | undecided: n^2.7 (rms 0.05) or 1.10^n (rms 0.08) | n^1.36 (R² 0.991) / 1.09^n (R² 0.982) | – | timeout (>20 s) at n=64; verdict differs from the intended one at n=3..32 |
| FULL | 2n + 143 (exact, n ≥ 3) | below 20 ms throughout (undecided: n^1.0 (rms 0.11) or 1.01^n (rms 0.17)) | n^0.44 (R² 0.956) / 1.01^n (R² 0.968) | – | completed |

### eqchain-goals

Valid: a chain of n links and n equality goals T0 == Ti, one per link. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72 | 13.7 | 2 | 5.6 | 72 | 1.1 | 2 | 0.8 |
| 2 | 951 | 67.0 | 4 | 4.6 | 951 | 11.7 | 4 | 1.6 |
| 3 | 15,485 | 196 | 6 | 6.2 | 15,485 | 442 | 6 | 1.1 |
| 4 | 35,677 | 682 | 8 | 8.0 | 35,677 | 868 | 8 | 1.4 |
| 5 | 61,925 | 1,376 | 10 | 7.1 | 61,925 | 2,110 | 10 | 2.0 |
| 6 | 94,937 | 2,486 | 12 | 24.2 | 94,937 | 2,427 | 12 | 1.7 |
| 8 | 184,205 | 7,361 | 16 | 17.6 | 184,205 | 4,434 | 16 | 2.3 |
| 12 | 477,725 | 16,491 | 24 | 10.5 | 477,725 | 12,831 | 24 | 11.8 |
| 16 | timeout | >20 s | 32 | 28.2 | timeout | >20 s | 32 | 17.2 |
| 24 | not run |  | 48 | 39.8 | not run |  | 48 | 9.7 |
| 32 | not run |  | 64 | 33.5 | not run |  | 64 | 14.3 |
| 64 | not run |  | 128 | 64.7 | not run |  | 128 | 41.6 |
| 128 | not run |  | 256 | 413 | not run |  | 256 | 356 |
| 256 | not run |  | 512 | 1,591 | not run |  | 512 | 730 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | undecided: n^3.6 (rms 0.66) or 2.17^n (rms 2.58) | n^3.25 (rms 0.17) | n^2.33 (R² 1.000) / 1.33^n (R² 0.986) | `coerced.slowPath`: n (exact) | timeout (>20 s) at n=16 |
| FIX | 2n (exact) | undecided: n^1.6 (rms 0.47) or 1.03^n (rms 0.86) | n^1.00 (R² 1.000) / 1.01^n (R² 0.863) | – | completed |
| MIN5 | undecided: n^3.6 (rms 0.66) or 2.17^n (rms 2.58) | undecided: n^3.9 (rms 0.95) or 2.29^n (rms 2.87) | n^2.33 (R² 1.000) / 1.33^n (R² 0.986) | `coerced.slowPath`: n (exact) | timeout (>20 s) at n=16 |
| FULL | 2n (exact) | undecided: n^1.7 (rms 0.48) or 1.03^n (rms 1.28) | n^1.00 (R² 1.000) / 1.01^n (R² 0.863) | – | completed |

### assoceq

Valid: n equalities T{i}.X == T{i+1}.X; goal T0.X == T{n}.X. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,110 | 57.3 | 293 | 21.1 | 810 | 27.1 | 293 | 10.3 |
| 2 | 4,423 | 236 | 447 | 23.3 | 4,115 | 118 | 447 | 18.5 |
| 3 | 60,438 | 1,679 | 607 | 49.4 | 60,122 | 1,038 | 607 | 29.8 |
| 4 | 75,042 | 1,800 | 773 | 42.5 | 74,718 | 1,068 | 773 | 46.5 |
| 5 | 91,512 | 2,463 | 945 | 83.1 | 91,180 | 1,662 | 945 | 60.2 |
| 6 | 109,938 | 2,973 | 1,123 | 82.8 | 109,598 | 2,258 | 1,123 | 58.4 |
| 8 | 153,018 | 3,599 | 1,497 | 111 | 152,662 | 2,658 | 1,497 | 108 |
| 12 | 266,610 | 9,148 | 2,317 | 244 | 266,222 | 5,407 | 2,317 | 165 |
| 16 | 421,578 | 16,124 | 3,233 | 374 | 421,158 | 8,522 | 3,233 | 258 |
| 24 | timeout | >20 s | 5,353 | 515 | timeout | >20 s | 5,353 | 478 |
| 32 | not run |  | 7,857 | 868 | not run |  | 7,857 | 798 |
| 64 | not run |  | 21,713 | 4,764 | not run |  | 21,713 | 3,012 |
| 128 | not run |  | timeout | >20 s | not run |  | 67,857 | 15,085 |
| 256 | not run |  | not run |  | not run |  | not run |  |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 15n^3 + 753n^2 + 8,778n + 26,922 (exact, n ≥ 3) | undecided: n^2.5 (rms 0.07) or 1.20^n (rms 0.07) | n^1.31 (R² 0.995) / 1.15^n (R² 0.994) | – | timeout (>20 s) at n=24 |
| FIX | 3n^2 + 145n + 145 (exact) | undecided: n^2.7 (rms 0.08) or 1.06^n (rms 0.07) | n^1.29 (R² 0.996) / 1.05^n (R² 0.942) | – | timeout (>20 s) at n=128 |
| MIN5 | 15n^3 + 753n^2 + 8,770n + 26,630 (exact, n ≥ 3) | undecided: n^1.8 (rms 0.09) or 1.18^n (rms 0.13) | n^1.32 (R² 0.995) / 1.15^n (R² 0.994) | – | timeout (>20 s) at n=24 |
| FULL | 3n^2 + 145n + 145 (exact) | n^2.00 for n ≥ 4 (rms 0.10) | n^1.38 (R² 0.994) / 1.03^n (R² 0.918) | – | stopped before n=256: predicted timeout: 15 s at n=128, power-law extrapolation gives 76 s at n=256 |

### assocneg

Ill-typed: like assoceq with the middle equality missing. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 441 | 41.5 | 145 | 7.6 | 5 | 1.1 | 5 | 2.0 |
| 2 | 899 | 43.9 | 295 | 18.0 | 595 | 31.1 | 295 | 22.2 |
| 3 | 47,781 (accepted!) | 954 | 452 | 29.1 | 47,469 (accepted!) | 862 | 452 | 26.8 |
| 4 | 60,817 (accepted!) | 1,384 | 614 | 42.7 | 60,497 (accepted!) | 1,199 | 614 | 42.1 |
| 5 | 75,969 (accepted!) | 1,421 | 782 | 43.9 | 75,641 (accepted!) | 1,420 | 782 | 56.6 |
| 6 | 92,611 (accepted!) | 2,371 | 956 | 127 | 92,275 (accepted!) | 1,845 | 956 | 99.7 |
| 8 | 131,895 (accepted!) | 3,224 | 1,322 | 124 | 131,543 (accepted!) | 3,142 | 1,322 | 96.0 |
| 12 | 236,983 (accepted!) | 6,904 | 2,126 | 181 | 236,599 (accepted!) | 5,732 | 2,126 | 291 |
| 16 | 382,231 (accepted!) | 9,290 | 3,026 | 237 | 381,815 (accepted!) | 9,106 | 3,026 | 376 |
| 24 | timeout | >20 s | 5,114 | 692 | timeout | >20 s | 5,114 | 690 |
| 32 | not run |  | 7,586 | 915 | not run |  | 7,586 | 1,155 |
| 64 | not run |  | 21,314 | 4,058 | not run |  | 21,314 | 4,177 |
| 128 | not run |  | timeout | >20 s | not run |  | 67,202 | 16,597 |
| 256 | not run |  | not run |  | not run |  | not run |  |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^1.75 for n ≥ 3 (rms 0.01) | n^1.75 for n ≥ 3 (rms 0.09) | n^1.39 (R² 0.995) / 1.16^n (R² 0.993) | – | timeout (>20 s) at n=24; verdict differs from the intended one at n=3..16 |
| FIX | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.15 for n ≥ 8 (rms 0.11) | n^1.34 (R² 0.997) / 1.05^n (R² 0.936) | – | timeout (>20 s) at n=128 |
| MIN5 | n^1.75 for n ≥ 3 (rms 0.01) | n^1.85 for n ≥ 3 (rms 0.04) | n^1.39 (R² 0.995) / 1.16^n (R² 0.993) | – | timeout (>20 s) at n=24; verdict differs from the intended one at n=3..16 |
| FULL | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.05 for n ≥ 12 (rms 0.02) | n^1.42 (R² 0.996) / 1.03^n (R² 0.912) | – | stopped before n=256: predicted timeout: 17 s at n=128, power-law extrapolation gives 66 s at n=256 |

### breadth-traits

Valid: n conformances A{i} is P{i} (n traits, n types) and one lookup. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 79 | 19.6 | 79 | 18.1 | 2 | 0.8 | 2 | 1.8 |
| 16 | 87 | 37.7 | 87 | 7.6 | 2 | 1.0 | 2 | 2.5 |
| 32 | 103 | 18.2 | 103 | 9.6 | 2 | 1.9 | 2 | 3.9 |
| 64 | 135 | 30.6 | 135 | 18.4 | 2 | 2.3 | 2 | 9.5 |
| 128 | 199 | 38.3 | 199 | 39.3 | 2 | 9.1 | 2 | 7.9 |
| 256 | 327 | 208 | 327 | 217 | 2 | 9.3 | 2 | 18.1 |
| 512 | 583 | 352 | 583 | 302 | 2 | 30.9 | 2 | 24.4 |
| 1024 | 1,095 | 1,805 | 1,095 | 2,022 | 2 | 61.6 | 2 | 41.7 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n + 71 (exact) | n^2.00 (rms 0.31) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| FIX | n + 71 (exact) | undecided: n^2.0 (rms 0.38) or 1.01^n (rms 1.47) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| MIN5 | flat | n^1.15 (rms 0.23) | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `index.skipped`: n + 66 (exact) | completed |
| FULL | flat | n^0.65 (rms 0.18) | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `absmodel.facts`: n + 63 (exact) | completed |

### breadth-types

Valid: n conformances A{i} is P (one trait, n types) and one lookup. Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 79 | 71.9 | 79 | 11.5 | 9 | 0.7 | 9 | 1.9 |
| 16 | 87 | 32.9 | 87 | 14.8 | 17 | 0.9 | 17 | 2.4 |
| 32 | 103 | 18.9 | 103 | 11.2 | 33 | 1.3 | 33 | 2.2 |
| 64 | 135 | 27.7 | 135 | 31.5 | 65 | 2.9 | 65 | 3.9 |
| 128 | 199 | 36.0 | 199 | 38.5 | 129 | 6.2 | 129 | 10.9 |
| 256 | 327 | 104 | 327 | 76.3 | 257 | 7.7 | 257 | 11.7 |
| 512 | 583 | 378 | 583 | 369 | 513 | 15.7 | 513 | 62.8 |
| 1024 | 1,095 | 1,992 | 1,095 | 1,862 | 1,025 | 43.5 | 1,025 | 69.4 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n + 71 (exact) | n^2.25 for n ≥ 32 (rms 0.09) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| FIX | n + 71 (exact) | n^2.60 for n ≥ 64 (rms 0.05) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| MIN5 | n + 1 (exact) | n^1.00 (rms 0.16) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |
| FULL | n + 1 (exact) | n^1.25 (rms 0.30) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |

### breadth-square

Valid: n traits x n types = n*n conformances and n lookups (the shape of breadth40). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 348 | 39.1 | 348 | 30.1 | 20 | 0.9 | 20 | 2.7 |
| 6 | 642 | 32.9 | 642 | 20.6 | 42 | 1.7 | 42 | 3.1 |
| 8 | 1,080 | 63.4 | 1,080 | 44.5 | 72 | 4.2 | 72 | 4.1 |
| 12 | 2,580 | 146 | 2,580 | 64.0 | 156 | 5.6 | 156 | 6.4 |
| 16 | 5,232 | 342 | 5,232 | 311 | 272 | 7.4 | 272 | 20.2 |
| 24 | 15,528 | 965 | 15,528 | 907 | 600 | 24.0 | 600 | 35.7 |
| 32 | 35,040 | 2,437 | 35,040 | 2,228 | 1,056 | 27.1 | 1,056 | 53.7 |
| 40 | 66,840 | 6,537 | 66,840 | 5,668 | 1,640 | 53.3 | 1,640 | 58.1 |
| 48 | 114,000 | 14,921 | 114,000 | 11,618 | 2,352 | 50.5 | 2,352 | 79.7 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^3 + 71n (exact) | undecided: n^3.9 (rms 0.12) or 1.14^n (rms 0.14) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980) | – | completed |
| FIX | n^3 + 71n (exact) | n^3.75 (rms 0.23) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980) | – | completed |
| MIN5 | n^2 + n (exact) | n^1.65 (rms 0.20) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975) | `index.skipped`: n^3 − n^2 + 67n (exact) | completed |
| FULL | n^2 + n (exact) | n^1.80 (rms 0.23) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975) | `index.skipped`: n^3 − n^2 + 67n (exact) | completed |

### div-branch

Ill-typed: Yb is P is underivable; b givens `S_j<T> is P => T is P` make the search grow. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,350 | 29.2 | 1,350 | 15.6 |  |  |  |  |
| 2 | 110,449 | 1,400 | 110,449 | 1,909 |  |  |  |  |
| 3 | timeout | >20 s | 159,579 | 3,362 |  |  |  |  |
| 4 | not run |  |  |  |  |  |  |  |
| 5 | not run |  |  |  |  |  |  |  |
| 6 | not run |  |  |  |  |  |  |  |
| 8 | not run |  |  |  |  |  |  |  |
| 12 | not run |  |  |  |  |  |  |  |
| 16 | not run |  |  |  |  |  |  |  |
| 32 | not run |  |  |  |  |  |  |  |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.81^n (R² 1.000) | – | timeout (>20 s) at n=3 |
| FIX | too few points (3) | too few points (3) | n^4.56 (R² 0.910) / 10.87^n (R² 0.807) | – | completed |
| MIN5 | – | – | – | – | completed |
| FULL | – | – | – | – | completed |

