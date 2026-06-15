from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from backend.core.config import settings
from backend.models.schemas import FAQPair


def get_gemini():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7
    )


def get_groq():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.7
    )


def invoke_llm(prompt_text: str) -> str:
    # Level 1 — Gemini (500/day, best accuracy)
    try:
        result = get_gemini().invoke(prompt_text).content
        print("[LLM] Used Gemini")
        return result
    except Exception as e:
        print(f"[LLM] Gemini failed ({e.__class__.__name__}), trying Groq")

    # Level 2 — Groq (14,400/day, fast fallback)
    try:
        result = get_groq().invoke(prompt_text).content
        print("[LLM] Used Groq")
        return result
    except Exception as e:
        print(f"[LLM] Groq also failed ({e.__class__.__name__})")
        raise RuntimeError("All LLM providers failed. Check your API keys and quota.")

def generate_full_response_from_all_docs(doc_chunks: dict[str, list[str]]) -> tuple[str, list[FAQPair]]:
    """Generate FAQs for each doc separately then combine."""
    all_faq_pairs = []
    summary_parts = []

    for doc_id, chunks in doc_chunks.items():
        if not chunks:
            continue

        context = "\n\n".join(chunks)
        doc_name = doc_id.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")

        prompt_text = f"""You are a helpful assistant. Use the context below from the document "{doc_name}" to generate FAQs.

Context:
{context}

Respond in EXACTLY this format, nothing else:

ANSWER: one sentence summary of what this document is about

Q1: question here
A1: answer here

Q2: question here
A2: answer here

Q3: question here
A3: answer here

Q4: question here
A4: answer here

Q5: question here
A5: answer here
"""
        print(f"[GENERATOR] Generating FAQs for {doc_id}")
        raw = invoke_llm(prompt_text)
        answer, pairs = parse_full_response(raw)
        summary_parts.append(f"{doc_name}: {answer}")
        all_faq_pairs.extend(pairs)

    combined_answer = " | ".join(summary_parts) if summary_parts else "FAQs generated from uploaded documents."
    return combined_answer, all_faq_pairs


def generate_full_response_from_chunks(prompt: str, chunks: list[str]) -> tuple[str, list[FAQPair]]:
    context = "\n\n".join(chunks)
    prompt_text = f"""You are a helpful assistant. Use the context below to answer the question and generate FAQs.

Question: {prompt}

Context:
{context}

Respond in EXACTLY this format, nothing else:

ANSWER: your direct answer here in 2-4 sentences

Q1: question here
A1: answer here

Q2: question here
A2: answer here

Q3: question here
A3: answer here

Q4: question here
A4: answer here

Q5: question here
A5: answer here
"""
    return parse_full_response(invoke_llm(prompt_text))


def generate_full_response_from_prompt(prompt: str) -> tuple[str, list[FAQPair]]:
    prompt_text = f"""You are a helpful assistant. Answer the question and generate FAQs about it.

Question: {prompt}

Respond in EXACTLY this format, nothing else:

ANSWER: your direct answer here in 2-4 sentences

Q1: question here
A1: answer here

Q2: question here
A2: answer here

Q3: question here
A3: answer here

Q4: question here
A4: answer here

Q5: question here
A5: answer here
"""
    return parse_full_response(invoke_llm(prompt_text))


def translate_response(direct_answer: str, faq_pairs: list[dict], target_language: str) -> tuple[str, list[dict]]:
    faqs_text = "\n".join([
        f"Q{i+1}: {p['question']}\nA{i+1}: {p['answer']}"
        for i, p in enumerate(faq_pairs)
    ])

    prompt_text = f"""Translate the following content to {target_language}.
Keep the exact same format. Do not add explanations.

ANSWER: {direct_answer}

{faqs_text}
"""
    raw = invoke_llm(prompt_text)
    return parse_full_response(raw)


def parse_full_response(raw: str) -> tuple[str, list[FAQPair]]:
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]

    direct_answer = ""
    faq_pairs = []

    i = 0
    while i < len(lines):
        if lines[i].startswith("ANSWER:"):
            direct_answer = lines[i].split(":", 1)[1].strip()
        elif lines[i].startswith("Q") and i + 1 < len(lines) and lines[i+1].startswith("A"):
            question = lines[i].split(":", 1)[1].strip()
            answer   = lines[i+1].split(":", 1)[1].strip()
            faq_pairs.append(FAQPair(question=question, answer=answer))
            i += 1
        i += 1

    if not direct_answer:
        direct_answer = "Please see the FAQs below for relevant information."

    return direct_answer, faq_pairs