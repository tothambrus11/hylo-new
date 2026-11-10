#!/bin/bash
# Type-checks a program under a named configuration and prints the diagnostics.
# usage: tc.sh (base|FIX|FULL) program.hylo
B=/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget
case "$1" in
  base) F="" ;;
  FIX)  F="$FIX" ;;
  FULL) F="$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo" ;;
  *) echo "usage: tc.sh (base|FIX|FULL) program.hylo" >&2; exit 2 ;;
esac
HYLO_TC_EXPERIMENTS="$F" timeout 60 "$B" "$2" | grep -v '^counters\|^parse\|^scope\|^type\.'
echo "exit code: ${PIPESTATUS[0]}"
