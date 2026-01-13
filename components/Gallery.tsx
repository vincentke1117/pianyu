import React, { useMemo, useEffect } from 'react';
import { Article, ArticleType } from '../types';
import Banner from './Banner';
import ArticleCard from './ArticleCard';

interface GalleryProps {
  articles: Article[];
  onArticleClick: (id: string) => void;
  selectedType: ArticleType | 'all';
  selectedAuthor: string | null;
  onTypeChange: (type: ArticleType | 'all') => void;
  onAuthorChange: (author: string | null) => void;
}

const CATEGORY_CONFIG = {
  video: { label: '视频', icon: '🎬' },
  podcast: { label: '播客', icon: '🎙️' },
  article: { label: '文章', icon: '📝' },
} as const;

const Gallery: React.FC<GalleryProps> = ({
  articles,
  onArticleClick,
  selectedType,
  selectedAuthor,
  onTypeChange,
  onAuthorChange
}) => {

  // 确保页面初始滚动到顶部
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // 过滤文章
  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      if (selectedType !== 'all' && article.type !== selectedType) {
        return false;
      }
      if (selectedAuthor && article.author !== selectedAuthor) {
        return false;
      }
      return true;
    });
  }, [articles, selectedType, selectedAuthor]);

  // 计算每个分类的数量
  const counts = useMemo(() => {
    return {
      all: articles.length,
      video: articles.filter(a => a.type === 'video').length,
      podcast: articles.filter(a => a.type === 'podcast').length,
      article: articles.filter(a => a.type === 'article').length,
    };
  }, [articles]);

  // 获取所有可用作者
  const availableAuthors = useMemo(() => {
    const authors = new Set<string>();
    articles.forEach(article => {
      if (article.author) authors.add(article.author);
    });
    return Array.from(authors).sort();
  }, [articles]);

  return (
    <div className="pt-16 min-h-screen">
      {/* Hero Section */}
      <Banner />

      {/* Grid Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pb-20">

        {/* Category Filter Buttons */}
        <div className="mb-8 flex items-center gap-3 flex-wrap">
          {(['all', 'video', 'podcast', 'article'] as const).map((type) => {
            const config = type === 'all'
              ? { label: '全部', icon: '📚' }
              : CATEGORY_CONFIG[type];

            const isActive = selectedType === type;
            const count = type === 'all' ? counts.all : counts[type];

            return (
              <button
                key={type}
                onClick={() => onTypeChange(type)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-sm font-sans text-sm
                  transition-all duration-300
                  ${isActive
                    ? 'bg-gold text-white shadow-lg'
                    : 'bg-paper-200 dark:bg-mineral-800 dark:text-gray-400 text-gray-600 hover:bg-paper-300 dark:hover:bg-mineral-700'
                  }
                `}
              >
                <span>{config.icon}</span>
                <span>{config.label}</span>
                <span className={`
                  text-xs px-2 py-0.5 rounded-full
                  ${isActive
                    ? 'bg-white/20'
                    : 'bg-black/5 dark:bg-white/10'
                  }
                `}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Author Filter Dropdown */}
        <div className="mb-8">
          <select
            value={selectedAuthor || 'all'}
            onChange={(e) => onAuthorChange(e.target.value === 'all' ? null : e.target.value)}
            className="w-full md:w-auto px-4 py-2 rounded-sm font-sans text-sm
              bg-paper-200 dark:bg-mineral-800
              dark:text-gray-300 text-gray-700
              border dark:border-white/10 border-black/5
              focus:outline-none focus:ring-2 focus:ring-gold/50
              transition-all duration-300
              cursor-pointer"
          >
            <option value="all">全部作者</option>
            {availableAuthors.map(author => (
              <option key={author} value={author}>{author}</option>
            ))}
          </select>
        </div>

        {/* Section Title */}
        <div className="mb-8 flex items-end justify-between border-b dark:border-white/5 border-black/5 pb-2">
           <h2 className="text-sm font-serif font-bold dark:text-gray-400 text-gray-500 uppercase tracking-widest">
             {selectedAuthor ? `${selectedAuthor} 的内容` :
              selectedType === 'all' ? 'Latest Collections' :
              CATEGORY_CONFIG[selectedType].label}
           </h2>
           <span className="text-xs dark:text-gray-500 text-gray-400">
             {filteredArticles.length} 篇内容
           </span>
        </div>

        <div className="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6" role="list" aria-label="文章列表">
          {filteredArticles.map((article) => (
            <ArticleCard key={article.id} article={article} onClick={onArticleClick} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Gallery;