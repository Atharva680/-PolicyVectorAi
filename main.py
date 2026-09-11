"""
FastAPI application providing OpenAI-compatible Vector Stores API.
Uses PostgreSQL + PGVector for storage and LiteLLM for embeddings.
"""
import os
import asyncio
import time
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prisma import Prisma
from dotenv import load_dotenv

from models import (
    VectorStoreCreateRequest,
    VectorStoreResponse,
    VectorStoreSearchRequest,
    VectorStoreSearchResponse,
    SearchResult,
    EmbeddingCreateRequest,
    EmbeddingResponse,
    EmbeddingBatchCreateRequest,
    EmbeddingBatchCreateResponse,
    VectorStoreListResponse,
    ContentChunk
)
from config import settings
from embedding_service import embedding_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OpenAI Vector Stores API",
    description="OpenAI-compatible Vector Stores API using PGVector and LiteLLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Prisma client
db = Prisma()

security = HTTPBearer()


async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API key from Authorization header"""
    expected_key = settings.api_key
    if credentials.credentials != expected_key:
        logger.warning(f"Invalid API key attempt: {credentials.credentials[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


@app.on_event("startup")
async def startup():
    """Connect to database on startup"""
    try:
        await db.connect()
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown"""
    try:
        await db.disconnect()
        logger.info("Disconnected from database")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Internal server error", "type": "internal_error"}}
    )


