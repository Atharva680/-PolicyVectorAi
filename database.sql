-- PostgreSQL Schema for OpenAI Vector Stores API with PGVector
-- This file creates all necessary tables, extensions, and indexes

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

-- Create indexes for better performance

-- Index on vector_store_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_store_id 
    ON embeddings(vector_store_id);

-- IVFFLAT index for fast similarity search using cosine distance
-- Note: This index requires data to exist. You may need to create it after loading initial data
-- or use a different index type like HNSW for better performance at scale
CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_ivfflat 
    ON embeddings USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Alternative: HNSW index (better performance, but slower to build)
-- Uncomment if you prefer HNSW over IVFFLAT
-- CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_hnsw 
--     ON embeddings USING hnsw (embedding vector_cosine_ops) 
--     WITH (m = 16, ef_construction = 64);

-- GIN index on metadata for faster JSONB queries
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_gin 
    ON embeddings USING GIN (metadata);

-- Index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at 
    ON embeddings(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_stores_created_at 
    ON vector_stores(created_at DESC);

-- Index on vector_stores status
CREATE INDEX IF NOT EXISTS idx_vector_stores_status 
    ON vector_stores(status);

-- Function to update vector store statistics
CREATE OR REPLACE FUNCTION update_vector_store_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE vector_stores
    SET 
        last_active_at = NOW(),
        usage_bytes = (
            SELECT COALESCE(SUM(LENGTH(content)), 0)
            FROM embeddings
            WHERE vector_store_id = NEW.vector_store_id
        ),
        file_counts = jsonb_set(
            jsonb_set(
                COALESCE(file_counts, '{"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0}'::jsonb),
                '{total}',
                to_jsonb((
                    SELECT COUNT(*)::int
                    FROM embeddings
                    WHERE vector_store_id = NEW.vector_store_id
                ))
            ),
            '{completed}',
            to_jsonb((
                SELECT COUNT(*)::int
                FROM embeddings
                WHERE vector_store_id = NEW.vector_store_id
            ))
        )
    WHERE id = NEW.vector_store_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update vector store stats when embeddings are added
CREATE TRIGGER trigger_update_vector_store_stats
    AFTER INSERT OR UPDATE OR DELETE ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_vector_store_stats();

-- Function to handle expires_after calculation
CREATE OR REPLACE FUNCTION calculate_expires_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_after IS NOT NULL THEN
        -- Support for expires_after in format: {"anchor": "last_active_at", "days": 7}
        IF NEW.expires_after->>'anchor' = 'last_active_at' AND NEW.expires_after->>'days' IS NOT NULL THEN
            NEW.expires_at := (NEW.last_active_at + (NEW.expires_after->>'days')::int * INTERVAL '1 day');
        ELSIF NEW.expires_after->>'anchor' = 'created_at' AND NEW.expires_after->>'days' IS NOT NULL THEN
            NEW.expires_at := (NEW.created_at + (NEW.expires_after->>'days')::int * INTERVAL '1 day');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to calculate expires_at from expires_after
CREATE TRIGGER trigger_calculate_expires_at
    BEFORE INSERT OR UPDATE ON vector_stores
    FOR EACH ROW
    EXECUTE FUNCTION calculate_expires_at();

-- Comments for documentation
COMMENT ON TABLE vector_stores IS 'Stores vector store metadata and statistics';
COMMENT ON TABLE embeddings IS 'Stores embedding vectors with content and metadata';
COMMENT ON COLUMN embeddings.embedding IS 'Vector embedding of dimension 1536 for OpenAI ada-002 model';
COMMENT ON INDEX idx_embeddings_embedding_ivfflat IS 'IVFFLAT index for fast cosine similarity search';

