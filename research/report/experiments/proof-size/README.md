# Ranking equality proofs by their size: an experiment

Status: experiment, not adopted. `../../questions/ANSWERS.md` (questions 6 and 10) explains the defect that it addresses and why it is not enough.

`0033-*.patch` applies after `../inferred-givens/0032-*.patch`, itself after the series of `../../patches`. It adds:

- the flag `eqsize`: a proof returned by the equality procedure waits as many layers as its derivation has steps, so that it completes where search would have completed it;
- self-check counters `selfcheck.equality.sizeConfirmed`, `searchSmaller`, `searchLarger`: whether search completes an equality in the layer that the procedure reports;
- counters `names.tiedOnDistance`, `names.decidedByWitnessSize`, `names.decidedByWitnessSizeWithCoercion`: the comparisons of name-resolution candidates that the size of a witness term decides.

| Program | Existing | Recommended | With `eqsize` |
|---|---|---|---|
| `test-programs/equalities/pen-ref-3.hylo` | rejected (ambiguous) | accepted | rejected (ambiguous) |
| `test-programs/performance/pending-var-3.hylo` | rejected (172,383 matches) | accepted (693) | rejected (34,161) |
| `test-programs/performance/pending-var-4.hylo` | accepted (102,150 matches) | accepted (782) | rejected at the work budget (171,221) |

No other verdict changes on 1,696 programs, and the semantic dump of the compiler's tests is unchanged. Data: `../../follow-up/data/answers/compare-eqsize.jsonl`, `size-parity.jsonl`, `witness-size.jsonl`.
