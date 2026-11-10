# Abstract model of the givens: proving that a search will fail (`absmodel`)

**Kind:** speed-up; results are unchanged.

## Problem

The checker rejects an unprovable goal only after exploring every alternative up to its depth cap of 10 steps. With branching or looping givens, that exploration is exponential. A function with an unsatisfiable requirement, like `fun f<T where T is P>()` called with a type that is not `P`, can take seconds to reject.

The question that started this work: is there a cheap, sound test that tells in advance that resolution will fail?

## How it works

1. **Givens as rules.** Every given becomes a logic rule:
   - `given <T where T is P> Box<T> is Q` becomes "`Q(Box(T))` holds if `P(T)` holds";
   - nominal types and type applications become function symbols;
   - tuples become lists;
   - the given's generic parameters become variables;
   - every other kind of type (functions, associated types, …) becomes a wildcard `⊤`.
2. **Bounded saturation.** Everything the rules derive is computed bottom-up. Terms are cut off below depth 2, and the cut parts become `⊤`, so only finitely many facts exist and the computation ends. This is depth-k abstraction (Sato and Tamaki, 1984).
   - It is semi-naive evaluation: a rule is re-applied only when one of its premises has a new fact.
   - Models are built incrementally along the scope tree, and shared between files that import the same modules.
3. **Test.** Before the search tries anything for a subgoal, it checks whether the subgoal matches some fact of the model. If none matches, the subgoal is refuted and no work is spent on it.

Some cases are treated conservatively:
- equality goals are never refuted;
- equality premises are assumed to hold;
- a given whose conclusion is an equality, or a bare type variable, makes the model inconclusive (it then refutes nothing), unless `absquotient` applies.

## Why it is correct

**The model over-approximates.** Every proof the real search can find maps to a derivation in the model:
- cutting terms off is monotone;
- `⊤` matches anything;
- dropping premises only adds facts.

So a goal that matches no fact has no proof, whatever the search order and the depth cap.

**Pruning changes nothing visible.** A refuted subgoal contributes no result in any search layer. Removing it leaves the chosen proof, its penalty and any ambiguity unchanged. The diagnostic is the same as well, because the caller reports the failure in both cases.

**Temporary assumptions.** A subgoal may be posed under assumptions made during the search, such as a pending requirement of a conditional given. The model ignores them, which is safe: every assumption must itself be proved from the scope before a proof is accepted. If the subgoal is not derivable from the scope, every proof that needs it fails anyway.

**Details that matter for soundness:**
- A repeated variable in a fact never matches a term containing `⊤`, because two `⊤`s denote unrelated terms.
- A variable that would be bound to a term containing itself is bound to `⊤` instead.
- File-level models are keyed by the file's imports.
- The variables of facts are renamed apart from those of rules.

## What it speeds up

Failing and looping resolutions:

| Program | Without | With `absmodel` |
|---|---:|---:|
| unprovable goal with branching givens | 2.2 s | 15 ms (150×) |
| 20 looping goals | 191 ms | 16 ms (12×) |
| standard library | 1.0 s | 0.79 s (1.3×) |

With the model, the cost of a refutable failure no longer depends on the depth cap: in the branching program, raising the cap from 10 to 14 takes the old checker from 2.3 s to 44.5 s, and the model from 3 ms to 3 ms.

**Limit.** A fact deeper than the cut-off makes the model derive `P(⊤)`, after which no `P` goal can be refuted. The search is still pruned inside, but it stays exponential in the cap. `budget` bounds what remains.

## Cost

- About 1,400 facts for the standard library, a few milliseconds to compute.
- A depth of 3 instead of 2 multiplies the facts on tuple-heavy code by 10 and refutes nothing more, so the default is 2 (`HYLO_TC_ABSDEPTH`).
