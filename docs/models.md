# Candidate model files

The weights live in `$GGUF_DIR` (an external SSD on my machine), and every model is served with Homebrew `llama-server` 1.0.0 (build 12359). See ADR 0001.

| Candidate | File | Source | Size | Cold load |
|---|---|---|---|---|
| Bonsai 2 27B | `Ternary-Bonsai-2-27B-Q2_0.gguf` | prism-ml/Ternary-Bonsai-2-27B-gguf | 7.63 GB | ~5.6 min |
| qwen3.5 9B | `Qwen3.5-9B-Q4_K_M.gguf` | unsloth/Qwen3.5-9B-GGUF | 5.68 GB | ~3.3 min |
| gemma4 E4B | `gemma-4-E4B-it-Q4_K_M.gguf` | unsloth/gemma-4-E4B-it-GGUF | 4.98 GB | under 3 min |

All three loaded on 2026-11-17 with `-c 8192 -ngl 99`. No prompts were sent.

- **Bonsai uses Q2_0**, the packing that stock llama.cpp runs. The smaller PTQ1_0 and PQ2_0 packings need Prism's llama.cpp fork, which would mean a second runtime.
- **gemma4 is the E4B model.** It's the same one Ollama serves as `gemma4:latest` (7.5B total parameters).
- **Cold loads are slow from the SSD.** Start the server and wait for `/health` before a run, so load time never lands in #4's first-sentence latency.

## Sampling settings

Each model runs on its vendor's recommended settings, decided 2026-11-17. A single shared temperature would put at least one model at a disadvantage. The values are in `runner/sampling.json`, keyed by candidate and by thinking on or off:

- **Bonsai 2:**
  - Thinking on: temperature 1.0, top_p 0.95, top_k 20, min_p 0.05
  - Thinking off: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5
- **qwen3.5 9B:** Qwen's "general tasks" values.
  - Thinking on: temperature 1.0, top_p 0.95, top_k 20, presence_penalty 1.5
  - Thinking off: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5

  Qwen also publishes a coding preset (temperature 0.6 with thinking). #7 may want it later.
- **gemma4:** temperature 1.0, top_p 0.95, top_k 64, the same in both modes.

Because sampling isn't deterministic, a single run per item is noisy. Each setup runs every item 3 times (`--repeat 3`). Pass rates are reported with 95% item-bootstrap confidence intervals (items resampled with their repeats), and only close calls get extra repeats (decided 2026-11-17).
