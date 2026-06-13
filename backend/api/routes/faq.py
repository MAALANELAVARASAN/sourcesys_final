from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from backend.rag.pipeline import run_pipeline
import io

router = APIRouter()

MAX_FILES = 5
MAX_FILE_SIZE_MB = 10


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


@router.post("/faq/generate")
async def generate_faq(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):
    if files and len(files) > MAX_FILES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Maximum {MAX_FILES} files allowed per session."}
        )

    all_texts = []

    if files:
        for file in files:
            if not file.filename:
                continue

            raw = await file.read()

            # size check
            size_mb = len(raw) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"{file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit."}
                )

            try:
                text = extract_text(file.filename, raw)
                if text:
                    all_texts.append((file.filename, text))
            except ValueError as e:
                return JSONResponse(status_code=400, content={"error": str(e)})
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Could not read {file.filename}: {str(e)}"}
                )

    # pass all texts to pipeline
    combined_text = "\n\n---\n\n".join(text for _, text in all_texts) if all_texts else None
    combined_filename = "_".join(fname for fname, _ in all_texts) if all_texts else None

    result = run_pipeline(
        prompt=prompt,
        file_text=combined_text,
        filename=combined_filename
    )
    return result