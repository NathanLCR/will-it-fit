# Use cases are folders that pick from reusable grader types

The repo is meant to be forked: other people point their own coding agent (Claude Code, Codex, Gemini/Antigravity) at AGENTS.md and build evals for their own uses and data. If grading stays hard-coded per use case number, every fork edits the grader for its own cases, and forks drift apart until fixes can't flow back. So grading is split into a few reusable grader types (tool-call match, fact check against passages, format and timing rules, blind judging). A use case is a folder holding its test set and naming the grader types it uses. Nathan's #1, #2 and #4 become the shipped examples.

## Considered Options

- **Keep hard-coded graders, document how to edit them**: less work now, but every fork rewrites the grader and the method in AGENTS.md has nothing stable to point at.

## Consequences

- A use case that needs a new kind of check needs a new grader type, not a special case inside an existing one.
- The refactor lands after the first full runs. Raw outputs are saved, so the earlier runs are re-graded offline to make sure the scores don't change.
- The private flag stays a convention that AGENTS.md documents. Code doesn't enforce it (decided 2026-11-17).
