"""REST API routes for the Smart Reading List."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    SourceType,
)
from ..services import get_storage_service, get_vector_service, get_llm_service
from ..parsers import get_parser_registry

router = APIRouter()


async def _process_document_background(doc_id: UUID, content: str, title: str):
    """Background task to generate summary and embeddings."""
    storage = await get_storage_service()
    vector = get_vector_service()
    llm = get_llm_service()
    
    # Generate summary
    summary = await llm.summarize(content, title)
    
    # Update document with summary
    doc = await storage.get_document(doc_id)
    if doc:
        doc.summary = summary
        await storage._db.execute(
            "UPDATE documents SET summary = ? WHERE id = ?",
            (summary, str(doc_id))
        )
        await storage._db.commit()
    
    # Add to vector store
    await vector.add_document(doc_id, content, title)


@router.post("/documents", response_model=DocumentResponse)
async def create_document(doc_in: DocumentCreate, background_tasks: BackgroundTasks):
    """
    Save a new document.
    
    The HTML content is parsed to extract article text, then:
    - Stored in SQLite for full-text search
    - Summary generated via Ollama (background)
    - Embeddings added to ChromaDB (background)
    """
    storage = await get_storage_service()
    
    # Check for duplicate URL
    existing = await storage.get_document_by_url(doc_in.url)
    if existing:
        raise HTTPException(status_code=409, detail="Document with this URL already exists")
    
    # Parse HTML content
    parser_registry = get_parser_registry()
    parsed = parser_registry.parse(
        doc_in.html_content,
        doc_in.url,
        "text/html"
    )
    
    # Create document
    doc = Document(
        url=doc_in.url,
        title=doc_in.title or parsed.title,
        author=parsed.author,
        published_date=None,  # TODO: Parse date from parsed.published_date
        source_type=doc_in.source_type,
        content=parsed.content,
        summary="Generating summary...",  # Placeholder
        tags=doc_in.tags,
    )
    
    await storage.create_document(doc)
    
    # Process in background (summary + embeddings)
    background_tasks.add_task(
        _process_document_background,
        doc.id,
        parsed.content,
        doc.title
    )
    
    return DocumentResponse(**doc.model_dump())


@router.get("/documents", response_model=dict)
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    tags: Optional[str] = None,  # Comma-separated
    read_status: Optional[bool] = None,
):
    """List all documents with pagination and filters."""
    storage = await get_storage_service()
    
    tag_list = tags.split(",") if tags else None
    
    documents, total = await storage.list_documents(
        limit=limit,
        offset=offset,
        tags=tag_list,
        read_status=read_status,
    )
    
    return {
        "documents": [DocumentResponse(**d.model_dump()) for d in documents],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: UUID):
    """Get a single document by ID."""
    storage = await get_storage_service()
    doc = await storage.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(**doc.model_dump())


@router.patch("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(doc_id: UUID, update: DocumentUpdate):
    """Update document fields (title, tags, read status)."""
    storage = await get_storage_service()
    doc = await storage.update_document(doc_id, update)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(**doc.model_dump())


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: UUID):
    """Delete a document."""
    storage = await get_storage_service()
    vector = get_vector_service()
    
    deleted = await storage.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Also remove from vector store
    await vector.delete_document(doc_id)
    
    return {"status": "deleted", "id": str(doc_id)}


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search documents using full-text and/or semantic search.
    
    - semantic=True: Uses ChromaDB vector similarity
    - semantic=False: Uses SQLite FTS5 full-text search
    """
    storage = await get_storage_service()
    
    if request.semantic:
        vector = get_vector_service()
        results = await vector.search(request.query, limit=request.limit)
        
        # Fetch full documents
        documents = []
        for r in results:
            doc = await storage.get_document(UUID(r["id"]))
            if doc:
                resp = DocumentResponse(**doc.model_dump())
                resp.relevance_score = r["score"]
                documents.append(resp)
        
        return SearchResponse(
            results=documents,
            total=len(documents),
            query=request.query,
        )
    else:
        # Full-text search
        documents = await storage.search_fulltext(request.query, limit=request.limit)
        
        return SearchResponse(
            results=[DocumentResponse(**d.model_dump()) for d in documents],
            total=len(documents),
            query=request.query,
        )


@router.get("/tags")
async def get_all_tags():
    """Get all tags with document counts."""
    storage = await get_storage_service()
    tags = await storage.get_all_tags()
    return {"tags": tags}


@router.get("/health")
async def health_check():
    """Check service health including Ollama connectivity."""
    llm = get_llm_service()
    vector = get_vector_service()
    
    ollama_available = await llm.is_available()
    
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_available else "unavailable",
        "vector_store_count": vector.get_count(),
    }
