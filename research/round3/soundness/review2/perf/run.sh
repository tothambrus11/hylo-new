#!/bin/bash
# usage: run.sh CONFIG file [extra env]
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
case "$1" in base) F=;; fix) F=$FIX;; full) F=$FULL;; *) F=$1;; esac
shift
s=$(date +%s.%N)
HYLO_TC_EXPERIMENTS=$F timeout ${TO:-120} /usr/bin/time -f "rss=%MKB wall=%es" $B --count "$@" 2>&1 | grep -E "diagnostics|error|type.user|summon.matches|summon.subgoals|eqsolve|depthExhausted|absmodel.refuted|rss=|Killed|signal" | head -${LINES_:-20}
echo "exit=${PIPESTATUS[0]}"
