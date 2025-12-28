import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Article } from '../types';
import { ArrowLeft, ExternalLink, Sparkles, Feather, List } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ReaderProps {
  article: Article;
  onBack: () => void;
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

const Reader: React.FC<ReaderProps> = ({ article, onBack, onCopyFragment }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState<string>('');

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

  return (
    <div className="pt-24 pb-20 min-h-screen">
      
      {/* Container for Centered Content + Absolute Sidebar */}
      <div className="max-w-[720px] mx-auto px-6 relative animate-slide-up">
        
        {/* TOC Sidebar - Adaptive positioning */}
        {toc.length > 0 && (
          <aside className="hidden lg:block absolute lg:left-[-220px] xl:left-[-280px] top-0 lg:w-48 xl:w-64 h-full pointer-events-none">
            {/* Inner fixed container (sticky behavior) - Enable pointer events here */}
            <div className="sticky top-32 transition-opacity duration-500 opacity-0 animate-fade-in pointer-events-auto" style={{ animationDelay: '0.3s', animationFillMode: 'forwards' }}>
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
        <article ref={contentRef} className="prose prose-lg dark:prose-invert max-w-none font-sans scroll-smooth">
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

        {/* Ritualistic End Symbol */}
        <div className="mt-24 mb-12 flex justify-center opacity-50">
           <Feather className="w-6 h-6 dark:text-gold text-gold-light" />
        </div>

      </div>
    </div>
  );
};

export default Reader;