# Smart Reading List

A personal knowledge base that saves web articles, generates AI summaries, and enables semantic search.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (for local LLM)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Chrome Extension
1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `extension/` folder

## Architecture

```
Browser Extension → FastAPI Backend → Ollama (LLM)
                         ↓
              SQLite + ChromaDB (storage)
```

## Tech Stack
- **Backend**: FastAPI, SQLite, ChromaDB, Ollama
- **Frontend**: React, Vite, TypeScript
- **Extension**: Chrome Manifest V3
