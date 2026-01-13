import React from 'react';
import { Feather } from 'lucide-react';

/**
 * 加载状态组件
 * 用于懒加载组件的 fallback
 */
const LoadingSpinner: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-paper-50 dark:bg-mineral-900">
      <div className="text-center">
        <div className="animate-pulse mb-4">
          <Feather className="w-12 h-12 mx-auto text-gold-light dark:text-gold opacity-60" />
        </div>
        <div className="animate-spin w-8 h-8 border-2 border-gold border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-sm dark:text-gray-400 text-gray-500 font-serif">
          加载中...
        </p>
      </div>
    </div>
  );
};

export default LoadingSpinner;
