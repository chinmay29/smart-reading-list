import { Tag } from '../services/api';
import './TagSidebar.css';

interface TagSidebarProps {
    tags: Tag[];
    selectedTags: string[];
    onTagSelect: (tag: string) => void;
    onClearTags: () => void;
}

export default function TagSidebar({ tags, selectedTags, onTagSelect, onClearTags }: TagSidebarProps) {
    return (
        <div className="tag-sidebar">
            <div className="tag-sidebar-header">
                <h3>Tags</h3>
                {selectedTags.length > 0 && (
                    <button className="clear-tags" onClick={onClearTags}>
                        Clear
                    </button>
                )}
            </div>

            {tags.length === 0 ? (
                <p className="no-tags">No tags yet</p>
            ) : (
                <ul className="tag-list">
                    {tags.map(tag => (
                        <li key={tag.name}>
                            <button
                                className={`tag-item ${selectedTags.includes(tag.name) ? 'selected' : ''}`}
                                onClick={() => onTagSelect(tag.name)}
                            >
                                <span className="tag-name">{tag.name}</span>
                                <span className="tag-count">{tag.count}</span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
