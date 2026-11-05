#!/bin/bash
# Differential test: run every single-file compiler test under each experiment configuration and
# compare the diagnostics against the baseline.
B=/home/hylo/hylo-tc/hylo-new/.build/release/tc-bench
OUT=/home/hylo/hylo-tc/research/diff
T=/home/hylo/hylo-tc/hylo-new/Tests/CompilerTests
run() { # config file
  local cfg=$1 f=$2 name
  name=$(echo "$f" | sed "s|$T/||; s|/|__|g")
  mkdir -p "$OUT/$cfg"
  HYLO_TC_ABSDEPTH=2 HYLO_TC_EXPERIMENTS=${cfg/baseline/} timeout 120 $B "$f" 2>&1 \
    | grep -vE "^(parse|scope|type\.|counters)" > "$OUT/$cfg/$name.txt"
  echo "exit=${PIPESTATUS[0]}" >> "$OUT/$cfg/$name.txt"
}
export -f run; export B OUT T
for cfg in "$@"; do
  find $T/positive $T/negative -maxdepth 1 -name "*.hylo" | xargs -P 8 -I{} bash -c "run $cfg {}"
done
