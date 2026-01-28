"""Data synchronization service to keep SQLite and ChromaDB in sync."""
from typing import Optional
from .storage import get_storage_service
from .vector import get_vector_service


async def sync_vector_store() -> dict:
    """
    Synchronize ChromaDB with SQLite database.
    
    This ensures all documents in SQLite are also indexed in ChromaDB.
    Useful after restarts or when data gets out of sync.
    
    Returns:
        dict with sync stats (added, already_synced, failed)
    """
    storage = await get_storage_service()
    vector = get_vector_service()
    
    if not vector.is_available:
        return {"error": "Vector store not available", "added": 0}
    
    # Get all documents from SQLite
    documents, total = await storage.list_documents(limit=10000, offset=0)
    
    # Get existing IDs in ChromaDB
    existing_ids = set()
    try:
        if vector._collection:
            result = vector._collection.get(include=[])
            existing_ids = set(result.get("ids", []))
    except Exception:
        pass
    
    added = 0
    failed = 0
    already_synced = 0
    
    for doc in documents:
        doc_id_str = str(doc.id)
        if doc_id_str in existing_ids:
            already_synced += 1
            continue
        
        try:
            await vector.add_document(
                doc.id,
                doc.content,
                doc.title,
                {"url": doc.url}
            )
            added += 1
        except Exception as e:
            print(f"Failed to sync document {doc.id}: {e}")
            failed += 1
    
    return {
        "total_documents": total,
        "added": added,
        "already_synced": already_synced,
        "failed": failed,
        "vector_count": vector.get_count(),
    }


async def cleanup_orphaned_vectors() -> dict:
    """
    Remove vectors that don't have corresponding SQLite entries.
    
    Returns:
        dict with cleanup stats
    """
    storage = await get_storage_service()
    vector = get_vector_service()
    
    if not vector.is_available:
        return {"error": "Vector store not available", "removed": 0}
    
    # Get all document IDs from SQLite
    documents, _ = await storage.list_documents(limit=10000, offset=0)
    sqlite_ids = {str(doc.id) for doc in documents}
    
    # Get all IDs from ChromaDB
    try:
        if vector._collection:
            result = vector._collection.get(include=[])
            chroma_ids = set(result.get("ids", []))
        else:
            return {"error": "Collection not initialized", "removed": 0}
    except Exception as e:
        return {"error": str(e), "removed": 0}
    
    # Find orphaned vectors
    orphaned = chroma_ids - sqlite_ids
    removed = 0
    
    for doc_id in orphaned:
        try:
            vector._collection.delete(ids=[doc_id])
            removed += 1
        except Exception:
            pass
    
    return {
        "orphaned_found": len(orphaned),
        "removed": removed,
    }
