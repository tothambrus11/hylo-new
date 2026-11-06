#!/bin/bash
# usage: run.sh bin(base|impl) flags depth file
B=/home/user/hylo-new/research/exp/bin
case $1 in base) X=$B/4587ce9e1a23/tc-bench;; impl) X=$B/impl10-37a7007e33a0/tc-bench;; esac
s=$(date +%s.%N)
out=$(HYLO_TC_MAXDEPTH=$3 HYLO_TC_EXPERIMENTS=$2 timeout 300 $X $4 2>&1); rc=$?
e=$(date +%s.%N)
echo "$(basename $4) [$1:$2 d=$3] rc=$rc $(echo "$out" | grep -E '^diagnostics|alloc' | tr '\n' ' ') t=$(echo "$e-$s"|bc)"
