#!/bin/bash
# usage: run.sh CONFIG file.hylo [extra args]; CONFIG in base|orig|fix|full or explicit flag list
B=/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench
O=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench
FIX=occurs,fixsubst,eqsolve,extorder
FULL=occurs,fixsubst,eqsolve,extorder,symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec
c=$1; shift
case $c in
  base) f="";; orig) f=""; B=$O;; fix) f=$FIX;; full) f=$FULL;; fixtrace) f=$FIX,trace;; fulltrace) f=$FULL,trace;; basetrace) f=trace;; *) f=$c;;
esac
s=$(date +%s.%N)
( ulimit -v 4000000; HYLO_TC_EXPERIMENTS=$f timeout 120 $B "$@" ) 2>&1 | grep -v '^\[trace\]' | head -${LINES_MAX:-15}
echo "exit=${PIPESTATUS[0]} wall=$(echo "$(date +%s.%N) - $s" | bc)"
