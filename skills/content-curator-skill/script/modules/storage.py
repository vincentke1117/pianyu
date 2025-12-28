"""
Storage Manager Module
管理视频内容的存储，支持四文件输出结构
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class StorageManager:
    """存储管理器 - 四文件输出结构"""

    def __init__(self, base_output_dir: str = None, logger=None):
        # 默认使用项目根目录下的 extracted_content
        if base_output_dir is None:
            # 获取项目根目录（从 modules/ -> script/ -> content-curator-skill/ -> skills/ -> content_extractor/）
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
            base_output_dir = os.path.join(project_root, "extracted_content")

        self.base_output_dir = base_output_dir
        self.logger = logger
        self.processed_log_path = os.path.join(base_output_dir, ".processed.json")

        # 确保基础目录存在
        os.makedirs(base_output_dir, exist_ok=True)

        # 加载已处理视频列表
        self.processed_videos = self._load_processed_log()

    def _load_processed_log(self) -> Dict:
        """加载已处理视频日志"""
        if os.path.exists(self.processed_log_path):
            try:
                with open(self.processed_log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_processed_log(self):
        """保存已处理视频日志"""
        try:
            with open(self.processed_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_videos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"无法保存处理日志: {e}")

    def is_processed(self, video_id: str) -> bool:
        """检查视频是否已处理"""
        return video_id in self.processed_videos

    def mark_processed(self, video_id: str, video_info: Optional[Dict] = None):
        """标记视频为已处理"""
        self.processed_videos[video_id] = {
            "processed_at": datetime.now().isoformat(),
            "info": video_info or {}
        }
        self._save_processed_log()

    def get_video_folder(self, video_title: str) -> str:
        """获取视频文件夹路径

        Args:
            video_title: 视频标题

        Returns:
            str: 文件夹路径
        """
        from modules.config import ConfigLoader

        folder_name = ConfigLoader.sanitize_folder_name(video_title)
        return os.path.join(self.base_output_dir, folder_name)

    def save_metadata(self, video_folder: str, video_info: Dict, processor_result: Dict) -> str:
        """保存 metadata.md

        包含: 中文标题、英文标题、嘉宾/作者
        """
        filepath = os.path.join(video_folder, "metadata.md")

        # 优先使用 processor_result 中的真实视频信息
        title = processor_result.get("title", video_info.get("title", ""))
        author = processor_result.get("author", processor_result.get("uploader", ""))
        platform = processor_result.get("service", video_info.get("platform", "unknown"))
        publish_date = processor_result.get("publish_date", processor_result.get("published_at", ""))
        duration = processor_result.get("duration", 0)
        video_id = processor_result.get("id", video_info.get("id", ""))
        description = processor_result.get("description", "")

        # 从 description 中提取嘉宾信息
        guest = self._extract_guest_info(description)

        # 自动确定分类
        category = self._determine_category(platform)

        content = f"""# 视频元数据

## 基本信息

| 字段 | 内容 |
|------|------|
| 视频ID | `{video_id}` |
| 平台 | {platform.upper()} |
| 分类 | {category} |
| 发布日期 | {publish_date} |
| 时长 | {self._format_duration(duration)} |

## 标题信息

| 字段 | 内容 |
|------|------|
| 标题 | {title} |

## 作者/嘉宾信息

| 字段 | 内容 |
|------|------|
| 作者/UP主 | {author} |
{"| 嘉宾 | {guest} |" if guest else ""}

## 视频简介

{description if description else '_暂无简介_'}

## 源链接

- 视频链接: {processor_result.get("source_url", video_info.get("url", ""))}
- 封面图: {processor_result.get("cover_url", processor_result.get("thumbnail", ""))}

---

