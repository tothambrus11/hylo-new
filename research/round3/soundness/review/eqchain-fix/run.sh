#!/bin/bash
# usage: run.sh BIN CONFIG MAXDEPTH file...   prints one line per file
B=/home/user/hylo-new/research/exp/bin/$1/tc-bench; C=$2; D=$3; shift 3
for f in "$@"; do
  s=$(date +%s.%N)
  o=$(HYLO_TC_MAXDEPTH=$D HYLO_TC_EXPERIMENTS=$C timeout ${TO:-300} $B --count $f 2>&1)
  rc=$?
  echo "$f [$C d=$D] rc=$rc diags=$(echo "$o" | grep -oP 'diagnostics: \K\d+') user_ms=$(echo "$o" | grep -oP 'type.user\s+\K[\d.]+') matches=$(echo "$o" | grep -oP 'counters.user.*summon.matches=\K\d+') subgoals=$(echo "$o" | grep -oP 'counters.user.*summon.subgoals=\K\d+') refuted=$(echo "$o" | grep -oP 'counters.user.*eqrefute.refuted=\K\d+')"
done
