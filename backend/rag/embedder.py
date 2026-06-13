from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_chroma import Chroma
from backend.core.config import settings


embeddings = NomicEmbeddings(
    model="nomic-embed-text-v1.5",
    nomic_api_key=settings.NOMIC_API_KEY
)

vectorstore = Chroma(
    persist_directory=settings.CHROMA_DB_PATH,
    embedding_function=embeddings
)

def embed_document(text: str, doc_id: str):
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)

    vectorstore.add_texts(
        texts=chunks,
        metadatas=[{"doc_id": doc_id} for _ in chunks]
    )

    return len(chunks)