*处理时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if self.logger:
            self.logger.info(f"已保存: {filepath}")
        return filepath

    def _determine_category(self, platform: str) -> str:
        """根据平台确定内容分类

        Args:
            platform: 平台名称

        Returns:
            str: 分类 (视频/播客/文章)
        """
        platform_lower = platform.lower()

        # 视频平台
        video_platforms = ['youtube', 'bilibili', 'vimeo', 'tiktok', 'douyin']
        if any(vp in platform_lower for vp in video_platforms):
            return '视频'

        # 播客平台
        podcast_platforms = ['spotify', 'apple_podcasts', 'podcast', 'google_podcasts', 'pocket_casts', 'xiaoyuzhoufm']
        if any(pp in platform_lower for pp in podcast_platforms):
            return '播客'

        # 文章平台
        article_platforms = ['wechat', 'zhihu', 'juejin', 'medium', 'substack', 'notion', 'web', 'bearblog']
        if any(ap in platform_lower for ap in article_platforms):
            return '文章'

        # 默认为文章类型
        return '文章'

    def save_article_metadata(self, article_folder: str, article_info: Dict) -> str:
        """保存文章 metadata.md

        Args:
            article_folder: 文章文件夹路径
            article_info: 文章信息字典

        Returns:
            str: metadata.md 文件路径
        """
        filepath = os.path.join(article_folder, "metadata.md")

        # 提取文章信息
        title = article_info.get("title", "")
        author = article_info.get("author", "")
        platform = article_info.get("platform", "web")
        publish_date = article_info.get("publish_date", "")
        source_url = article_info.get("source_url", "")
        cover_url = article_info.get("cover_url", "")

        # 自动确定分类
        category = self._determine_category(platform)

        content = f"""# 文章元数据

## 基本信息

| 字段 | 内容 |
|------|------|
| 平台 | {platform.upper()} |
| 分类 | {category} |
| 发布日期 | {publish_date} |

## 标题信息

| 字段 | 内容 |
|------|------|
| 标题 | {title} |

## 作者信息

| 字段 | 内容 |
|------|------|
| 作者 | {author} |

## 源链接

- 文章链接: {source_url}
- 封面图: {cover_url}

---

*处理时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if self.logger:
            self.logger.info(f"已保存: {filepath}")
        return filepath

    def _extract_guest_info(self, description: str) -> str:
        """从视频简介中提取嘉宾信息"""
        if not description:
            return ""

        import re

        # 非人名黑名单 - 常见的概念、主题、组织等
        non_name_blacklist = [
            'AI', 'High Agency', 'Deep Learning', 'Machine Learning', 'Artificial Intelligence',
            'The Future', 'This Episode', 'Today\'s Episode', 'Today', 'The Company',
            'The Team', 'The Industry', 'The Market', 'The Economy', 'The World',
            'The Government', 'The Policy', 'The Strategy', 'The Approach',
            'A Mesopotamian', 'The biblical', 'The ancient', 'Modern', 'Traditional',
            'Digital', 'Physical', 'Mental', 'Emotional', 'Social', 'Political',
        ]

        # 尝试多种模式匹配
        guest_patterns = [
            # 英文格式 - 常见格式
            r'Guest[:：]\s+([A-Z][a-zA-Z\s]+?)(?:\n|,|\.|In this)',
            r'featuring\s+([A-Z][a-zA-Z\s]+?)(?:\n|,|\.|In this)',
            r'ft\.\s+([A-Z][a-zA-Z\s]+?)(?:\n|,|\.|In this)',
            r'with\s+([A-Z][a-zA-Z\s]+?)(?:\n|,|\.|In this)',
            # 名字开头 + "is the/a/an" 格式 (常见于访谈类节目)
            # 更严格的模式：2-4个单词，每个首字母大写，后面小写
            r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\s+is\s+(?:the|a|an)',
            # 中文格式
            r'嘉宾[:：]\s+([^\n\r，。]+?)(?:\n|,|。|本期)',
            r'本期嘉宾[:：]\s+([^\n\r，。]+?)(?:\n|,|。)',
        ]

        for pattern in guest_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                guest = match.group(1).strip()
                # 清理可能的额外字符和标点
                guest = re.sub(r'^\s+|\s+$|[,，。.]*$', '', guest)

                # 检查是否在黑名单中
                if guest in non_name_blacklist:
                    continue

                # 验证人名格式：2-4个单词，每个单词首字母大写
                words = guest.split()
                if 2 <= len(words) <= 4:
                    # 检查每个单词是否首字母大写，其余小写（允许如McDonald等）
                    all_proper = all(
                        (word[0].isupper() and word[1:].islower()) or
                        (len(word) <= 4 and word.isupper())  # 允许如 "AI" 但已在黑名单中过滤
                        for word in words if len(word) > 1
                    )
                    if all_proper and len(guest) < 100:
                        return guest

                # 对于明确标记的 Guest/featuring 格式，放宽限制
                if 'Guest:' in description or 'featuring' in description or 'ft.' in description:
                    if guest and len(guest) > 1 and len(guest) < 100:
                        return guest

        return ""

    def save_transcript(self, video_folder: str, transcript: str, video_info: Dict) -> str:
        """保存 transcript.md (带时间戳的转录)"""
        filepath = os.path.join(video_folder, "transcript.md")

        title = video_info.get("title", "未知标题")
        platform = video_info.get("platform", "").upper()

        content = f"""# {title}

