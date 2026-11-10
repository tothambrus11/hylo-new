#!/bin/bash
# usage: tc.sh CONFIG FILE [extra tc-bench args]: prints the diagnostics and the sigrounds counters of one run.
# CONFIG is as in run.py (base, FULL, NEW, NOSIG, +flag...).
HERE=$(cd "$(dirname "$0")" && pwd)
FLAGS=$(python3 - "$1" <<'PY'
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath("x"))))
sys.path.insert(0, "/home/user/hylo-new/research/followup")
import tcrun
tcrun.CONFIGS["NOSIG"] = tcrun.CONFIGS["NEW"].replace(",sigrounds", "")
print(tcrun.flags(sys.argv[1]))
PY
)
f=$2; shift; shift
HYLO_TC_EXPERIMENTS=$FLAGS timeout 60 /home/user/hylo-new/research/exp/bin/eq22-554540c3a507/tc-bench --count "$@" "$f" 2>&1 | grep -v '^counters.stdlib\|^parse\|^scope\|^type\.\|^total\|^load' | sed -e 's/^counters.user:.*\(sigrounds[^ ]* \)/counters.user: ... \1/' | cut -c1-400
echo "exit: ${PIPESTATUS[0]}"
