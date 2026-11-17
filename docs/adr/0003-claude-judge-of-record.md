# Claude is the judge of record; a local judge runs alongside

#5 and #6 are scored by blind side-by-side comparison. Bonsai 2 and qwen3.5 are both Qwen-based, so a local Qwen judge would favour them. Claude, which is independent of every candidate, is the judge whose verdict counts. A local judge scores the same pairs. Every disagreement goes to Nathan to review, and these disagreements are the test data for #9 (how well a local model judges).

## Consequences

- Test sets with the private flag can never be judged by Claude. They are graded only by local, automatic checks.
- Judging costs API tokens per comparison, so the number of setups compared side by side is kept small.
