import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import faq, health
from backend.core.config import settings

app = FastAPI(
    title="Tim FAQ Generator",
    description="Generate FAQs from documents and prompts",
    version="1.0.0"
)

# CORS - allow both local and deployed Flask frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Render URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(faq.router, prefix="/api/v1", tags=["FAQ"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.FASTAPI_PORT))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )