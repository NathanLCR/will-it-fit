# local-model-eval

Which local models, run on my Apple M2 16 GB Mac, are good enough for each of my real use cases? Public leaderboards rank models on tasks I never do, on hardware I don't own. I would rather know which setup wins at the three jobs I actually give a local model, at what speed and memory cost, and where the winner is only tied with something cheaper.

The candidates are Bonsai 2 27B (Q2_0), qwen3.5 9B and gemma4 E4B, all served by `llama-server`. No model has been run yet; the harness, test sets and decisions are in place.

## Results

**Runs in progress.** The table below is empty on purpose. I won't fill it with numbers until the full runs finish.

| Use case | Winner | Pass rate (95% CI) | Runner-up | Safety score (#1 only) | Tokens/s | Peak RAM |
|---|---|---|---|---|---|---|
| #1 Tool-calling agent | | | | | | |
| #2 Answering from my PDFs | | | | n/a | | |
| #4 PT-BR voice desk assistant | | | | n/a | | |
| Cloud baseline (Claude, reference only) | n/a | | n/a | | | |

The baseline row is a reference point for how far local setups are from the frontier. Claude can never win a use case, and it never sees a test set with the private flag.

_Pareto charts (pass rate against speed and against memory), one per use case: pending._

## How it works

**Use cases.** This first slice covers three of my uses:

- **#1 Tool-calling agent.** The model gets a task and a set of tools and has to call the right ones with the right arguments. Every tool is a fake that only records the call. The test set has 16 normal items and 4 trap scenarios that invite a destructive tool call. Traps get a separate safety score.
- **#2 Answering from my PDFs.** The model answers from retrieved passages. The corpus is 9 papers, 2 of them written in Portuguese. The test set has 34 items (25 answerable, 9 unanswerable, where the right answer is to say the text doesn't contain it).
- **#4 PT-BR voice desk assistant.** 20 Brazilian Portuguese utterances answered in my assistant's persona. The first sentence must be ready in under 1 s (first sentence latency), with at most 3 sentences, an emotion tag, correct action and fact tags, and no Portugal Portuguese. With thinking on, the first sentence comes only after the thinking, so it can't meet the 1 s rule. Think-on setups are scored on the content checks only, in a side column outside the #4 winner race.

**Setups.** A setup is a candidate with thinking on or off, written `candidate-think` or `candidate-nothink`. That is the unit that gets a score.

**Frozen context.** Every setup reads the same input. For #2, article-rag's retrieval ran once and the passages are saved in the test items. For #4, the runner reuses my desk assistant's real system prompt and sentence splitter. For #1, tool schemas are reconstructed from my real agent's tools, and every tool is a mock. See [ADR 0002](docs/adr/0002-standalone-runner-frozen-context.md).

**Serving.** Every candidate runs on the same `llama-server` build, so timings measure the model and not the engine. Weights live on an external SSD. See [ADR 0001](docs/adr/0001-llama-server-and-ssd-weights.md) and [docs/models.md](docs/models.md).

**Sampling.** Each model uses its vendor's recommended settings, because one shared temperature would handicap at least one of them. The values are in `runner/sampling.json`:

| Candidate | Thinking on | Thinking off |
|---|---|---|
| Bonsai 2 27B | temp 1.0, top_p 0.95, top_k 20, min_p 0.05 | temp 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 |
| qwen3.5 9B | temp 1.0, top_p 0.95, top_k 20, presence_penalty 1.5 | temp 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 |
| gemma4 E4B | temp 1.0, top_p 0.95, top_k 64 | same |

**Repeats and confidence intervals.** Sampling is not deterministic, so each setup runs every item 3 times (`--repeat 3`). Pass rates are reported with 95% confidence intervals from an item bootstrap. Whole items are resampled together with their repeats, because a hard item tends to fail every repeat and treating the runs as independent would make the intervals too narrow. Only close calls get extra repeats.

**Winner rule.** The highest pass rate wins. If its confidence interval overlaps the runner-up's, the result is a tie and the cheaper setup wins: thinking off before thinking on, then the smaller weights. #1 picks its winner on accuracy alone, with the safety score shown next to it, so a setup that made a destructive call can still win and the reader sees that. The reasoning is in the [glossary](GLOSSARY.md) and [docs/models.md](docs/models.md); ADR [0003](docs/adr/0003-claude-judge-of-record.md) and [0004](docs/adr/0004-use-cases-over-grader-types.md) cover judging and the grader design.

## What makes the numbers trustworthy

- **Run provenance.** Every run appends a record to `results/<setup>/<set>.provenance.json`. It holds the model file sha256, the llama-server build, the sampling settings actually sent, the test set sha256, the git commit (and whether the tree was dirty) and the command line. `grade.py` carries it into `grades.json`.
- **Grader audit (planned).** I will hand-check about 10% of the automatic verdicts and report the agreement rate here.
- **Failure types (partly done).** Each failed item gets a reason from a fixed list (wrong tool, invented argument, Portugal Portuguese, too long, missed "not in the text"). They explain scores and do not change them. `grade.py` prints reasons per item; a tally by type is planned.
- **Robustness probe (planned).** A paraphrased copy of the test items, to check that a setup's score doesn't depend on my exact wording.
- **Offline grader test.** `python3 runner/test_grade.py` checks the graders without a model.

## What this eval caught

Building the #2 test set found a problem in my own retrieval. article-rag's retrieval missed every passage holding the answer for 4 of the 20 #2 items (p05, p11, p12 and p14), mostly specific numbers in the results section of one paper. If I had left them in, #2 would have partly measured the retriever and not the model. I injected the missing gold passages in place of the lowest-ranked results, and the freeze script keeps that swap. When I grew the corpus from 2 papers to 9, retrieval lost the answer for 2 more items, which is the distractor effect a small corpus hides. Indexing the two Portuguese-language papers also showed that the PDF extraction splits accents into separate characters ("recuperac¸˜ao"). That hurts any Portuguese search on those words. Details are in [testsets/README.md](testsets/README.md).

## Run it yourself

**Prerequisites**

- Homebrew `llama-server` (`brew install llama.cpp`). I used 1.0.0, build 12359.
- The GGUF files, listed in [docs/models.md](docs/models.md). Mine are on an external SSD at `/Volumes/ZX20/models/gguf/`.
- Python 3, standard library only.

**1. Start the server and wait until it is ready.** Cold loads take 3 to 6 minutes from the SSD, and the load must not land inside #4's timings.

```bash
llama-server -m /Volumes/ZX20/models/gguf/Qwen3.5-9B-Q4_K_M.gguf -c 8192 -ngl 99 --port 8080 &
until curl -sf http://localhost:8080/health >/dev/null; do sleep 5; done
```

**2. Run a test set.** `--candidate` is `bonsai2`, `qwen3.5-9b` or `gemma4`. Raw results go to `results/<setup>/<set>.jsonl`.

```bash
python3 runner/run.py \
  --set testsets/01-tool-agent.json \
  --base-url http://localhost:8080 \
  --model qwen3.5-9b --candidate qwen3.5-9b --think off \
  --setup qwen3.5-9b-nothink --repeat 3 \
  --gguf /Volumes/ZX20/models/gguf/Qwen3.5-9B-Q4_K_M.gguf
```

Other flags: `--only ID,ID` runs selected items, and `--include-drafts` also runs items not marked `approved`.

**3. Grade a setup's results.** Pass the results folder; it prints a table per set and writes `grades.json` there.

```bash
python3 runner/grade.py results/qwen3.5-9b-nothink
```

**4. Self-test, offline.**

```bash
python3 runner/test_grade.py
```

`testsets/02-pdf-answers.json` and the persona prompt are kept local (see below), so a fresh clone can run #1 only until you supply your own #2 and #4 material.

## Use it for your own use cases

Planned: `AGENTS.md` will become a guide for your own coding agent (Claude Code, Codex, Gemini/Antigravity) to build evals for your uses and data. A use case will be a folder with a test set that names reusable grader types (tool-call match, fact check against passages, format and timing rules, blind judging), as decided in [ADR 0004](docs/adr/0004-use-cases-over-grader-types.md). Today the graders are still per use case.

## Limitations

- The #1 tool schemas are reconstructed, not exported from the real app.
- Frozen context goes stale when the apps change their prompts or retrieval. Re-freeze before trusting new results.
- One machine: an M2 with 16 GB. Speed and memory numbers will not transfer to other hardware.
- The #2 corpus is 9 papers (2 written in Portuguese). That's enough for retrieval to need to tell papers apart, but it's far smaller than a real library.
- Sampling is noisy. Repeats and intervals reduce that and do not remove it.
- A win here does not prove the model works inside the app. I plan one end-to-end check with each winner before I switch to it.

## What's not in this repo

My real persona prompt (`testsets/frozen/desk-system-prompt.txt`) and the copied paper passages (`testsets/02-pdf-answers.json`) are kept local through `.gitignore`. Raw model outputs under `results/` are also ignored because they can quote that private context. Only summaries in `results/summary/` are published.

The **private flag** marks a test set whose content must never leave this machine. Claude, as baseline or as judge, never sees such a set, and it is graded only by local, automatic checks. The flag is a convention, not enforced by code. The planned `AGENTS.md` guide will document it.

## Roadmap

- Use cases #3 and #5 to #9. (#8 was retired and replaced by the private flag.)
- #5 and #6 are judged by blind side-by-side comparison. Claude is the judge of record, with a local judge running alongside it. Their disagreements go to me for review and become the test data for #9, how well a local model judges. See [ADR 0003](docs/adr/0003-claude-judge-of-record.md).
- Grader-type refactor, with earlier runs re-graded offline to confirm the scores don't change.
- A static results page and a write-up post.

## License

MIT. See [LICENSE](LICENSE).
