#!/bin/bash
# Type-checks the seven order-dependent programs of the review in permuted declaration orders.
# usage: run-seven.sh CONFIG MAX OUT.jsonl
cd "$(dirname "$0")/.."
D=/home/user/hylo-new/research/report/test-programs/declaration-order
while read -r f fix; do
  python3 scripts/orders.py "$3" "$1" --max "$2" --fix "$fix" "$D/$f"
done <<'LIST'
al1.hylo 2
al2.hylo 2
al3.hylo 2
names-n11_poison_via_summon.hylo 3
names-n12_poison_via_summon_noearly.hylo 3
names-verify-names-1-v6_summon_swapped.hylo 3
names-verify-names-2-v01_ext_declares_foo.hylo 0
LIST
