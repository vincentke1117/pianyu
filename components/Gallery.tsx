import React, { useState, useMemo } from 'react';
import { Article, ArticleType } from '../types';
import { Calendar, User } from 'lucide-react';
import Banner from './Banner';

interface GalleryProps {
  articles: Article[];
  onArticleClick: (id: string) => void;
}

const CATEGORY_CONFIG = {
  video: { label: '视频', icon: '🎬' },
  podcast: { label: '播客', icon: '🎙️' },
  article: { label: '文章', icon: '📝' },
} as const;

const Gallery: React.FC<GalleryProps> = ({ articles, onArticleClick }) => {
  const [selectedType, setSelectedType] = useState<ArticleType | 'all'>('all');

  // 过滤文章
  const filteredArticles = useMemo(() => {
    if (selectedType === 'all') {
      return articles;
    }
    return articles.filter(article => article.type === selectedType);
  }, [articles, selectedType]);

  // 计算每个分类的数量
  const counts = useMemo(() => {
    return {
      all: articles.length,
      video: articles.filter(a => a.type === 'video').length,
      podcast: articles.filter(a => a.type === 'podcast').length,
      article: articles.filter(a => a.type === 'article').length,
    };
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
                onClick={() => setSelectedType(type)}
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

        {/* Section Title */}
        <div className="mb-8 flex items-end justify-between border-b dark:border-white/5 border-black/5 pb-2">
           <h2 className="text-sm font-serif font-bold dark:text-gray-400 text-gray-500 uppercase tracking-widest">
             {selectedType === 'all' ? 'Latest Collections' : CATEGORY_CONFIG[selectedType].label}
           </h2>
           <span className="text-xs dark:text-gray-500 text-gray-400">
             {filteredArticles.length} 篇内容
           </span>
        </div>

        <div className="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
          {filteredArticles.map((article) => (
            <div 
              key={article.id}
              onClick={() => onArticleClick(article.id)}
              className="break-inside-avoid group cursor-pointer animate-fade-in"
            >
              {/* Card Container */}
              <div className="relative overflow-hidden rounded-sm bg-paper-100 dark:bg-mineral-800 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
                
                {/* Image Container */}
                <div className="relative aspect-video overflow-hidden">
                  <img 
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
                      <span key={tag} className="text-[10px] uppercase tracking-wider px-2 py-1 rounded-sm border dark:border-white/10 border-black/10 dark:text-gray-400 text-gray-500">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Gallery;