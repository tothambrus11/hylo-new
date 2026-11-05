#!/bin/bash
# usage: run.sh file.hylo [flags]  -> prints user-file diff between baseline and flags (default index)
B=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench
f=$1; fl=${2:-index}; n=$(basename $f .hylo); d=$(dirname $f)/out; mkdir -p $d
HYLO_TC_ABSDEPTH=2 $B --quiet --dump $d/base_$n.txt $f >/dev/null 2>&1
HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=$fl $B --quiet --dump $d/${fl}_$n.txt $f >/dev/null 2>&1
sed -i 's/(erased: [0-9]*)/(erased: _)/g' $d/base_$n.txt $d/${fl}_$n.txt
if cmp -s $d/base_$n.txt $d/${fl}_$n.txt; then echo "$n: identical ($(grep -c '^diag' $d/base_$n.txt) diags)"; else echo "$n: MISMATCH"; diff $d/base_$n.txt $d/${fl}_$n.txt | head -30; fi
