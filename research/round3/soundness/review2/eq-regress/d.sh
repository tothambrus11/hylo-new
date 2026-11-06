#!/bin/bash
# usage: d.sh file.hylo -> diffs of dumps base vs FIX vs FULL
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
D=/home/user/hylo-new/research/round3/soundness/review2/eq-regress/dumps
for f in "$@"; do n=$(basename $f .hylo)
 HYLO_TC_EXPERIMENTS= timeout 120 $B --dump $D/$n.base.txt $f >/dev/null 2>&1
 HYLO_TC_EXPERIMENTS=$FIX timeout 120 $B --dump $D/$n.fix.txt $f >/dev/null 2>&1
 HYLO_TC_EXPERIMENTS=$FULL timeout 120 $B --dump $D/$n.full.txt $f >/dev/null 2>&1
 for c in base fix full; do sed -n '/^== module Test/,$p' $D/$n.$c.txt > $D/$n.$c.t; mv $D/$n.$c.t $D/$n.$c.txt; done
 echo "=== $n base-vs-fix: $(diff $D/$n.base.txt $D/$n.fix.txt | grep -c '^[<>]') lines; fix-vs-full: $(diff $D/$n.fix.txt $D/$n.full.txt | grep -c '^[<>]') lines"
done
