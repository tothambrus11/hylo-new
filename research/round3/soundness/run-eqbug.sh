#!/bin/bash
# Runs the equality-bug variants with and without the fixsubst fix; prints diagnostics, time, matches.
B=${1:-../../exp/bin/impl9-19b99de44e68/tc-bench}
for f in eqbug-*.hylo; do
  for c in "" fixsubst; do
    o=$(HYLO_TC_EXPERIMENTS=$c timeout 600 $B --count $f 2>&1)
    echo "$f [${c:-baseline}] diags=$(echo "$o" | grep -oP 'diagnostics: \K\d+') ms=$(echo "$o" | grep -oP 'type.user\s+\K[\d.]+' || echo TIMEOUT) matches=$(echo "$o" | grep -oP 'counters.user.*summon.matches=\K\d+')"
  done
done
