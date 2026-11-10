#!/bin/bash
# Prints the verdict and the counters of the user module for the programs of problem/, under
# base and FULL. usage: run-problem.sh > results/problem.txt
cd "$(dirname "$0")/.."
for f in problem/*.hylo; do
  for c in base FULL; do
    r=$(./run.sh $c --count "$f")
    n=$(echo "$r" | sed -n 's/^diagnostics: //p')
    echo "== $(basename $f) $c: $([ "$n" = 0 ] && echo accepted || echo "rejected ($n errors)")"
    echo "$r" | grep "^counters.user" | sed 's/^counters.user: */   counters: /'
    echo "$r" | grep ": error: " | sed 's/^.*hylo:/   /'
  done
done
