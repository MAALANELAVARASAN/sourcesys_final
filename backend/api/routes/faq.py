from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from backend.rag.pipeline import run_pipeline, run_pipeline_all
from backend.rag.generator import translate_response
from pydantic import BaseModel
import io

router = APIRouter()

MAX_FILES = 10
MAX_FILE_SIZE_MB = 10


class TranslateRequest(BaseModel):
    direct_answer: str
    faq_pairs: list[dict]
    target_language: str


class DeleteDocRequest(BaseModel):
    doc_id: str


class ExportRequest(BaseModel):
    direct_answer: str
    faq_pairs: list[dict]
    title: str = "FAQ Export"


def extract_text_from_pdf(raw: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def extract_text_from_docx(raw: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(raw))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def extract_text(filename: str, raw: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(raw)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(raw)
    elif ext in ("txt", "md"):
        return raw.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


async def read_files(files: List[UploadFile]) -> list[tuple[str, str]]:
    """Read and extract text from uploaded files. Returns list of (filename, text)."""
    file_texts = []
    for file in files:
        if not file.filename:
            continue
        raw = await file.read()
        size_mb = len(raw) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"{file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit.")
        try:
            text = extract_text(file.filename, raw)
            if text:
                file_texts.append((file.filename, text))
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Could not read {file.filename}: {str(e)}")
    return file_texts


@router.get("/faq/debug")
async def debug_chroma():
    from backend.rag.embedder import vectorstore
    try:
        result = vectorstore.get(limit=100)  # add limit
        doc_ids = list(set(m.get("doc_id") for m in result["metadatas"]))
        return {"total_chunks": len(result["ids"]), "doc_ids": doc_ids}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/faq/generate")
async def generate_faq(
    prompt: str = Form(""),
    files: Optional[List[UploadFile]] = File(None)
):
    if files and len(files) > MAX_FILES:
        return JSONResponse(status_code=400, content={"error": f"Maximum {MAX_FILES} files allowed."})

    try:
        file_texts = await read_files(files) if files else []
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    effective_prompt = prompt.strip()
    single_file = None

    if file_texts:
        # check if prompt mentions a specific filename
        mentioned_file = None
        for filename, text in file_texts:
            name_variants = [
                filename.lower(),                                      # test.pdf
                filename.rsplit(".", 1)[0].lower(),                    # test
                filename.rsplit(".", 1)[0].lower().replace("_", " "), # test doc
                filename.rsplit(".", 1)[0].lower().replace("-", " "), # test doc
            ]
            if any(v in effective_prompt.lower() for v in name_variants):
                mentioned_file = (filename, text)
                print(f"[FAQ] Prompt mentions file: {filename} — isolating it")
                break

        if mentioned_file:
            # user asked about a specific file — use only that file
            single_file = [mentioned_file]
            effective_prompt = "Generate detailed FAQs based on the content of the uploaded document."
        else:
            # no specific file mentioned — use last uploaded file
            single_file = [file_texts[-1]]
            if not effective_prompt:
                effective_prompt = "Generate detailed FAQs based on the content of the uploaded document."

    if not effective_prompt:
        return JSONResponse(status_code=400, content={"error": "Prompt or file required."})

    result = run_pipeline(
        prompt=effective_prompt,
        file_texts=single_file
    )
    return result


@router.post("/faq/generate-all")
async def generate_faq_all(
    prompt: str = Form(""),
    files: Optional[List[UploadFile]] = File(None)
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "At least one file required."})

    if len(files) > MAX_FILES:
        return JSONResponse(status_code=400, content={"error": f"Maximum {MAX_FILES} files allowed."})

    try:
        file_texts = await read_files(files)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    if not file_texts:
        return JSONResponse(status_code=400, content={"error": "Could not extract text from uploaded files."})

    effective_prompt = prompt.strip()

    # check if prompt mentions a specific file — if so, isolate it
    if effective_prompt and file_texts:
        mentioned_file = None
        for filename, text in file_texts:
            name_variants = [
                filename.lower(),
                filename.rsplit(".", 1)[0].lower(),
                filename.rsplit(".", 1)[0].lower().replace("_", " "),
                filename.rsplit(".", 1)[0].lower().replace("-", " "),
            ]
            if any(v in effective_prompt.lower() for v in name_variants):
                mentioned_file = (filename, text)
                print(f"[FAQ-ALL] Prompt mentions file: {filename} — isolating it")
                break

        if mentioned_file:
            # redirect to single file pipeline
            result = run_pipeline(
                prompt="Generate detailed FAQs based on the content of the uploaded document.",
                file_texts=[mentioned_file]
            )
            return result

    # no specific file mentioned — process all docs
    result = run_pipeline_all(file_texts=file_texts, prompt=effective_prompt)
    return result
@router.post("/faq/translate")
async def translate_faq(req: TranslateRequest):
    try:
        direct_answer, faq_pairs = translate_response(
            req.direct_answer,
            req.faq_pairs,
            req.target_language
        )
        return {
            "direct_answer": direct_answer,
            "faq_pairs": [{"question": p.question, "answer": p.answer} for p in faq_pairs]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/faq/export/pdf")
async def export_pdf(req: ExportRequest):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
            fontSize=18, textColor=colors.HexColor("#00d4a4"), spaceAfter=12)
        answer_style = ParagraphStyle("answer", parent=styles["Normal"],
            fontSize=11, leading=16, textColor=colors.HexColor("#1a1a2e"), spaceAfter=20)
        q_style = ParagraphStyle("question", parent=styles["Normal"],
            fontSize=11, leading=16, textColor=colors.HexColor("#1a1a2e"),
            fontName="Helvetica-Bold", spaceAfter=6)
        a_style = ParagraphStyle("ans", parent=styles["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor("#444444"),
            leftIndent=20, spaceAfter=16)

        story = []
        story.append(Paragraph(req.title, title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#00d4a4")))
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(req.direct_answer, answer_style))
        story.append(Paragraph("Related FAQs", ParagraphStyle("sub",
            parent=styles["Heading2"], fontSize=13,
            textColor=colors.HexColor("#555d78"), spaceAfter=10)))

        for i, pair in enumerate(req.faq_pairs):
            story.append(Paragraph(f"Q{i+1}: {pair['question']}", q_style))
            story.append(Paragraph(pair['answer'], a_style))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=faqs.pdf"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/faq/delete-doc")
async def delete_doc(req: DeleteDocRequest):
    from backend.rag.embedder import delete_document
    deleted = delete_document(req.doc_id)
    return {"ok": True, "deleted_chunks": deleted}