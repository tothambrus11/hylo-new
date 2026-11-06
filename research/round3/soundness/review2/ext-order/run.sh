#!/bin/bash
# usage: run.sh file.hylo...  -> baseline / FIX / FULL diagnostics
BIN=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
for f in "$@"; do
  echo "=== $f"
  for c in base FIX FULL; do
    case $c in base) E="";; FIX) E=$FIX;; FULL) E=$FULL;; esac
    out=$(HYLO_TC_EXPERIMENTS=$E timeout 120 $BIN "$f" 2>&1); rc=$?
    echo "[$c rc=$rc] $(echo "$out" | grep -E '^diagnostics|type.user' | tr '\n' ' ')"
    echo "$out" | grep -E 'error|warning' | grep -v '^diagnostics' | sed 's/^/    /' | head -6
  done
done
