-- Migration: 002_add_triggers.sql
-- Description: Add triggers for automatic statistics updates
-- Date: 2024-01-01

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

-- Trigger to automatically update vector store stats
CREATE TRIGGER trigger_update_vector_store_stats
    AFTER INSERT OR UPDATE OR DELETE ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_vector_store_stats();

-- Function to handle expires_after calculation
CREATE OR REPLACE FUNCTION calculate_expires_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_after IS NOT NULL THEN
        IF NEW.expires_after->>'anchor' = 'last_active_at' AND NEW.expires_after->>'days' IS NOT NULL THEN
            NEW.expires_at := (NEW.last_active_at + (NEW.expires_after->>'days')::int * INTERVAL '1 day');
        ELSIF NEW.expires_after->>'anchor' = 'created_at' AND NEW.expires_after->>'days' IS NOT NULL THEN
            NEW.expires_at := (NEW.created_at + (NEW.expires_after->>'days')::int * INTERVAL '1 day');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to calculate expires_at
CREATE TRIGGER trigger_calculate_expires_at
    BEFORE INSERT OR UPDATE ON vector_stores
    FOR EACH ROW
    EXECUTE FUNCTION calculate_expires_at();

