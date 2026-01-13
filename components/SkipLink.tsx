import React from 'react';

/**
 * 跳转链接组件
 * 允许键盘用户跳过导航直接进入主要内容
 * 符合 WCAG 2.1 A 级标准
 */
const SkipLink: React.FC = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-6 focus:py-3 focus:bg-gold focus:text-white focus:rounded-sm focus:font-medium focus:shadow-lg transition-all"
    >
      跳转到主要内容
    </a>
  );
};

export default SkipLink;
