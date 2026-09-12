"""
Pydantic models for OpenAI Vector Stores API requests and responses.
Fully compatible with OpenAI's Vector Store API specification.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class VectorStoreCreateRequest(BaseModel):
    """Request model for creating a vector store"""
    name: str = Field(..., description="Name of the vector store")
    file_ids: Optional[List[str]] = Field(None, description="List of file IDs (not used in this implementation)")
    expires_after: Optional[Dict[str, Any]] = Field(
        None,
        description="Expiration configuration, e.g., {'anchor': 'last_active_at', 'days': 7}"
    )
    chunking_strategy: Optional[Dict[str, Any]] = Field(
        None,
        description="Chunking strategy configuration (optional)"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata dictionary")


class VectorStoreResponse(BaseModel):
    """Response model for vector store operations"""
    id: str = Field(..., description="Unique identifier for the vector store")
    object: str = Field(default="vector_store", description="Object type")
    created_at: int = Field(..., description="Unix timestamp of creation")
    name: str = Field(..., description="Name of the vector store")
    usage_bytes: int = Field(default=0, description="Total bytes used")
    file_counts: Dict[str, int] = Field(
        default_factory=lambda: {"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
        description="File count statistics"
    )
    status: str = Field(default="completed", description="Status of the vector store")
    expires_after: Optional[Dict[str, Any]] = Field(None, description="Expiration configuration")
    expires_at: Optional[int] = Field(None, description="Unix timestamp of expiration")
    last_active_at: Optional[int] = Field(None, description="Unix timestamp of last activity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata dictionary")


class VectorStoreSearchRequest(BaseModel):
    """Request model for searching a vector store"""
    query: str = Field(..., description="Search query text")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters for search")
    return_metadata: Optional[bool] = Field(default=True, description="Whether to return metadata in results")
    search_type: Optional[str] = Field(default="hybrid", description="Search type: 'semantic', 'keyword', or 'hybrid'")


class ContentChunk(BaseModel):
    """Content chunk in search results"""
    type: str = Field(default="text", description="Type of content chunk")
    text: str = Field(..., description="Text content")


class SearchResult(BaseModel):
    """Single search result"""
    file_id: str = Field(..., description="Unique identifier of the embedding/file")
    filename: str = Field(..., description="Filename or identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Metadata attributes")
    content: List[ContentChunk] = Field(..., description="Content chunks")


class VectorStoreSearchResponse(BaseModel):
    """Response model for vector store search"""
    object: str = Field(default="vector_store.search_results.page", description="Object type")
    search_query: str = Field(..., description="The original search query")
    data: List[SearchResult] = Field(..., description="List of search results")
    has_more: bool = Field(default=False, description="Whether more results are available")
    next_page: Optional[str] = Field(None, description="Cursor for next page of results")


class EmbeddingCreateRequest(BaseModel):
    """Request model for creating a single embedding"""
    content: str = Field(..., description="Text content to embed")
    embedding: Optional[List[float]] = Field(
        None,
        description="Pre-computed embedding vector. If not provided, will be generated using LiteLLM"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata dictionary")


class EmbeddingResponse(BaseModel):
    """Response model for embedding operations"""
    id: str = Field(..., description="Unique identifier for the embedding")
    object: str = Field(default="embedding", description="Object type")
    vector_store_id: str = Field(..., description="ID of the parent vector store")
    content: str = Field(..., description="Text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata dictionary")
    created_at: int = Field(..., description="Unix timestamp of creation")


class EmbeddingBatchCreateRequest(BaseModel):
    """Request model for batch creating embeddings"""
    embeddings: List[EmbeddingCreateRequest] = Field(..., description="List of embedding requests")


class EmbeddingBatchCreateResponse(BaseModel):
    """Response model for batch embedding creation"""
    object: str = Field(default="embedding.batch", description="Object type")
    data: List[EmbeddingResponse] = Field(..., description="List of created embeddings")
    created: int = Field(..., description="Unix timestamp of creation")


class VectorStoreListResponse(BaseModel):
    """Response model for listing vector stores"""
    object: str = Field(default="list", description="Object type")
    data: List[VectorStoreResponse] = Field(..., description="List of vector stores")
    first_id: Optional[str] = Field(None, description="ID of the first item")
    last_id: Optional[str] = Field(None, description="ID of the last item")
    has_more: bool = Field(default=False, description="Whether more results are available")

