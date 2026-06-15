from backend.rag.embedder import vectorstore

RELEVANCE_THRESHOLD = 0.75


def retrieve_chunks(query: str, doc_ids: list[str] = None, k: int = 6) -> list[str]:

    if not doc_ids:
        results = vectorstore.similarity_search_with_score(query, k=k)
        for doc, score in results:
            print(f"[RETRIEVER] score={score:.4f} | doc={doc.metadata.get('doc_id','?')} | chunk={doc.page_content[:60]}")
        chunks = [doc.page_content for doc, score in results if score <= RELEVANCE_THRESHOLD]
        print(f"[RETRIEVER] {len(chunks)} chunks passed threshold")
        return chunks

    all_chunks = []

    for doc_id in doc_ids:
        try:
            results = vectorstore.similarity_search_with_score(
                query,
                k=k,
                filter={"doc_id": {"$eq": doc_id}}
            )
            for doc, score in results:
                print(f"[RETRIEVER] score={score:.4f} | doc={doc_id} | chunk={doc.page_content[:60]}")
                all_chunks.append((score, doc_id, doc.page_content))
        except Exception as e:
            print(f"[RETRIEVER] Failed for doc_id={doc_id}: {e}")

    all_chunks.sort(key=lambda x: x[0])
    chunks = [content for _, _, content in all_chunks[:k * len(doc_ids)]]
    print(f"[RETRIEVER] {len(chunks)} chunks returned across {len(doc_ids)} docs")
    return chunks


def retrieve_chunks_per_doc(query: str, doc_ids: list[str], k_per_doc: int = 6) -> dict[str, list[str]]:
    """Retrieve k chunks per document independently — used for generate-all."""
    doc_chunks = {}

    for doc_id in doc_ids:
        try:
            results = vectorstore.similarity_search_with_score(
                query,
                k=k_per_doc,
                filter={"doc_id": {"$eq": doc_id}}
            )
            chunks = []
            for doc, score in results:
                print(f"[RETRIEVER-ALL] score={score:.4f} | doc={doc_id} | chunk={doc.page_content[:60]}")
                chunks.append(doc.page_content)
            doc_chunks[doc_id] = chunks
            print(f"[RETRIEVER-ALL] {len(chunks)} chunks for {doc_id}")
        except Exception as e:
            print(f"[RETRIEVER-ALL] Failed for doc_id={doc_id}: {e}")
            doc_chunks[doc_id] = []

    return doc_chunks