#!/bin/bash
# Resumable counter matrix: for each workload and each flag subset, record tc-bench --count output.
# Usage: countmatrix.sh BIN OUTDIR workload[:required-flag] ...
# A config is skipped if its output file exists (resumable). Counters are deterministic.
B=$1; O=$2; shift 2
FL=(names unify index absmodel solver loopcheck)
run() {
  local wl=$1 cfg=$2 f=$3
  local out=$O/$(basename $wl .hylo)__${cfg:-baseline}.txt
  [ -s "$out" ] && return
  HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=$cfg timeout 300 $B --count $f > $out.tmp 2>&1 && mv $out.tmp $out || echo "TIMEOUT/ERR" > $out
}
export -f run; export B O
for spec in "$@"; do
  wl=${spec%%:*}; req=${spec#*:}; [ "$req" = "$spec" ] && req=""
  f=/home/hylo/hylo-tc/research/workloads/$wl
  for m in $(seq 0 63); do
    cfg=""; ok=1
    for i in 0 1 2 3 4 5; do (( (m>>i)&1 )) && cfg="$cfg${cfg:+,}${FL[$i]}"; done
    for r in ${req//+/ }; do [[ ",$cfg," == *",$r,"* ]] || ok=0; done
    [ $ok = 1 ] && echo "$wl $cfg $f"
  done
done | xargs -P 4 -L 1 bash -c 'run "$0" "$1" "$2"' 
