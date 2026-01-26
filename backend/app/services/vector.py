"""ChromaDB vector storage service for semantic search."""
from typing import Optional
from uuid import UUID
from ..config import settings

# Import chromadb
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None


class VectorService:
    """ChromaDB-based vector storage for semantic search."""
    
    COLLECTION_NAME = "documents"
    
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self._client = None
        self._collection = None
        self._available = False
    
    def initialize(self):
        """Initialize ChromaDB client and collection."""
        if not CHROMADB_AVAILABLE:
            print("⚠️  ChromaDB not available - semantic search disabled")
            return
        
        try:
            # ChromaDB 1.x API
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
            )
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            self._available = True
            print(f"✅ ChromaDB initialized with {self._collection.count()} documents")
        except Exception as e:
            print(f"⚠️  ChromaDB initialization failed: {e}")
            self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    async def add_document(self, doc_id: UUID, content: str, title: str, metadata: dict = None):
        """Add a document to the vector store."""
        if not self._available:
            return
        
        try:
            doc_metadata = {
                "title": title,
                **(metadata or {})
            }
            
            # ChromaDB will generate embeddings automatically using its default model
            self._collection.upsert(
                ids=[str(doc_id)],
                metadatas=[doc_metadata],
                documents=[content[:8000]]  # Store content for embedding
            )
            print(f"✅ Added document to vector store: {title[:50]}...")
        except Exception as e:
            print(f"Failed to add document to vector store: {e}")
    
    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """Semantic search across documents."""
        if not self._available:
            return []
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(limit, self._collection.count() or 1),
                include=["metadatas", "distances", "documents"]
            )
            
            # Format results
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 1
                    # Convert distance to similarity score (cosine distance -> similarity)
                    score = max(0, 1 - distance)
                    formatted.append({
                        "id": doc_id,
                        "score": score,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "content_preview": results["documents"][0][i][:200] if results["documents"] else "",
                    })
            
            return formatted
        except Exception as e:
            print(f"Semantic search failed: {e}")
            return []
    
    async def delete_document(self, doc_id: UUID):
        """Remove a document from the vector store."""
        if not self._available:
            return
        
        try:
            self._collection.delete(ids=[str(doc_id)])
        except Exception:
            pass  # Document might not exist in vector store
    
    def get_count(self) -> int:
        """Get the number of documents in the vector store."""
        if not self._available or not self._collection:
            return 0
        return self._collection.count()


# Singleton
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get or create the vector service singleton."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
        _vector_service.initialize()
    return _vector_service
