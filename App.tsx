import React, { useEffect, lazy, Suspense } from 'react';
import Navbar from './components/Navbar';
import Gallery from './components/Gallery';
import CopyFeedback from './components/CopyFeedback';
import LoadingSpinner from './components/LoadingSpinner';
import GallerySkeleton from './components/GallerySkeleton';
import SkipLink from './components/SkipLink';
import { AppProvider, useApp } from './context/AppContext';
import { ARTICLES } from './constants';
import { useArticles } from './hooks/useArticles';

// 代码分割：懒加载大型组件
const Reader = lazy(() => import('./components/Reader'));
const SearchDrawer = lazy(() => import('./components/SearchDrawer'));

/**
 * App 内部组件（使用 Context）
 */
const AppContent: React.FC = () => {
  const { state, actions } = useApp();
  const { articles, loading } = useArticles();

  // 如果动态加载失败，使用静态常量作为降级
  const displayArticles = articles.length > 0 ? articles : ARTICLES;

  // 主题处理
  useEffect(() => {
    const html = document.documentElement;
    if (state.isDark) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }, [state.isDark]);

  // 获取当前文章
  const currentArticle = displayArticles.find(a => a.id === state.currentArticleId);

  // 加载状态显示
  if (loading) {
    return <GallerySkeleton />;
  }

  return (
    <div className="min-h-screen relative font-sans">
      {/* Skip Link for accessibility */}
      <SkipLink />

      <Navbar
        isDark={state.isDark}
        toggleTheme={actions.toggleTheme}
        onHomeClick={actions.navigateBack}
        onSearchClick={actions.openSearch}
      />

      <main id="main-content">
        <div className={state.view === 'gallery' ? 'animate-fade-in' : 'hidden'}>
          <Gallery
            articles={displayArticles}
            onArticleClick={actions.navigateToArticle}
            selectedType={state.galleryFilters.selectedType}
            selectedAuthor={state.galleryFilters.selectedAuthor}
            onTypeChange={actions.setSelectedType}
            onAuthorChange={actions.setSelectedAuthor}
          />
        </div>

        {state.view === 'reader' && currentArticle && (
          <div className="animate-slide-up">
            <Suspense fallback={<LoadingSpinner />}>
              <Reader
                article={currentArticle}
                allArticles={displayArticles}
                onBack={actions.navigateBack}
                onArticleClick={actions.navigateToArticle}
                onCopyFragment={actions.showCopyFeedback}
              />
            </Suspense>
          </div>
        )}
      </main>

      <CopyFeedback
        isVisible={state.showCopyFeedback}
        onHide={actions.hideCopyFeedback}
      />

      <Suspense fallback={null}>
        <SearchDrawer
          isOpen={state.isSearchOpen}
          onClose={actions.closeSearch}
          articles={displayArticles}
          onArticleClick={actions.navigateToArticle}
        />
      </Suspense>
    </div>
  );
};

/**
 * App 根组件（提供 Context）
 */
const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;