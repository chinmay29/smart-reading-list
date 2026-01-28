"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import router
from .services import get_storage_service, get_vector_service, get_llm_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 Starting {settings.app_name}")
    print(f"📁 Data directory: {settings.data_dir}")
    
    # Initialize services
    await get_storage_service()
    get_vector_service()
    
    # Auto-sync ChromaDB with SQLite to ensure consistency
    from .services import sync_vector_store
    sync_result = await sync_vector_store()
    if sync_result.get("added", 0) > 0:
        print(f"🔄 Synced {sync_result['added']} documents to vector store")
    print(f"📊 Vector store: {sync_result.get('vector_count', 0)} documents indexed")
    
    # Check Ollama
    llm = get_llm_service()
    if await llm.is_available():
        print(f"✅ Ollama connected ({settings.ollama_model})")
    else:
        print(f"⚠️  Ollama not available at {settings.ollama_base_url}")
        print("   Summarization will be disabled until Ollama is running.")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    storage = await get_storage_service()
    await storage.close()
    await llm.close()


app = FastAPI(
    title=settings.app_name,
    description="Personal knowledge base with AI-powered summarization and semantic search",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for browser extension and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }
