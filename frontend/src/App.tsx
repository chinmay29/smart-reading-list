import { useState, useCallback } from 'react';
import { useDocuments, useSearch, useTags } from './hooks/useApi';
import { Document, updateDocument, deleteDocument } from './services/api';
import SearchBar from './components/SearchBar';
import TagSidebar from './components/TagSidebar';
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';
import './App.css';

function App() {
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [selectedArticle, setSelectedArticle] = useState<Document | null>(null);

    const { documents, loading, error, reload } = useDocuments({ tags: selectedTags.length ? selectedTags : undefined });
    const { tags, reload: reloadTags } = useTags();
    const { results: searchResults, loading: searching, query, search, clear: clearSearch } = useSearch();

    // Determine what to display
    const displayDocs = query ? searchResults : documents;
    const isSearching = !!query;

    const handleTagSelect = useCallback((tag: string) => {
        setSelectedTags(prev =>
            prev.includes(tag)
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        );
        clearSearch();
    }, [clearSearch]);

    const handleClearTags = useCallback(() => {
        setSelectedTags([]);
    }, []);

    const handleArticleClick = useCallback((article: Document) => {
        setSelectedArticle(article);
    }, []);

    const handleCloseDetail = useCallback(() => {
        setSelectedArticle(null);
    }, []);

    const handleToggleRead = useCallback(async (article: Document) => {
        await updateDocument(article.id, { read_status: !article.read_status });
        reload();
    }, [reload]);

    const handleDelete = useCallback(async (article: Document) => {
        if (confirm('Delete this article?')) {
            await deleteDocument(article.id);
            setSelectedArticle(null);
            reload();
            reloadTags();
        }
    }, [reload, reloadTags]);

    const handleUpdateTags = useCallback(async (article: Document, newTags: string[]) => {
        await updateDocument(article.id, { tags: newTags });
        reload();
        reloadTags();
    }, [reload, reloadTags]);

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h1 className="logo">📚 Reading List</h1>
                </div>
                <TagSidebar
                    tags={tags}
                    selectedTags={selectedTags}
                    onTagSelect={handleTagSelect}
                    onClearTags={handleClearTags}
                />
            </aside>

            <main className="main-content">
                <header className="content-header">
                    <SearchBar
                        onSearch={search}
                        onClear={clearSearch}
                        isSearching={searching}
                    />
                </header>

                <div className="content-body">
                    {error ? (
                        <div className="error-state">
                            <p>⚠️ {error}</p>
                            <button onClick={reload} className="btn btn-secondary">Retry</button>
                        </div>
                    ) : loading ? (
                        <div className="loading-state">
                            <div className="loading-spinner"></div>
                            <p>Loading articles...</p>
                        </div>
                    ) : displayDocs.length === 0 ? (
                        <div className="empty-state">
                            {isSearching ? (
                                <>
                                    <h2>No results found</h2>
                                    <p>Try a different search term or use the browser extension to save articles.</p>
                                </>
                            ) : (
                                <>
                                    <h2>No articles yet</h2>
                                    <p>Use the browser extension to save your first article!</p>
                                </>
                            )}
                        </div>
                    ) : (
                        <>
                            <div className="results-header">
                                <h2>
                                    {isSearching
                                        ? `${displayDocs.length} results for "${query}"`
                                        : `${displayDocs.length} articles`}
                                </h2>
                                {selectedTags.length > 0 && (
                                    <div className="active-filters">
                                        {selectedTags.map(tag => (
                                            <span key={tag} className="filter-tag">
                                                {tag}
                                                <button onClick={() => handleTagSelect(tag)}>×</button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <ArticleList
                                articles={displayDocs}
                                onArticleClick={handleArticleClick}
                                onToggleRead={handleToggleRead}
                            />
                        </>
                    )}
                </div>
            </main>

            {selectedArticle && (
                <ArticleDetail
                    article={selectedArticle}
                    onClose={handleCloseDetail}
                    onToggleRead={handleToggleRead}
                    onDelete={handleDelete}
                    onUpdateTags={handleUpdateTags}
                />
            )}
        </div>
    );
}

export default App;
