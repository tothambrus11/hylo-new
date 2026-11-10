#!/bin/bash
# Usage: scripts/tc.sh CONFIG program.hylo [timeout-seconds]
#   CONFIG is base, FULL, or a literal flag list.
# Prints one line: verdict, the solver counters of the user module, type.user time (indicative),
# followed by the diagnostics, one per line.
B=/home/user/hylo-new/research/exp/bin/eq9-723cc0e6b0f8/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget
FULL=$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo
case "$1" in base) C="";; FULL) C="$FULL";; FIX) C="$FIX";; *) C="$1";; esac
T=${3:-60}
out=$(HYLO_TC_EXPERIMENTS="$C" timeout "$T" "$B" --count "$2" 2>&1); rc=$?
if [ $rc -ne 0 ]; then echo "exit=$rc"; echo "$out" | tail -3; exit 0; fi
n=$(echo "$out" | sed -n 's/^diagnostics: //p')
ctr=$(echo "$out" | grep '^counters.user:' | tr ' ' '\n' | grep -E '^solver\.' | tr '\n' ' ')
tm=$(echo "$out" | grep '^type.user' | awk '{print $2}')
echo "diagnostics=$n $ctr type.user=${tm}ms"
echo "$out" | awk '/^diagnostics:/{p=1;next} /^parse /{p=0} p' 
