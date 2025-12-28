"""
Configuration Loader Module
从 video.yaml 加载视频配置
"""

import os
import yaml
from typing import Dict, List, Optional


class ConfigLoader:
    """配置加载器 - 从 video.yaml 读取视频列表"""

    def __init__(self, config_path: str = "video.yaml", logger=None):
        self.config_path = config_path
        self.logger = logger
        self._config = None

    def load(self) -> List[Dict]:
        """加载视频配置

        Returns:
            List[Dict]: 视频列表
        """
        if not os.path.exists(self.config_path):
            error_msg = f"未找到配置文件: {self.config_path}"
            if self.logger:
                self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            # 验证配置结构
            if not self._config or 'videos' not in self._config:
                error_msg = "配置文件无效: 缺少 'videos' 字段"
                if self.logger:
                    self.logger.error(error_msg)
                raise ValueError(error_msg)

            videos = self._config['videos']

            if self.logger:
                self.logger.info(f"成功加载 {len(videos)} 个视频配置")

            return videos

        except yaml.YAMLError as e:
            error_msg = f"配置文件格式错误: {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"加载配置失败: {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise

    def get_videos_by_platform(self, platform: str) -> List[Dict]:
        """获取指定平台的视频列表

        Args:
            platform: 平台名称 (youtube/bilibili)

        Returns:
            List[Dict]: 视频列表
        """
        if self._config is None:
            self.load()

        videos = [v for v in self._config['videos'] if v.get('platform') == platform]

        if self.logger:
            self.logger.info(f"{platform} 平台: {len(videos)} 个视频")

        return videos

    @staticmethod
    def extract_video_id(url: str, platform: str) -> Optional[str]:
        """从 URL 中提取视频 ID

        Args:
            url: 视频 URL
            platform: 平台名称

        Returns:
            str: 视频 ID
        """
        if platform == "youtube":
            from modules.youtube import YouTubeProcessor
            return YouTubeProcessor.extract_video_id(url)
        elif platform == "bilibili":
            from modules.bilibili import BilibiliProcessor
            return BilibiliProcessor.extract_video_id(url)
        return None

    @staticmethod
    def sanitize_folder_name(title: str) -> str:
        """清理标题作为文件夹名

        Args:
            title: 原始标题

        Returns:
            str: 清理后的文件夹名
        """
        import re

        # 移除或替换非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(illegal_chars, '_', title)

        # 去除两端空白
        sanitized = sanitized.strip()

        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized


__all__ = ['ConfigLoader']
