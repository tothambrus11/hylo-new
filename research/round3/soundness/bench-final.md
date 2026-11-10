Typing time in ms (best of --repeat 3, pinned to one core; stdlib row = stdlib typing, others = user typing). d = diagnostics. Binary eq8-acc8f2fdf588. FIX = occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget; FULL = FIX + symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo.

| workload | baseline | FIX | FULL |
|---|---|---|---|
| stdlib | 615.95 (d=0) | 388.72 (d=0) | 151.40 (d=0) |
| members-big | 13171.59 (d=0) | 543.92 (d=0) | 355.69 (d=0) |
| breadth40 | 4617.40 (d=0) | 4936.68 (d=0) | 38.17 (d=0) |
| div-loop-20 | 131.21 (d=20) | 91.42 (d=20) | 2.56 (d=20) |
| div-branch | 1350.17 (d=1) | 1333.20 (d=1) | 1.84 (d=1) |
| wide-tuple-5 | 50.69 (d=1) | 53.09 (d=1) | 3.03 (d=1) |
| trans-8 | 1076.39 (d=0) | 7.48 (d=0) | 3.52 (d=0) |
| assoceq-5 | 1441.99 (d=0) | 51.30 (d=0) | 46.87 (d=0) |
| assoceq-8 | 2749.81 (d=0) | 92.30 (d=0) | 74.47 (d=0) |
| orig-coerc-cache | 2165.06 (d=0) | 12.20 (d=0) | 3.92 (d=0) |
| assocneg-8 | 2486.52 (d=0) | 78.61 (d=1) | 65.81 (d=1) |
| refine-8 | 43.94 (d=0) | 23.55 (d=0) | 3.99 (d=0) |
| nestwide-8 | 60.19 (d=0) | 39.88 (d=0) | 4.98 (d=0) |
| ovl-4-8 | 3880.44 (d=0) | 157.69 (d=0) | 117.81 (d=0) |
| ovr-3-8 | 236.43 (d=0) | 226.45 (d=0) | 141.45 (d=0) |
| x10b-ext-where-assoc | 1405.76 (d=0) | 16.64 (d=0) | 14.46 (d=0) |
| open-wide-4 | crash/OOM | 344.23 (d=0) | 189.04 (d=0) |
| div-eq-ovl-b3-1 | crash/OOM | 3096.06 (d=1) | 3.15 (d=0) |
| occurs-dag-16 | 2323.83 (d=0) | 2163.83 (d=0) | 2.28 (d=0) |
| p02-cc-big | crash/OOM | 63.80 (d=0) | 62.72 (d=0) |
| perf-alias-7 | 23.22 (d=1) | 9.19 (d=0) | 4.09 (d=0) |
