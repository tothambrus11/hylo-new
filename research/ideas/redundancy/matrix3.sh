#!/bin/bash
# Counter matrix on the frozen binary 4587ce9e1a23: base, all-on, leave-one-out, each flag alone.
# Usage: PAR=2 matrix3.sh OUTDIR workload...
B=/home/user/hylo-new/research/exp/bin/4587ce9e1a23/tc-bench
O=$1; shift
FL=(names unify index absmodel solver loopcheck)
ALL=$(IFS=,; echo "${FL[*]}")
cfgs=(base "$ALL")
for f in "${FL[@]}"; do cfgs+=("$(echo ",$ALL," | sed "s/,$f,/,/; s/^,//; s/,$//")"); cfgs+=("$f"); done
cfgs+=(${EXTRA})
for wl in "$@"; do for c in "${cfgs[@]}"; do echo "$wl $c"; done; done |
xargs -P ${PAR:-2} -L 1 bash -c '
  wl=$0; c=$1; out='"$O"'/${wl}__${c}.txt; [ -s "$out" ] && exit 0
  cc=$c; [ "$c" = base ] && cc=
  HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=$cc timeout ${TMO:-400} '"$B"' --count /home/user/hylo-new/research/workloads/$wl.hylo > $out.tmp 2>&1 && mv $out.tmp $out || { echo "TIMEOUT/ERR" >> $out.tmp; mv $out.tmp $out; }'