@app.post("/v1/vector_stores", response_model=VectorStoreResponse)
async def create_vector_store(
    request: VectorStoreCreateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Create a new vector store.
    
    Compatible with OpenAI's Vector Store API.
    """
    try:
        vector_store_table = settings.table_names["vector_stores"]
        
        result = await db.query_raw(
            f"""
            INSERT INTO {vector_store_table} (id, name, file_counts, status, usage_bytes, expires_after, metadata, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW())
            RETURNING id, name, file_counts, status, usage_bytes, expires_after, expires_at, last_active_at, metadata, 
                     EXTRACT(EPOCH FROM created_at)::bigint as created_at_timestamp
            """,
            request.name,
            {"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
            "completed",
            0,
            request.expires_after,
            request.metadata or {}
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create vector store")
            
        vector_store = result[0]
        
        # Convert to response format
        created_at = int(vector_store["created_at_timestamp"])
        expires_at = int(vector_store["expires_at"].timestamp()) if vector_store.get("expires_at") else None
        last_active_at = int(vector_store["last_active_at"].timestamp()) if vector_store.get("last_active_at") else None
        
        logger.info(f"Created vector store: {vector_store['id']}")
        
        return VectorStoreResponse(
            id=vector_store["id"],
            created_at=created_at,
            name=vector_store["name"],
            usage_bytes=vector_store["usage_bytes"] or 0,
            file_counts=vector_store["file_counts"] or {"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
            status=vector_store["status"],
            expires_after=vector_store["expires_after"],
            expires_at=expires_at,
            last_active_at=last_active_at,
            metadata=vector_store["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create vector store: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create vector store: {str(e)}")


@app.get("/v1/vector_stores", response_model=VectorStoreListResponse)
async def list_vector_stores(
    limit: Optional[int] = 20,
    after: Optional[str] = None,
    before: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """
    List vector stores with optional pagination.
    
    Compatible with OpenAI's Vector Store API.
    """
    try:
        limit = min(limit or 20, 100)  # Cap at 100 results
        
        vector_store_table = settings.table_names["vector_stores"]
        
        # Build base query
        base_query = f"""
        SELECT id, name, file_counts, status, usage_bytes, expires_after, expires_at, last_active_at, metadata,
               EXTRACT(EPOCH FROM created_at)::bigint as created_at_timestamp
        FROM {vector_store_table}
        """
        
        # Add pagination conditions
        conditions = []
        params = []
        param_count = 1
        
        if after:
            conditions.append(f"id > ${param_count}")
            params.append(after)
            param_count += 1
            
        if before:
            conditions.append(f"id < ${param_count}")
            params.append(before)
            param_count += 1
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Add ordering and limit
        final_query = base_query + f" ORDER BY created_at DESC LIMIT {limit + 1}"
        
        # Execute query
        results = await db.query_raw(final_query, *params)
        
        # Check if there are more results
        has_more = len(results) > limit
        if has_more:
            results = results[:limit]  # Remove extra result
        
        # Convert to response format
        vector_stores = []
        for row in results:
            created_at = int(row["created_at_timestamp"])
            expires_at = int(row["expires_at"].timestamp()) if row.get("expires_at") else None
            last_active_at = int(row["last_active_at"].timestamp()) if row.get("last_active_at") else None
            
            vector_store = VectorStoreResponse(
                id=row["id"],
                created_at=created_at,
                name=row["name"],
                usage_bytes=row["usage_bytes"] or 0,
                file_counts=row["file_counts"] or {"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
                status=row["status"],
                expires_after=row["expires_after"],
                expires_at=expires_at,
                last_active_at=last_active_at,
                metadata=row["metadata"]
            )
            vector_stores.append(vector_store)
        
        # Determine first_id and last_id
        first_id = vector_stores[0].id if vector_stores else None
        last_id = vector_stores[-1].id if vector_stores else None
        
        return VectorStoreListResponse(
            data=vector_stores,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list vector stores: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list vector stores: {str(e)}")


@app.post("/v1/vector_stores/{vector_store_id}/search", response_model=VectorStoreSearchResponse)
async def search_vector_store(
    vector_store_id: str,
    request: VectorStoreSearchRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Search a vector store for similar content using cosine similarity.
    
    Compatible with OpenAI's Vector Store API.
    """
    try:
        # Check if vector store exists
        vector_store_table = settings.table_names["vector_stores"]
        vector_store_result = await db.query_raw(
            f"SELECT id FROM {vector_store_table} WHERE id = $1",
            vector_store_id
        )
        if not vector_store_result:
            raise HTTPException(status_code=404, detail="Vector store not found")
        
        # Generate embedding for query
        logger.debug(f"Generating embedding for search query: {request.query[:50]}...")
        query_embedding = await embedding_service.generate_embedding(request.query)
        query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Build the raw SQL query for vector similarity search
        limit = min(request.limit or 20, 100)  # Cap at 100 results
        
        fields = settings.db_fields
        table_name = settings.table_names["embeddings"]
        
        # Build query with proper parameter placeholders for Prisma
        param_count = 1
        query_params = [query_vector_str, vector_store_id]
        
        base_query = f"""
        SELECT 
            {fields.id_field},
            {fields.content_field},
            {fields.metadata_field},
            ({fields.embedding_field} <=> ${param_count}::vector) as distance
        FROM {table_name} 
        WHERE {fields.vector_store_id_field} = ${param_count + 1}
        """
        param_count += 2
        
        # Add metadata filters if provided
        filter_conditions = []
        
        if request.filters:
            for key, value in request.filters.items():
                filter_conditions.append(f"{fields.metadata_field}->>${param_count} = ${param_count + 1}")
                query_params.extend([key, str(value)])
                param_count += 2
        
        if filter_conditions:
            base_query += " AND " + " AND ".join(filter_conditions)
        
        # Add ordering and limit
        final_query = base_query + f" ORDER BY distance ASC LIMIT {limit}"
        
        # Execute the query
        results = await db.query_raw(final_query, *query_params)
        
        # Convert results to SearchResult objects
        search_results = []
        for row in results:
            # Convert distance to similarity score (1 - normalized_distance)
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            distance = float(row['distance'])
            similarity_score = max(0.0, min(1.0, 1 - (distance / 2)))
            
            # Extract filename from metadata or use a default
            metadata = row[fields.metadata_field] or {}
            filename = metadata.get('filename', f"embedding_{row[fields.id_field][:8]}")
            
            content_chunks = [ContentChunk(type="text", text=row[fields.content_field])]
            
            result = SearchResult(
                file_id=row[fields.id_field],
                filename=filename,
                score=similarity_score,
                attributes=metadata if request.return_metadata else None,
                content=content_chunks
            )
            search_results.append(result)
        
        logger.info(f"Search returned {len(search_results)} results for vector store {vector_store_id}")
        
        return VectorStoreSearchResponse(
            search_query=request.query,
            data=search_results,
            has_more=False,  # TODO: Implement pagination
            next_page=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/v1/vector_stores/{vector_store_id}/embeddings", response_model=EmbeddingResponse)
async def create_embedding(
    vector_store_id: str,
    request: EmbeddingCreateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Add a single embedding to a vector store.
    
    If embedding is not provided, it will be generated from the content using LiteLLM.
    
    Compatible with OpenAI's Vector Store API.
    """
    try:
        # Check if vector store exists
        vector_store_table = settings.table_names["vector_stores"]
        vector_store_result = await db.query_raw(
            f"SELECT id FROM {vector_store_table} WHERE id = $1",
            vector_store_id
        )
        if not vector_store_result:
            raise HTTPException(status_code=404, detail="Vector store not found")
        
        # Generate embedding if not provided
        embedding = request.embedding
        if embedding is None:
            logger.debug(f"Generating embedding for content: {request.content[:50]}...")
            embedding = await embedding_service.generate_embedding(request.content)
        else:
            # Validate provided embedding
            embedding_service.validate_embedding(embedding)
        
        # Convert embedding to vector string format
        embedding_vector_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Insert embedding using configurable field names
        fields = settings.db_fields
        table_name = settings.table_names["embeddings"]
        
        result = await db.query_raw(
            f"""
            INSERT INTO {table_name} ({fields.id_field}, {fields.vector_store_id_field}, {fields.content_field}, 
                                     {fields.embedding_field}, {fields.metadata_field}, {fields.created_at_field})
            VALUES (gen_random_uuid(), $1, $2, $3::vector, $4, NOW())
            RETURNING {fields.id_field}, {fields.vector_store_id_field}, {fields.content_field}, 
                     {fields.metadata_field}, EXTRACT(EPOCH FROM {fields.created_at_field})::bigint as created_at_timestamp
            """,
            vector_store_id,
            request.content,
            embedding_vector_str,
            request.metadata or {}
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create embedding")
            
        embedding_row = result[0]
        
        # Update vector store statistics
        await db.query_raw(
            f"""
            UPDATE {vector_store_table} 
            SET file_counts = jsonb_set(
                    COALESCE(file_counts, '{{"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0}}'::jsonb),
                    '{{completed}}',
                    (COALESCE((file_counts->>'completed')::int, 0) + 1)::text::jsonb
                ),
                file_counts = jsonb_set(
                    file_counts,
                    '{{total}}',
                    (COALESCE((file_counts->>'total')::int, 0) + 1)::text::jsonb
                ),
                usage_bytes = COALESCE(usage_bytes, 0) + LENGTH($2),
                last_active_at = NOW()
            WHERE id = $1
            """,
            vector_store_id,
            request.content
        )
        
        logger.info(f"Created embedding {embedding_row[fields.id_field]} in vector store {vector_store_id}")
        
        return EmbeddingResponse(
            id=embedding_row[fields.id_field],
            vector_store_id=embedding_row[fields.vector_store_id_field],
            content=embedding_row[fields.content_field],
            metadata=embedding_row[fields.metadata_field],
            created_at=int(embedding_row["created_at_timestamp"])
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create embedding: {str(e)}")


@app.post("/v1/vector_stores/{vector_store_id}/embeddings/batch", response_model=EmbeddingBatchCreateResponse)
async def create_embeddings_batch(
    vector_store_id: str,
    request: EmbeddingBatchCreateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Add multiple embeddings to a vector store in batch.
    
    If embeddings are not provided, they will be generated from the content using LiteLLM.
    
    Compatible with OpenAI's Vector Store API.
    """
    try:
        # Check if vector store exists
        vector_store_table = settings.table_names["vector_stores"]
        vector_store_result = await db.query_raw(
            f"SELECT id FROM {vector_store_table} WHERE id = $1",
            vector_store_id
        )
        if not vector_store_result:
            raise HTTPException(status_code=404, detail="Vector store not found")
        
        if not request.embeddings:
            raise HTTPException(status_code=400, detail="No embeddings provided")
        
        # Generate embeddings for items that don't have them
        embeddings_to_process = []
        texts_to_embed = []
        text_indices = []
        
        for i, emb_req in enumerate(request.embeddings):
            if emb_req.embedding is None:
                texts_to_embed.append(emb_req.content)
                text_indices.append(i)
        
        # Batch generate embeddings if needed
        if texts_to_embed:
            logger.debug(f"Generating {len(texts_to_embed)} embeddings in batch")
            generated_embeddings = await embedding_service.generate_embeddings(texts_to_embed)
            for idx, gen_emb in zip(text_indices, generated_embeddings):
                request.embeddings[idx].embedding = gen_emb
        
        # Validate all embeddings
        for emb_req in request.embeddings:
            if emb_req.embedding:
                embedding_service.validate_embedding(emb_req.embedding)
        
        # Prepare batch insert
        fields = settings.db_fields
        table_name = settings.table_names["embeddings"]
        
        # Build VALUES clause for batch insert
        values_clauses = []
        params = []
        param_count = 1
        
        for embedding_req in request.embeddings:
            embedding_vector_str = "[" + ",".join(map(str, embedding_req.embedding)) + "]"
            values_clauses.append(f"(gen_random_uuid(), ${param_count}, ${param_count + 1}, ${param_count + 2}::vector, ${param_count + 3}, NOW())")
            params.extend([
                vector_store_id,
                embedding_req.content,
                embedding_vector_str,
                embedding_req.metadata or {}
            ])
            param_count += 4
        
        values_clause = ", ".join(values_clauses)
        
        # Execute batch insert
        result = await db.query_raw(
            f"""
            INSERT INTO {table_name} ({fields.id_field}, {fields.vector_store_id_field}, {fields.content_field}, 
                                     {fields.embedding_field}, {fields.metadata_field}, {fields.created_at_field})
            VALUES {values_clause}
            RETURNING {fields.id_field}, {fields.vector_store_id_field}, {fields.content_field}, 
                     {fields.metadata_field}, EXTRACT(EPOCH FROM {fields.created_at_field})::bigint as created_at_timestamp
            """,
            *params
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create embeddings")
        
        # Calculate total content length for usage bytes update
        total_content_length = sum(len(emb.content) for emb in request.embeddings)
        
        # Update vector store statistics
        await db.query_raw(
            f"""
            UPDATE {vector_store_table} 
            SET file_counts = jsonb_set(
                    COALESCE(file_counts, '{{"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0}}'::jsonb),
                    '{{completed}}',
                    (COALESCE((file_counts->>'completed')::int, 0) + $2)::text::jsonb
                ),
                file_counts = jsonb_set(
                    file_counts,
                    '{{total}}',
                    (COALESCE((file_counts->>'total')::int, 0) + $2)::text::jsonb
                ),
                usage_bytes = COALESCE(usage_bytes, 0) + $3,
                last_active_at = NOW()
            WHERE id = $1
            """,
            vector_store_id,
            len(request.embeddings),
            total_content_length
        )
        
        # Convert results to response format
        embeddings = []
        for row in result:
            embeddings.append(EmbeddingResponse(
                id=row[fields.id_field],
                vector_store_id=row[fields.vector_store_id_field],
                content=row[fields.content_field],
                metadata=row[fields.metadata_field],
                created_at=int(row["created_at_timestamp"])
            ))
        
        logger.info(f"Created {len(embeddings)} embeddings in batch for vector store {vector_store_id}")
        
        return EmbeddingBatchCreateResponse(
            data=embeddings,
            created=int(time.time())
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create embeddings batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create embeddings batch: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db.query_raw("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": int(time.time())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )

