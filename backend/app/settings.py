from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # DB (relacional)
    DB_URL: str = "sqlite:///./data/agent.db"

    # Embeddings
    EMB_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Vector index path (FAISS)
    FAISS_DIR: str = "./data/faiss_index"

    # LLM provider: none | openai | ollama | groq
    LLM_PROVIDER: str = "none"
    
    # OpenAI
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_API_KEY: str | None = None

    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b-instruct"

    # Groq (API rápida y gratis)
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Muy rápido, gratis

    # Neo4j (grafo de funciones) - opcional
    NEO4J_URI: str | None = None  # ej: "bolt://localhost:7687"
    NEO4J_USER: str | None = None
    NEO4J_PASSWORD: str | None = None

settings = Settings()
