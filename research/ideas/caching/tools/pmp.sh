#!/bin/bash
# Poor man's profiler: attaches gdb N times to a running tc-bench and saves backtraces.
# usage: pmp.sh OUT N -- tc-bench.real args...
OUT=$1; N=$2; shift 3
"$@" > /dev/null 2>&1 &
P=$!
sleep 1.5
: > "$OUT"
for i in $(seq 1 $N); do
  kill -0 $P 2>/dev/null || break
  gdb -batch --readnever -iex "set complaints 0" -p $P -ex "thread apply all bt 60" 2>/dev/null | grep -E "^Thread|^#" >> "$OUT"
  echo "=== END" >> "$OUT"
  sleep 0.05
done
kill $P 2>/dev/null
