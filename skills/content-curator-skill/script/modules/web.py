"""
网页内容提取模块
使用 web-reader MCP 提取网页文章内容
"""

import re
from typing import Dict, Optional
from datetime import datetime


class WebExtractor:
    """网页文章提取器"""

    def __init__(self, logger=None):
        self.logger = logger

    def extract(self, url: str) -> Dict:
        """提取网页文章信息

        Args:
            url: 文章 URL

        Returns:
            Dict: 包含 title, author, cover_url, content, publish_date, source_url
        """
        try:
            # 使用 web-reader MCP（通过外部调用）
            # 这里返回结构化的数据，实际调用由上层完成
            # 此方法用于处理原始 web-reader 返回的数据

            raise NotImplementedError(
                "请使用 extract_from_reader() 方法处理 web-reader 返回的数据"
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"提取网页内容失败 {url}: {e}")
            return {}

    def extract_from_reader(self, reader_data: dict) -> Dict:
        """从 web-reader 返回的数据中提取信息

        Args:
            reader_data: web-reader 返回的数据

        Returns:
            Dict: 标准化的文章信息
        """
        try:
            # web-reader 返回的数据结构
            text_data = reader_data.get("text", {})

            # 提取基本信息
            title = text_data.get("title", "")
            content = text_data.get("content", "")
            source_url = text_data.get("url", "")

            # 提取元数据
            metadata = text_data.get("metadata", {})

            # 作者 - 从多个可能的字段中提取
            author = (
                metadata.get("author") or
                metadata.get("og:article:author") or
                metadata.get("twitter:creator") or
                metadata.get("og:site_name") or
                "Unknown"
            )

            # 封面图 - 优先级：og:image > twitter:image > 第一张图
            cover_url = (
                metadata.get("og:image") or
                metadata.get("twitter:image") or
                self._extract_first_image(content) or
                ""
            )

            # 发布日期 - 尝试多个字段
            publish_date = (
                metadata.get("article:published_time") or
                metadata.get("publishedTime") or
                self._extract_date_from_content(content) or
                datetime.now().strftime("%Y-%m-%d")
            )

            # 平台标识
            platform = self._detect_platform(source_url)

            result = {
                "title": title,
                "author": author,
                "cover_url": cover_url,
                "content": content,
                "publish_date": publish_date,
                "source_url": source_url,
                "platform": platform,
                "service": platform,
            }

            if self.logger:
                self.logger.info(f"成功提取文章: {title}")

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"解析 web-reader 数据失败: {e}")
            return {}

    def _detect_platform(self, url: str) -> str:
        """检测文章来源平台

        Args:
            url: 文章 URL

        Returns:
            str: 平台名称
        """
        url_lower = url.lower()

        # 微信公众号
        if "mp.weixin.qq.com" in url_lower:
            return "wechat"

        # 知乎
        if "zhihu.com" in url_lower:
            return "zhihu"

        # 掘金
        if "juejin.cn" in url_lower:
            return "juejin"

        # Medium
        if "medium.com" in url_lower:
            return "medium"

        # Substack
        if "substack.com" in url_lower:
            return "substack"

        # 个人博客（从 URL 提取域名）
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            return domain.split(".")[0]
        except:
            return "web"

    def _extract_first_image(self, content: str) -> Optional[str]:
        """从内容中提取第一张图片 URL

        Args:
            content: Markdown 内容

        Returns:
            Optional[str]: 图片 URL 或 None
        """
        # 匹配 Markdown 图片语法
        img_pattern = r'!\[.*?\]\((https?://[^\s)]+)\)'
        match = re.search(img_pattern, content)
        if match:
            return match.group(1)

        # 匹配 HTML img 标签
        html_pattern = r'<img[^>]+src=["\'](https?://[^"\']+)["\']'
        match = re.search(html_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_date_from_content(self, content: str) -> Optional[str]:
        """从内容中提取日期

        Args:
            content: 文章内容

        Returns:
            Optional[str]: 日期字符串 YYYY-MM-DD 或 None
        """
        # 常见日期格式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',           # 2025-12-26
            r'\d{4}/\d{2}/\d{2}',           # 2025/12/26
            r'\d{4}\.\d{2}\.\d{2}',         # 2025.12.26
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # Dec 26, 2025
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content[:500])  # 只在开头500字符查找
            if match:
                date_str = match.group(0)
                # 尝试标准化为 YYYY-MM-DD
                try:
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        return date_str
                    elif re.match(r'\d{4}/\d{2}/\d{2}', date_str):
                        return date_str.replace("/", "-")
                    elif re.match(r'\d{4}\.\d{2}\.\d{2}', date_str):
                        return date_str.replace(".", "-")
                except:
                    pass

        return None

    def is_article_url(self, url: str) -> bool:
        """判断 URL 是否为文章链接（非视频）

        Args:
            url: 待检测的 URL

        Returns:
            bool: 是否为文章链接
        """
        url_lower = url.lower()

        # 明确的视频平台
        video_platforms = [
            'youtube.com', 'youtu.be',
            'bilibili.com',
            'vimeo.com',
            'douyin.com', 'tiktok.com'
        ]

        for platform in video_platforms:
            if platform in url_lower:
                return False

        # 明确的文章平台
        article_platforms = [
            'mp.weixin.qq.com',  # 微信公众号
            'zhihu.com',         # 知乎
            'juejin.cn',         # 掘金
            'medium.com',        # Medium
            'substack.com',      # Substack
        ]

        for platform in article_platforms:
            if platform in url_lower:
                return True

        # 默认认为是文章（个人博客等）
        return True


__all__ = ['WebExtractor']
