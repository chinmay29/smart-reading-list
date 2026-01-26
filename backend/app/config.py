from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Paths
    app_name: str = "Smart Reading List"
    data_dir: Path = Path.home() / ".smart-reading-list"
    
    # Database
    database_url: str = ""  # Will be set in __init__
    
    # ChromaDB
    chroma_persist_dir: str = ""  # Will be set in __init__
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Processing
    max_content_length: int = 50000  # chars
    summary_max_tokens: int = 300
    
    class Config:
        env_prefix = "SRL_"
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set computed paths
        if not self.database_url:
            self.database_url = f"sqlite+aiosqlite:///{self.data_dir}/reading_list.db"
        if not self.chroma_persist_dir:
            self.chroma_persist_dir = str(self.data_dir / "chroma")


settings = Settings()
