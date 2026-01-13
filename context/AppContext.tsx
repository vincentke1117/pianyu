import React, { createContext, useContext, useState, useMemo, useCallback, ReactNode } from 'react';
import { ViewMode, ArticleType } from '../types';

/**
 * 应用全局状态
 */
interface AppState {
  // 视图状态
  view: ViewMode;
  currentArticleId: string | null;

  // 筛选状态
  galleryFilters: {
    selectedType: ArticleType | 'all';
    selectedAuthor: string | null;
  };

  // UI 状态
  isDark: boolean;
  isSearchOpen: boolean;
  showCopyFeedback: boolean;
}

/**
 * 应用操作方法
 */
interface AppActions {
  // 视图操作
  setView: (view: ViewMode) => void;
  setCurrentArticleId: (id: string | null) => void;
  navigateToArticle: (id: string) => void;
  navigateBack: () => void;

  // 筛选操作
  setGalleryFilters: (filters: AppState['galleryFilters']) => void;
  setSelectedType: (type: ArticleType | 'all') => void;
  setSelectedAuthor: (author: string | null) => void;

  // UI 操作
  toggleTheme: () => void;
  openSearch: () => void;
  closeSearch: () => void;
  showCopyFeedback: () => void;
  hideCopyFeedback: () => void;
}

/**
 * App Context 类型
 */
interface AppContextValue {
  state: AppState;
  actions: AppActions;
}

// 创建 Context
const AppContext = createContext<AppContextValue | null>(null);

/**
 * App Provider 组件
 */
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 视图状态
  const [view, setView] = useState<ViewMode>('gallery');
  const [currentArticleId, setCurrentArticleId] = useState<string | null>(null);

  // 筛选状态
  const [galleryFilters, setGalleryFilters] = useState<AppState['galleryFilters']>({
    selectedType: 'all',
    selectedAuthor: null,
  });

  // UI 状态
  const [isDark, setIsDark] = useState(true);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [showCopyFeedback, setShowCopyFeedback] = useState(false);

  // 导航到文章
  const navigateToArticle = useCallback((id: string) => {
    setCurrentArticleId(id);
    setView('reader');
  }, []);

  // 返回上一页
  const navigateBack = useCallback(() => {
    setView('gallery');
    setCurrentArticleId(null);
  }, []);

  // 设置筛选类型
  const setSelectedType = useCallback((type: ArticleType | 'all') => {
    setGalleryFilters(prev => ({ ...prev, selectedType: type }));
  }, []);

  // 设置筛选作者
  const setSelectedAuthor = useCallback((author: string | null) => {
    setGalleryFilters(prev => ({ ...prev, selectedAuthor: author }));
  }, []);

  // 切换主题
  const toggleTheme = useCallback(() => {
    setIsDark(prev => !prev);
  }, []);

  // 打开搜索
  const openSearch = useCallback(() => {
    setIsSearchOpen(true);
  }, []);

  // 关闭搜索
  const closeSearch = useCallback(() => {
    setIsSearchOpen(false);
  }, []);

  // 显示复制反馈
  const showCopyFeedbackFn = useCallback(() => {
    setShowCopyFeedback(true);
  }, []);

  // 隐藏复制反馈
  const hideCopyFeedbackFn = useCallback(() => {
    setShowCopyFeedback(false);
  }, []);

  // 组合状态
  const state = useMemo<AppState>(
    () => ({ view, currentArticleId, galleryFilters, isDark, isSearchOpen, showCopyFeedback }),
    [view, currentArticleId, galleryFilters, isDark, isSearchOpen, showCopyFeedback]
  );

  // 组合操作
  const actions = useMemo<AppActions>(
    () => ({
      setView,
      setCurrentArticleId,
      navigateToArticle,
      navigateBack,
      setGalleryFilters,
      setSelectedType,
      setSelectedAuthor,
      toggleTheme,
      openSearch,
      closeSearch,
      showCopyFeedback: showCopyFeedbackFn,
      hideCopyFeedback: hideCopyFeedbackFn,
    }),
    [
      navigateToArticle,
      navigateBack,
      setSelectedType,
      setSelectedAuthor,
      toggleTheme,
      openSearch,
      closeSearch,
      showCopyFeedbackFn,
      hideCopyFeedbackFn,
    ]
  );

  const contextValue = useMemo<AppContextValue>(
    () => ({ state, actions }),
    [state, actions]
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};

/**
 * 使用 App Context 的 Hook
 */
export const useApp = (): AppContextValue => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};
