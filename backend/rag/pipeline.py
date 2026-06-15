from backend.rag.embedder import embed_document
from backend.rag.retriever import retrieve_chunks, retrieve_chunks_per_doc
from backend.rag.generator import (
    generate_full_response_from_chunks,
    generate_full_response_from_prompt,
    generate_full_response_from_all_docs
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


def run_pipeline(prompt: str, file_texts: list[tuple[str,str]] = None) -> FAQResponse:
    doc_ids = []

    if file_texts:
        for filename, text in file_texts:
            embed_document(text, doc_id=filename)
            doc_ids.append(filename)

    print(f"[PIPELINE] doc_ids: {doc_ids}")
    chunks = retrieve_chunks(query=prompt, doc_ids=doc_ids if doc_ids else None)
    print(f"[PIPELINE] chunks returned: {len(chunks)}")

    if doc_ids and not chunks:
        print("[PIPELINE] No chunks found — falling back to Gemini prompt")
        direct_answer, faq_pairs = generate_full_response_from_prompt(prompt)
        return FAQResponse(
            source="ai_knowledge",
            direct_answer=direct_answer,
            faq_pairs=faq_pairs,
            total=len(faq_pairs)
        )

    if chunks:
        direct_answer, faq_pairs = generate_full_response_from_chunks(prompt, chunks)
        print(f"[PIPELINE] direct_answer preview: {direct_answer[:150]}")
        print(f"[PIPELINE] is_irrelevant: {is_irrelevant_answer(direct_answer)}")

        if is_irrelevant_answer(direct_answer):
            print("[PIPELINE] Flagged irrelevant — falling back to Gemini")
            direct_answer, faq_pairs = generate_full_response_from_prompt(prompt)
            return FAQResponse(
                source="ai_knowledge",
                direct_answer=direct_answer,
                faq_pairs=faq_pairs,
                total=len(faq_pairs)
            )

        print("[PIPELINE] Returning knowledge_base response")
        return FAQResponse(
            source="knowledge_base",
            direct_answer=direct_answer,
            faq_pairs=faq_pairs,
            total=len(faq_pairs)
        )

    else:
        print("[PIPELINE] No chunks at all — falling back to Gemini")
        direct_answer, faq_pairs = generate_full_response_from_prompt(prompt)
        return FAQResponse(
            source="ai_knowledge",
            direct_answer=direct_answer,
            faq_pairs=faq_pairs,
            total=len(faq_pairs)
        )


def run_pipeline_all(file_texts: list[tuple[str,str]], prompt: str = "") -> FAQResponse:
    """Pipeline for generate-all — processes each doc independently and combines FAQs."""
    doc_ids = []

    for filename, text in file_texts:
        embed_document(text, doc_id=filename)
        doc_ids.append(filename)

    print(f"[PIPELINE-ALL] doc_ids: {doc_ids}")

    # get chunks per doc independently
    query = prompt if prompt else "Generate comprehensive FAQs covering all content"
    doc_chunks = retrieve_chunks_per_doc(query=query, doc_ids=doc_ids, k_per_doc=6)

    # check if any doc has chunks
    total_chunks = sum(len(v) for v in doc_chunks.values())
    print(f"[PIPELINE-ALL] total chunks across all docs: {total_chunks}")

    if total_chunks == 0:
        print("[PIPELINE-ALL] No chunks — falling back to Gemini")
        direct_answer, faq_pairs = generate_full_response_from_prompt(
            prompt or "Generate FAQs about the uploaded documents"
        )
        return FAQResponse(
            source="ai_knowledge",
            direct_answer=direct_answer,
            faq_pairs=faq_pairs,
            total=len(faq_pairs)
        )

    direct_answer, faq_pairs = generate_full_response_from_all_docs(doc_chunks)
    print(f"[PIPELINE-ALL] total FAQs generated: {len(faq_pairs)}")

    return FAQResponse(
        source="knowledge_base",
        direct_answer=direct_answer,
        faq_pairs=faq_pairs,
        total=len(faq_pairs)
    )