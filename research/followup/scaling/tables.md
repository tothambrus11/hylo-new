## Summary: growth of the primary counter / of the time

| Family | base | FIX | MIN5 | FULL |
|---|---|---|---|---|
| eqchain | n^3 exact / n^1.8 † | n^1 exact / <50 ms | n^3 exact / n^1.5 † | n^1 exact / <50 ms |
| eqchain-neg | n^3 exact / n^1.5 † ✗ | n^1 exact / <50 ms | n^3 exact / undecided † ✗ | n^1 exact / <50 ms |
| eqchain-goals | n^2.4 / n^3.3 † | n^1 exact / n^2.6 | n^2.4 / n^2.4 † | n^1 exact / n^2.1 |
| assoceq | n^3 exact / undecided † | n^2 exact / undecided † | n^3 exact / undecided † | n^2 exact / n^2.0 † |
| assocneg | n^1.7 / n^1.7 † ✗ | n^2 exact / n^2.2 † | n^1.7 / n^1.8 † ✗ | n^2 exact / n^2.0 † |
| breadth-traits | n^1 exact / n^1.9 | n^1 exact / n^1.8 | flat / n^1.2 | flat / <50 ms |
| breadth-types | n^1 exact / n^2.3 | n^1 exact / n^2.6 | n^1 exact / <50 ms | n^1 exact / n^1.3 |
| breadth-square | n^3 exact / undecided | n^3 exact / n^3.6 | n^2 exact / undecided | n^2 exact / n^1.7 |
| div-branch | too few / too few † | undecided / undecided † [B] | too few / too few † | flat / <50 ms |
| div-branch-eq | too few / too few † | undecided / undecided † [B] | too few / too few † | flat / <50 ms |
| div-trunc | too few / too few † | undecided / undecided † [B] | too few / too few † | too few / too few † [B] |
| div-depth | 2.0^n / undecided † | undecided / undecided [B] | 2.0^n / undecided † | flat / <50 ms |
| div-valid | 2.0^n / undecided | 2.0^n / undecided | 2.0^n / undecided | 2.0^n / undecided |
| cyc-ring | n^1 exact / undecided | n^1 exact / undecided | n^1 exact / <50 ms | flat / <50 ms |
| cyc-clique | too few / too few † | too few / too few † | too few / too few † | flat / <50 ms |
| members-ext | n^1 exact / undecided | flat / n^0.3 | flat / n^0.6 | flat / n^0.9 |
| members-use | n^1 exact / n^1.3 | n^1 exact / undecided | n^1 exact / n^0.9 | n^1 exact / n^0.8 |
| members-both | n^2 exact / n^1.4 | n^1 exact / n^1.5 | n^1 exact / n^2.0 | n^1 exact / n^1.8 |
| condext | n^1 exact / n^2.2 | flat / n^1.1 | flat / <50 ms | flat / <50 ms |
| ovl-calls | undecided / undecided † | n^6.9 / undecided | n^6.9 / n^7.2 | n^6.9 / n^6.8 |
| ovl-width | n^2 exact / undecided | n^2 exact / undecided | n^2 exact / <50 ms | n^2 exact / <50 ms |
| ovl-stmts | n^1 exact / n^0.6 | n^1 exact / undecided | n^1 exact / <50 ms | n^1 exact / <50 ms |
| ovr-args | 3.0^n / undecided † | 3.0^n / undecided | – / – | – / – |

