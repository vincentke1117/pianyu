#!/usr/bin/env python3
"""
飞书多维表格上传测试脚本
将提取的视频内容上传到飞书多维表格
"""

import os
import sys

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.feishu import FeishuTableUploader
from modules.logger import setup_logger


def main():
    logger = setup_logger()

    # 初始化上传器
    try:
        uploader = FeishuTableUploader(logger=logger)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        print("\n请确保已正确配置飞书凭证:")
        print("1. 在 reference/feishu.txt 中配置")
        print("2. 或设置环境变量:")
        print("   - FEISHU_APP_ID")
        print("   - FEISHU_APP_SECRET")
        print("   - FEISHU_BASE_ID")
        print("   - FEISHU_TABLE_ID")
        return 1

    # extracted_content 目录
    base_dir = "extracted_content"

    if not os.path.exists(base_dir):
        logger.error(f"未找到目录: {base_dir}")
        return 1

    # 遍历所有视频文件夹
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)

        # 跳过文件和隐藏文件
        if not os.path.isdir(folder_path) or folder_name.startswith('.'):
            continue

        logger.info(f"\n处理视频: {folder_name}")

        try:
            result = uploader.upload_from_folder(
                folder_path,
                skip_existing=False
            )

            action = result.get("action", "unknown")

            if action == "skipped":
                skipped_count += 1
                logger.info(f"跳过已存在: {folder_name}")
            else:
                success_count += 1
                logger.info(f"上传成功: {folder_name}")

        except Exception as e:
            failed_count += 1
            logger.error(f"上传失败 {folder_name}: {e}")
            import traceback
            traceback.print_exc()

    # 打印摘要
    print("\n" + "=" * 50)
    print(f"上传完成!")
    print(f"成功: {success_count} 个")
    print(f"跳过: {skipped_count} 个")
    print(f"失败: {failed_count} 个")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
