# Vendored from article-rag (github.com/NathanLCR/article-rag) rag/prompts.py (build_answer_prompt, _build_context, CHUNK_ID_PATTERN); chunks are dicts here instead of RetrievedChunk.
import re

CHUNK_ID_PATTERN = re.compile(r"[\w.-]+-p\d+-c\d+\b")


def build_answer_prompt(question: str, chunks: list[dict]) -> str:
    context = _build_context(chunks)

    return f"""You are answering a question using only the provided context.

Rules:
- Answer only using the context blocks below.
- Cite claims using only citations copied from the context blocks.
- Do not invent citations or cite chunks that are not shown.
- If the evidence is insufficient, say the evidence is insufficient.
- Do not use outside knowledge.
- Write plain prose paragraphs. Do not use Markdown.

Question:
{question}

Context:
{context}

Answer:"""


def _build_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No context was retrieved."

    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"""Context block {index}
paper_id: {chunk["paper_id"]}
page_number: {chunk["page_number"]}
chunk_id: {chunk["id"]}
chunk_index: {chunk["chunk_index"]}
citation: [{chunk["paper_id"]}, page {chunk["page_number"]}, {chunk["id"]}]
text:
{chunk["text"]}"""
        )

    return "\n\n".join(blocks)
