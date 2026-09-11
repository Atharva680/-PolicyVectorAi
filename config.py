"""
Configuration module with support for nested environment variables.
Supports configuration like EMBEDDING__MODEL, EMBEDDING__BASE_URL, etc.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseFieldConfig(BaseModel):
    """Configuration for database field mappings"""
    id_field: str = "id"
    content_field: str = "content"
    metadata_field: str = "metadata"
    embedding_field: str = "embedding"
    vector_store_id_field: str = "vector_store_id"
    created_at_field: str = "created_at"


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation via LiteLLM proxy"""
    model: str = Field(default="text-embedding-ada-002", description="Embedding model name")
    base_url: str = Field(default="http://localhost:4000", description="LiteLLM proxy base URL")
    api_key: str = Field(default="sk-1234", description="LiteLLM proxy API key")
    dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class Settings(BaseSettings):
    """Application settings with nested configuration support"""
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/vectordb?schema=public",
        description="PostgreSQL database URL"
    )
    
    # API configuration
    # Supports both OPENAI_API_KEY (preferred) and SERVER_API_KEY (backward compatibility)
    server_api_key: str = Field(
        default="your-api-key-here",
        description="API key for authentication"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (alternative to server_api_key)"
    )
    port: int = Field(default=8000, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Database field mappings
    db_fields: DatabaseFieldConfig = Field(
        default_factory=DatabaseFieldConfig,
        description="Database field name mappings"
    )
    
    # Embedding configuration
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig,
        description="Embedding service configuration"
    )
    
    # Performance tuning
    max_connections: int = Field(default=20, description="Maximum database connections")
    connection_timeout: int = Field(default=10, description="Database connection timeout")
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
        
        # Allow environment variables like:
        # DATABASE_URL=postgresql://...
        # SERVER_API_KEY=your-api-key
        # EMBEDDING__MODEL=text-embedding-ada-002
        # EMBEDDING__BASE_URL=http://localhost:4000
        # EMBEDDING__API_KEY=sk-xxx
        # EMBEDDING__DIMENSIONS=1536
        # DB_FIELDS__ID_FIELD=custom_id
        
    @property
    def api_key(self) -> str:
        """Get API key, preferring OPENAI_API_KEY over SERVER_API_KEY"""
        return self.openai_api_key or self.server_api_key
    
    @property
    def table_names(self) -> Dict[str, str]:
        """Get table names mapping"""
        return {
            "vector_stores": "vector_stores",
            "embeddings": "embeddings"
        }


# Global settings instance
settings = Settings()

