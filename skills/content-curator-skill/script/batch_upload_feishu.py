"""
批量上传所有已提取视频到飞书多维表格
"""

import os
import sys
import time

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.feishu import FeishuTableUploader
from modules.storage import StorageManager
from modules.logger import setup_logger


def main():
    """主函数"""
    logger = setup_logger("batch_upload")

    # 初始化上传器
    try:
        uploader = FeishuTableUploader(logger=logger)
        logger.info("飞书上传器初始化成功")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        print(f"错误: {e}")
        return 1

    # 获取输出目录
    storage = StorageManager(logger=logger)
    base_dir = storage.base_output_dir

    logger.info(f"扫描目录: {base_dir}")
    print(f"扫描目录: {base_dir}")

    # 遍历所有子目录
    folders = [f for f in os.listdir(base_dir)
               if os.path.isdir(os.path.join(base_dir, f)) and not f.startswith('.')]

    logger.info(f"发现 {len(folders)} 个视频文件夹")
    print(f"发现 {len(folders)} 个视频文件夹")

    if not folders:
        print("没有找到视频文件夹")
        return 0

    # 列出所有视频
    print("\n待上传的视频:")
    for i, folder in enumerate(folders, 1):
        print(f"{i}. {folder}")

    # 确认上传
    try:
        response = input(f"\n是否上传这 {len(folders)} 个视频到飞书? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return 0
    except EOFError:
        # 非交互模式，自动继续
        print(f"\n自动上传 {len(folders)} 个视频...")

    # 批量上传
    success_count = 0
    skip_count = 0
    error_count = 0

    for i, folder_name in enumerate(folders, 1):
        folder_path = os.path.join(base_dir, folder_name)

        print(f"\n{'='*60}")
        print(f"[{i}/{len(folders)}] 上传: {folder_name}")
        print(f"{'='*60}")

        # 检查必要文件
        required_files = ['metadata.md', 'transcript.md', 'rewritten.md']
        missing_files = [f for f in required_files
                        if not os.path.exists(os.path.join(folder_path, f))]

        if missing_files:
            print(f"跳过: 缺少文件 {missing_files}")
            skip_count += 1
            continue

        try:
            # 上传到飞书
            result = uploader.upload_from_folder(
                folder_path=folder_path,
                unique_field="源链接",
                skip_existing=False  # 不跳过已存在的记录（会智能更新空字段）
            )

            # 检查返回结果
            # code=0 表示成功，或者 action 为相关值也算成功
            action = result.get('action', '')
            if result.get('code') == 0 or action in ['skipped', 'recreated', 'created', 'no_update']:
                chunks = result.get('chunks', 1)
                if action == 'no_update':
                    print(f"成功: 记录已完整，无需更新")
                else:
                    print(f"成功: {action} ({chunks} 条记录)")
                success_count += 1
            else:
                error_msg = result.get('msg', result.get('error', 'unknown error'))
                print(f"失败: {error_msg}")
                error_count += 1

        except Exception as e:
            print(f"失败: {e}")
            logger.error(f"上传失败 {folder_name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1

        # 避免请求过快
        if i < len(folders):
            time.sleep(1)

    # 打印总结
    print("\n" + "=" * 60)
    print("批量上传完成!")
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  失败: {error_count}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
