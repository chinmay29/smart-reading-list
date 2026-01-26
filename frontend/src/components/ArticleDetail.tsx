import { useState, useCallback } from 'react';
import { Document, formatDate } from '../services/api';
import './ArticleDetail.css';

interface ArticleDetailProps {
    article: Document;
    onClose: () => void;
    onToggleRead: (article: Document) => void;
    onDelete: (article: Document) => void;
    onUpdateTags: (article: Document, tags: string[]) => void;
}

export default function ArticleDetail({
    article,
    onClose,
    onToggleRead,
    onDelete,
    onUpdateTags
}: ArticleDetailProps) {
    const [tagInput, setTagInput] = useState('');
    const [isEditingTags, setIsEditingTags] = useState(false);

    const handleAddTag = useCallback(() => {
        const newTag = tagInput.trim().toLowerCase();
        if (newTag && !article.tags.includes(newTag)) {
            onUpdateTags(article, [...article.tags, newTag]);
        }
        setTagInput('');
    }, [article, tagInput, onUpdateTags]);

    const handleRemoveTag = useCallback((tagToRemove: string) => {
        onUpdateTags(article, article.tags.filter(t => t !== tagToRemove));
    }, [article, onUpdateTags]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddTag();
        }
    }, [handleAddTag]);

    const handleBackdropClick = useCallback((e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    }, [onClose]);

    return (
        <div className="article-detail-overlay" onClick={handleBackdropClick}>
            <div className="article-detail animate-slide-up">
                <header className="detail-header">
                    <button className="close-btn" onClick={onClose}>✕</button>
                    <h1 className="detail-title">{article.title}</h1>
                    <div className="detail-meta">
                        {article.author && <span className="author">{article.author}</span>}
                        <span className="date">{formatDate(article.created_at)}</span>
                        <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-link"
                        >
                            {new URL(article.url).hostname} ↗
                        </a>
                    </div>
                </header>

                <div className="detail-body">
                    <section className="summary-section">
                        <h2>Summary</h2>
                        <p className="summary-text">{article.summary}</p>
                    </section>

                    <section className="tags-section">
                        <div className="tags-header">
                            <h2>Tags</h2>
                            <button
                                className="edit-tags-btn"
                                onClick={() => setIsEditingTags(!isEditingTags)}
                            >
                                {isEditingTags ? 'Done' : 'Edit'}
                            </button>
                        </div>

                        <div className="tags-list">
                            {article.tags.map(tag => (
                                <span key={tag} className="tag">
                                    {tag}
                                    {isEditingTags && (
                                        <button
                                            className="remove-tag"
                                            onClick={() => handleRemoveTag(tag)}
                                        >
                                            ×
                                        </button>
                                    )}
                                </span>
                            ))}

                            {isEditingTags && (
                                <div className="add-tag-input">
                                    <input
                                        type="text"
                                        placeholder="Add tag..."
                                        value={tagInput}
                                        onChange={(e) => setTagInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                    />
                                    <button onClick={handleAddTag}>+</button>
                                </div>
                            )}
                        </div>
                    </section>

                    <section className="content-preview">
                        <h2>Content Preview</h2>
                        <p className="content-text">
                            {article.content.slice(0, 1000)}
                            {article.content.length > 1000 && '...'}
                        </p>
                    </section>
                </div>

                <footer className="detail-footer">
                    <button
                        className={`btn ${article.read_status ? 'btn-secondary' : 'btn-primary'}`}
                        onClick={() => onToggleRead(article)}
                    >
                        {article.read_status ? '📖 Mark as Unread' : '✓ Mark as Read'}
                    </button>

                    <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                    >
                        Open Original ↗
                    </a>

                    <button
                        className="btn btn-danger"
                        onClick={() => onDelete(article)}
                    >
                        🗑 Delete
                    </button>
                </footer>
            </div>
        </div>
    );
}
