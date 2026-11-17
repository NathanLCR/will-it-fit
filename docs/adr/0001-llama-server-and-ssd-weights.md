# Serve every candidate from llama-server, with weights on the ZX20 SSD

Ternary-Bonsai-2-27B uses a custom ternary format that Ollama may not load, and #4 compares speed between candidates. If some candidates ran on Ollama and others on llama.cpp, the timings would partly measure the engine instead of the model. So every candidate runs on the same llama-server build (Prism's fork if Bonsai needs it), loading GGUF files. The internal disk has about 13 GB free, so weights live on the external ZX20 SSD, and `OLLAMA_MODELS` points there too.

## Considered Options

- **Ollama for qwen3.5/gemma4, llama-server for Bonsai**: easier, but #4 timings are confounded.
- **MLX for all**: often faster on Apple Silicon, but desk-assistant and article-rag talk to an OpenAI-compatible server, not MLX.

## Consequences

- No candidate can run when the SSD is unplugged.
- The winners still have to be served from llama-server in production, or #4 timings need checking again under Ollama.
