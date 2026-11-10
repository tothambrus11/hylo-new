#!/bin/bash
cd /home/user/hylo-new/research/followup/metamorphic
MM_PER_GROUP=1 python3 reduce_all.py r5
T=../../report/test-programs
C=../../../Tests/CompilerTests/positive
for spec in "$C/generic-member.hylo intro-all:0" "$T/equalities/decomp-1.hylo intro-generic:0" "$C/context-bound.hylo intro-generic:0" \
            "$C/implicit-qualification.hylo intro-generic:0" "$C/overload-priority.hylo intro-generic:0" \
            "$T/equalities/x01-ext-arg-member.hylo intro-generic:0" "$T/cycles-and-crashes/o1-value-ctx.hylo intro-generic:0" \
            "$T/abstract-model/probe1.hylo intro-generic:0" "$T/equalities/x10b-ext-where-assoc.hylo intro-generic:0" \
            "$T/declaration-order/red2.hylo intro-all-top:0" "$T/equalities/x05-alias-ext.hylo intro-all:0" "$T/equalities/x07-given-arg-member.hylo intro-generic:0"; do
  set -- $spec
  python3 reduce.py $1 r5 $2 > /dev/null 2>&1; echo "done $spec"
done
