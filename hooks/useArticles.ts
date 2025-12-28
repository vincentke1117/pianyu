import { useState, useEffect } from 'react';
import { Article } from '../types';
import { ARTICLES } from '../constants';

/**
 * 文章数据加载Hook
 * 静态网站环境：从本地 public/data/articles.json 加载
 * 降级：使用 constants.ts 的静态数据
 */
export const useArticles = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadArticles = async () => {
      setLoading(true);
      setError(null);

      try {
        // 从本地JSON加载（Vercel静态托管）
        const response = await fetch('/data/articles.json');
        if (response.ok) {
          const data: Article[] = await response.json();
          setArticles(data);
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (err) {
        console.warn('Failed to load JSON, using fallback data:', err);
        // 降级到静态数据
        setArticles(ARTICLES);
        setError(null); // 静默降级
      } finally {
        setLoading(false);
      }
    };

    loadArticles();
  }, []);

  return { articles, loading, error };
};

/**
 * 搜索文章Hook
 */
export const useArticleSearch = (articles: Article[]) => {
  const [query, setQuery] = useState('');

  const results = articles.filter(article =>
    article.title.toLowerCase().includes(query.toLowerCase()) ||
    article.author.toLowerCase().includes(query.toLowerCase()) ||
    article.content.toLowerCase().includes(query.toLowerCase()) ||
    article.nuggets.some(n => n.toLowerCase().includes(query.toLowerCase()))
  );

  return { query, setQuery, results };
};

/**
 * 按标签筛选Hook
 */
export const useArticleFilter = (articles: Article[]) => {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const filteredArticles = selectedTag
    ? articles.filter(article =>
        article.tags.some(t => t.toLowerCase() === selectedTag.toLowerCase())
      )
    : articles;

  // 获取所有唯一标签
  const allTags = Array.from(
    new Set(articles.flatMap(a => a.tags))
  ).sort();

  return { selectedTag, setSelectedTag, filteredArticles, allTags };
};
