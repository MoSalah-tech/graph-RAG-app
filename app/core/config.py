from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"

    GROQ_API_KEY: str
    OPENROUTER_API_KEY: str
    VOYAGE_API_KEY: str
    SEC_IDENTITY: str

    EMBEDDING_MODEL: str = "voyage-4"
    LLM_MODEL: str = "openai/gpt-oss-120b"

    SECRET_KEY: str

settings = Settings()