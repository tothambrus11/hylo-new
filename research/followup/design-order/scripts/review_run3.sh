#!/bin/bash
# Prints the diagnostics of each FILE under base and FULL (binary eq9) and under FULL+sigrounds+selfcheck (binary eq17).
# usage: review_run3.sh FILE...
D="$(dirname "$0")"
FIX="occurs,fixsubst,eqsolve,extorder,arrowenv,eqmgu,givencheck,budget"
FULL="$FIX,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,absquotient,typevec,reifymemo"
show() { grep -v "^parse\|^scope\|^type\.\|^counters.stdlib" | sed -e 's|/[^ ]*/||' -e 's/^counters.user: *//' | grep -o "sigrounds[^ ]*\|selfcheck.sigrounds[^ ]*\|diagnostics.*\|.*error:.*\|.*VIOLATION.*\|extorder[^ ]*\|givencheck[^ ]*" | tr '\n' ';'; echo " exit=${PIPESTATUS[0]}"; }
for f in "$@"; do
  echo "== $f"
  echo -n "  base:   "; "$D/tcb.sh" eq9-723cc0e6b0f8 "" --count "$f" 2>&1 | show
  echo -n "  FULL:   "; "$D/tcb.sh" eq9-723cc0e6b0f8 "$FULL" --count "$f" 2>&1 | show
  echo -n "  rounds: "; "$D/tcb.sh" ${TCB17:-eq17-4c2982653305} "$FULL,sigrounds,selfcheck" --count "$f" 2>&1 | show
done
