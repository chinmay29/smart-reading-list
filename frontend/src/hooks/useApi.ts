import { useState, useEffect, useCallback } from 'react';
import { Document, Tag, fetchDocuments, fetchTags, searchDocuments } from '../services/api';

// Hook for fetching and managing documents
export function useDocuments(options: {
    tags?: string[];
    readStatus?: boolean;
} = {}) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetchDocuments({
                limit: 50,
                tags: options.tags,
                read_status: options.readStatus,
            });
            setDocuments(response.documents);
            setTotal(response.total);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load documents');
        } finally {
            setLoading(false);
        }
    }, [options.tags, options.readStatus]);

    useEffect(() => {
        load();
    }, [load]);

    return { documents, total, loading, error, reload: load };
}

// Hook for search
export function useSearch() {
    const [results, setResults] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState('');

    const search = useCallback(async (searchQuery: string, semantic: boolean = true) => {
        if (!searchQuery.trim()) {
            setResults([]);
            return;
        }

        setQuery(searchQuery);
        setLoading(true);
        setError(null);

        try {
            const response = await searchDocuments(searchQuery, { semantic });
            setResults(response.results);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed');
        } finally {
            setLoading(false);
        }
    }, []);

    const clear = useCallback(() => {
        setResults([]);
        setQuery('');
    }, []);

    return { results, loading, error, query, search, clear };
}

// Hook for tags
export function useTags() {
    const [tags, setTags] = useState<Tag[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await fetchTags();
            setTags(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load tags');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    return { tags, loading, error, reload: load };
}
