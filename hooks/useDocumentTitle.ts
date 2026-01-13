import { useEffect } from 'react';

const DEFAULT_TITLE = '片羽 Pian Yu - 繁芜世界，仅取片羽';
const DEFAULT_DESCRIPTION = '在信息过载的洪流中，建立高信噪比的个人珍藏。拾取那些在暗夜中闪光的智慧碎片。';

/**
 * 动态更新文档标题和 meta 描述
 *
 * @param title - 页面标题（可选）
 * @param description - 页面描述（可选）
 *
 * @example
 * useDocumentTitle('文章标题');
 * // document.title = '文章标题 - 片羽 Pian Yu'
 *
 * @example
 * useDocumentTitle('文章标题', '文章描述...');
 * // document.title = '文章标题 - 片羽 Pian Yu'
 * // meta description = '文章描述...'
 */
export const useDocumentTitle = (title?: string, description?: string) => {
  useEffect(() => {
    // 更新标题
    if (title) {
      document.title = `${title} - 片羽 Pian Yu`;
    } else {
      document.title = DEFAULT_TITLE;
    }

    // 更新描述
    if (description) {
      const metaDescription = document.querySelector('meta[name="description"]');
      if (metaDescription) {
        metaDescription.setAttribute('content', description);
      }
    }

    // 清理函数：组件卸载时恢复默认值
    return () => {
      document.title = DEFAULT_TITLE;
      const metaDescription = document.querySelector('meta[name="description"]');
      if (metaDescription) {
        metaDescription.setAttribute('content', DEFAULT_DESCRIPTION);
      }
    };
  }, [title, description]);
};

/**
 * 重置文档标题和描述为默认值
 */
export const useResetDocumentTitle = () => {
  useEffect(() => {
    document.title = DEFAULT_TITLE;
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', DEFAULT_DESCRIPTION);
    }
  }, []);
};
