#!/bin/sh
# The whole campaign, in order. Every step is restartable: rows already in results.jsonl are
# skipped. All compiler runs go through tc.py, which runs one compiler process at a time.
set -e
cd "$(dirname "$0")"
[ -f problems.jsonl ] || python3 fuzz.py gen
# FIX and FULL on every problem, six problems per compiler run (disjoint names).
python3 fuzz.py run FULL FIX --batch 6
# The existing checker (base) on a subset: it often fails to terminate on equalities, so each
# query is run alone with a short time limit outside the conformance-only kind.
python3 fuzz.py run base --kinds conf --limit 120 --timeout 8
python3 fuzz.py run base --kinds eq-param,eq-app,chain,cond,assoc,twin,blanket --limit 5 --isolate --timeout 8
# Every problem with a disagreement in a batch is run again alone; report.py uses that run.
# The acceptances of underivable goals first, then the rest.
python3 fuzz.py confirm FULL FIX --classes UNSOUND,BEYOND-SPEC,ILLFORMED-accept,BUDGET-agree
python3 fuzz.py confirm FULL FIX
python3 report.py --markdown > tables.md
