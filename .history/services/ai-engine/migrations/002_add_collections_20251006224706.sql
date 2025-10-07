-- Migration: Add Collections Support
-- Description: Create collections table and add collection_id to documents
-- Date: 2025-01-04

-- Create collections table
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_collection_name UNIQUE (user_id, name)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_created_at ON collections(created_at DESC);

-- Add collection_id to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS collection_id UUID,
ADD CONSTRAINT fk_documents_collection 
    FOREIGN KEY (collection_id) 
    REFERENCES collections(id) 
    ON DELETE SET NULL;

-- Create index for collection filtering
CREATE INDEX IF NOT EXISTS idx_documents_collection_id ON documents(collection_id);

-- Create trigger to update document_count
CREATE OR REPLACE FUNCTION update_collection_document_count()
RETURNS TRIGGER AS $$
BEGIN
    -- If document is being added to a collection
    IF NEW.collection_id IS NOT NULL AND (OLD.collection_id IS NULL OR OLD.collection_id != NEW.collection_id) THEN
        UPDATE collections 
        SET document_count = document_count + 1,
            updated_at = NOW()
        WHERE id = NEW.collection_id;
        
        -- Decrement old collection if changed
        IF OLD.collection_id IS NOT NULL THEN
            UPDATE collections 
            SET document_count = GREATEST(document_count - 1, 0),
                updated_at = NOW()
            WHERE id = OLD.collection_id;
        END IF;
    END IF;
    
    -- If document is being removed from a collection
    IF NEW.collection_id IS NULL AND OLD.collection_id IS NOT NULL THEN
        UPDATE collections 
        SET document_count = GREATEST(document_count - 1, 0),
            updated_at = NOW()
        WHERE id = OLD.collection_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to documents table
DROP TRIGGER IF EXISTS trigger_update_collection_count ON documents;
CREATE TRIGGER trigger_update_collection_count
AFTER INSERT OR UPDATE OF collection_id ON documents
FOR EACH ROW
EXECUTE FUNCTION update_collection_document_count();

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_collections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_collections_timestamp ON collections;
CREATE TRIGGER trigger_update_collections_timestamp
BEFORE UPDATE ON collections
FOR EACH ROW
EXECUTE FUNCTION update_collections_updated_at();

-- Add comments
COMMENT ON TABLE collections IS 'User-created collections for organizing documents';
COMMENT ON COLUMN collections.document_count IS 'Automatically maintained count of documents in collection';
COMMENT ON COLUMN documents.collection_id IS 'Optional collection membership';
