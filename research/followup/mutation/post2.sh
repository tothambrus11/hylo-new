#!/bin/bash
# Second pass: the decisive configurations on every blow-up, then the 2.5 GB recheck.
cd "$(dirname "$0")"
ALL="corpus/del-bound/011 corpus/del-bound/014 corpus/del-bound/015 corpus/del-bound/027 corpus/del-bound/028 corpus/del-given/031 corpus/del-where-req/000 corpus/del-where-req/009 corpus/del-where-req/013 corpus/del-where-req/025 corpus/del-where-req/026 corpus/repl-typearg/005 corpus/repl-typearg/018 tests/del-where-req/012 tests/del-where-req/019 tests/repl-typearg/007 workloads/del-where-req/016"
python3 attrib.py --configs "min5+budget;min5+eqmgu;fix;fix-eqmgu;fix-eqsolve;fix-budget;full-absmodel,absquotient" $ALL >> attrib.log 2>&1
python3 recheck.py min5 > recheck.log 2>&1
echo post2-done
