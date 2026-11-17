# A standalone runner with frozen context, not the real apps

The question is which candidate is better, so every setup must see the same input. Instead of swapping models inside article-rag and desk-assistant, a standalone runner sends each test item's frozen context to an OpenAI-compatible endpoint. For #2, article-rag's retrieval runs once and the passages are saved into the test items. For #4, the runner reuses desk-assistant's real system prompt and sentence splitter. For #1, tool schemas are copied from the real apps, but every tool is a fake that only records the call.

## Considered Options

- **End to end in the real apps**: more realistic, but differences in retrieval, prompts and app state blur the model comparison, and #1 would run real tools.

## Consequences

- A frozen test set goes stale when an app changes its prompt or retrieval; re-freeze it before trusting new results.
- The eval does not prove the winner works inside the app; run one end-to-end check with the winner before switching.
