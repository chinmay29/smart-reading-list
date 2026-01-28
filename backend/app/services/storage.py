"""SQLite storage service for document metadata."""
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID
from ..config import settings
from ..models import Document, DocumentUpdate, SourceType


class StorageService:
    """SQLite-based storage for document metadata."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.data_dir / "reading_list.db")
        self._db: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize database and create tables."""
        print(f"📦 SQLite connecting to: {self.db_path}")
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row
        
        # Create documents table
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                published_date TEXT,
                source_type TEXT NOT NULL DEFAULT 'web_article',
                content TEXT NOT NULL,
                summary TEXT DEFAULT '',
                read_status INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create tags table (many-to-many)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS document_tags (
                document_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (document_id, tag_id),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        # Create FTS5 virtual table for full-text search
        await self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                title, content, summary,
                content='documents',
                content_rowid='rowid'
            )
        """)
        
        # Triggers to keep FTS in sync
        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, title, content, summary)
                VALUES (NEW.rowid, NEW.title, NEW.content, NEW.summary);
            END
        """)
        
        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content, summary)
                VALUES ('delete', OLD.rowid, OLD.title, OLD.content, OLD.summary);
            END
        """)
        
        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content, summary)
                VALUES ('delete', OLD.rowid, OLD.title, OLD.content, OLD.summary);
                INSERT INTO documents_fts(rowid, title, content, summary)
                VALUES (NEW.rowid, NEW.title, NEW.content, NEW.summary);
            END
        """)
        
        # Create indexes
        await self._db.execute("CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url)")
        await self._db.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)")
        
        await self._db.commit()
    
    async def close(self):
        """Close database connection."""
        if self._db:
            await self._db.close()
    
    async def create_document(self, doc: Document) -> Document:
        """Insert a new document."""
        now = datetime.utcnow().isoformat()
        
        await self._db.execute("""
            INSERT INTO documents (id, url, title, author, published_date, source_type, 
                                   content, summary, read_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(doc.id), doc.url, doc.title, doc.author,
            doc.published_date.isoformat() if doc.published_date else None,
            doc.source_type.value, doc.content, doc.summary,
            1 if doc.read_status else 0, now, now
        ))
        
        # Handle tags
        for tag_name in doc.tags:
            await self._ensure_tag(tag_name)
            await self._db.execute("""
                INSERT OR IGNORE INTO document_tags (document_id, tag_id)
                SELECT ?, id FROM tags WHERE name = ?
            """, (str(doc.id), tag_name))
        
        await self._db.commit()
        return doc
    
    async def _ensure_tag(self, tag_name: str) -> int:
        """Ensure tag exists and return its ID."""
        await self._db.execute(
            "INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,)
        )
        cursor = await self._db.execute(
            "SELECT id FROM tags WHERE name = ?", (tag_name,)
        )
        row = await cursor.fetchone()
        return row["id"]
    
    async def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        cursor = await self._db.execute(
            "SELECT * FROM documents WHERE id = ?", (str(doc_id),)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return await self._row_to_document(row)
    
    async def get_document_by_url(self, url: str) -> Optional[Document]:
        """Get a document by URL."""
        cursor = await self._db.execute(
            "SELECT * FROM documents WHERE url = ?", (url,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return await self._row_to_document(row)
    
    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        tags: Optional[list[str]] = None,
        read_status: Optional[bool] = None,
    ) -> tuple[list[Document], int]:
        """List documents with pagination and filters."""
        query = "SELECT * FROM documents"
        count_query = "SELECT COUNT(*) as count FROM documents"
        params = []
        where_clauses = []
        
        if read_status is not None:
            where_clauses.append("read_status = ?")
            params.append(1 if read_status else 0)
        
        if tags:
            placeholders = ",".join("?" * len(tags))
            where_clauses.append(f"""
                id IN (
                    SELECT document_id FROM document_tags dt
                    JOIN tags t ON dt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                )
            """)
            params.extend(tags)
        
        if where_clauses:
            where = " WHERE " + " AND ".join(where_clauses)
            query += where
            count_query += where
        
        # Get total count
        cursor = await self._db.execute(count_query, params)
        row = await cursor.fetchone()
        total = row["count"]
        
        # Get documents
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()
        
        documents = []
        for row in rows:
            doc = await self._row_to_document(row)
            documents.append(doc)
        
        return documents, total
    
    async def update_document(self, doc_id: UUID, update: DocumentUpdate) -> Optional[Document]:
        """Update a document."""
        doc = await self.get_document(doc_id)
        if not doc:
            return None
        
        updates = []
        params = []
        
        if update.title is not None:
            updates.append("title = ?")
            params.append(update.title)
        
        if update.read_status is not None:
            updates.append("read_status = ?")
            params.append(1 if update.read_status else 0)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(str(doc_id))
            
            await self._db.execute(
                f"UPDATE documents SET {', '.join(updates)} WHERE id = ?",
                params
            )
        
        # Handle tags update
        if update.tags is not None:
            await self._db.execute(
                "DELETE FROM document_tags WHERE document_id = ?",
                (str(doc_id),)
            )
            for tag_name in update.tags:
                await self._ensure_tag(tag_name)
                await self._db.execute("""
                    INSERT INTO document_tags (document_id, tag_id)
                    SELECT ?, id FROM tags WHERE name = ?
                """, (str(doc_id), tag_name))
        
        await self._db.commit()
        return await self.get_document(doc_id)
    
    async def delete_document(self, doc_id: UUID) -> bool:
        """Delete a document."""
        cursor = await self._db.execute(
            "DELETE FROM documents WHERE id = ?", (str(doc_id),)
        )
        await self._db.commit()
        return cursor.rowcount > 0
    
    async def search_fulltext(self, query: str, limit: int = 20) -> list[Document]:
        """Full-text search using SQLite FTS5."""
        cursor = await self._db.execute("""
            SELECT d.*, bm25(documents_fts) as rank
            FROM documents d
            JOIN documents_fts fts ON d.rowid = fts.rowid
            WHERE documents_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        rows = await cursor.fetchall()
        documents = []
        for row in rows:
            doc = await self._row_to_document(row)
            documents.append(doc)
        return documents
    
    async def get_all_tags(self) -> list[dict]:
        """Get all tags with document counts."""
        cursor = await self._db.execute("""
            SELECT t.name, COUNT(dt.document_id) as count
            FROM tags t
            LEFT JOIN document_tags dt ON t.id = dt.tag_id
            GROUP BY t.id, t.name
            ORDER BY count DESC, t.name
        """)
        rows = await cursor.fetchall()
        return [{"name": row["name"], "count": row["count"]} for row in rows]
    
    async def _row_to_document(self, row: aiosqlite.Row) -> Document:
        """Convert database row to Document model."""
        doc_id = row["id"]
        
        # Get tags for this document
        cursor = await self._db.execute("""
            SELECT t.name FROM tags t
            JOIN document_tags dt ON t.id = dt.tag_id
            WHERE dt.document_id = ?
        """, (doc_id,))
        tag_rows = await cursor.fetchall()
        tags = [r["name"] for r in tag_rows]
        
        return Document(
            id=UUID(doc_id),
            url=row["url"],
            title=row["title"],
            author=row["author"],
            published_date=datetime.fromisoformat(row["published_date"]) if row["published_date"] else None,
            source_type=SourceType(row["source_type"]),
            content=row["content"],
            summary=row["summary"],
            tags=tags,
            read_status=bool(row["read_status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# Singleton
_storage_service: Optional[StorageService] = None


async def get_storage_service() -> StorageService:
    """Get or create the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
        await _storage_service.initialize()
    return _storage_service
