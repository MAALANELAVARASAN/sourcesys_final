from backend.rag.embedder import vectorstore

RELEVANCE_THRESHOLD = 1.2  # cosine distance with Nomic; tune down if too loose

def retrieve_chunks(query: str, k: int = 5) -> list[str]:
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    # debug: print scores so you can see what's coming back
    for doc, score in results:
        print(f"[RETRIEVER] score={score:.4f} | chunk={doc.page_content[:80]}")
    
    chunks = [doc.page_content for doc, score in results if score <= RELEVANCE_THRESHOLD]
    return chunks