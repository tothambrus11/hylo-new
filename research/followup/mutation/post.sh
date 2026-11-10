#!/bin/bash
# Post-processing after the main run: attribution of the blow-ups, repeated timing, depth sweep, shape probe.
cd "$(dirname "$0")"
A="tests/repl-typearg/007 corpus/del-bound/014 corpus/del-where-req/013 tests/del-where-req/012"
python3 attrib.py --configs "min5+eqmgu;min5+givencheck;min5+arrowenv;min5+extorder;min5+occurs;fix;fix-eqmgu;fix-givencheck;fix-arrowenv;fix-occurs;fix-extorder;fix-eqsolve;fix-budget" $A > attrib.log 2>&1
python3 timing.py -n 5 workloads/del-bound/002 workloads/del-bound/021 corpus/del-given/011 corpus/del-bound/022 tests/del-bound/017 tests/repl-typearg/018 corpus/del-ext-member/003 workloads/del-given/023 corpus/del-type-member/022 corpus/del-bound/012 workloads/del-ext-member/001 workloads/del-ext-member/002 workloads/del-type-member/030 stdlib/del-given/025 workloads/repl-typearg/041 > timing.log 2>&1
python3 depth.py workloads/swap-args/000 workloads/repl-typearg/041 tests/del-given/004 tests/del-given/020 workloads/del-bound/002 corpus/del-given/011 workloads/del-given/023 stdlib/del-given/002 > depth.log 2>&1
python3 depth.py --depths 6,10,14 tests/repl-typearg/007 corpus/del-bound/015 corpus/del-where-req/013 >> depth.log 2>&1
python3 shapes.py > shapes.log 2>&1
echo post-done
