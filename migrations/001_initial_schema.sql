-- Migration: 001_initial_schema.sql
-- Description: Initial database schema with PGVector extensions
-- Date: 2024-01-01

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create vector_stores table
CREATE TABLE IF NOT EXISTS vector_stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    file_counts JSONB DEFAULT '{"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0}'::jsonb,
    status TEXT DEFAULT 'completed',
    usage_bytes BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_after JSONB,
    expires_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vector_store_id UUID NOT NULL REFERENCES vector_stores(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_store_id 
    ON embeddings(vector_store_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_ivfflat 
    ON embeddings USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_gin 
    ON embeddings USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_embeddings_created_at 
    ON embeddings(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_stores_created_at 
    ON vector_stores(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_stores_status 
    ON vector_stores(status);

