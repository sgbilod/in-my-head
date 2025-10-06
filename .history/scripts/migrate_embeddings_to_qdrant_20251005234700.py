"""
Migration Script: PostgreSQL Embeddings → Qdrant

This script migrates existing document embeddings from PostgreSQL (JSON format)
to Qdrant vector database for improved search performance.

Usage:
    python scripts/migrate_embeddings_to_qdrant.py [--batch-size 100] [--skip-existing]
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

# Configuration
DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "document_embeddings"
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 100


class EmbeddingMigrator:
    """Handles migration of embeddings from PostgreSQL to Qdrant."""
    
    def __init__(
        self,
        database_url: str,
        qdrant_url: str,
        collection_name: str,
        batch_size: int = 100
    ):
        """Initialize migrator."""
        self.database_url = database_url
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.batch_size = batch_size
        
        # Initialize connections
        self.engine = create_engine(database_url)
        self.qdrant_client = QdrantClient(url=qdrant_url)
        
        # Statistics
        self.total_documents = 0
        self.migrated_documents = 0
        self.failed_documents = 0
        self.errors: List[str] = []
    
    def setup_qdrant_collection(self) -> None:
        """
        Set up Qdrant collection for embeddings.
        
        Creates collection if it doesn't exist.
        """
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name in collection_names:
                print(f"✓ Collection '{self.collection_name}' already exists")
                
                # Get collection info
                info = self.qdrant_client.get_collection(self.collection_name)
                print(f"  - Vectors: {info.vectors_count}")
                print(f"  - Points: {info.points_count}")
            else:
                # Create new collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection '{self.collection_name}'")
                print(f"  - Dimension: {EMBEDDING_DIMENSION}")
                print(f"  - Distance: COSINE")
        
        except Exception as e:
            print(f"✗ Failed to setup collection: {e}")
            raise
    
    def fetch_documents_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        Fetch all documents with embeddings from PostgreSQL.
        
        Returns:
            List of document dictionaries with id, embedding, and metadata
        """
        try:
            with Session(self.engine) as session:
                # Query documents with embeddings
                query = text("""
                    SELECT 
                        d.id,
                        d.title,
                        d.file_type,
                        d.file_size,
                        d.embedding,
                        d.created_at,
                        u.username,
                        c.name as collection_name
                    FROM documents d
                    LEFT JOIN users u ON d.user_id = u.id
                    LEFT JOIN collections c ON d.collection_id = c.id
                    WHERE d.embedding IS NOT NULL
                    ORDER BY d.created_at DESC
                """)
                
                result = session.execute(query)
                rows = result.fetchall()
                
                documents = []
                for row in rows:
                    # Parse embedding JSON
                    try:
                        embedding = json.loads(row.embedding) if isinstance(row.embedding, str) else row.embedding
                        
                        documents.append({
                            "id": str(row.id),
                            "embedding": embedding,
                            "payload": {
                                "document_id": str(row.id),
                                "title": row.title,
                                "file_type": row.file_type,
                                "file_size": row.file_size,
                                "username": row.username,
                                "collection_name": row.collection_name,
                                "created_at": row.created_at.isoformat() if row.created_at else None
                            }
                        })
                    except (json.JSONDecodeError, TypeError) as e:
                        self.errors.append(f"Failed to parse embedding for document {row.id}: {e}")
                        self.failed_documents += 1
                        continue
                
                return documents
        
        except Exception as e:
            print(f"✗ Failed to fetch documents: {e}")
            raise
    
    def migrate_batch(self, documents: List[Dict[str, Any]]) -> int:
        """
        Migrate a batch of documents to Qdrant.
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            Number of successfully migrated documents
        """
        try:
            # Create point structures
            points = [
                PointStruct(
                    id=doc["id"],
                    vector=doc["embedding"],
                    payload=doc["payload"]
                )
                for doc in documents
            ]
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return len(points)
        
        except Exception as e:
            error_msg = f"Failed to migrate batch: {e}"
            self.errors.append(error_msg)
            return 0
    
    def run_migration(self, skip_existing: bool = True) -> Dict[str, Any]:
        """
        Run the complete migration process.
        
        Args:
            skip_existing: If True, skip documents already in Qdrant
        
        Returns:
            Migration statistics
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("EMBEDDING MIGRATION: PostgreSQL → Qdrant")
        print("="*70 + "\n")
        
        # Step 1: Setup Qdrant collection
        print("Step 1: Setting up Qdrant collection...")
        self.setup_qdrant_collection()
        print()
        
        # Step 2: Fetch documents from PostgreSQL
        print("Step 2: Fetching documents from PostgreSQL...")
        documents = self.fetch_documents_with_embeddings()
        self.total_documents = len(documents)
        print(f"✓ Found {self.total_documents} documents with embeddings")
        print()
        
        if self.total_documents == 0:
            print("No documents to migrate. Exiting.")
            return self._get_statistics(time.time() - start_time)
        
        # Step 3: Migrate in batches
        print(f"Step 3: Migrating embeddings (batch size: {self.batch_size})...")
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
            
            print(f"  Batch {batch_num}/{total_batches}: ", end="", flush=True)
            
            migrated = self.migrate_batch(batch)
            self.migrated_documents += migrated
            
            if migrated == len(batch):
                print(f"✓ {migrated} documents")
            else:
                failed = len(batch) - migrated
                self.failed_documents += failed
                print(f"⚠ {migrated} documents ({failed} failed)")
        
        print()
        
        # Step 4: Verify migration
        print("Step 4: Verifying migration...")
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        print(f"✓ Qdrant collection now contains {collection_info.points_count} vectors")
        print()
        
        # Step 5: Summary
        elapsed_time = time.time() - start_time
        print("="*70)
        print("MIGRATION COMPLETE")
        print("="*70)
        
        return self._get_statistics(elapsed_time)
    
    def _get_statistics(self, elapsed_time: float) -> Dict[str, Any]:
        """Generate migration statistics."""
        stats = {
            "total_documents": self.total_documents,
            "migrated_documents": self.migrated_documents,
            "failed_documents": self.failed_documents,
            "success_rate": (
                round(self.migrated_documents / self.total_documents * 100, 2)
                if self.total_documents > 0
                else 0
            ),
            "processing_time_ms": round(elapsed_time * 1000, 2),
            "errors": self.errors
        }
        
        # Print summary
        print(f"\nTotal documents:     {stats['total_documents']}")
        print(f"Migrated:            {stats['migrated_documents']} ✓")
        print(f"Failed:              {stats['failed_documents']} ✗")
        print(f"Success rate:        {stats['success_rate']}%")
        print(f"Processing time:     {stats['processing_time_ms']} ms")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")
        
        print()
        
        return stats


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate embeddings from PostgreSQL to Qdrant"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for migration (default: 100)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip documents already in Qdrant"
    )
    
    args = parser.parse_args()
    
    try:
        # Create migrator
        migrator = EmbeddingMigrator(
            database_url=DATABASE_URL,
            qdrant_url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            batch_size=args.batch_size
        )
        
        # Run migration
        stats = migrator.run_migration(skip_existing=args.skip_existing)
        
        # Exit with appropriate code
        if stats["failed_documents"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
