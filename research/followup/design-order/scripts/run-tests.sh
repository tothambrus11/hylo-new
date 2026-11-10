#!/bin/bash
# Type-checks the programs of tests/ in permuted declaration orders, one process at a time.
# usage: run-tests.sh CONFIG MAX OUT.jsonl      (CONFIG = base | FIX | FULL; MAX = permutations per program)
# Restartable: programs already in OUT.jsonl for CONFIG are skipped.
cd "$(dirname "$0")/.."
grep -v '^#' tests/MANIFEST.tsv | while IFS=$'\t' read -r f fix expected; do
  python3 scripts/orders.py "$3" "$1" --max "$2" --fix "$fix" "tests/$f"
done