† the series ends with a timeout (or was stopped because a timeout was predicted); ‡ it ends with a crash; ✗ at some size the verdict differs from the intended one; [B] the resource bound of `budget` stopped a resolution, so the count is capped.

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
| base | 2n^3 + 206n^2 + 3,915n + 16,148 (exact, n ≥ 3) | n^1.79 for n ≥ 3 (rms 0.04) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984) | – | stopped before n=64: predicted timeout: 13 s at n=32, power-law extrapolation gives 55 s at n=64 |
| FIX | 3n + 218 (exact) | below 50 ms throughout | n^0.44 (R² 0.956) / 1.01^n (R² 0.969) | – | completed |
| MIN5 | 2n^3 + 206n^2 + 3,911n + 15,856 (exact, n ≥ 3) | n^1.51 for n ≥ 3 (rms 0.07) | n^1.30 (R² 0.989) / 1.09^n (R² 0.984) | – | timeout (>20 s) at n=64 |
| FULL | 3n + 218 (exact) | below 50 ms throughout | n^0.44 (R² 0.956) / 1.01^n (R² 0.969) | – | completed |

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
| base | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | n^1.49 for n ≥ 5 (rms 0.11) | n^1.36 (R² 0.991) / 1.09^n (R² 0.982) | – | timeout (>20 s) at n=64; verdict differs from the intended one at n=3..32 |
| FIX | 2n + 143 (exact, n ≥ 3) | below 50 ms throughout | n^0.44 (R² 0.956) / 1.01^n (R² 0.968) | – | completed |
| MIN5 | n^3 + 100n^2 + 1,752n + 6,041 (exact, n ≥ 5) | undecided: n^2.7 (rms 0.05) or 1.10^n (rms 0.08) | n^1.36 (R² 0.991) / 1.09^n (R² 0.982) | – | timeout (>20 s) at n=64; verdict differs from the intended one at n=3..32 |
| FULL | 2n + 143 (exact, n ≥ 3) | below 50 ms throughout | n^0.44 (R² 0.956) / 1.01^n (R² 0.968) | – | completed |

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
| base | n^2.44 for n ≥ 3 (rms 0.05) | n^3.25 (rms 0.17) | n^2.33 (R² 1.000) / 1.33^n (R² 0.986) | – | timeout (>20 s) at n=16 |
| FIX | 2n (exact) | n^2.57 for n ≥ 16 (rms 0.17) | n^1.00 (R² 1.000) / 1.01^n (R² 0.863) | – | completed |
| MIN5 | n^2.44 for n ≥ 3 (rms 0.05) | n^2.38 for n ≥ 3 (rms 0.13) | n^2.33 (R² 1.000) / 1.33^n (R² 0.986) | – | timeout (>20 s) at n=16 |
| FULL | 2n (exact) | n^2.06 for n ≥ 24 (rms 0.29) | n^1.00 (R² 1.000) / 1.01^n (R² 0.863) | – | completed |

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
| FULL | 3n^2 + 145n + 145 (exact) | n^1.99 for n ≥ 4 (rms 0.10) | n^1.38 (R² 0.994) / 1.03^n (R² 0.918) | – | stopped before n=256: predicted timeout: 15 s at n=128, power-law extrapolation gives 76 s at n=256 |

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
| base | n^1.75 for n ≥ 3 (rms 0.01) | n^1.73 for n ≥ 3 (rms 0.09) | n^1.39 (R² 0.995) / 1.16^n (R² 0.993) | – | timeout (>20 s) at n=24; verdict differs from the intended one at n=3..16 |
| FIX | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.17 for n ≥ 8 (rms 0.11) | n^1.34 (R² 0.997) / 1.05^n (R² 0.936) | – | timeout (>20 s) at n=128 |
| MIN5 | n^1.75 for n ≥ 3 (rms 0.01) | n^1.83 for n ≥ 3 (rms 0.04) | n^1.39 (R² 0.995) / 1.16^n (R² 0.993) | – | timeout (>20 s) at n=24; verdict differs from the intended one at n=3..16 |
| FULL | 3n^2 + 141n + 2 (exact, n ≥ 3) | n^2.04 for n ≥ 12 (rms 0.02) | n^1.42 (R² 0.996) / 1.03^n (R² 0.912) | – | stopped before n=256: predicted timeout: 17 s at n=128, power-law extrapolation gives 66 s at n=256 |

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
| base | n + 71 (exact) | n^1.87 for n ≥ 32 (rms 0.26) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| FIX | n + 71 (exact) | n^1.80 for n ≥ 16 (rms 0.28) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| MIN5 | flat | n^1.17 (rms 0.23) | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `index.skipped`: n + 66 (exact) | completed |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `absmodel.facts`: n + 63 (exact) | completed |

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
| base | n + 71 (exact) | n^2.27 for n ≥ 32 (rms 0.09) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| FIX | n + 71 (exact) | n^2.60 for n ≥ 64 (rms 0.05) | n^0.82 (R² 0.997) / 1.00^n (R² 0.945) | – | completed |
| MIN5 | n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |
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
| base | n^3 + 71n (exact) | undecided: n^3.9 (rms 0.12) or 1.13^n (rms 0.14) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980) | – | completed |
| FIX | n^3 + 71n (exact) | n^3.56 for n ≥ 12 (rms 0.18) | n^2.81 (R² 1.000) / 1.10^n (R² 0.980) | – | completed |
| MIN5 | n^2 + n (exact) | undecided: n^1.7 (rms 0.19) or 1.07^n (rms 0.30) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975) | `index.skipped`: n^3 − n^2 + 67n (exact) | completed |
| FULL | n^2 + n (exact) | n^1.66 for n ≥ 6 (rms 0.22) | n^1.96 (R² 1.000) / 1.07^n (R² 0.975) | `index.skipped`: n^3 − n^2 + 67n (exact) | completed |

