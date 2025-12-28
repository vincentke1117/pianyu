export type ArticleType = 'video' | 'podcast' | 'article';

export interface Article {
  id: string;
  title: string;
  author: string; // 保留用于兼容性，播客为 "嘉宾: xxx" 或 "主播: xxx"
  host?: string; // 主播/主持人
  guest?: string; // 嘉宾
  date: string;
  coverUrl: string;
  tags: string[];
  type: ArticleType; // 文章类型
  previewQuote: string; // Golden quote for the card
  nuggets: string[]; // Deep wisdom fragments for the top of the article
  content: string; // Markdown content
  sourceLink?: string;
}

export type ViewMode = 'gallery' | 'reader';