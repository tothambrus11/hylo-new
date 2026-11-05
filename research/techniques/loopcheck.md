# `loopcheck` (retired): prune subgoals identical to an ancestor

## How it works

Each pending premise records the goals it is a subgoal of. `summon` returns no thread for a subgoal whose reified type equals one of its ancestors.

## Why it is NOT sound here

The Bol–Apt–Klop argument says that in a smallest derivation no subgoal repeats an ancestor, because the ancestor's derivation could be replaced by the subgoal's. That argument assumes pure SLD resolution. Hylo's engine differs in three ways:
- it lets a goal use **pending sibling premises** as hypotheses;
- it selects results by (BFS layer, penalty);
- it reports ambiguity among equally good results.

With a pending premise, the repeated subgoal can be strictly cheaper than the ancestor, so the graft argument fails. Confirmed counterexamples (`research/review/loopcheck/`):
- LC-1: a different witness is selected;
- LC-2: a success within the depth cap becomes "no given instance";
- LC-3: an ambiguity the baseline reports disappears.

## Status

Every divergence workload it helped with is also handled by `absmodel`, and it never fires on the stdlib. Retired. A restricted variant that prunes only when no pending sibling premise was introduced between the ancestor and the subgoal would restore the argument (see the LC-1..3 fixes in `review/RESULTS-round2.md`). It is only worth doing if it is needed for termination.