### div-branch

Ill-typed: Yb is P is underivable; b givens `S_j<T> is P => T is P` make the search grow. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,350 | 29.2 | 1,350 | 15.6 | 20 | 2.8 | 1 | 2.4 |
| 2 | 110,449 | 1,400 | 110,449 | 1,909 | 3,069 | 207 | 1 | 6.4 |
| 3 | timeout | >20 s | 159,579 [B] | 3,362 | 118,096 | 10,239 | 1 | 2.4 |
| 4 | not run |  | 202,021 [B] | 6,422 | not run |  | 1 | 2.5 |
| 5 | not run |  | 117,151 [B] | 4,309 | not run |  | 1 | 5.4 |
| 6 | not run |  | 236,361 [B] | 9,622 | not run |  | 1 | 4.0 |
| 8 | not run |  | 91,261 [B] | 5,332 | not run |  | 1 | 2.9 |
| 12 | not run |  | 25,749 [B] | 2,353 | not run |  | 1 | 3.2 |
| 16 | not run |  | 46,957 [B] | 5,730 | not run |  | 1 | 7.7 |
| 32 | not run |  | not run |  | not run |  | 1 | 4.3 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.81^n (R² 1.000) | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^12.0 (rms 1.07) or 2.36^n (rms 1.07) | undecided: no polynomial or 40.00^n (rms 0.49) | n^-1.42 (R² 0.644) / 0.87^n (R² 0.597) | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=32: predicted timeout: 6 s at n=16, power-law extrapolation gives 49 s at n=32; resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (3) | too few points (3) | n^7.83 (R² 0.997) / 76.84^n (R² 0.992) | – | stopped before n=4: predicted timeout: 10 s at n=3, power-law extrapolation gives 163 s at n=4 |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `solver.goalSteps`: 6n + 6 (exact) | completed |

### div-branch-eq

Ill-typed: div_branch with an unrelated equality A == B in scope. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,369 | 67.5 | 1,369 | 28.2 | 1,369 | 16.1 | 1 | 4.2 |
| 2 | 111,983 | 1,954 | 111,983 | 2,008 | 111,983 | 1,472 | 1 | 5.0 |
| 3 | timeout | >20 s | 161,765 [B] | 4,458 | timeout | >20 s | 1 | 7.8 |
| 4 | not run |  | 204,751 [B] | 7,567 | not run |  | 1 | 3.7 |
| 5 | not run |  | 118,713 [B] | 5,319 | not run |  | 1 | 8.5 |
| 6 | not run |  | 239,471 [B] | 11,422 | not run |  | 1 | 4.5 |
| 8 | not run |  | 92,431 [B] | 6,522 | not run |  | 1 | 4.7 |
| 12 | not run |  | 26,063 [B] | 2,888 | not run |  | 1 | 4.8 |
| 16 | not run |  | 47,503 [B] | 6,871 | not run |  | 1 | 5.9 |
| 32 | not run |  | not run |  | not run |  | 1 | 10.1 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.80^n (R² 1.000) | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^12.0 (rms 1.07) or 2.36^n (rms 1.07) | undecided: no polynomial or 40.00^n (rms 0.47) | n^-1.42 (R² 0.644) / 0.87^n (R² 0.597) | `solver.goalSteps`: 6n + 6 (exact) | stopped before n=32: predicted timeout: 7 s at n=16, power-law extrapolation gives 55 s at n=32; resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (2) | too few points (2) | n^6.35 (R² 1.000) / 81.80^n (R² 1.000) | – | timeout (>20 s) at n=3 |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `solver.goalSteps`: 6n + 6 (exact) | completed |

### div-trunc

