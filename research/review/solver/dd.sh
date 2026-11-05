#!/bin/bash
# usage: dd.sh prog.hylo [flags]  -> prints user-file part diff between baseline and flags (default solver)
B=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench
D=/home/user/hylo-new/research/review/solver/dumps
f=$1; n=$(basename $f .hylo); fl=${2:-solver}
HYLO_TC_ABSDEPTH=2 $B --quiet --dump $D/$n.base.txt $f >/dev/null 2>&1
HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=$fl $B --quiet --dump $D/$n.$fl.txt $f >/dev/null 2>&1
grep -v '^[1-9][0-9]*:' $D/$n.base.txt | grep -v '^diag .*Library' > $D/$n.base.u.txt
grep -v '^[1-9][0-9]*:' $D/$n.$fl.txt | grep -v '^diag .*Library' > $D/$n.$fl.u.txt
diff $D/$n.base.u.txt $D/$n.$fl.u.txt
