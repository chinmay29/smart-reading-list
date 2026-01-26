import { useState, useCallback } from 'react';
import './SearchBar.css';

interface SearchBarProps {
    onSearch: (query: string, semantic: boolean) => void;
    onClear: () => void;
    isSearching: boolean;
}

export default function SearchBar({ onSearch, onClear, isSearching }: SearchBarProps) {
    const [query, setQuery] = useState('');
    const [semantic, setSemantic] = useState(true);

    const handleSubmit = useCallback((e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query, semantic);
        }
    }, [query, semantic, onSearch]);

    const handleClear = useCallback(() => {
        setQuery('');
        onClear();
    }, [onClear]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            handleClear();
        }
    }, [handleClear]);

    return (
        <form className="search-bar" onSubmit={handleSubmit}>
            <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                    type="text"
                    className="search-input"
                    placeholder="Search articles..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
                {query && (
                    <button type="button" className="clear-btn" onClick={handleClear}>
                        ✕
                    </button>
                )}
            </div>

            <div className="search-options">
                <label className="search-mode">
                    <input
                        type="checkbox"
                        checked={semantic}
                        onChange={(e) => setSemantic(e.target.checked)}
                    />
                    <span className="mode-label">
                        {semantic ? '🧠 Semantic' : '📝 Full-text'}
                    </span>
                </label>

                <button
                    type="submit"
                    className="search-btn"
                    disabled={!query.trim() || isSearching}
                >
                    {isSearching ? 'Searching...' : 'Search'}
                </button>
            </div>
        </form>
    );
}