Ill-typed: div_branch with base facts S_j<S_j<Xi>> is P (deeper than the model's truncation). Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,369 | 30.4 | 1,369 | 35.6 | 39 | 1.4 | 39 | 7.0 |
| 2 | 113,517 | 2,047 | 113,517 | 2,369 | 6,137 | 231 | 6,137 | 293 |
| 3 | timeout | >20 s | 166,137 [B] | 4,586 | 236,191 | 12,397 | 118,093 [B] | 7,230 |
| 4 | not run |  | 212,941 [B] | 8,465 | not run |  | not run |  |
| 5 | not run |  | 124,961 [B] | 6,541 | not run |  | not run |  |
| 6 | not run |  | 42,477 [B] | 2,341 | not run |  | not run |  |
| 8 | not run |  | 100,621 [B] | 8,045 | not run |  | not run |  |
| 12 | not run |  | not run |  | not run |  | not run |  |
| 16 | not run |  | not run |  | not run |  | not run |  |
| 32 | not run |  | not run |  | not run |  | not run |  |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^6.37 (R² 1.000) / 82.92^n (R² 1.000) | – | timeout (>20 s) at n=3 |
| FIX | undecided: n^5.6 (rms 0.68) or 2.16^n (rms 0.68) | undecided: no polynomial or 40.00^n (rms 0.57) | n^-1.30 (R² 0.324) / 0.82^n (R² 0.242) | `solver.goalSteps`: 12n + 6 (exact) | stopped before n=12: predicted timeout: 8 s at n=8, power-law extrapolation gives 46 s at n=12; resource bound (`budget`) hit from n=3 |
| MIN5 | too few points (3) | too few points (3) | n^7.86 (R² 0.997) / 77.82^n (R² 0.991) | – | stopped before n=4: predicted timeout: 12 s at n=3, power-law extrapolation gives 209 s at n=4 |
| FULL | too few points (3) | too few points (3) | n^7.30 (R² 1.000) / 55.03^n (R² 0.978) | – | stopped before n=4: predicted timeout: 7 s at n=3, power-law extrapolation gives 70 s at n=4; resource bound (`budget`) hit from n=3 |

### div-depth

Ill-typed: div_branch with b = 2; the size is the depth bound HYLO_TC_MAXDEPTH = d (>= 5, below which the standard library fails). Intended verdict: rejected. Primary counter: `summon.matches`. Environment: `HYLO_TC_MAXDEPTH=n`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3,313 | 44.7 | 3,313 | 37.3 | 93 | 3.7 | 1 | 5.8 |
| 6 | 6,769 | 148 | 6,769 | 129 | 189 | 19.9 | 1 | 4.5 |
| 8 | 27,505 | 365 | 27,505 | 339 | 765 | 78.2 | 1 | 2.3 |
| 10 | 110,449 | 1,953 | 110,449 | 2,241 | 3,069 | 179 | 1 | 1.9 |
| 12 | 442,225 | 8,442 | 294,769 [B] | 5,115 | 12,285 | 1,405 | 1 | 2.0 |
| 14 | timeout | >20 s | 294,769 [B] | 5,758 | 49,149 | 4,208 | 1 | 22.4 |
| 16 | not run |  | 294,769 [B] | 5,599 | timeout | >20 s | 1 | 1.9 |
| 20 | not run |  | 294,769 [B] | 5,345 | not run |  | 1 | 6.2 |
| 24 | not run |  | 294,769 [B] | 5,346 | not run |  | 1 | 7.1 |
| 32 | not run |  | 294,769 [B] | 5,407 | not run |  | 1 | 2.0 |
| 40 | not run |  | 294,769 [B] | 5,506 | not run |  | 1 | 2.3 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.01^n (rms 0.01) | undecided: n^6.9 (rms 0.26) or 2.06^n (rms 0.19) | n^6.83 (R² 0.997) / 2.00^n (R² 1.000) | – | timeout (>20 s) at n=14 |
| FIX | undecided: n^0.4 (rms 0.31) or 1.02^n (rms 0.34) | undecided: n^0.4 (rms 0.27) or 1.02^n (rms 0.30) | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | – | completed; resource bound (`budget`) hit from n=12 |
| MIN5 | 2.01^n (rms 0.01) | undecided: n^6.7 (rms 0.43) or 2.12^n (rms 0.39) | n^8.22 (R² 0.998) / 2.00^n (R² 1.000) | – | timeout (>20 s) at n=16 |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | – | completed |

### div-valid

Valid: two growing givens; Xi is P holds through S1^d<Xi> is P (a derivation of depth d). Intended verdict: accepted. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 220 | 38.5 | 220 | 7.8 | 10 | 0.8 | 10 | 1.9 |
| 2 | 512 | 21.9 | 512 | 10.5 | 22 | 1.1 | 22 | 2.2 |
| 3 | 1,096 | 54.7 | 1,096 | 17.6 | 46 | 1.6 | 46 | 6.2 |
| 4 | 2,264 | 40.7 | 2,264 | 41.2 | 94 | 3.0 | 94 | 5.2 |
| 5 | 4,600 | 118 | 4,600 | 139 | 190 | 6.0 | 190 | 13.5 |
| 6 | 9,272 | 194 | 9,272 | 129 | 382 | 10.1 | 382 | 20.0 |
| 7 | 18,616 | 413 | 18,616 | 398 | 766 | 17.8 | 766 | 25.8 |
| 8 | 37,304 | 601 | 37,304 | 622 | 1,534 | 54.3 | 1,534 | 82.8 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2.04^n for n ≥ 2 (rms 0.02) | undecided: n^4.2 (rms 0.25) or 1.90^n (rms 0.25) | n^4.44 (R² 0.995) / 2.01^n (R² 1.000) | – | completed |
| FIX | 2.04^n for n ≥ 2 (rms 0.02) | undecided: n^4.1 (rms 0.21) or 2.05^n (rms 0.24) | n^4.44 (R² 0.995) / 2.01^n (R² 1.000) | – | completed |
| MIN5 | 2.03^n for n ≥ 2 (rms 0.01) | undecided: n^4.3 (rms 0.18) or 2.10^n (rms 0.11) | n^4.43 (R² 0.995) / 2.01^n (R² 1.000) | – | completed |
| FULL | 2.03^n for n ≥ 2 (rms 0.01) | undecided: n^3.5 (rms 0.29) or 1.83^n (rms 0.26) | n^4.43 (R² 0.995) / 2.01^n (R² 1.000) | – | completed |

### cyc-ring

Ill-typed: a ring of n givens A{i+1} is P => A{i} is P with no base case. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1,369 | 28.7 | 1,369 | 24.9 | 39 | 1.4 | 1 | 2.1 |
| 3 | 1,388 | 23.4 | 1,388 | 14.4 | 58 | 1.3 | 1 | 3.7 |
| 4 | 1,407 | 23.4 | 1,407 | 19.4 | 77 | 1.5 | 1 | 7.3 |
| 6 | 1,445 | 50.6 | 1,445 | 32.9 | 115 | 1.5 | 1 | 3.5 |
| 8 | 1,483 | 52.5 | 1,483 | 49.0 | 153 | 1.4 | 1 | 2.1 |
| 12 | 1,559 | 36.0 | 1,559 | 61.3 | 229 | 1.9 | 1 | 6.6 |
| 16 | 1,635 | 44.4 | 1,635 | 71.2 | 305 | 7.0 | 1 | 7.7 |
| 32 | 1,939 | 113 | 1,939 | 109 | 609 | 4.8 | 1 | 10.1 |
| 64 | 2,547 | 225 | 2,547 | 280 | 1,217 | 9.3 | 1 | 5.8 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 19n + 1,331 (exact) | undecided: n^1.9 (rms 0.20) or 1.03^n (rms 0.22) | n^0.26 (R² 0.960) / 1.01^n (R² 0.995) | – | completed |
| FIX | 19n + 1,331 (exact) | undecided: n^1.1 (rms 0.11) or 1.03^n (rms 0.15) | n^0.26 (R² 0.960) / 1.01^n (R² 0.995) | – | completed |
| MIN5 | 19n + 1 (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.930) | – | completed |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `solver.goalSteps`: 4n + 6 (exact) | completed |

### cyc-clique

Ill-typed: n types, A{j} is P => A{i} is P for every i != j (branching n - 1), no base case. Intended verdict: rejected. Primary counter: `summon.matches`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1,369 | 43.7 | 1,369 | 26.6 | 39 | 5.1 | 1 | 6.7 |
| 3 | 116,585 | 2,789 | 116,585 | 2,082 | 9,205 | 63.6 | 1 | 7.8 |
| 4 | not run |  | not run |  | 472,381 | 3,975 | 1 | 3.3 |
| 5 | not run |  | not run |  | not run |  | 1 | 4.3 |
| 6 | not run |  | not run |  | not run |  | 1 | 10.1 |
| 8 | not run |  | not run |  | not run |  | 1 | 7.0 |
| 12 | not run |  | not run |  | not run |  | 1 | 11.9 |
| 16 | not run |  | not run |  | not run |  | 1 | 30.9 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | too few points (2) | too few points (2) | n^10.96 (R² 1.000) / 85.16^n (R² 1.000) | – | stopped before n=4: predicted timeout: 3 s at n=3, power-law extrapolation gives 53 s at n=4 |
| FIX | too few points (2) | too few points (2) | n^10.96 (R² 1.000) / 85.16^n (R² 1.000) | – | stopped before n=4: predicted timeout: 2 s at n=3, power-law extrapolation gives 46 s at n=4 |
| MIN5 | too few points (3) | too few points (3) | n^13.56 (R² 1.000) / 110.06^n (R² 0.991) | – | stopped before n=5: predicted timeout: 4 s at n=4, power-law extrapolation gives 98 s at n=5 |
| FULL | flat | below 50 ms throughout | n^0.00 (R² 1.000) / 1.00^n (R² 1.000) | `solver.goalSteps`: 4n^2 − 4n + 6 (exact) | completed |

### members-ext

Valid: n extensions over n/10 types, 20 member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 960 | 146 | 20 | 42.5 | 20 | 11.0 | 20 | 4.3 |
| 40 | 1,760 | 166 | 20 | 13.2 | 20 | 3.3 | 20 | 7.4 |
| 80 | 3,360 | 262 | 20 | 55.5 | 20 | 13.8 | 20 | 6.4 |
| 160 | 6,560 | 185 | 20 | 69.8 | 20 | 17.0 | 20 | 13.6 |
| 320 | 12,960 | 241 | 20 | 107 | 20 | 22.0 | 20 | 19.6 |
| 640 | 25,760 | 356 | 20 | 85.2 | 20 | 68.4 | 20 | 41.1 |
| 1280 | 51,360 | 423 | 20 | 129 | 20 | 52.8 | 20 | 73.0 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 40n + 160 (exact) | undecided: n^1.3 (rms 0.15) or 1.01^n (rms 0.22) | n^0.99 (R² 1.000) / 1.00^n (R² 0.922) | – | completed |
| FIX | flat | n^0.27 for n ≥ 80 (rms 0.14) | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | – | completed |
| MIN5 | flat | n^0.63 for n ≥ 80 (rms 0.28) | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | `memberskip.skipped`: 40n + 140 (exact) | completed |
| FULL | flat | n^0.86 for n ≥ 80 (rms 0.08) | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | – | completed |

### members-use

Valid: 100 extensions over 10 types, m member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 2,080 | 171 | 10 | 50.9 | 10 | 8.4 | 10 | 4.9 |
| 20 | 4,160 | 235 | 20 | 25.2 | 20 | 14.3 | 20 | 5.0 |
| 40 | 8,320 | 400 | 40 | 47.4 | 40 | 6.9 | 40 | 10.7 |
| 80 | 16,640 | 248 | 80 | 101 | 80 | 18.8 | 80 | 11.8 |
| 160 | 33,280 | 915 | 160 | 104 | 160 | 40.0 | 160 | 40.9 |
| 320 | 66,560 | 1,584 | 320 | 77.5 | 320 | 74.6 | 320 | 29.7 |
| 640 | 133,120 | 3,459 | 640 | 263 | 640 | 88.9 | 640 | 77.8 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 208n (exact) | n^1.35 (rms 0.28) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |
| FIX | n (exact) | undecided: n^8.9 (rms 0.32) or 1.01^n (rms 0.32) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |
| MIN5 | n (exact) | n^0.93 for n ≥ 40 (rms 0.23) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |
| FULL | n (exact) | n^0.83 (rms 0.29) | n^1.00 (R² 1.000) / 1.00^n (R² 0.920) | – | completed |

### members-both

Valid: n extensions over n/10 types and n member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 960 | 119 | 20 | 32.8 | 20 | 2.8 | 20 | 3.9 |
| 40 | 3,520 | 193 | 40 | 32.3 | 40 | 13.8 | 40 | 20.2 |
| 80 | 13,440 | 495 | 80 | 48.8 | 80 | 10.9 | 80 | 19.8 |
| 160 | 52,480 | 882 | 160 | 99.3 | 160 | 54.9 | 160 | 31.8 |
| 320 | 207,360 | 2,917 | 320 | 278 | 320 | 164 | 320 | 50.3 |
| 640 | 824,320 | 7,004 | 640 | 547 | 640 | 423 | 640 | 139 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 2n^2 + 8n (exact) | n^1.42 (rms 0.10) | n^1.99 (R² 1.000) / 1.01^n (R² 0.965) | – | completed |
| FIX | n (exact) | n^1.49 (rms 0.11) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964) | – | completed |
| MIN5 | n (exact) | n^1.98 for n ≥ 40 (rms 0.32) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964) | `memberskip.skipped`: 2n^2 + 7n (exact) | completed |
| FULL | n (exact) | n^1.77 for n ≥ 40 (rms 0.07) | n^1.00 (R² 1.000) / 1.00^n (R² 0.964) | – | completed |

