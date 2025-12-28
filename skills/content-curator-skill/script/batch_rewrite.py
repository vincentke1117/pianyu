"""
批量重写所有已提取视频的rewritten内容
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.logger import setup_logger
from modules.rewriter import ContentRewriter
from modules.storage import StorageManager


class SimpleLogger:
    """简单日志包装器"""
    def __init__(self):
        self.logger = setup_logger("batch_rewrite")

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)


def parse_metadata_file(metadata_path: str) -> dict:
    """解析metadata.md文件，提取视频信息"""
    video_info = {
        "title": "",
        "platform": "unknown",
        "author": ""
    }

    processor_result = {
        "title": "",
        "author": "",
        "uploader": "",
        "service": "",
        "platform": "",
        "description": ""
    }

    if not os.path.exists(metadata_path):
        return video_info, processor_result

    with open(metadata_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析表格格式
    in_table = False
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ''
                if len(parts) > 2:
                    value = '|'.join(parts[1:])

                if key == '视频ID':
                    processor_result['id'] = value
                    video_info['id'] = value
                elif key == '平台':
                    processor_result['platform'] = value.lower()
                    video_info['platform'] = value.lower()
                elif key == '标题':
                    processor_result['title'] = value
                    video_info['title'] = value
                elif key == '作者/UP主':
                    processor_result['author'] = value
                    processor_result['uploader'] = value
                    video_info['author'] = value

    # 从处理器结果同步
    if not video_info.get('title'):
        video_info['title'] = processor_result.get('title', '')
    if not video_info.get('author'):
        video_info['author'] = processor_result.get('author', processor_result.get('uploader', ''))

    return video_info, processor_result


def read_transcript(transcript_path: str) -> str:
    """读取transcript.md文件内容"""
    if not os.path.exists(transcript_path):
        return ""

    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取"原始字幕"之后的内容
    if "## 原始字幕" in content:
        parts = content.split("## 原始字幕")
        if len(parts) > 1:
            return parts[1].strip()

    return content


def main():
    """主函数"""
    logger = SimpleLogger()
    rewriter = ContentRewriter(logger=logger)

    # 获取输出目录
    storage_manager = StorageManager(logger=logger)
    base_dir = storage_manager.base_output_dir

    logger.info(f"开始批量重写: {base_dir}")

    # 遍历所有子目录
    folders = [f for f in os.listdir(base_dir)
               if os.path.isdir(os.path.join(base_dir, f)) and not f.startswith('.')]

    logger.info(f"发现 {len(folders)} 个视频文件夹")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, folder_name in enumerate(folders, 1):
        folder_path = os.path.join(base_dir, folder_name)
        metadata_path = os.path.join(folder_path, "metadata.md")
        transcript_path = os.path.join(folder_path, "transcript.md")
        rewritten_path = os.path.join(folder_path, "rewritten.md")

        logger.info(f"[{i}/{len(folders)}] 处理: {folder_name}")

        # 检查必要文件
        if not os.path.exists(transcript_path):
            logger.warning(f"  跳过: 缺少 transcript.md")
            skip_count += 1
            continue

        # 读取transcript
        transcript = read_transcript(transcript_path)
        if not transcript:
            logger.warning(f"  跳过: transcript内容为空")
            skip_count += 1
            continue

        # 解析metadata
        video_info, processor_result = parse_metadata_file(metadata_path)

        try:
            # 调用rewriter
            rewritten_content = rewriter.rewrite(transcript, video_info, processor_result)

            # 保存到rewritten.md
            title = video_info.get("title", folder_name)
            content = f"""# {title} - 深度摘要

---

{rewritten_content}

---

*摘要生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            with open(rewritten_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"  完成: 输出长度 {len(rewritten_content)} 字符")
            success_count += 1

        except Exception as e:
            logger.error(f"  失败: {e}")
            error_count += 1
            continue

    # 总结
    logger.info("=" * 50)
    logger.info(f"批量重写完成!")
    logger.info(f"  成功: {success_count}")
    logger.info(f"  跳过: {skip_count}")
    logger.info(f"  失败: {error_count}")


if __name__ == "__main__":
    main()
