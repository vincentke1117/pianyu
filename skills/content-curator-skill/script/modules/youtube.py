"""
YouTube Processor Module
处理YouTube视频获取、字幕提取等功能
基于 yt-dlp 实现，无需 API Key

使用示例：
    processor = YouTubeProcessor(logger)
    result = processor.get_transcript(video_info, output_format="text", include_metadata=True)
"""

import os
from typing import Dict, Optional, List


class YouTubeProcessor:
    """YouTube视频处理器 - 使用 yt-dlp"""

    def __init__(self, logger):
        self.logger = logger
        self._init_ytdlp()

    def _init_ytdlp(self):
        """初始化 yt-dlp"""
        try:
            import yt_dlp
            self.yt_dlp = yt_dlp
            self.logger.info("✅ yt-dlp 初始化成功")
        except ImportError as e:
            self.logger.error(f"yt-dlp 未安装: {e}")
            raise

        # 配置选项
        self.cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
        self.proxy_url = os.environ.get("YOUTUBE_PROXY_URL")

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """获取视频元数据

        Args:
            video_id: YouTube 视频ID

        Returns:
            Dict: 视频元数据字典
        """
        # yt-dlp 配置
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }

        # 添加 cookies
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
            self.logger.info(f"使用 cookies 文件: {self.cookies_path}")

        # 添加代理
        if self.proxy_url:
            ydl_opts['proxy'] = self.proxy_url
            self.logger.info(f"使用代理: {self.proxy_url}")

        try:
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"获取视频信息: {video_id}")
                info = ydl.extract_info(video_id, download=False)

                # 提取并返回视频信息
                return {
                    "id": video_id,
                    "title": info.get('title', ''),
                    "author": info.get('uploader', ''),
                    "author_id": info.get('channel_id', ''),
                    "cover_url": info.get('thumbnail', ''),
                    "duration": info.get('duration', 0),
                    "publish_date": info.get('upload_date', ''),
                    "source_url": f"https://www.youtube.com/watch?v={video_id}",
                    "service": "youtube",
                    "description": info.get('description', ''),
                    "tags": info.get('tags', []),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "raw_info": info  # 原始信息
                }

        except Exception as e:
            self.logger.error(f"❌ 获取视频信息失败: {e}")
            return None

    def get_transcript(
        self,
        video: Dict,
        output_format: str = "text",
        preserve_formatting: Optional[bool] = None,
        include_metadata: bool = True,
        include_timestamps: bool = False,
    ) -> Optional[Dict]:
        """获取视频字幕

        Args:
            video: 视频信息字典
            output_format: 输出格式: "text", "json", "srt"
            preserve_formatting: 保留格式（备用方案使用）
            include_metadata: 是否包含元数据
            include_timestamps: 是否在文本格式中包含时间戳

        Returns:
            Dict: 包含字幕和元数据的字典
        """
        video_id = video['id']

        # 获取视频信息（包含元数据和字幕）
        video_info = self.get_video_info(video_id)

        if not video_info:
            return None

        # 提取字幕（使用备用方案）
        subtitles_text = self._extract_subtitles(video_id, output_format, preserve_formatting, include_timestamps)

        # 返回结果
        if include_metadata:
            # 只返回需要的字段
            metadata = {k: v for k, v in video_info.items() if k != 'raw_info'}
            metadata["subtitles"] = subtitles_text or ""
            return metadata
        else:
            # 仅返回字幕（向后兼容）
            return subtitles_text

    def _extract_subtitles(self, video_id: str, output_format: str, preserve_formatting: Optional[bool], include_timestamps: bool) -> Optional[str]:
        """提取字幕（使用 youtube-transcript-api 作为备用方案）"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api.formatters import (
                TextFormatter,
                JSONFormatter,
                SRTFormatter,
            )

            self.logger.info(f"正在获取字幕: {video_id}")

            # 配置选项
            list_kwargs = {}
            if self.cookies_path and os.path.exists(self.cookies_path):
                list_kwargs["cookies"] = self.cookies_path
            if self.proxy_url:
                list_kwargs["proxies"] = {"https": self.proxy_url}

            # 获取字幕列表
            transcript_list = YouTubeTranscriptApi().list(video_id, **list_kwargs)

            # 优先尝试中文
            transcript = None
            for lang in ['zh-CN', 'zh-TW', 'zh', 'en']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    self.logger.info(f"✅ 找到字幕: {lang}")
                    break
                except:
                    continue

            if not transcript:
                self.logger.warning("未找到任何字幕")
                return None

            # 获取字幕数据
            transcript_data = transcript.fetch()

            # 格式化输出
            if output_format == "json":
                formatter = JSONFormatter()
                return formatter.format_transcript(transcript_data, indent=2)
            elif output_format == "srt":
                formatter = SRTFormatter()
                return formatter.format_transcript(transcript_data)
            else:  # text
                if include_timestamps:
                    # 手动添加时间戳 (FetchedTranscriptSnippet 对象有 .text 和 .start 属性)
                    lines = []
                    for item in transcript_data:
                        start_time = item.start  # 直接访问属性
                        minutes = int(start_time // 60)
                        seconds = int(start_time % 60)
                        timestamp = f"[{minutes:02d}:{seconds:02d}]"
                        text = item.text.strip()  # 直接访问属性
                        lines.append(f"{timestamp} {text}")
                    return '\n'.join(lines)
                else:
                    formatter = TextFormatter()
                    return formatter.format_transcript(transcript_data)

        except Exception as e:
            self.logger.error(f"❌ 获取字幕失败: {e}")
            return None

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """从 URL 中提取视频ID

        Args:
            url: YouTube URL

        Returns:
            str: 视频ID
        """
        import re

        patterns = [
            r'(?:v=|/v/|/embed/|/watch\?v=|/youtu.be/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None


if __name__ == "__main__":
    # 测试代码
    import logging
    import sys
    import os

    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 创建处理器
    processor = YouTubeProcessor(logger)

    # 测试视频
    test_urls = [
        "https://www.youtube.com/watch?v=0XI_Xt0ci2Y",  # 测试视频
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",   # 你的示例
    ]

    for url in test_urls:
        video_id = processor.extract_video_id(url)
        if video_id:
            print(f"\n{'='*80}")
            print(f"测试视频: {url}")
            print(f"视频ID: {video_id}")
            print('='*80)

            # 获取完整信息
            result = processor.get_transcript(
                {'id': video_id},
                output_format='text',
                include_metadata=True
            )

            if result:
                print(f"\n✅ 成功获取视频信息")
                print(f"标题: {result.get('title')}")
                print(f"作者: {result.get('author')}")
                print(f"时长: {result.get('duration')}秒")
                print(f"字幕长度: {len(result.get('subtitles', ''))}字符")
            else:
                print(f"\n❌ 获取失败")