### condext

Valid: n conditional extensions of Box<T> (each needs T is P{i}), 8 member lookups. Intended verdict: accepted. Primary counter: `names.appliesCalls`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 96 | 87.7 | 8 | 12.4 | 8 | 3.0 | 8 | 7.9 |
| 4 | 128 | 47.8 | 8 | 40.4 | 8 | 7.5 | 8 | 7.6 |
| 8 | 192 | 68.2 | 8 | 20.6 | 8 | 8.8 | 8 | 8.1 |
| 16 | 320 | 87.0 | 8 | 64.9 | 8 | 9.0 | 8 | 17.2 |
| 32 | 576 | 265 | 8 | 112 | 8 | 23.4 | 8 | 15.7 |
| 64 | 1,088 | 903 | 8 | 216 | 8 | 17.5 | 8 | 31.4 |
| 128 | 2,112 | 4,258 | 8 | 537 | 8 | 23.8 | 8 | 39.6 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 16n + 64 (exact) | n^2.18 for n ≥ 4 (rms 0.08) | n^0.91 (R² 0.999) / 1.02^n (R² 0.933) | `summon.matches`: n^2 + 105n + 2,444 (exact) | completed |
| FIX | flat | n^1.11 for n ≥ 8 (rms 0.13) | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | `solver.goalSteps`: 6n + 104 (exact) | completed |
| MIN5 | flat | below 50 ms throughout | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | `index.skipped`: 10n + 650 (exact, n ≥ 8) | completed |
| FULL | flat | below 50 ms throughout | n^-0.00 (R² 1.000) / 1.00^n (R² 1.000) | `absmodel.facts`: n + 63 (exact) | completed |

