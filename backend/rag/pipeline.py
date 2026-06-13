from backend.rag.embedder import embed_document
from backend.rag.retriever import retrieve_chunks
from backend.rag.generator import (
    generate_full_response_from_chunks,
    generate_full_response_from_prompt
)
from backend.models.schemas import FAQResponse

NO_INFO_SIGNALS = [
    "does not contain",
    "no information",
    "not mentioned",
    "cannot find",
    "not found",
    "no relevant",
    "context does not",
    "provided context",
    "not available in",
    "i don't have information",
    "not discussed",
]

def is_irrelevant_answer(answer: str) -> bool:
    return any(signal in answer.lower() for signal in NO_INFO_SIGNALS)


def run_pipeline(prompt: str, file_text: str = None, filename: str = None) -> FAQResponse:

    chunks = []

    if file_text and filename:
        embed_document(file_text, doc_id=filename)
        chunks = retrieve_chunks(query=prompt)

    if chunks:
        direct_answer, faq_pairs = generate_full_response_from_chunks(prompt, chunks)

        if is_irrelevant_answer(direct_answer):
            direct_answer, faq_pairs = generate_full_response_from_prompt(prompt)
            source = "ai_knowledge"
        else:
            source = "knowledge_base"
    else:
        direct_answer, faq_pairs = generate_full_response_from_prompt(prompt)
        source = "ai_knowledge"

    return FAQResponse(
        source=source,
        direct_answer=direct_answer,
        faq_pairs=faq_pairs,
        total=len(faq_pairs)
    )