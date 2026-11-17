"""Fill context_chunks in testsets/02-pdf-answers.json from article-rag's index.

Retrieved items: article-rag Retriever.hybrid_retrieve([question], top_k=6).
Items with injected_gold: those chunks replace the lowest-ranked results (total stays top_k).
Full-paper items: every chunk of each context_papers paper, page/chunk order.
Run with article-rag's venv: /Users/nathanlucio/Desktop/Projects/article-rag/.venv/bin/python scripts/freeze_pdf_context.py
"""
import json
import sys
from pathlib import Path

RAG = Path("/Users/nathanlucio/Desktop/Projects/article-rag")
sys.path.insert(0, str(RAG))
from rag.embeddings import create_embedder  # noqa: E402
from rag.retrieval import Retriever  # noqa: E402
from rag.vector_store import ChromaVectorStore  # noqa: E402

PATH = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "testsets" / "02-pdf-answers.json")
TOP_K = 6


def conv(c):
    return {"chunk_id": c.id, "paper_id": c.paper_id, "page_number": c.page_number,
            "chunk_index": c.chunk_index, "text": c.text}


store = ChromaVectorStore()
retriever = Retriever(create_embedder(), store)
data = json.loads(PATH.read_text(encoding="utf-8"))
for it in data["items"]:
    if it["context_mode"] == "full_paper":
        chunks = [c for p in it["context_papers"] for c in store.get_paper_chunks(p)]
    else:
        hits, _ = retriever.hybrid_retrieve([it["question"]], top_k=TOP_K)
        chunks = [h.chunk for h in hits]
        inj = it.get("injected_gold")
        if inj:  # keep top-ranked non-injected chunks, then append the injected gold from the index
            chunks = [c for c in chunks if c.id not in inj][: TOP_K - len(inj)] + [store.get_chunk(i) for i in inj]
    it["context_chunks"] = [conv(c) for c in chunks]
    ids = [c.id for c in chunks]
    if it["answerable"]:
        g = it["gold_chunks"]
        print(it["id"], it["context_mode"], f"{sum(x in ids for x in g)}/{len(g)}", [x for x in g if x not in ids])
    else:
        print(it["id"], "unanswerable", ids)
PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