### ovl-calls

Valid: one expression with k calls, each choosing among 4 overloads by argument type. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 40.0 | 4 | 25.3 | 4 | 4.9 | 4 | 6.4 |
| 2 | 8 | 80.3 | 8 | 9.7 | 8 | 1.0 | 8 | 2.1 |
| 3 | 16 | 35.1 | 16 | 30.7 | 16 | 5.6 | 16 | 6.6 |
| 4 | 44 | 66.3 | 44 | 43.2 | 44 | 6.9 | 44 | 7.9 |
| 5 | 144 | 200 | 144 | 54.5 | 144 | 15.1 | 144 | 22.1 |
| 6 | 448 | 731 | 448 | 72.9 | 448 | 70.5 | 448 | 71.2 |
| 7 | 1,248 | 2,243 | 1,248 | 213 | 1,248 | 124 | 1,248 | 145 |
| 8 | 3,184 | 5,410 | 3,184 | 437 | 3,184 | 371 | 3,184 | 430 |
| 9 | 7,316 | 13,063 | 7,316 | 964 | 7,316 | 673 | 7,316 | 878 |
| 10 | timeout | >20 s | 15,396 | 1,686 | 15,396 | 1,780 | 15,396 | 1,569 |
| 12 | not run |  | 59,820 | 7,026 | 59,820 | 7,093 | 59,820 | 6,367 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | undecided: n^6.5 (rms 0.09) or 2.83^n (rms 0.12) | undecided: n^7.7 (rms 0.25) or 3.26^n (rms 0.34) | n^6.69 (R² 0.999) / 2.67^n (R² 0.996) | `summon.cacheHits`: n^6.54 for n ≥ 2 (rms 0.08) | timeout (>20 s) at n=10 |
| FIX | n^6.93 for n ≥ 3 (rms 0.05) | undecided: n^7.0 (rms 0.11) or 2.16^n (rms 0.15) | n^7.06 (R² 1.000) / 2.25^n (R² 0.992) | `summon.matches`: 2.07^n for n ≥ 3 (rms 0.05) | completed |
| MIN5 | n^6.93 for n ≥ 3 (rms 0.05) | n^7.16 for n ≥ 3 (rms 0.16) | n^7.06 (R² 1.000) / 2.25^n (R² 0.992) | – | completed |
| FULL | n^6.93 for n ≥ 3 (rms 0.05) | n^6.76 for n ≥ 3 (rms 0.10) | n^7.06 (R² 1.000) / 2.25^n (R² 0.992) | – | completed |

