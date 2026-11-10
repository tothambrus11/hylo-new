#!/bin/bash
# Runs one tc-bench process at a time (file lock), under a timeout.
# usage: tcb.sh BINARY-DIR-NAME FLAGS [tc-bench args]     e.g. tcb.sh eq17-4c2982653305 "sigrounds" --count file.hylo
L="${TCB_LOCK:-$(dirname "$0")/../results/.tcb.lock}"
B="/home/user/hylo-new/research/exp/bin/$1/tc-bench"; shift
F="$1"; shift
HYLO_TC_EXPERIMENTS="$F" exec flock "$L" timeout 60 "$B" "$@"
