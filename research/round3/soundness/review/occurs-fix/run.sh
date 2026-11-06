#!/bin/bash
# usage: run.sh <bin: impl|base> <flags> file
case $1 in impl) B=/home/user/hylo-new/research/exp/bin/impl10-37a7007e33a0/tc-bench;; base) B=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench;; esac
HYLO_TC_EXPERIMENTS=$2 timeout 300 $B $3 > /tmp/claude-0/out.$$ 2>&1; rc=$?
grep -v '^\(parse\|scope\|type\.\)' /tmp/claude-0/out.$$ | tail -${TAILN:-6}; echo "[exit $rc]"; rm -f /tmp/claude-0/out.$$
