import React, { useEffect, useState } from 'react';
import { Feather } from 'lucide-react';

interface CopyFeedbackProps {
  isVisible: boolean;
  onHide: () => void;
}

const CopyFeedback: React.FC<CopyFeedbackProps> = ({ isVisible, onHide }) => {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(onHide, 2000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onHide]);

  if (!isVisible) return null;

  return (
    <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 animate-fade-in pointer-events-none">
      <div className="bg-paper-900/90 dark:bg-mineral-100/90 backdrop-blur-sm px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 border dark:border-transparent border-white/10">
        <div className="p-1 bg-gold rounded-full">
          <Feather className="w-3 h-3 text-white" />
        </div>
        <span className="text-sm font-serif text-paper-50 dark:text-mineral-900 font-medium">
          已拾取一枚碎片
        </span>
      </div>
    </div>
  );
};

export default CopyFeedback;