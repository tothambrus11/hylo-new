#!/bin/bash
# usage: r.sh file.hylo  -> baseline / FIX / FULL summary
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
for f in "$@"; do
 echo "=== $f"
 for c in base FIX FULL; do
  case $c in base) e="";; FIX) e=$FIX;; FULL) e=$FULL;; esac
  out=$(HYLO_TC_EXPERIMENTS=$e timeout 120 $B "$f" 2>&1); rc=$?
  echo "[$c rc=$rc] $(echo "$out" | grep -E 'diagnostics:|type.user' | tr '\n' ' ')"
  echo "$out" | grep -iE 'error' | head -3 | sed 's/^/    /'
 done
done
