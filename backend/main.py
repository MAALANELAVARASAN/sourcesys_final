from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import faq, health
from backend.core.config import settings

app = FastAPI(
    title="Tim FAQ Generator",
    description="Generate FAQs from documents and prompts",
    version="1.0.0"
)

# CORS - allows Flask frontend to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000"],  # Flask URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(faq.router, prefix="/api/v1", tags=["FAQ"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True
    )