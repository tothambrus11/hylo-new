#!/bin/bash
# usage: run.sh CONFIG file.hylo [extra tc-bench args]   (CONFIG = base | FIX | FULL | <flag list>)
B=/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench
FIX="occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
case "$1" in
  base) F="";;
  FIX) F="$FIX";;
  FULL) F="$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo";;
  *) F="$1";;
esac
shift
HYLO_TC_EXPERIMENTS="$F" timeout 60 "$B" "$@"
echo "exit: $?"
