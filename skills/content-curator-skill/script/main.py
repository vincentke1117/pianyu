#!/usr/bin/env python3
"""
Content Extractor Main Script

从 video.yaml 读取视频配置，提取字幕并改写成结构化文档。

Usage:
    python main.py                  # 处理所有视频
    python main.py --platform youtube  # 只处理指定平台
    python main.py --id youtube_test_1  # 只处理指定视频
"""

import os
import sys
import argparse
from typing import Dict, List, Optional

# 导入模块
from modules.config import ConfigLoader
from modules.youtube import YouTubeProcessor
from modules.bilibili import BilibiliProcessor
from modules.rewriter import ContentRewriter
from modules.storage import StorageManager
from modules.logger import setup_logger


class ContentExtractor:
    """主处理类"""

    def __init__(self, config_path: str = "video.yaml", output_dir: str = "extracted_content"):
        self.config_path = config_path
        self.output_dir = output_dir
        self.logger = setup_logger()

        # 初始化组件
        self.config_loader = ConfigLoader(config_path, self.logger)
        self.storage = StorageManager(output_dir, self.logger)
        self.rewriter = ContentRewriter(self.logger)

        # 初始化处理器
        self.processors = {}
        self._init_processors()

    def _init_processors(self):
        """初始化平台处理器"""
        try:
            self.processors["youtube"] = YouTubeProcessor(self.logger)
        except Exception as e:
            self.logger.warning(f"YouTube处理器初始化失败: {e}")

        try:
            self.processors["bilibili"] = BilibiliProcessor(self.logger)
        except Exception as e:
            self.logger.warning(f"Bilibili处理器初始化失败: {e}")

    def run(
        self,
        platform_filter: Optional[str] = None,
        video_id_filter: Optional[str] = None
    ) -> Dict:
        """执行内容提取流程

        Args:
            platform_filter: 平台过滤 (youtube/bilibili)
            video_id_filter: 视频ID过滤

        Returns:
            Dict: 处理统计
        """
        # 加载配置
        videos = self.config_loader.load()

        # 过滤
        if platform_filter:
            videos = [v for v in videos if v.get("platform") == platform_filter]
            self.logger.info(f"平台过滤: {platform_filter}, 剩余 {len(videos)} 个视频")

        if video_id_filter:
            videos = [v for v in videos if v.get("id") == video_id_filter]
            self.logger.info(f"视频ID过滤: {video_id_filter}, 剩余 {len(videos)} 个视频")

        if not videos:
            self.logger.warning("没有符合条件的视频")
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        # 统计
        stats = {
            "total": len(videos),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "processed": []
        }

        self.logger.info(f"=== 开始处理 {len(videos)} 个视频 ===")

        for video_config in videos:
            self._process_video(video_config, stats)

        # 打印摘要
        self._print_summary(stats)

        return stats

    def _process_video(self, video_config: Dict, stats: Dict):
        """处理单个视频

        Args:
            video_config: 视频配置
            stats: 统计信息
        """
        video_id = video_config.get("id")
        platform = video_config.get("platform")
        title = video_config.get("title", "未知")
        url = video_config.get("url")

        self.logger.info(f"\n处理视频: {title} ({platform})")

        # 检查是否已处理
        if self.storage.is_processed(video_id):
            self.logger.info(f"视频已处理，跳过: {video_id}")
            stats["skipped"] += 1
            return

        # 检查平台处理器
        if platform not in self.processors:
            self.logger.warning(f"平台 {platform} 不可用，跳过: {video_id}")
            stats["failed"] += 1
            return

        processor = self.processors[platform]

        try:
            # 1. 获取视频信息和字幕
            self.logger.info(f"获取字幕: {url}")

            # 从 URL 提取视频 ID
            extracted_id = self.config_loader.extract_video_id(url, platform)
            if not extracted_id:
                self.logger.error(f"无法从 URL 提取视频 ID: {url}")
                stats["failed"] += 1
                return

            # 获取字幕（包含元数据）
            processor_result = processor.get_transcript(
                {"id": extracted_id, "url": url, "title": title},
                output_format="text",
                include_metadata=True,
                include_timestamps=True
            )

            if not processor_result:
                self.logger.error(f"获取字幕失败: {video_id}")
                stats["failed"] += 1
                return

            # 提取字幕文本
            transcript = processor_result.get("subtitles", "")

            if not transcript or len(transcript.strip()) < 50:
                self.logger.warning(f"字幕内容过短，跳过: {video_id}")
                stats["failed"] += 1
                return

            self.logger.info(f"字幕长度: {len(transcript)} 字符")

            # 2. 改写内容
            self.logger.info(f"改写内容...")
            rewritten = self.rewriter.rewrite(transcript, video_config, processor_result)

            # 3. 保存文件
            self.logger.info(f"保存文件...")
            video_config["url"] = url  # 确保配置中有 URL
            video_config["platform"] = platform

            saved_files = self.storage.save_all(
                video_config,
                processor_result,
                transcript,
                rewritten
            )

            # 标记已处理
            self.storage.mark_processed(video_id, video_config)

            stats["success"] += 1
            stats["processed"].append({
                "id": video_id,
                "title": title,
                "platform": platform,
                "files": saved_files
            })

            self.logger.info(f"成功: {title}")

        except Exception as e:
            self.logger.error(f"处理视频失败 {video_id}: {e}")
            stats["failed"] += 1

    def _print_summary(self, stats: Dict):
        """打印处理摘要"""
        print("\n" + "=" * 50)
        print("处理完成!")
        print(f"总计: {stats['total']} 个视频")
        print(f"成功: {stats['success']} 个")
        print(f"失败: {stats['failed']} 个")
        print(f"跳过: {stats['skipped']} 个")

        if stats['success'] > 0:
            print(f"\n已处理的视频:")
            for item in stats['processed']:
                print(f"  - [{item['platform']}] {item['title']}")
                if item.get('files'):
                    for file_type, file_path in item['files'].items():
                        if file_path:
                            print(f"    {file_type}: {file_path}")

        print("\n输出目录:", self.output_dir)
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Content Extractor - 视频内容提取工具")
    parser.add_argument("--config", default="video.yaml", help="配置文件路径 (默认: video.yaml)")
    parser.add_argument("--platform", choices=["youtube", "bilibili"], help="只处理指定平台")
    parser.add_argument("--id", help="只处理指定视频ID")
    parser.add_argument("--output", default="extracted_content", help="输出目录 (默认: extracted_content)")

    args = parser.parse_args()

    # 初始化
    try:
        extractor = ContentExtractor(
            config_path=args.config,
            output_dir=args.output
        )
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    # 处理内容
    try:
        extractor.run(
            platform_filter=args.platform,
            video_id_filter=args.id
        )
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
