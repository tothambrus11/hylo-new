#!/bin/bash
# usage: run.sh file.hylo [configs...]; env DEPTH
N=/home/user/hylo-new/research/exp/bin/impl10-37a7007e33a0/tc-bench
B=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench
f=$1; shift
cfgs=("$@"); [ ${#cfgs[@]} -eq 0 ] && cfgs=(base "" fixsubst fixsubst,eqrefute)
for c in "${cfgs[@]}"; do
  if [ "$c" = base ]; then bin=$B; cc=""; else bin=$N; cc=$c; fi
  o=$(HYLO_TC_MAXDEPTH=${DEPTH:-10} HYLO_TC_EXPERIMENTS=$cc timeout 300 $bin $f 2>&1)
  echo "$(basename $f) [${c:-impl-off}] diags=$(echo "$o" | grep -oP 'diagnostics: \K\d+' || echo CRASH/TO) user=$(echo "$o" | grep -oP 'type.user\s+\K[\d.]+')"
  [ -n "$V" ] && echo "$o" | grep -E 'error|rror' | head -5
done
