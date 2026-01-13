import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Article } from '../types';
import { ArrowLeft, ExternalLink, Sparkles, Feather, List, Minus, Plus, Type, ArrowLeft as ChevronLeft, ArrowRight as ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useScrollProgress } from '../hooks/useScrollProgress';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

interface ReaderProps {
  article: Article;
  allArticles: Article[];
  onBack: () => void;
  onArticleClick: (id: string) => void;
  onCopyFragment: (text: string) => void;
}

interface TocItem {
  id: string;
  text: string;
  level: number;
}

// Helper to extract plain text from React children (for markdown headings)
const extractText = (children: any): string => {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) return children.map(extractText).join('');
  if (typeof children === 'object' && children?.props?.children) return extractText(children.props.children);
  return '';
};

// Helper to generate IDs
const slugify = (text: string) => {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5\-]+/g, '') // Keep Chinese, letters, numbers, hyphens
    .replace(/\-\-+/g, '-');
};

const Reader: React.FC<ReaderProps> = ({ article, allArticles, onBack, onArticleClick, onCopyFragment }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState<string>('');
  const [fontSize, setFontSize] = useState(100); // 字体大小，默认 100%
  const [isMobileTOCOpen, setIsMobileTOCOpen] = useState(false); // 移动端 TOC 状态
  const progress = useScrollProgress(); // 阅读进度

  // 获取当前文章在列表中的索引
  const currentIndex = allArticles.findIndex(a => a.id === article.id);
  const prevArticle = currentIndex > 0 ? allArticles[currentIndex - 1] : null;
  const nextArticle = currentIndex < allArticles.length - 1 ? allArticles[currentIndex + 1] : null;

  // 动态更新文档标题
  useDocumentTitle(article.title, article.previewQuote);

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Copy detection logic
  useEffect(() => {
    const handleCopy = () => {
      const selection = window.getSelection();
      if (selection && selection.toString().length > 0) {
        onCopyFragment(selection.toString());
      }
    };

    const element = contentRef.current;
    if (element) {
      element.addEventListener('copy', handleCopy);
    }

    return () => {
      if (element) {
        element.removeEventListener('copy', handleCopy);
      }
    };
  }, [onCopyFragment]);

  // Extract headings for TOC
  const toc = useMemo(() => {
    const lines = article.content.split('\n');
    const items: TocItem[] = [];
    
    // Improved regex: allow optional leading whitespace before ###
    const regex = /^\s*(#{2,3})\s+(.*)$/;
    
    lines.forEach(line => {
      const match = line.match(regex);
      if (match) {
        const level = match[1].length;
        const text = match[2].replace(/\*\*/g, '').replace(/\*/g, '').trim(); // Remove bold/italic chars & trim
        if (text) {
          items.push({
            id: slugify(text),
            text: text,
            level: level
          });
        }
      }
    });
    return items;
  }, [article.content]);

  // Scroll Spy for Active TOC Item
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: '-20% 0px -35% 0px' }
    );

    toc.forEach((item) => {
      const element = document.getElementById(item.id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [toc]);

  // Custom heading renderer to inject IDs
  const HeadingRenderer = ({ level, children, ...props }: any) => {
    const text = extractText(children);
    const id = slugify(text);
    const Tag = `h${level}` as React.ElementType;
    
    // Style classes based on level
    let className = "font-serif dark:text-mineral-100 text-paper-900";
    if (level === 1) className += " mt-12 mb-6";
    if (level === 2) className += " mt-10 mb-5 border-b dark:border-white/10 border-black/10 pb-2";
    if (level === 3) className += " mt-8 mb-4 dark:text-gray-200 text-gray-800";

    return (
      <Tag id={id} className={className} {...props}>
        {children}
      </Tag>
    );
  };

  // 字体大小控制器
  const FontSizeController = () => {
    const decreaseFont = () => setFontSize(prev => Math.max(85, prev - 5));
    const increaseFont = () => setFontSize(prev => Math.min(130, prev + 5));

    return (
      <div className="mb-4 p-4 rounded-sm bg-paper-100 dark:bg-mineral-800 border dark:border-white/10 border-black/5">
        <div className="flex items-center gap-3 mb-3">
          <Type className="w-4 h-4 dark:text-gold text-gold-light opacity-80" />
          <span className="text-xs font-bold tracking-widest uppercase dark:text-gray-400 text-gray-500">
            文字大小
          </span>
          <span className="ml-auto text-xs dark:text-gray-400 text-gray-500">
            {fontSize}%
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={decreaseFont}
            className="w-8 h-8 flex items-center justify-center rounded-sm dark:bg-mineral-700 bg-paper-200 dark:text-gray-300 text-gray-600 hover:text-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            disabled={fontSize <= 85}
          >
            <Minus className="w-4 h-4" />
          </button>
          <input
            type="range"
            min="85"
            max="130"
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="flex-1 h-2 bg-paper-200 dark:bg-mineral-700 rounded-lg appearance-none cursor-pointer accent-gold"
          />
          <button
            onClick={increaseFont}
            className="w-8 h-8 flex items-center justify-center rounded-sm dark:bg-mineral-700 bg-paper-200 dark:text-gray-300 text-gray-600 hover:text-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            disabled={fontSize >= 130}
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="pt-24 pb-20 min-h-screen">
      {/* 阅读进度条 */}
      <div
        className="fixed top-16 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-800 z-50"
        role="progressbar"
        aria-valuenow={Math.round(progress)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="阅读进度"
      >
        <div
          className="h-full bg-gold transition-all duration-150 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 移动端 TOC 按钮 */}
      <button
        onClick={() => setIsMobileTOCOpen(true)}
        className="lg:hidden fixed bottom-6 right-6 z-40 p-4 rounded-full bg-gold text-white shadow-lg hover:opacity-90 transition-opacity"
        aria-label="打开目录"
      >
        <List className="w-6 h-6" />
      </button>

      {/* 移动端 TOC 抽屉 */}
      {isMobileTOCOpen && (
        <>
          {/* 背景遮罩 */}
          <div
            className="lg:hidden fixed inset-0 bg-black/50 z-50 animate-fade-in"
            onClick={() => setIsMobileTOCOpen(false)}
          />
          {/* 抽屉内容 */}
          <div className="lg:hidden fixed inset-y-0 right-0 w-80 max-w-full bg-paper-50 dark:bg-mineral-900 z-50 shadow-2xl animate-slide-up overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2 dark:text-gold text-gold-light">
                  <List className="w-5 h-5" />
                  <span className="font-serif text-sm font-bold tracking-widest uppercase">目录</span>
                </div>
                <button
                  onClick={() => setIsMobileTOCOpen(false)}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
                  aria-label="关闭目录"
                >
                  <Feather className="w-5 h-5 dark:text-gray-400 text-gray-500" />
                </button>
              </div>

              {/* 字体大小控制 */}
              <div className="mb-6">
                <FontSizeController />
              </div>

              {/* 目录列表 */}
              <nav className="border-l dark:border-white/10 border-black/5 pl-4">
                <ul className="space-y-3">
                  {toc.map((item) => (
                    <li key={item.id} className={`${item.level === 3 ? 'pl-4' : ''}`}>
                      <a
                        href={`#${item.id}`}
                        onClick={(e) => {
                          e.preventDefault();
                          document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth' });
                          setActiveId(item.id);
                          setIsMobileTOCOpen(false);
                        }}
                        className={`text-xs block transition-colors duration-300 leading-relaxed
                          ${activeId === item.id
                            ? 'dark:text-gold text-gold-light font-medium'
                            : 'dark:text-gray-500 text-gray-400 hover:dark:text-gray-300 hover:text-gray-600'
                          }`}
                      >
                        {item.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </div>
        </>
      )}

      {/* Container for Centered Content + Absolute Sidebar */}
      <div className="max-w-[720px] mx-auto px-6 relative animate-slide-up">
        
        {/* TOC Sidebar - Adaptive positioning */}
        {toc.length > 0 && (
          <aside className="hidden lg:block absolute lg:left-[-220px] xl:left-[-280px] top-0 lg:w-48 xl:w-64 h-full pointer-events-none">
            {/* Inner fixed container (sticky behavior) - Enable pointer events here */}
            <div className="sticky top-32 transition-opacity duration-500 opacity-0 animate-fade-in pointer-events-auto" style={{ animationDelay: '0.3s', animationFillMode: 'forwards' }}>
              <FontSizeController />
              <div className="flex items-center gap-2 mb-4 dark:text-gold text-gold-light opacity-80">
                <List className="w-4 h-4" />
                <span className="font-serif text-xs font-bold tracking-widest uppercase">目录</span>
              </div>
              <nav className="border-l dark:border-white/10 border-black/5 pl-4">
                <ul className="space-y-3">
                  {toc.map((item) => (
                    <li key={item.id} className={`${item.level === 3 ? 'pl-4' : ''}`}>
                      <a 
                        href={`#${item.id}`}
                        onClick={(e) => {
                          e.preventDefault();
                          document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth' });
                          setActiveId(item.id);
                        }}
                        className={`text-xs block transition-colors duration-300 leading-relaxed
                          ${activeId === item.id 
                            ? 'dark:text-gold text-gold-light font-medium' 
                            : 'dark:text-gray-500 text-gray-400 hover:dark:text-gray-300 hover:text-gray-600'
                          }`}
                      >
                        {item.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </aside>
        )}

        {/* Back Button */}
        <button 
          onClick={onBack}
          className="mb-8 flex items-center gap-2 text-sm dark:text-gray-400 text-gray-500 hover:text-gold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="font-serif">返回珍藏馆</span>
        </button>

        {/* Header */}
        <header className="mb-10 text-center">
          <h1 className="text-3xl md:text-4xl font-serif font-bold dark:text-mineral-100 text-paper-900 mb-6 leading-tight">
            {article.title}
          </h1>
          <div className="flex items-center justify-center gap-6 text-xs dark:text-gray-400 text-gray-500 font-sans tracking-wide">
            <span>{article.date}</span>
            <span>·</span>
            <span>
              {article.guest ? `嘉宾: ${article.guest}` :
               article.host ? `主播: ${article.host}` :
               article.author}
            </span>
            <span>·</span>
            <a href={article.sourceLink || '#'} className="flex items-center gap-1 hover:text-gold transition-colors">
              {article.type === 'video' ? '查看原视频' : article.type === 'podcast' ? '查看原播客' : '查看原文章'} <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </header>

        {/* Golden Nuggets Box */}
        <div className="mb-12 p-6 md:p-8 rounded-sm border dark:border-gold/30 border-gold-light/30 dark:bg-white/5 bg-black/5 relative overflow-hidden">
          <div className="flex items-center gap-2 mb-4 dark:text-gold text-gold-light">
             <Sparkles className="w-4 h-4" />
             <span className="text-xs font-bold tracking-widest uppercase">Golden Nuggets</span>
          </div>
          <ul className="space-y-4">
            {article.nuggets.map((nugget, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="shrink-0 w-1.5 h-1.5 rounded-full dark:bg-gold bg-gold-light mt-2" />
                <p className="font-serif italic dark:text-gray-200 text-gray-700 leading-relaxed">
                  {nugget}
                </p>
              </li>
            ))}
          </ul>
        </div>

        {/* Main Content */}
        <article ref={contentRef} className="prose prose-lg dark:prose-invert max-w-none font-sans scroll-smooth" style={{ fontSize: `${fontSize}%` }} aria-label="文章内容">
          <ReactMarkdown
            components={{
              // Styling overrides for Markdown
              h1: (props) => <HeadingRenderer level={1} {...props} />,
              h2: (props) => <HeadingRenderer level={2} {...props} />,
              h3: (props) => <HeadingRenderer level={3} {...props} />,
              p: ({node, ...props}) => <p className="leading-8 text-gray-600 dark:text-gray-300 mb-6 font-light" {...props} />,
              strong: ({node, ...props}) => (
                <strong className="font-bold dark:text-mineral-100 text-paper-900 border-b-2 dark:border-gold/50 border-gold-light/50 pb-0.5" {...props} />
              ),
              blockquote: ({node, ...props}) => (
                <blockquote className="border-l-4 dark:border-gold border-gold-light pl-4 py-1 my-8 italic font-serif dark:text-gray-400 text-gray-600 bg-transparent" {...props} />
              ),
              li: ({node, ...props}) => <li className="text-gray-600 dark:text-gray-300 my-1" {...props} />,
            }}
          >
            {article.content}
          </ReactMarkdown>
        </article>

        {/* 文章间导航 */}
        <div className="mt-16 mb-12 flex justify-between items-center gap-4 pt-8 border-t dark:border-white/10 border-black/5">
          {/* 上一篇 */}
          <button
            disabled={!prevArticle}
            onClick={() => prevArticle && onArticleClick(prevArticle.id)}
            className="flex items-center gap-3 px-4 py-3 rounded-sm bg-paper-100 dark:bg-mineral-800 hover:bg-gold/10 dark:hover:bg-gold/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 group flex-1 min-w-0"
          >
            <ChevronLeft className="w-5 h-5 flex-shrink-0 dark:text-gray-400 text-gray-500 group-hover:text-gold transition-colors" />
            <div className="text-left min-w-0 flex-1">
              <div className="text-xs dark:text-gray-500 text-gray-400 mb-1">上一篇</div>
              <div className="text-sm font-serif dark:text-mineral-100 text-paper-900 line-clamp-1">
                {prevArticle?.title || '无'}
              </div>
            </div>
          </button>

          {/* 返回列表按钮 */}
          <button
            onClick={onBack}
            className="p-3 rounded-full hover:bg-gray-100 dark:hover:bg-white/5 transition-colors flex-shrink-0"
            aria-label="返回列表"
          >
            <Feather className="w-5 h-5 dark:text-gold text-gold-light opacity-60" />
          </button>

          {/* 下一篇 */}
          <button
            disabled={!nextArticle}
            onClick={() => nextArticle && onArticleClick(nextArticle.id)}
            className="flex items-center gap-3 px-4 py-3 rounded-sm bg-paper-100 dark:bg-mineral-800 hover:bg-gold/10 dark:hover:bg-gold/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 group flex-1 min-w-0"
          >
            <div className="text-right min-w-0 flex-1">
              <div className="text-xs dark:text-gray-500 text-gray-400 mb-1">下一篇</div>
              <div className="text-sm font-serif dark:text-mineral-100 text-paper-900 line-clamp-1">
                {nextArticle?.title || '无'}
              </div>
            </div>
            <ChevronRight className="w-5 h-5 flex-shrink-0 dark:text-gray-400 text-gray-500 group-hover:text-gold transition-colors" />
          </button>
        </div>

        {/* Ritualistic End Symbol */}
        <div className="mb-12 flex justify-center opacity-50">
           <Feather className="w-6 h-6 dark:text-gold text-gold-light" />
        </div>

      </div>
    </div>
  );
};

export default Reader;