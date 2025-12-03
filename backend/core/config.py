from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Enterprise-grade configuration management"""
    
    # Application
    APP_NAME: str = "Planalytics AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # PostgreSQL Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Cosmos DB Gremlin API (for knowledge graph)
    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DATABASE: str
    COSMOS_GRAPH: str
    COSMOS_PORT: int = 443
    
    # Azure OpenAI (Main LLM for chat and SQL generation)
    OPENAI_ENDPOINT: str
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "openai.gpt-4.1"
    OPENAI_MODEL_4_1_NANO: str = "openai.gpt-4.1-nano"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    
    # Azure OpenAI Embeddings (for vector search)
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "azure.text-embedding-ada-002"
    
    # Azure AI Search (for entity resolution and semantic search)
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_KEY: str
    
    # Redis Cache (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
