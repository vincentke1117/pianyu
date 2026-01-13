import { useState, useEffect } from 'react';

/**
 * 滚动进度 Hook
 * 监听页面滚动，返回当前阅读进度百分比 (0-100)
 */
export const useScrollProgress = (): number => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const scrollTop = window.scrollY;

      // 计算滚动百分比
      const scrollPercentage = (scrollTop / (documentHeight - windowHeight)) * 100;
      setProgress(Math.min(100, Math.max(0, scrollPercentage)));
    };

    // 使用 passive: true 提升滚动性能
    window.addEventListener('scroll', handleScroll, { passive: true });

    // 初始化时计算一次
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return progress;
};
