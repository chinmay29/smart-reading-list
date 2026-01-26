import { Document, formatDate, truncate } from '../services/api';
import './ArticleCard.css';

interface ArticleCardProps {
    article: Document;
    onClick: () => void;
    onToggleRead: () => void;
}

export default function ArticleCard({ article, onClick, onToggleRead }: ArticleCardProps) {
    const handleToggleRead = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggleRead();
    };

    const isGeneratingSummary = article.summary.includes('Generating');

    return (
        <div
            className={`article-card ${article.read_status ? 'read' : ''}`}
            onClick={onClick}
        >
            <div className="card-header">
                <h3 className="card-title">{article.title}</h3>
                <button
                    className={`read-toggle ${article.read_status ? 'is-read' : ''}`}
                    onClick={handleToggleRead}
                    title={article.read_status ? 'Mark as unread' : 'Mark as read'}
                >
                    {article.read_status ? '✓' : '○'}
                </button>
            </div>

            <div className="card-meta">
                {article.author && <span className="author">{article.author}</span>}
                <span className="date">{formatDate(article.created_at)}</span>
                <span className="source">{new URL(article.url).hostname}</span>
            </div>

            <p className={`card-summary ${isGeneratingSummary ? 'generating' : ''}`}>
                {isGeneratingSummary
                    ? '✨ Generating AI summary...'
                    : truncate(article.summary, 200)}
            </p>

            {article.tags.length > 0 && (
                <div className="card-tags">
                    {article.tags.slice(0, 4).map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                    ))}
                    {article.tags.length > 4 && (
                        <span className="tag more">+{article.tags.length - 4}</span>
                    )}
                </div>
            )}

            {article.relevance_score !== undefined && (
                <div className="relevance-score">
                    {Math.round(article.relevance_score * 100)}% match
                </div>
            )}
        </div>
    );
}
