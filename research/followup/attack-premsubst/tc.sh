#!/bin/bash
# usage: tc.sh CONFIG FILE [extra tc-bench args]: prints the full output of one run (diagnostics, trace).
HERE=$(cd "$(dirname "$0")" && pwd)
FLAGS=$(cd "$HERE" && python3 -c "import run,sys; print(run.flags(sys.argv[1]))" "$1")
f=$2; shift; shift
HYLO_TC_EXPERIMENTS=$FLAGS timeout 60 /home/user/hylo-new/research/exp/bin/eq22-554540c3a507/tc-bench "$@" "$f" 2>&1 | grep -v '^counters.stdlib\|^parse\|^scope\|^type\.\|^total\|^load'
echo "exit: ${PIPESTATUS[0]}"
