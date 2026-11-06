Typing time in ms (best of --repeat 3, pinned to one core; stdlib row = stdlib typing, others = user typing). d = diagnostics. Binary eq2-e965a058dfd0.

| workload | baseline | FIX (semantic fixes) | FULL (fixes + performance flags) |
|---|---|---|---|
| stdlib | 712.71 (d=0) | 455.49 (d=0) | 184.13 (d=0) |
| members-big | 14851.09 (d=0) | 743.20 (d=0) | 477.66 (d=0) |
| breadth40 | 5076.42 (d=0) | 4938.61 (d=0) | 52.68 (d=0) |
| div-loop-20 | 138.79 (d=20) | 130.40 (d=20) | 3.52 (d=20) |
| div-branch | 1548.77 (d=1) | 1604.70 (d=1) | 2.19 (d=1) |
| wide-tuple-5 | 62.02 (d=1) | 56.78 (d=1) | 4.02 (d=1) |
| trans-8 | 1283.24 (d=0) | 8.64 (d=0) | 3.69 (d=0) |
| assoceq-5 | 1963.22 (d=0) | 76.71 (d=0) | 67.72 (d=0) |
| assoceq-8 | 3497.19 (d=0) | 132.92 (d=0) | 116.41 (d=0) |
| orig-coerc-cache | 2706.42 (d=0) | 12.26 (d=0) | 4.50 (d=0) |
| assocneg-8 | 3025.33 (d=0) | 114.99 (d=1) | 101.27 (d=1) |
| refine-8 | 51.70 (d=0) | 32.86 (d=0) | 4.43 (d=0) |
| nestwide-8 | 68.09 (d=0) | 48.16 (d=0) | 7.31 (d=0) |
| ovl-4-8 | 4790.61 (d=0) | 226.15 (d=0) | 170.49 (d=0) |
| ovr-3-8 | 268.66 (d=0) | 272.68 (d=0) | 203.52 (d=0) |
