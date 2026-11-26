import chromadb
from llm import ask_llm

client = chromadb.PersistentClient(path="chroma_db")

CHUNK_SIZE = 800
OVERLAP = 100
TOP_K = 4

RAG_PROMPT = """You are a study assistant answering questions about a student's notes.
Use ONLY the excerpts below. If the answer is not in the excerpts, reply exactly:
"I couldn't find this in your notes."
Keep the answer clear and short. Mention page numbers like (p. 3).

EXCERPTS:
{context}

QUESTION: {question}
"""


def _name(user_id, doc_id) -> str:
    # one collection per document; the user id in the name keeps users separate
    return f"u{user_id}_d{doc_id}"


def _collection(user_id, doc_id):
    return client.get_or_create_collection(name=_name(user_id, doc_id))


def chunk_pages(pages):
    """Split each page into overlapping pieces, remembering the page number."""
    chunks = []
    for page_no, text in pages:
        text = text.strip()
        start = 0
        while start < len(text):
            piece = text[start:start + CHUNK_SIZE].strip()
            if piece:
                chunks.append((page_no, piece))
            start += CHUNK_SIZE - OVERLAP
    return chunks


def index_document(user_id, doc_id, pages) -> int:
    col = _collection(user_id, doc_id)
    chunks = chunk_pages(pages)
    for i in range(0, len(chunks), 500):          # add in batches
        batch = chunks[i:i + 500]
        col.add(
            ids=[f"c{i + j}" for j in range(len(batch))],
            documents=[c[1] for c in batch],
            metadatas=[{"page": c[0]} for c in batch],
        )
    return len(chunks)


def ensure_indexed(user_id, doc_id, pages):
    """Rebuilds the index if the vector DB folder was lost."""
    if _collection(user_id, doc_id).count() == 0:
        index_document(user_id, doc_id, pages)


def delete_index(user_id, doc_id):
    try:
        client.delete_collection(_name(user_id, doc_id))
    except Exception:
        pass


def retrieve(user_id, doc_id, question):
    col = _collection(user_id, doc_id)
    total = col.count()
    if total == 0:
        return []
    res = col.query(query_texts=[question], n_results=min(TOP_K, total))
    return [{"text": d, "page": m["page"]}
            for d, m in zip(res["documents"][0], res["metadatas"][0])]


def answer(user_id, doc_id, question):
    hits = retrieve(user_id, doc_id, question)
    if not hits:
        return "I couldn't find this in your notes.", []
    context = "\n\n".join(f"[Page {h['page']}]\n{h['text']}" for h in hits)
    reply = ask_llm(RAG_PROMPT.format(context=context, question=question))
    return reply, hits