### ovl-width

Valid: one expression with 4 calls, each choosing among m overloads by argument type. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 14 | 69.6 | 14 | 23.5 | 14 | 2.3 | 14 | 6.8 |
| 3 | 30 | 55.9 | 30 | 15.2 | 30 | 3.6 | 30 | 3.9 |
| 4 | 44 | 207 | 44 | 19.2 | 44 | 7.9 | 44 | 10.8 |
| 6 | 78 | 216 | 78 | 24.6 | 78 | 11.2 | 78 | 10.6 |
| 8 | 120 | 372 | 120 | 35.0 | 120 | 23.5 | 120 | 24.6 |
| 12 | 228 | 433 | 228 | 38.3 | 228 | 19.1 | 228 | 25.5 |
| 16 | 368 | 1,127 | 368 | 59.3 | 368 | 23.6 | 368 | 31.7 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | n^2 + 7n (exact, n ≥ 3) | undecided: n^3.3 (rms 0.16) or 1.28^n (rms 0.14) | n^1.58 (R² 1.000) / 1.17^n (R² 0.988) | – | completed |
| FIX | n^2 + 7n (exact, n ≥ 3) | undecided: n^0.9 (rms 0.08) or 1.10^n (rms 0.11) | n^1.58 (R² 1.000) / 1.17^n (R² 0.988) | – | completed |
| MIN5 | n^2 + 7n (exact, n ≥ 3) | below 50 ms throughout | n^1.58 (R² 1.000) / 1.17^n (R² 0.988) | – | completed |
| FULL | n^2 + 7n (exact, n ≥ 3) | below 50 ms throughout | n^1.58 (R² 1.000) / 1.17^n (R² 0.988) | – | completed |

