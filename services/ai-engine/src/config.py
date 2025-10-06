"""
Configuration management for AI Engine service.

This module handles all configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database Configuration
    database_url: str = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_documents: str = "document_embeddings"
    qdrant_collection_chunks: str = "chunk_embeddings"
    qdrant_collection_queries: str = "query_embeddings"

    # AI Model Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    max_chunk_size: int = 500
    chunk_overlap: int = 50

    # LLM Provider Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Local LLM Configuration
    use_local_llm: bool = True
    local_llm_model: str = "llama2"
    local_llm_url: str = "http://localhost:11434"

    # RAG Configuration
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    rag_max_context_length: int = 4000
    rag_temperature: float = 0.7

    # Service Configuration
    service_name: str = "ai-engine"
    service_port: int = 8000
    log_level: str = "INFO"

    @property
    def qdrant_config(self) -> dict:
        """Get Qdrant client configuration."""
        config = {
            "url": self.qdrant_url,
            "timeout": 30.0,
        }
        if self.qdrant_api_key:
            config["api_key"] = self.qdrant_api_key
        return config


# Global settings instance
settings = Settings()
