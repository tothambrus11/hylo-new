#!/bin/bash
# Counter matrix: baseline, all-on, leave-one-out, and each flag alone.
# Usage: matrix2.sh OUTDIR workload...   (config token "base" = no flags)
B=/home/hylo/hylo-tc/research/exp/bin/15f1d9abd0da/tc-bench
O=$1; shift
FL=(names unify index absmodel solver loopcheck)
ALL=$(IFS=,; echo "${FL[*]}")
cfgs=(base "$ALL")
for f in "${FL[@]}"; do cfgs+=("$(echo ",$ALL," | sed "s/,$f,/,/; s/^,//; s/,$//")"); cfgs+=("$f"); done
for wl in "$@"; do for c in "${cfgs[@]}"; do echo "$wl $c"; done; done |
xargs -P ${PAR:-3} -L 1 bash -c '
  wl=$0; c=$1; out='"$O"'/${wl}__${c}.txt; [ -s "$out" ] && exit 0
  cc=$c; [ "$c" = base ] && cc=
  HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=$cc timeout ${TMO:-400} '"$B"' --count /home/hylo/hylo-tc/research/workloads/$wl.hylo > $out.tmp 2>&1 && mv $out.tmp $out || { echo "TIMEOUT/ERR" >> $out.tmp; mv $out.tmp $out; }'
