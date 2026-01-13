import React from 'react';
import { Article } from '../types';
import { Calendar, User } from 'lucide-react';
import LazyImage from './LazyImage';

interface ArticleCardProps {
  article: Article;
  onClick: (id: string) => void;
}

/**
 * 文章卡片组件
 * 显示文章封面、标题、作者、日期和预览金句
 */
const ArticleCard: React.FC<ArticleCardProps> = React.memo(({ article, onClick }) => {
  return (
    <article
      onClick={() => onClick(article.id)}
      className="break-inside-avoid group cursor-pointer animate-fade-in"
      role="listitem"
      tabIndex={0}
      onKeyPress={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick(article.id);
        }
      }}
    >
      {/* Card Container */}
      <div className="relative overflow-hidden rounded-sm bg-paper-100 dark:bg-mineral-800 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
        {/* Image Container */}
        <div className="relative aspect-video overflow-hidden">
          <LazyImage
            src={article.coverUrl}
            alt={article.title}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
          {/* Dark Mode Overlay: Fades out on hover */}
          <div className="absolute inset-0 bg-black/40 dark:bg-black/60 transition-opacity duration-500 group-hover:opacity-0" />
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs dark:text-gray-400 text-gray-500 font-sans mb-3">
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{article.date}</span>
            </div>
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span>{article.author}</span>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-xl font-serif font-bold leading-snug mb-4 dark:text-mineral-100 text-paper-900 group-hover:text-gold transition-colors duration-300 line-clamp-2">
            {article.title}
          </h2>

          {/* Golden Quote Preview */}
          <div className="relative pl-4 py-1">
            {/* Gold Bar Decoration */}
            <div className="absolute left-0 top-0 bottom-0 w-[2px] dark:bg-gold bg-gold-light" />
            <p className="text-sm font-serif italic dark:text-gray-300 text-gray-600 line-clamp-3">
              {article.previewQuote}
            </p>
          </div>

          {/* Tags */}
          <div className="mt-5 flex gap-2">
            {article.tags.map(tag => (
              <span
                key={tag}
                className="text-[10px] uppercase tracking-wider px-2 py-1 rounded-sm border dark:border-white/10 border-black/10 dark:text-gray-400 text-gray-500"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
});

export default ArticleCard;
