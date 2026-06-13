from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000

    # Flask
    FLASK_HOST: str = "127.0.0.1"
    FLASK_PORT: int = 5000
    FLASK_SECRET_KEY: str

    # PostgreSQL
    DATABASE_URL: str

    # OpenAI
    GEMINI_API_KEY: str
    GROQ_API_KEY: str

    # Nomic
    NOMIC_API_KEY: str

    # ChromaDB
    CHROMA_DB_PATH: str = "./chroma_db"

    class Config:
        env_file = ".env"
        extra = "ignore"       

settings = Settings()