#!/bin/bash
# usage: r.sh file.hylo...  -> baseline / FIX / FULL (eq3 binary, final configuration)
B=${B:-/home/user/hylo-new/research/exp/bin/eq5-2577ef0198c2/tc-bench}
FIX=occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget
FULL=$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec
for f in "$@"; do
 echo "=== $(basename $f)"
 for c in ${CFGS:-base FIX FULL}; do
  case $c in base) e="";; FIX) e=$FIX;; FULL) e=$FULL;; esac
  out=$(HYLO_TC_EXPERIMENTS=$e timeout ${T:-60} $B "$f" 2>&1); rc=$?
  echo "[$c rc=$rc] $(echo "$out" | grep -E 'diagnostics:|type.user' | tr '\n' ' ')"
  echo "$out" | grep -iE 'error' | head -2 | sed 's/^/    /'
 done
done