*平台: {platform}*

---

## 原始字幕

{transcript}

---

*转录生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if self.logger:
            self.logger.info(f"已保存: {filepath}")
        return filepath

    def save_rewritten(self, video_folder: str, rewritten_content: str, video_info: Dict) -> str:
        """保存 rewritten.md (3-5条金句 + 2000字深度摘要)"""
        filepath = os.path.join(video_folder, "rewritten.md")

        title = video_info.get("title", "未知标题")

        content = f"""# {title} - 深度摘要

---

{rewritten_content}

---

*摘要生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if self.logger:
            self.logger.info(f"已保存: {filepath}")
        return filepath

    def save_all(
        self,
        video_info: Dict,
        processor_result: Dict,
        transcript: str,
        rewritten_content: str
    ) -> Dict[str, str]:
        """保存所有文件

        Args:
            video_info: 视频配置信息
            processor_result: 处理器返回的视频元数据
            transcript: 字幕内容
            rewritten_content: 改写后的内容

        Returns:
            Dict[str, str]: 各文件路径
        """
        # 优先使用 processor_result 中的真实标题创建文件夹
        title = processor_result.get("title", video_info.get("title", "未知"))
        video_folder = self.get_video_folder(title)

        try:
            os.makedirs(video_folder, exist_ok=True)
            if self.logger:
                self.logger.info(f"创建输出文件夹: {video_folder}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"创建文件夹失败: {e}")
            raise

        # 保存三个文件（封面 URL 已在 metadata.md 中）
        result = {}

        # 独立保存每个文件，确保一个失败不影响其他
        try:
            result["metadata"] = self.save_metadata(video_folder, video_info, processor_result)
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存 metadata.md 失败: {e}")

        try:
            result["transcript"] = self.save_transcript(video_folder, transcript, video_info)
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存 transcript.md 失败: {e}")

        try:
            result["rewritten"] = self.save_rewritten(video_folder, rewritten_content, video_info)
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存 rewritten.md 失败: {e}")

        return result

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if not seconds:
            return "未知"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"

    def get_processed_stats(self) -> Dict:
        """获取处理统计信息"""
        total = len(self.processed_videos)
        by_platform = {}

        for video_id, info in self.processed_videos.items():
            platform = info['info'].get('platform', 'unknown')
            by_platform[platform] = by_platform.get(platform, 0) + 1

        return {
            'total': total,
            'by_platform': by_platform,
        }

    def clear_processed_log(self, backup=True):
        """清空已处理视频日志"""
        if backup and os.path.exists(self.processed_log_path):
            backup_path = f"{self.processed_log_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.processed_log_path, backup_path)
            if self.logger:
                self.logger.info(f"已备份到: {backup_path}")

        self.processed_videos = {}
        self._save_processed_log()
        if self.logger:
            self.logger.info("已处理视频日志已清空")


__all__ = ['StorageManager']
