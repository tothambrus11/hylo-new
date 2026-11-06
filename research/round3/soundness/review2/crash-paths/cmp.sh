#!/bin/bash
# cmp.sh files... : compare normalized dumps of FIX vs FULL
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
T=$(mktemp -d)
for f in "$@"; do
  n=$(basename $f .hylo)
  HYLO_TC_EXPERIMENTS=$FIX timeout 120 $B --quiet --dump $T/$n.fix $f >/dev/null 2>&1 & 
  HYLO_TC_EXPERIMENTS=$FULL timeout 120 $B --quiet --dump $T/$n.full $f >/dev/null 2>&1 ; e2=$?
  wait $!; e1=$?
  for k in fix full; do [ -f $T/$n.$k ] && sed -E 's/\(erased: [0-9]+\)/(erased: _)/g; s/%[0-9a-z]+/%v/g' $T/$n.$k > $T/$n.$k.n; done
  if [ $e1 != $e2 ]; then echo "DIFF-EXIT $f fix=$e1 full=$e2";
  elif [ -f $T/$n.fix.n ] && ! cmp -s $T/$n.fix.n $T/$n.full.n; then echo "DIFF $f"; diff $T/$n.fix.n $T/$n.full.n | head -6;
  else echo "same $f (exit $e1)"; fi
done
rm -rf $T
