import React, { useEffect, useCallback } from 'react';
import { Search, X, Calendar, User, Filter, XCircle } from 'lucide-react';
import { Article, ArticleType } from '../types';
import { useArticleSearchAndFilter } from '../hooks/useArticleSearchAndFilter';

interface SearchDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  articles: Article[];
  onArticleClick: (id: string) => void;
}

const CATEGORY_CONFIG = {
  video: { label: '视频', icon: '🎬' },
  podcast: { label: '播客', icon: '🎙️' },
  article: { label: '文章', icon: '📝' },
} as const;

const SearchDrawer: React.FC<SearchDrawerProps> = ({ isOpen, onClose, articles, onArticleClick }) => {
  const {
    filters,
    setQuery,
    setTag,
    setType,
    setAuthor,
    resetFilters,
    filteredArticles,
    availableTags,
    availableAuthors,
    resultCount,
  } = useArticleSearchAndFilter(articles);

  // 锁定背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // ESC 关闭
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  // 检查是否有活动筛选
  const hasActiveFilters = filters.query || filters.selectedTag || filters.selectedAuthor || filters.selectedType !== 'all';

  return (
    <>
      {/* Overlay */}
      <div
        className={`
          fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-40
          transition-opacity duration-300
          ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
        `}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={`
          fixed inset-y-0 right-0 w-full sm:w-96
          bg-paper-50 dark:bg-mineral-900
          shadow-2xl z-50
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="搜索珍藏"
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b dark:border-white/10 border-black/5">
            <h2 className="text-xl font-serif font-bold dark:text-mineral-100 text-paper-900">
              搜索珍藏
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full transition-colors dark:hover:bg-white/10 hover:bg-black/5 dark:text-mineral-100 text-paper-900"
              aria-label="关闭搜索"
            >
              <X className="w-5 h-5" strokeWidth={1.5} />
            </button>
          </div>

          {/* Search Input */}
          <div className="px-6 py-4 border-b dark:border-white/10 border-black/5">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 dark:text-gray-400 text-gray-500" strokeWidth={1.5} />
              <input
                type="text"
                value={filters.query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="搜索标题、作者、内容..."
                className="w-full pl-10 pr-10 py-3 rounded-sm bg-paper-200 dark:bg-mineral-800 dark:text-mineral-100 text-paper-900 dark:placeholder-gray-500 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/50 transition-all"
                autoFocus
              />
              {filters.query && (
                <button
                  onClick={() => setQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 dark:text-gray-400 text-gray-500 hover:text-gold dark:hover:text-gold transition-colors"
                  aria-label="清除搜索"
                >
                  <XCircle className="w-5 h-5" strokeWidth={1.5} />
                </button>
              )}
            </div>
          </div>

          {/* Filters */}
          <div className="px-6 py-4 border-b dark:border-white/10 border-black/5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 dark:text-gray-400 text-gray-600 text-sm">
                <Filter className="w-4 h-4" strokeWidth={1.5} />
                <span>筛选</span>
              </div>
              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  className="text-xs dark:text-gray-400 text-gray-500 hover:text-gold dark:hover:text-gold transition-colors"
                >
                  清除全部
                </button>
              )}
            </div>

            {/* Type Filter */}
            <div className="mb-4">
              <div className="flex gap-2 flex-wrap">
                {(['all', 'video', 'podcast', 'article'] as const).map((type) => {
                  const config = type === 'all' ? { label: '全部', icon: '📚' } : CATEGORY_CONFIG[type];
                  const isActive = filters.selectedType === type;

                  return (
                    <button
                      key={type}
                      onClick={() => setType(type)}
                      className={`
                        flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs
                        transition-all duration-300
                        ${isActive
                          ? 'bg-gold text-white shadow-sm'
                          : 'bg-paper-200 dark:bg-mineral-800 dark:text-gray-400 text-gray-600 hover:bg-paper-300 dark:hover:bg-mineral-700'
                        }
                      `}
                    >
                      <span>{config.icon}</span>
                      <span>{config.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tag Filter */}
            {availableTags.length > 0 && (
              <div className="mb-4">
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                  {availableTags.slice(0, 15).map((tag) => {
                    const isActive = filters.selectedTag === tag;
                    return (
                      <button
                        key={tag}
                        onClick={() => setTag(isActive ? null : tag)}
                        className={`
                          px-3 py-1 rounded-full text-xs whitespace-nowrap
                          transition-all duration-300
                          ${isActive
                            ? 'bg-gold text-white'
                            : 'bg-paper-200 dark:bg-mineral-800 dark:text-gray-400 text-gray-600 hover:bg-paper-300 dark:hover:bg-mineral-700'
                          }
                        `}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Author Filter */}
            {availableAuthors.length > 0 && (
              <div>
                <select
                  value={filters.selectedAuthor || ''}
                  onChange={(e) => setAuthor(e.target.value || null)}
                  className="w-full px-3 py-2 rounded-sm bg-paper-200 dark:bg-mineral-800 dark:text-mineral-100 text-paper-900 text-sm focus:outline-none focus:ring-2 focus:ring-gold/50 transition-all cursor-pointer"
                >
                  <option value="">全部作者</option>
                  {availableAuthors.map((author) => (
                    <option key={author} value={author}>
                      {author}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Results Stats */}
          <div className="px-6 py-3 border-b dark:border-white/10 border-black/5">
            <span className="text-xs dark:text-gray-400 text-gray-500">
              找到 <span className="font-bold dark:text-gold text-gold-light">{resultCount}</span> 篇内容
            </span>
          </div>

          {/* Results List */}
          <div className="flex-1 overflow-y-auto">
            {filteredArticles.length > 0 ? (
              <div className="divide-y dark:divide-white/5 divide-black/5">
                {filteredArticles.map((article) => (
                  <div
                    key={article.id}
                    onClick={() => {
                      onArticleClick(article.id);
                      onClose();
                    }}
                    className="p-4 hover:bg-paper-100 dark:hover:bg-mineral-800 transition-colors cursor-pointer group"
                  >
                    <div className="flex gap-4">
                      {/* Thumbnail */}
                      <div className="w-20 h-14 flex-shrink-0 rounded-sm overflow-hidden">
                        <img
                          src={article.coverUrl}
                          alt={article.title}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-serif text-sm font-bold dark:text-mineral-100 text-paper-900 line-clamp-2 mb-2 group-hover:text-gold transition-colors">
                          {article.title}
                        </h3>

                        <div className="flex items-center gap-2 text-xs dark:text-gray-400 text-gray-500">
                          <span>{article.date}</span>
                          <span>·</span>
                          <span className="truncate max-w-[100px]">{article.author}</span>
                          <span>·</span>
                          <span>{CATEGORY_CONFIG[article.type].icon}</span>
                        </div>

                        <div className="flex gap-1 mt-2 flex-wrap">
                          {article.tags.slice(0, 3).map((tag) => (
                            <span
                              key={tag}
                              className="text-[10px] px-1.5 py-0.5 rounded-sm border dark:border-white/10 border-black/10 dark:text-gray-400 text-gray-500"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Empty State
              <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
                <div className="w-16 h-16 rounded-full bg-paper-200 dark:bg-mineral-800 flex items-center justify-center mb-4">
                  <Search className="w-8 h-8 dark:text-gray-400 text-gray-500" strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-serif dark:text-mineral-100 text-paper-900 mb-2">
                  未找到相关内容
                </h3>
                <p className="text-sm dark:text-gray-400 text-gray-500 mb-6">
                  试着调整搜索关键词或筛选条件
                </p>
                {hasActiveFilters && (
                  <button
                    onClick={resetFilters}
                    className="px-6 py-2 rounded-sm bg-gold text-white text-sm font-medium hover:opacity-90 transition-opacity"
                  >
                    清除所有筛选
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default SearchDrawer;
