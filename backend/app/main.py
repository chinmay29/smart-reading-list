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
    
    # Initialize services
    await get_storage_service()
    get_vector_service()
    
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
