Typing time in ms (best of --repeat 3, pinned to one core; stdlib row = stdlib typing, others = user typing). d = diagnostics. Binary eq6-c98a4662fc60. FIX = occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget; FULL = FIX + symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo.

| workload | baseline | FIX | FULL |
|---|---|---|---|
| stdlib | 734.88 (d=0) | 443.65 (d=0) | 191.00 (d=0) |
| members-big | 15320.58 (d=0) | 760.68 (d=0) | 485.90 (d=0) |
| breadth40 | 4881.30 (d=0) | 4871.55 (d=0) | 55.27 (d=0) |
| div-loop-20 | 135.90 (d=20) | 135.01 (d=20) | 3.61 (d=20) |
| div-branch | 1609.02 (d=1) | 1634.08 (d=1) | 2.18 (d=1) |
| wide-tuple-5 | 61.80 (d=1) | 54.80 (d=1) | 4.08 (d=1) |
| trans-8 | 1246.64 (d=0) | 8.65 (d=0) | 3.77 (d=0) |
| assoceq-5 | 1971.69 (d=0) | 75.80 (d=0) | 65.01 (d=0) |
| assoceq-8 | 3635.06 (d=0) | 143.13 (d=0) | 116.35 (d=0) |
| orig-coerc-cache | 2695.95 (d=0) | 12.45 (d=0) | 4.43 (d=0) |
| assocneg-8 | 3064.45 (d=0) | 108.89 (d=1) | 100.33 (d=1) |
| refine-8 | 48.58 (d=0) | 33.02 (d=0) | 4.37 (d=0) |
| nestwide-8 | 66.49 (d=0) | 47.76 (d=0) | 6.75 (d=0) |
| ovl-4-8 | 4692.71 (d=0) | 232.77 (d=0) | 182.39 (d=0) |
| ovr-3-8 | 279.30 (d=0) | 276.15 (d=0) | 218.57 (d=0) |
| x10b-ext-where-assoc | 1779.30 (d=0) | 23.20 (d=0) | 16.88 (d=0) |
| open-wide-4 | crash/OOM | 495.72 (d=0) | 202.00 (d=0) |
| div-eq-ovl-b3-1 | crash/OOM | 3301.23 (d=1) | 4.16 (d=0) |
| occurs-dag-16 | 2860.28 (d=0) | 2872.15 (d=0) | 3.34 (d=0) |
| p02-cc-big | crash/OOM | 81.95 (d=0) | 63.37 (d=0) |
| perf-alias-7 | 28.21 (d=1) | 10.16 (d=0) | 4.62 (d=0) |
