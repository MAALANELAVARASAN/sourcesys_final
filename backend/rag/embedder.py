from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from backend.core.config import settings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY
)

vectorstore = Chroma(
    persist_directory=settings.CHROMA_DB_PATH,
    embedding_function=embeddings
)


def embed_document(text: str, doc_id: str) -> int:
    # delete existing chunks for this doc first to avoid duplicates
    try:
        existing = vectorstore.get(where={"doc_id": {"$eq": doc_id}})
        if existing and existing["ids"]:
            vectorstore.delete(ids=existing["ids"])
            print(f"[EMBEDDER] Deleted {len(existing['ids'])} old chunks for {doc_id}")
    except Exception as e:
        print(f"[EMBEDDER] Could not delete old chunks: {e}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)

    vectorstore.add_texts(
        texts=chunks,
        metadatas=[{"doc_id": doc_id} for _ in chunks]
    )

    print(f"[EMBEDDER] Embedded {len(chunks)} chunks for {doc_id}")
    return len(chunks)


def delete_document(doc_id: str) -> int:
    try:
        existing = vectorstore.get(where={"doc_id": {"$eq": doc_id}})
        if existing and existing["ids"]:
            vectorstore.delete(ids=existing["ids"])
            return len(existing["ids"])
    except Exception as e:
        print(f"[EMBEDDER] Delete failed: {e}")
    return 0