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
    """Try Gemini first, fall back to Groq on any error including quota."""
    try:
        return get_gemini().invoke(prompt_text).content
    except Exception as e:
        print(f"[LLM] Gemini failed ({e.__class__.__name__}), falling back to Groq")
        return get_groq().invoke(prompt_text).content


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