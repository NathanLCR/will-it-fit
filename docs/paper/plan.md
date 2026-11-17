# Paper plan (drafted 2026-11-17)

Two outputs from one body of work. Venue facts, sources and prior work are in [venues.md](venues.md). All 2027 dates are estimates until the calls are published.

## What the papers claim

1. **Method.** Pick a local model per use case, not from a leaderboard. Real use cases are graded with checks fixed in advance, on frozen context, and every setup reads the same input.
2. **Honest comparison under noise.** Pass rates come with 95% intervals from a bootstrap over items (repeats kept with their item). Overlapping intervals count as a tie, and a tie goes to the cheaper setup. On small test sets like these, many "wins" turn out to be ties.
3. **Brazilian Portuguese findings.** A voice desk assistant needs a first sentence in under 1 s, short replies, tags, and no Portugal Portuguese. Thinking-on setups can't meet the latency rule. The two Portuguese papers in the #2 corpus test Portuguese answers.
4. **What building the eval caught.** The retriever missed the answer passage on 6 of the 20 original #2 items. PDF extraction splits Portuguese accents into separate characters and keeps typographic ligatures. These are side findings, and they make the case for evaluating each part of a pipeline separately.

Claims 1 and 2 need the phase 2 results. Without results there is no paper, only a method note.

## Output 1: arXiv technical report (English, cs.CL)

- **Scope:** everything. Covers #1, #2 and #4 with full results, speed and memory, the cloud baseline, the grader audit, failure types, and the robustness probe if it's done.
- **Length:** no limit. Aim for 8–12 pages plus appendices: test-set schema, sampling table, provenance format.
- **Artifact:** the public repo, tagged at the commit that produced the numbers. The report cites the tag, and every number traces back to `grades.json` and its provenance.
- **Blocker: endorsement.** A first-time arXiv submitter needs one. Check whether the university email auto-endorses. If not, ask a co-author or the supervisor.

## Output 2: STIL 2027 short paper (6 pages plus references)

- **Scope:** the Brazilian Portuguese part. That covers #4, with all its results, and #2 restricted to the 2 Portuguese papers. The accent-extraction finding fits here too.
- **Language:** Portuguese fits the venue and the topic. English is also accepted.
- **Review is double-anonymous.** The paper refers to the repo anonymously (e.g. anonymous.4open.science) until acceptance.
- **Fallback:** Linguamática (rolling, Portuguese). BRACIS (English, LNAI) if the paper grows toward the general method.

## Timing and the anonymity window

STIL and BRACIS ban public non-anonymous versions from 1 month before the deadline until notification. Pick one of these:

- **A (recommended):** post the arXiv report at least 5 weeks before the STIL deadline. Last year's deadline started at 30 Mar, so the target is **arXiv by mid-February 2027**.
- **B:** if results slip, hold arXiv until STIL notification.

| When (estimate) | Step |
|---|---|
| Dec 2026 | Phase 2: full runs with speed and memory, cloud baseline |
| Early Jan 2027 | Grader audit, failure-type tally, Pareto charts |
| Jan 2027 | Draft the tech report; publish public versions of the #2 and #4 material |
| Mid-Feb 2027 | Post to arXiv (path A) |
| Mar–Apr 2027 | Write the STIL short paper in Portuguese, anonymised |
| Apr–May 2027 | STIL deadline (estimate, watch for the call) |

## Before writing

- **Dissertation overlap.** Some #2 papers come from the MSc dissertation's references, and the method may overlap with the dissertation itself. Ask the supervisor whether this can be published separately, and whether they want to be a co-author.
- **Private material.** The papers describe the persona prompt and the copied passages but never reproduce them. Excerpts of the two STIL 2026 papers stay out, because neither prints a licence. The public test sets (phase 3) are what reviewers can rerun.
- **AI assistance.** Claude drafted test items and is the baseline. Disclose this per each venue's policy.
- **Prior work.** Open every link in venues.md before citing it. The research agent flagged ID and date mismatches. Not yet covered: LREC and the ACL-family Portuguese workshops, the PROPOR 2028 call, and JBCS.
