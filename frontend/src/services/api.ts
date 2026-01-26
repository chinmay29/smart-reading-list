// API service for Smart Reading List frontend

const API_BASE = '/api';

export interface Document {
    id: string;
    url: string;
    title: string;
    author: string | null;
    published_date: string | null;
    source_type: string;
    content: string;
    summary: string;
    tags: string[];
    read_status: boolean;
    created_at: string;
    updated_at: string;
    relevance_score?: number;
}

export interface DocumentListResponse {
    documents: Document[];
    total: number;
    limit: number;
    offset: number;
}

export interface SearchResponse {
    results: Document[];
    total: number;
    query: string;
}

export interface Tag {
    name: string;
    count: number;
}

export interface HealthStatus {
    status: string;
    ollama: string;
    vector_store_count: number;
}

// Fetch documents with optional filters
export async function fetchDocuments(
    options: {
        limit?: number;
        offset?: number;
        tags?: string[];
        read_status?: boolean;
    } = {}
): Promise<DocumentListResponse> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', String(options.limit));
    if (options.offset) params.append('offset', String(options.offset));
    if (options.tags?.length) params.append('tags', options.tags.join(','));
    if (options.read_status !== undefined) params.append('read_status', String(options.read_status));

    const response = await fetch(`${API_BASE}/documents?${params}`);
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
}

// Get single document
export async function fetchDocument(id: string): Promise<Document> {
    const response = await fetch(`${API_BASE}/documents/${id}`);
    if (!response.ok) throw new Error('Document not found');
    return response.json();
}

// Update document (tags, read status)
export async function updateDocument(
    id: string,
    updates: { tags?: string[]; read_status?: boolean; title?: string }
): Promise<Document> {
    const response = await fetch(`${API_BASE}/documents/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update document');
    return response.json();
}

// Delete document
export async function deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/documents/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete document');
}

// Search documents
export async function searchDocuments(
    query: string,
    options: { semantic?: boolean; limit?: number } = {}
): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query,
            semantic: options.semantic ?? true,
            limit: options.limit ?? 20,
        }),
    });
    if (!response.ok) throw new Error('Search failed');
    return response.json();
}

// Get all tags
export async function fetchTags(): Promise<Tag[]> {
    const response = await fetch(`${API_BASE}/tags`);
    if (!response.ok) throw new Error('Failed to fetch tags');
    const data = await response.json();
    return data.tags;
}

// Health check
export async function checkHealth(): Promise<HealthStatus> {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
}

// Format date for display
export function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
}

// Truncate text
export function truncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
}
