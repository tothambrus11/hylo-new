#!/bin/bash
# Runs one tc-bench process at a time (file lock), under a timeout.
# usage: tcb.sh BINARY-DIR-NAME FLAGS [tc-bench args]     e.g. tcb.sh eq17-4c2982653305 "sigrounds" --count file.hylo
L="${TCB_LOCK:-/tmp/claude-0/-home-user-hylo-new/fd857f11-b63a-5859-949e-90078fb8fdea/scratchpad/tcb.lock}"
B="/home/user/hylo-new/research/exp/bin/$1/tc-bench"; shift
F="$1"; shift
HYLO_TC_EXPERIMENTS="$F" exec flock "$L" timeout 60 "$B" "$@"
