# Equalities in scope: keeping the index, deciding at once (`eqindex`, `eqeager`)

**Kind:** result-preserving, with one intended exception stated below. About 200 lines. Design and adversarial review: `../follow-up/designs/eqnorm.md`.

## The problem

Two costs appear as soon as a scope has a where clause with an equality, however unrelated to the goal at hand.

1. **The index of givens is switched off.** The index (`index.md`) hands resolution only the givens whose head constructor is that of the goal. An equality could relate two different constructors, so one equality in scope made every resolution in that scope try every given again. With 40 conformances in scope and `where A == B`, 40 resolutions make 4,480 candidate matches instead of 1,680.
2. **Each equality between parts of two types costs one search step.** To use `given W<T0, …, T7> is P` for the goal `P<W<U0, …, U7>>` under `Ti == Ui`, matching assumes eight equalities and proves them one per step, last first. The search depth is bounded by 10, so a type with eight or more differing arguments cannot be matched at all: the valid program is rejected, and the existing implementation exhausts memory on it.

## How it works

**`eqindex`.** The index stays valid when every equality in scope is closed (no type parameters of its own) and neither of its sides is a type constructor that takes arguments: such equalities cannot relate two different head constructors. The index is then used as if there were no equality. It is still switched off if a given or the goal is a type alias at its root, because matching may coerce the whole type of such a given.

**`eqeager`.** When a match leaves closed mismatching parts, the equality procedure (`eqsolve.md`) is asked about each of them at once, in the environment in which search would have asked: the earlier parts assumed, the later ones not. If any part is refuted, the match fails immediately. Otherwise the match proceeds with the proofs' penalties, and the resulting thread *waits* as many steps as search would have spent, so that it completes at the same step and is ranked as before. The waiting steps do not count against the depth bound.

## Why results are preserved

- `eqindex` skips a given only if matching it would fail: with rigid equalities, two types with different head constructors cannot be coerced. The self-checking mode re-matches every skipped given.
- `eqeager` asks the equality procedure the questions that search would have asked, with the same hypotheses, and reproduces the step at which the thread completes. Search would have called the same procedure for each part; the only difference is when.
- The self-checking mode runs each resolution a second time with the equalities assumed and proved by search, and compares the results.

The semantic dump of the 216 files of the compiler's tests and workloads is identical with and without the two flags.

**The intended exception.** A match that needs more equalities than the depth bound allows was rejected and is now accepted (the eight-argument example above). A search that used to stop silently at the depth bound can now run deeper; if it then exceeds the work budget it also ends silently, as before, and not with an error.

## What it costs

A resolution that fails at the depth bound today can do more work before it fails, up to the work budget. This was not measured on real code; no resolution of the standard library or of the compiler's tests reaches the bound.

## What the review found

The first implementation of these two flags had three defects that the corpus comparison and the self-check did not show, and that an adversarial review found by reading the code: an index entry filed under the constructor of an aliased type, an error reported where the search used to end silently, and a condition that made the result depend on whether a call was the initializer of a binding or the operand of `return`. All three are corrected and have regression tests (`follow-up/design-eqnorm/tests/attack-01`, `-04`, `-05`). One consequence remains by design: an extension or overload that did not apply because its resolution ended at the depth bound can apply now.

## Measurements

| Program | Counter | Without | With |
|---|---|---:|---:|
| `cost-01` (40 conformances, one unrelated equality) | candidate matches | 4,480 | 1,680 |
| `gain-01` (eight differing type arguments) | verdict | rejected at the depth bound | accepted, 11 candidate matches |
