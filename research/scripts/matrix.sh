#!/bin/bash
# Usage: matrix.sh "cfg1 cfg2 ..." workload...  -> prints type.user (best of 3) and key counters.
B=/home/hylo/hylo-tc/hylo-new/.build/release/tc-bench
cfgs=$1; shift
for f in "$@"; do
  for c in $cfgs; do
    x=${c/baseline/}
    o=$(HYLO_TC_ABSDEPTH=${ABSDEPTH:-2} HYLO_TC_EXPERIMENTS=$x timeout 600 $B --count $f 2>&1)
    t=$(HYLO_TC_ABSDEPTH=${ABSDEPTH:-2} HYLO_TC_EXPERIMENTS=$x timeout 600 $B --repeat 3 --quiet $f 2>&1 | awk '/type.user/{print $2}')
    d=$(echo "$o" | awk '/^diagnostics/{print $2}')
    k=$(echo "$o" | grep counters.user | tr ' ' '\n' | grep -E "^(summon.matches|summon.layers|summon.depthExhausted|absmodel.refuted|names.appliesCalls|solver.forks|loopcheck.pruned)=" | tr '\n' ' ')
    printf "%-22s %-36s %10s ms  diag=%s  %s\n" "$(basename $f .hylo)" "[$c]" "$t" "$d" "$k"
  done
done