### ovl-stmts

Valid: k separate statements, each one call choosing among 4 overloads. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 43.2 | 4 | 15.4 | 4 | 0.9 | 4 | 9.8 |
| 2 | 8 | 82.6 | 8 | 21.1 | 8 | 1.4 | 8 | 10.8 |
| 4 | 16 | 108 | 16 | 21.0 | 16 | 6.0 | 16 | 12.4 |
| 8 | 32 | 171 | 32 | 39.9 | 32 | 6.7 | 32 | 7.7 |
| 16 | 64 | 213 | 64 | 29.9 | 64 | 12.1 | 64 | 13.6 |
| 32 | 128 | 393 | 128 | 40.6 | 128 | 16.5 | 128 | 30.4 |
| 64 | 256 | 652 | 256 | 57.6 | 256 | 31.0 | 256 | 25.1 |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 4n (exact) | n^0.62 (rms 0.10) | n^1.00 (R² 1.000) / 1.04^n (R² 0.920) | – | completed |
| FIX | 4n (exact) | undecided: n^0.3 (rms 0.16) or 1.02^n (rms 0.25) | n^1.00 (R² 1.000) / 1.04^n (R² 0.920) | – | completed |
| MIN5 | 4n (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.920) | – | completed |
| FULL | 4n (exact) | below 50 ms throughout | n^1.00 (R² 1.000) / 1.04^n (R² 0.920) | – | completed |

### ovr-args

Valid: g(h(), ..., h()) with n arguments; h has 3 overloads differing in return type only. Intended verdict: accepted. Primary counter: `solver.forks`.

| n | base count | base ms | FIX count | FIX ms | MIN5 count | MIN5 ms | FULL count | FULL ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 56.6 | 3 | 12.7 |  |  |  |  |
| 2 | 12 | 57.4 | 12 | 22.6 |  |  |  |  |
| 3 | 39 | 71.8 | 39 | 27.0 |  |  |  |  |
| 4 | 120 | 68.0 | 120 | 24.9 |  |  |  |  |
| 5 | 363 | 76.6 | 363 | 20.4 |  |  |  |  |
| 6 | 1,092 | 112 | 1,092 | 28.1 |  |  |  |  |
| 7 | 3,279 | 304 | 3,279 | 169 |  |  |  |  |
| 8 | 9,840 | 620 | 9,840 | 264 |  |  |  |  |
| 9 | 29,523 | 1,888 | 29,523 | 1,047 |  |  |  |  |
| 10 | 88,572 | 4,877 | 88,572 | 3,544 |  |  |  |  |
| 12 | timeout | >20 s |  |  |  |  |  |  |

| Configuration | Counter growth | Time growth | Log-log exponent / semi-log base (counter, upper half) | Fastest other counter | Ends with |
|---|---|---|---|---|---|
| base | 3.03^n for n ≥ 2 (rms 0.03) | undecided: n^8.7 (rms 0.09) or 2.93^n (rms 0.09) | n^8.58 (R² 0.994) / 3.00^n (R² 1.000) | – | timeout (>20 s) at n=12 |
| FIX | 3.03^n for n ≥ 2 (rms 0.03) | undecided: n^10.5 (rms 0.25) or 3.72^n (rms 0.28) | n^8.58 (R² 0.994) / 3.00^n (R² 1.000) | – | completed |
| MIN5 | – | – | – | – | completed |
| FULL | – | – | – | – | completed |

