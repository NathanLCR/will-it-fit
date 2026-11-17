# Local Model Eval

A way to measure which local models, run on this Mac, are good enough for each of Nathan's real uses, and to pick a winner per use.

## What is being tested

**Use case**:
One real job a local model is asked to do, with its own definition of "good" and its own way of grading it. Numbered #1 to #9 (#8 retired, see **Private flag**).
_Avoid_: Task, category, benchmark

**Candidate**:
A model being evaluated, as a specific set of weights (e.g. Ternary-Bonsai-2-27B, qwen3.5:9b, gemma4).
_Avoid_: Model under test, contender

**Setup**:
One candidate with thinking mode on or off; the unit that gets a score. Written as `candidate-think` or `candidate-nothink`.
_Avoid_: Config, variant, run config

**Baseline**:
A cloud model run on the same test sets as a reference point for how far local setups are from the frontier. It is never a candidate and cannot be a winner, and it never sees a test set with the private flag.
_Avoid_: Upper bound, reference model, oracle

**Winner**:
The setup with the best score on one use case. Each use case has its own winner. When the best score is within the noise of the runner-up's, the result is a **tie**, and the cheaper setup of the two is named the winner. Cheaper means thinking off before thinking on, then the candidate with the smaller weights.
_Avoid_: Best model, champion

## Test material

**Test set**:
The fixed list of test items for one use case.
_Avoid_: Dataset, benchmark, suite

**Test item**:
One input plus what a good answer must contain or do.
_Avoid_: Case, example, sample, prompt

**Gold answer**:
The approved expected answer for a test item, drafted by Claude and approved by Nathan.
_Avoid_: Ground truth, reference, label

**Unanswerable item**:
A test item for #2 whose answer is not in the papers; the right response is to say so.
_Avoid_: Negative, trick question

**Trap scenario**:
A test item for #1 that invites a destructive tool call.
_Avoid_: Adversarial case, red-team item

**Frozen context**:
The exact passages, prompt and history fixed in a test item, so every setup reads the same input.
_Avoid_: Cached retrieval, snapshot

**Private flag**:
A mark on a test set whose content must never leave this machine. It replaces use case #8.
_Avoid_: Sensitive, confidential, use case #8

## Grading

**Grader**:
Whatever decides if an answer is good: an automatic check, unit tests, a judge or Nathan.
_Avoid_: Scorer, evaluator, metric

**Grader type**:
A reusable kind of grader that a use case picks: tool-call match, fact check against passages, format and timing rules, or blind judging. A use case may use more than one.
_Avoid_: Metric, scorer class, check

**Failure type**:
The reason a setup failed a test item, from a fixed list (e.g. wrong tool, invented argument, Portugal Portuguese, too long, missed "not in the text"). Used to explain scores, not to make them.
_Avoid_: Error category, bug, failure mode

**Judge**:
A model that compares two answers blind and picks the better one. Claude is the judge of record; a local judge runs alongside it.
_Avoid_: Evaluator model, critic, rater

**Disagreement**:
A test item where Claude and the local judge picked different answers. Claude's verdict counts; Nathan reviews it, and it feeds #9.
_Avoid_: Conflict, tie

**Safety score**:
For #1, the share of trap scenarios where the setup made no destructive tool call. Reported next to accuracy, not folded into it.
_Avoid_: Harm score, refusal rate

**First sentence latency**:
For #4, time from sending the request until the first full sentence is ready to be spoken.
_Avoid_: Latency, TTFT, response time
