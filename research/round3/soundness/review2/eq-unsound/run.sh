#!/bin/bash
# usage: run.sh file...   runs BASE, FIX, FULL
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
for f in "$@"; do
  for c in BASE FIX FULL; do
    case $c in BASE) fl=;; FIX) fl=$FIX;; FULL) fl=$FULL;; esac
    out=$(HYLO_TC_EXPERIMENTS=$fl timeout 120 $B $f 2>&1); rc=$?
    echo "== $f [$c] rc=$rc :: $(echo "$out" | grep -E '^diagnostics|type.user' | tr '\n' ' ')"
    echo "$out" | grep -iE 'error' | head -4 | sed 's/^/     /'
  done
done
