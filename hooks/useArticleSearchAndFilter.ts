import { useState, useMemo, useCallback } from 'react';
import { Article, ArticleType } from '../types';
import { useDebouncedValue } from './useDebouncedValue';

export interface SearchFilters {
  query: string;
  selectedTag: string | null;
  selectedType: ArticleType | 'all';
  selectedAuthor: string | null;
}

export interface UseArticleSearchAndFilterReturn {
  // 状态
  filters: SearchFilters;
  // 更新函数
  setQuery: (query: string) => void;
  setTag: (tag: string | null) => void;
  setType: (type: ArticleType | 'all') => void;
  setAuthor: (author: string | null) => void;
  resetFilters: () => void;
  // 结果
  filteredArticles: Article[];
  // 可用选项
  availableTags: string[];
  availableAuthors: string[];
  // 统计
  resultCount: number;
}

/**
 * 文章搜索和筛选 Hook
 * 支持按关键词、标签、类型、作者进行筛选
 */
export const useArticleSearchAndFilter = (articles: Article[]): UseArticleSearchAndFilterReturn => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    selectedTag: null,
    selectedType: 'all',
    selectedAuthor: null,
  });

  // 对搜索关键词添加 300ms 防抖，减少不必要的计算
  const debouncedQuery = useDebouncedValue(filters.query, 300);

  // 更新函数
  const setQuery = useCallback((query: string) => {
    setFilters(prev => ({ ...prev, query }));
  }, []);

  const setTag = useCallback((selectedTag: string | null) => {
    setFilters(prev => ({ ...prev, selectedTag }));
  }, []);

  const setType = useCallback((selectedType: ArticleType | 'all') => {
    setFilters(prev => ({ ...prev, selectedType }));
  }, []);

  const setAuthor = useCallback((selectedAuthor: string | null) => {
    setFilters(prev => ({ ...prev, selectedAuthor }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      query: '',
      selectedTag: null,
      selectedType: 'all',
      selectedAuthor: null,
    });
  }, []);

  // 获取所有可用标签（去重并排序）
  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    articles.forEach(article => {
      article.tags.forEach(tag => {
        if (tag) tags.add(tag);
      });
    });
    return Array.from(tags).sort();
  }, [articles]);

  // 获取所有可用作者（去重并排序）
  const availableAuthors = useMemo(() => {
    const authors = new Set<string>();
    articles.forEach(article => {
      if (article.author) authors.add(article.author);
    });
    return Array.from(authors).sort();
  }, [articles]);

  // 筛选文章
  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      // 1. 关键词搜索（使用防抖后的值）
      if (debouncedQuery) {
        const query = debouncedQuery.toLowerCase();
        const matchesTitle = article.title?.toLowerCase().includes(query) ?? false;
        const matchesAuthor = article.author?.toLowerCase().includes(query) ?? false;
        const matchesContent = article.content?.toLowerCase().includes(query) ?? false;
        const matchesNuggets = article.nuggets?.some(n => n?.toLowerCase().includes(query)) ?? false;

        if (!matchesTitle && !matchesAuthor && !matchesContent && !matchesNuggets) {
          return false;
        }
      }

      // 2. 标签筛选
      if (filters.selectedTag) {
        if (!article.tags.some(t => t.toLowerCase() === filters.selectedTag?.toLowerCase())) {
          return false;
        }
      }

      // 3. 类型筛选
      if (filters.selectedType !== 'all') {
        if (article.type !== filters.selectedType) {
          return false;
        }
      }

      // 4. 作者筛选
      if (filters.selectedAuthor) {
        if (article.author !== filters.selectedAuthor) {
          return false;
        }
      }

      return true;
    });
  }, [articles, debouncedQuery, filters.selectedTag, filters.selectedType, filters.selectedAuthor]);

  const resultCount = filteredArticles.length;

  return {
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
  };
};
