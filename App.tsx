import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Gallery from './components/Gallery';
import Reader from './components/Reader';
import CopyFeedback from './components/CopyFeedback';
import SearchDrawer from './components/SearchDrawer';
import { ARTICLES } from './constants';
import { useArticles } from './hooks/useArticles';
import { ViewMode } from './types';

const App: React.FC = () => {
  const [isDark, setIsDark] = useState(true);
  const [view, setView] = useState<ViewMode>('gallery');
  const [currentArticleId, setCurrentArticleId] = useState<string | null>(null);
  const [showCopyFeedback, setShowCopyFeedback] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // 动态加载文章数据（优先使用本地JSON）
  const { articles, loading, error } = useArticles();
  // 如果动态加载失败，使用静态常量作为降级
  const displayArticles = articles.length > 0 ? articles : ARTICLES;

  // Theme Handling
  useEffect(() => {
    const html = document.documentElement;
    if (isDark) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  // Navigation Logic
  const handleArticleClick = (id: string) => {
    setCurrentArticleId(id);
    setView('reader');
  };

  const handleHomeClick = () => {
    setView('gallery');
    setCurrentArticleId(null);
  };

  // Copy Feedback Logic
  const handleCopyFragment = () => {
    setShowCopyFeedback(true);
  };

  // Search Logic
  const handleSearchOpen = () => setIsSearchOpen(true);
  const handleSearchClose = () => setIsSearchOpen(false);

  const currentArticle = displayArticles.find(a => a.id === currentArticleId);

  // 加载状态显示
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper-50 dark:bg-mineral-900">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-gold border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm dark:text-gray-400 text-gray-500 font-serif">
            从飞书加载珍藏...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative font-sans">
      <Navbar
        isDark={isDark}
        toggleTheme={toggleTheme}
        onHomeClick={handleHomeClick}
        onSearchClick={handleSearchOpen}
      />

      <main>
        {view === 'gallery' && (
          <Gallery
            articles={displayArticles}
            onArticleClick={handleArticleClick}
          />
        )}

        {view === 'reader' && currentArticle && (
          <Reader 
            article={currentArticle} 
            onBack={handleHomeClick}
            onCopyFragment={handleCopyFragment}
          />
        )}
      </main>

      <CopyFeedback
        isVisible={showCopyFeedback}
        onHide={() => setShowCopyFeedback(false)}
      />

      <SearchDrawer
        isOpen={isSearchOpen}
        onClose={handleSearchClose}
        articles={displayArticles}
        onArticleClick={handleArticleClick}
      />
    </div>
  );
};

export default App;