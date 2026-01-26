import { Document } from '../services/api';
import ArticleCard from './ArticleCard';
import './ArticleList.css';

interface ArticleListProps {
    articles: Document[];
    onArticleClick: (article: Document) => void;
    onToggleRead: (article: Document) => void;
}

export default function ArticleList({ articles, onArticleClick, onToggleRead }: ArticleListProps) {
    return (
        <div className="article-list">
            {articles.map((article, index) => (
                <div
                    key={article.id}
                    className="article-list-item animate-slide-up"
                    style={{ animationDelay: `${index * 0.05}s` }}
                >
                    <ArticleCard
                        article={article}
                        onClick={() => onArticleClick(article)}
                        onToggleRead={() => onToggleRead(article)}
                    />
                </div>
            ))}
        </div>
    );
}
