"""Ollama LLM service for summarization and embeddings."""
import httpx
from typing import Optional
from ..config import settings


class LLMService:
    """Service for interacting with Ollama for LLM operations."""
    
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.embedding_model = settings.ollama_embedding_model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def summarize(self, content: str, title: str = "") -> str:
        """Generate a summary of the content using Ollama."""
        # Truncate content if too long
        max_chars = settings.max_content_length
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        
        prompt = f"""Summarize the following article in 2-3 concise paragraphs. 
Focus on the key points, main arguments, and conclusions.

Title: {title}

Article:
{content}

Summary:"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": settings.summary_max_tokens,
                        "temperature": 0.3,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except httpx.HTTPError as e:
            # Return placeholder if Ollama is unavailable
            return f"[Summary unavailable: {str(e)}]"
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text using Ollama."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text[:8000],  # Limit input
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except httpx.HTTPError:
            # Return empty embedding if unavailable
            return []
    
    async def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
