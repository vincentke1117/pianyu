#!/usr/bin/env python3
"""
从飞书表格读取待处理的链接，自动提取内容并上传
支持：YouTube, Bilibili 视频，以及各类文章（通过 zhipu-cli）
"""

import os
import sys
import time
import json
import subprocess
import re
import ast
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.feishu import FeishuTableUploader
from modules.youtube import YouTubeProcessor
from modules.bilibili import BilibiliProcessor
from modules.web import WebExtractor
from modules.rewriter import ContentRewriter
from modules.storage import StorageManager
from modules.config import ConfigLoader
from modules.logger import setup_logger


def remove_ansi_codes(text: str) -> str:
    """去除字符串中的 ANSI 转义序列（颜色代码等）

    Args:
        text: 包含 ANSI 代码的字符串

    Returns:
        str: 清理后的字符串
    """
    # ANSI 转义序列的正则表达式
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def extract_podcast_metadata_with_zhipu(url: str, logger=None) -> dict:
    """使用 zhipu-cli 提取播客元数据（作者、嘉宾、封面等）

    Args:
        url: 播客 URL
        logger: 日志记录器

    Returns:
        dict: 包含 title, author, cover_url, guests 等信息
    """
    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zhipu_cli = os.path.join(script_dir, "dist", "zhipu-cli.exe" if sys.platform == "win32" else "zhipu-cli")

    # 检查 zhipu-cli 是否存在
    if not os.path.exists(zhipu_cli):
        if logger:
            logger.warning(f"zhipu-cli 不存在，跳过元数据提取")
        return {}

    # 准备环境变量（优先从 .env 读取）
    env = os.environ.copy()
    env_path = os.path.join(script_dir, "dist", ".env")

    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == 'ZHIPU_API_KEY':
                            env['ZHIPU_API_KEY'] = value.strip()
                            break
        except Exception as e:
            if logger:
                logger.warning(f"读取 .env 文件失败: {e}")

    # 检查 API 密钥是否存在
    if not env.get('ZHIPU_API_KEY'):
        if logger:
            logger.warning("未设置 ZHIPU_API_KEY，跳过元数据提取")
        return {}

    try:
        # 调用 zhipu-cli read 命令
        result = subprocess.run(
            [zhipu_cli, "read", url],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            env=env
        )

        if result.returncode != 0:
            if logger:
                logger.warning(f"zhipu-cli 执行失败: {result.stderr}")
            return {}

        # 去除 ANSI 转义序列
        raw_output = remove_ansi_codes(result.stdout.strip())

        # 解析 JSON 数据
        idx = raw_output.find('"{\\"url\\"')
        if idx == -1:
            idx = raw_output.find('"{\\"title\\"')

        if idx == -1:
            idx = raw_output.find('{"url"')
            if idx == -1:
                idx = raw_output.find('{"title"')

        if idx == -1:
            return {}

        start_pos = idx + 1 if raw_output[idx:idx+2] == '"{' else idx

        # 使用括号计数找到完整的 JSON 对象
        json_str = raw_output[start_pos:]
        bracket_count = 0
        in_string = False
        escape_next = False
        json_end = 0

        for i, char in enumerate(json_str):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string:
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break

        json_str = json_str[:json_end]

        try:
            inner_json_str = json.loads('"' + json_str + '"')
            article_data = json.loads(inner_json_str)
        except json.JSONDecodeError:
            return {}

        if not article_data:
            return {}

        metadata = article_data.get("metadata", {})

        # 提取作者/主持人信息
        author = metadata.get("author", "") or metadata.get("og:article:author", "") or metadata.get("twitter:creator", "")

        # 提取标题
        title = metadata.get("og:title", "") or article_data.get("title", "")

        # 提取封面
        cover_url = metadata.get("og:image", "") or metadata.get("twitter:image", "")

        # 尝试从描述或内容中提取嘉宾信息
        description = metadata.get("description", "") or article_data.get("description", "")

        # 从内容中提取主播和嘉宾信息
        content = article_data.get("content", "")
        host = ""
        guest = ""

        if content:
            # 提取主播信息（格式：__【主播介绍】XXX：描述）
            import re
            host_match = re.search(r'【主播介绍】([^：:]+)[：:]', content)
            if host_match:
                host = host_match.group(1).strip()

            # 提取嘉宾信息（格式：__【本期嘉宾】XXX：描述）
            guest_match = re.search(r'【本期嘉宾】([^：:]+)[：:]', content)
            if guest_match:
                guest = guest_match.group(1).strip()

        # 构造作者信息：优先使用 author，否则用 "主播: 嘉宾" 格式
        if not author:
            if host and guest:
                author = f"嘉宾: {guest}"
            elif host:
                author = f"主播: {host}"
            elif guest:
                author = f"嘉宾: {guest}"

        result = {
            "title": title,
            "author": author,
            "host": host,
            "guest": guest,
            "cover_url": cover_url,
            "description": description,
        }

        if logger:
            logger.info(f"从 zhipu-cli 提取播客元数据:")
            logger.info(f"  标题: {title}")
            logger.info(f"  作者: {author}")
            if host:
                logger.info(f"  主播: {host}")
            if guest:
                logger.info(f"  嘉宾: {guest}")
            logger.info(f"  封面: {cover_url}")

        return result

    except subprocess.TimeoutExpired:
        if logger:
            logger.warning(f"zhipu-cli 执行超时")
        return {}
    except Exception as e:
        if logger:
            logger.warning(f"zhipu-cli 提取元数据失败: {e}")
        return {}


def extract_article_with_zhipu(url: str, logger=None) -> dict:
    """使用 zhipu-cli 提取文章内容

    Args:
        url: 文章 URL
        logger: 日志记录器

    Returns:
        dict: 包含 raw_output（原始输出）和 content（提取的内容）
    """
    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zhipu_cli = os.path.join(script_dir, "dist", "zhipu-cli.exe" if sys.platform == "win32" else "zhipu-cli")

    # 检查 zhipu-cli 是否存在
    if not os.path.exists(zhipu_cli):
        if logger:
            logger.error(f"zhipu-cli 不存在，请参考 {os.path.join(script_dir, 'dist', 'README.md')} 进行安装")
        return None

    # 准备环境变量（优先从 .env 读取）
    env = os.environ.copy()
    env_path = os.path.join(script_dir, "dist", ".env")

    if os.path.exists(env_path):
        # 从 .env 文件加载
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == 'ZHIPU_API_KEY':
                            env['ZHIPU_API_KEY'] = value.strip()
                            if logger:
                                logger.info("从 .env 文件加载 API 密钥")
                            break
        except Exception as e:
            if logger:
                logger.warning(f"读取 .env 文件失败: {e}")

    # 检查 API 密钥是否存在
    if not env.get('ZHIPU_API_KEY'):
        if logger:
            logger.error("未设置 ZHIPU_API_KEY，请设置环境变量或在 dist/.env 文件中配置")
        return None

    try:
        # 调用 zhipu-cli read 命令
        result = subprocess.run(
            [zhipu_cli, "read", url],
            capture_output=True,
            text=True,
            timeout=120,  # 增加超时时间到 120 秒
            encoding='utf-8',
            env=env  # 传入环境变量
        )

        if result.returncode != 0:
            if logger:
                logger.error(f"zhipu-cli 执行失败: {result.stderr}")
            return None

        # 去除 ANSI 转义序列（颜色代码等）
        raw_output = remove_ansi_codes(result.stdout.strip())

        # 返回原始输出，稍后从 transcript.md 中解析
        return {
            "raw_output": raw_output,
            "content": ""  # 稍后从 JSON 中提取
        }

    except subprocess.TimeoutExpired:
        if logger:
            logger.error(f"zhipu-cli 执行超时")
        return None
    except Exception as e:
        if logger:
            logger.error(f"zhipu-cli 执行异常: {e}")
        return None


def parse_metadata_from_transcript(transcript_file: str, logger=None) -> dict:
    """从 transcript.md 文件中解析元数据

    Args:
        transcript_file: transcript.md 文件路径
        logger: 日志记录器

    Returns:
        dict: 包含 title, author, cover_url, publish_date
    """
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 找到 JSON 开始位置
        # zhipu-cli 输出格式: "{\"url\":\"...\",\"content\":\"...\"}"
        idx = content.find('"{\\"url\\"')
        if idx == -1:
            idx = content.find('"{\\"title\\"')

        if idx == -1:
            # 尝试标准格式
            idx = content.find('{"url"')
            if idx == -1:
                idx = content.find('{"title"')

        if idx == -1:
            if logger:
                logger.warning("未在 transcript.md 中找到 JSON 数据")
            return {}

        # 如果以 "{ 开头，跳过开头的 "，从 { 开始
        start_pos = idx + 1 if content[idx:idx+2] == '"{' else idx

        # 使用括号计数找到完整的 JSON 对象
        json_str = content[start_pos:]
        bracket_count = 0
        in_string = False
        escape_next = False
        json_end = 0

        for i, char in enumerate(json_str):
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break

        json_str = json_str[:json_end]

        # 尝试解析 JSON
        # zhipu-cli 输出格式: "{\"url\":\"...\",\"title\":\"90天...\"}"
        # 需要包裹在引号中，然后用 json.loads 解码两次
        try:
            # 第一次 json.loads: 解码转义字符，得到真实的 JSON 字符串
            inner_json_str = json.loads('"' + json_str + '"')
            # 第二次 json.loads: 解析 JSON 对象
            article_data = json.loads(inner_json_str)
        except json.JSONDecodeError as e:
            if logger:
                logger.warning(f"JSON 解析失败: {e}")
            return {}

        if article_data is None:
            if logger:
                logger.warning(f"JSON 解析失败: 无法解析转义的 JSON 字符串")
            return {}

        metadata = article_data.get("metadata", {})

        result = {
            "title": metadata.get("og:title", "") or article_data.get("title", ""),
            "author": metadata.get("author", "") or metadata.get("og:article:author", "") or metadata.get("twitter:creator", ""),
            "cover_url": metadata.get("og:image", "") or metadata.get("twitter:image", ""),
            "publish_date": article_data.get("publishedTime", "") or metadata.get("article:published_time", "")
        }

        if logger:
            logger.info(f"从 transcript.md 解析元数据:")
            logger.info(f"  标题: {result['title']}")
            logger.info(f"  作者: {result['author']}")
            logger.info(f"  封面: {result['cover_url']}")
            logger.info(f"  发布时间: {result['publish_date']}")

        return result

    except Exception as e:
        if logger:
            logger.warning(f"解析 transcript.md 失败: {e}")
        return {}


def is_record_incomplete(fields):
    """检查记录是否不完整（需要处理）

    通过检查"上传时间"字段来判断：
    - 如果有上传时间 → 已处理，跳过
    - 如果没有上传时间 → 未处理，需要处理
    """
    # 跳过分片记录（标题带 [x/y] 标记）
    title = fields.get('标题', '')
    if isinstance(title, str) and '[' in title and ']' in title and '/' in title:
        # 这是分片记录，跳过
        return False

    # 如果有上传时间，说明已处理过
    if fields.get('上传时间'):
        return False

    # 没有上传时间，需要处理
    return True


def extract_video_id(url, platform):
    """从URL提取视频ID"""
    if platform == 'youtube':
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
    elif platform == 'bilibili':
        if '/video/BV' in url:
            return url.split('/video/')[1]
    elif platform == 'podcast':
        # 小宇宙播客: https://www.xiaoyuzhoufm.com/episode/{episode_id}
        if 'xiaoyuzhoufm.com/episode/' in url.lower():
            return url.split('/episode/')[-1].split('?')[0]
        # Spotify: https://open.spotify.com/episode/{episode_id}
        if 'spotify.com/episode/' in url.lower():
            return url.split('/episode/')[-1].split('?')[0]
        # Apple Podcasts: URL格式多样，直接使用URL作为ID
        return url
    return None


def detect_platform(url):
    """检测URL平台类型

    Returns:
        str: 'youtube', 'bilibili', 'podcast', 'article' 或 None
    """
    url_lower = url.lower()

    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'bilibili.com' in url_lower:
        return 'bilibili'
    elif 'xiaoyuzhoufm.com' in url_lower:
        return 'podcast'
    elif 'spotify.com' in url_lower or 'podcasts.apple.com' in url_lower:
        return 'podcast'
    elif 'mp.weixin.qq.com' in url_lower or 'zhihu.com' in url_lower or 'juejin.cn' in url_lower:
        return 'article'
    elif 'medium.com' in url_lower or 'substack.com' in url_lower or 'notion.com' in url_lower:
        return 'article'
    else:
        # 默认当作文章处理
        return 'article'


def main():
    # 修复 Windows 控制台 GBK 编码问题
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    logger = setup_logger()

    # 初始化组件
    # 使用项目根目录下的 extracted_content (向上 3 级到 content_extractor 目录)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    output_dir = os.path.join(project_root, "extracted_content")
    storage = StorageManager(output_dir, logger)
    rewriter = ContentRewriter(logger)
    config_loader = ConfigLoader('video.yaml', logger)

    # 初始化视频处理器
    processors = {}
    try:
        processors['youtube'] = YouTubeProcessor(logger)
        logger.info("YouTube处理器已就绪")
    except Exception as e:
        logger.warning(f"YouTube处理器初始化失败: {e}")

    try:
        processors['bilibili'] = BilibiliProcessor(logger)
        logger.info("Bilibili处理器已就绪")
    except Exception as e:
        logger.warning(f"Bilibili处理器初始化失败: {e}")

    # 播客使用与 bilibili 相同的处理器（bibigpt）
    try:
        processors['podcast'] = BilibiliProcessor(logger)
        logger.info("播客处理器已就绪（使用 bibigpt）")
    except Exception as e:
        logger.warning(f"播客处理器初始化失败: {e}")

    # 初始化网页提取器
    web_extractor = WebExtractor(logger=logger)
    logger.info("网页提取器已就绪")

    # 初始化飞书上传器
    try:
        uploader = FeishuTableUploader(logger=logger)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return 1

    # 获取所有记录
    logger.info("获取飞书表格记录...")
    records = uploader.get_existing_records(force_refresh=True)
    logger.info(f"共 {len(records)} 条记录")

    # 找出需要处理的记录
    incomplete_records = []
    processed_urls = set()  # 用于去重，确保每个源链接只处理一次

    for record in records:
        fields = record.get('fields', {})
        source_url = fields.get('源链接', '')

        if not source_url:
            continue

        # 去重：如果该 URL 已处理过，跳过
        if source_url in processed_urls:
            continue

        if is_record_incomplete(fields):
            # 判断平台
            platform = detect_platform(source_url)
            if not platform:
                logger.warning(f"不支持的平台: {source_url}")
                continue

            incomplete_records.append({
                'record': record,
                'url': source_url,
                'platform': platform,
                'record_id': record.get('record_id'),
            })

            # 标记该 URL 已处理
            processed_urls.add(source_url)

    logger.info(f"找到 {len(incomplete_records)} 条待处理记录")

    if not incomplete_records:
        print("\n没有需要处理的记录!")
        return 0

    print(f"\n待处理的链接:")
    for i, item in enumerate(incomplete_records, 1):
        print(f"{i}. [{item['platform']}] {item['url']}")

    # 询问是否继续（自动模式下跳过）
    try:
        response = input(f"\n是否处理这 {len(incomplete_records)} 个链接? (y/n): ").strip().lower()
        if response != 'y':
            print("取消操作")
            return 0
    except EOFError:
        # 非交互模式，自动继续
        print(f"\n自动处理 {len(incomplete_records)} 个链接...")

    # 处理每个链接
    success_count = 0
    failed_count = 0

    for i, item in enumerate(incomplete_records, 1):
        url = item['url']
        platform = item['platform']

        print(f"\n{'='*60}")
        print(f"[{i}/{len(incomplete_records)}] 处理: {url}")
        print(f"{'='*60}")
        print(f"平台: {platform}")

        try:
            if platform == 'article':
                # === 文章处理流程（自动抓取） ===
                print("检测到文章链接，使用 zhipu-cli 提取内容...")

                # 使用 zhipu-cli 自动抓取文章（获取原始输出）
                article_data = extract_article_with_zhipu(url, logger)

                if not article_data:
                    print("跳过: 文章提取失败")
                    failed_count += 1
                    continue

                raw_output = article_data.get("raw_output", "")

                # 检测平台
                platform_name = detect_platform(url)
                if "mp.weixin.qq.com" in url:
                    platform_name = "wechat"
                elif "zhihu.com" in url:
                    platform_name = "zhihu"
                elif "juejin.cn" in url:
                    platform_name = "juejin"
                elif "medium.com" in url:
                    platform_name = "medium"
                elif "substack.com" in url:
                    platform_name = "substack"
                elif "notion.com" in url or "notion.site" in url:
                    platform_name = "notion"
                else:
                    platform_name = "web"

                # 使用 URL 的 hash 作为 ID
                import hashlib
                url_id = hashlib.md5(url.encode()).hexdigest()[:12]

                # 先创建文件夹（使用 URL 路径作为临时标题）
                from urllib.parse import urlparse
                temp_title = urlparse(url).path.strip('/').replace('-', ' ').replace('_', ' ')
                if temp_title:
                    temp_title = temp_title.replace('/', ' - ').title()
                else:
                    temp_title = url_id

                temp_folder = storage.get_video_folder(temp_title)
                os.makedirs(temp_folder, exist_ok=True)

                # 保存 transcript.md（包含原始 JSON 输出）
                transcript_file = os.path.join(temp_folder, "transcript.md")
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {temp_title}\n\n")
                    f.write(f"*平台: {platform_name.upper()}*\n\n")
                    f.write("---\n\n")
                    f.write("## 原始字幕\n\n")
                    f.write(raw_output)
                    f.write("\n\n")
                    f.write("---\n\n")
                    f.write(f"*转录生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

                if logger:
                    logger.info(f"已保存 transcript.md: {transcript_file}")

                # 从 transcript.md 解析元数据
                metadata = parse_metadata_from_transcript(transcript_file, logger)
                title = metadata.get("title", "").strip()
                author = metadata.get("author", "")
                cover_url = metadata.get("cover_url", "")
                publish_date = metadata.get("publish_date", "")

                # 从 raw_output 中提取 content（用于 AI 改写）
                # 使用与 parse_metadata_from_transcript 相同的 JSON 解析方法
                content = ""
                try:
                    # 找到 JSON 开始位置
                    idx = raw_output.find('"{\\"url\\"')
                    if idx == -1:
                        idx = raw_output.find('"{\\"title\\"')

                    if idx == -1:
                        idx = raw_output.find('{"url"')
                        if idx == -1:
                            idx = raw_output.find('{"title"')

                    if idx != -1:
                        # 如果以 "{ 开头，跳过开头的 "
                        start_pos = idx + 1 if raw_output[idx:idx+2] == '"{' else idx

                        # 使用括号计数找到完整的 JSON 对象
                        json_str = raw_output[start_pos:]
                        bracket_count = 0
                        in_string = False
                        escape_next = False
                        json_end = 0

                        for i, char in enumerate(json_str):
                            if escape_next:
                                escape_next = False
                                continue
                            if char == '\\':
                                escape_next = True
                                continue
                            if char == '"':
                                in_string = not in_string
                                continue
                            if not in_string:
                                if char == '{':
                                    bracket_count += 1
                                elif char == '}':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        json_end = i + 1
                                        break

                        json_str = json_str[:json_end]

                        # 尝试解析 JSON
                        # zhipu-cli 输出格式: "{\"url\":\"...\",\"content\":\"...\",\"title\":\"90天...\"}"
                        # 需要包裹在引号中，然后用 json.loads 解码两次
                        article_data = None
                        try:
                            # 第一次 json.loads: 解码转义字符，得到真实的 JSON 字符串
                            inner_json_str = json.loads('"' + json_str + '"')
                            # 第二次 json.loads: 解析 JSON 对象
                            article_data = json.loads(inner_json_str)
                        except json.JSONDecodeError as e:
                            if logger:
                                logger.warning(f"JSON 解析失败: {e}")

                        if article_data:
                            content = article_data.get("content", "")

                except Exception as e:
                    if logger:
                        logger.warning(f"JSON 解析失败: {e}")

                # 如果 JSON 解析失败，尝试提取纯文本内容
                if not content:
                    lines = raw_output.split('\n')
                    content_lines = []
                    skip_header = True
                    for line in lines:
                        if skip_header:
                            if '## 原始字幕' in line or '原始字幕' in line:
                                skip_header = False
                            continue
                        if line.strip() and not line.startswith('*') and not line.startswith('---'):
                            content_lines.append(line)
                    content = '\n'.join(content_lines)

                if not content or len(content.strip()) < 50:
                    print("跳过: 文章内容过短")
                    failed_count += 1
                    continue

                # 如果标题为空，使用临时标题
                if not title:
                    title = temp_title

                print(f"标题: {title}")
                print(f"作者: {author}")
                print(f"内容长度: {len(content)} 字符")

                # 构造 processor_result
                processor_result = {
                    "title": title,
                    "author": author,
                    "service": platform_name,
                    "platform": platform_name,
                    "cover_url": cover_url,
                    "source_url": url,
                    "publish_date": publish_date,
                }

                # 构造 video_config
                video_config = {
                    "id": url_id,
                    "url": url,
                    "platform": platform_name,
                    "title": title,
                }

                # AI 改写
                print("AI 改写内容...")
                rewritten = rewriter.rewrite(content, video_config, processor_result)

                # 保存 metadata.md 和 rewritten.md
                print("保存文件...")

                # 保存 metadata.md
                storage.save_metadata(temp_folder, video_config, processor_result)

                # 保存 rewritten.md
                storage.save_rewritten(temp_folder, rewritten, video_config)

                # 获取文件夹路径
                folder_path = temp_folder
                print(f"内容已保存到: {folder_path}")

                # 验证 metadata.md 是否包含必要信息
                print("验证 metadata.md...")
                metadata_file = os.path.join(folder_path, "metadata.md")
                if not os.path.exists(metadata_file):
                    print("跳过: metadata.md 不存在")
                    failed_count += 1
                    continue

                # 读取并验证 metadata.md
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_content = f.read()

                # 检查是否包含作者信息
                has_author = False
                author_lines = [
                    '| 作者/UP主 |',
                    '| 作者 |',
                    '| 作者: |'
                ]
                for line in author_lines:
                    if line in metadata_content:
                        # 检查该行是否有内容（不只是标题）
                        idx = metadata_content.find(line)
                        if idx != -1:
                            # 获取该行完整内容
                            end_idx = metadata_content.find('\n', idx)
                            full_line = metadata_content[idx:end_idx]
                            # 检查是否有值（不只是 | 或空格）
                            parts = full_line.split('|')
                            if len(parts) >= 3 and parts[2].strip() and parts[2].strip() != '':
                                has_author = True
                                break

                # 检查是否包含封面图（文章使用 URL）
                has_cover = '封面图' in metadata_content and 'http' in metadata_content

                if not has_author:
                    print("警告: metadata.md 缺少作者信息，但仍会上传")
                    logger.warning(f"metadata.md 缺少作者信息: {metadata_file}")

                if not has_cover:
                    print("警告: metadata.md 缺少封面图，但仍会上传")
                    logger.warning(f"metadata.md 缺少封面图: {metadata_file}")

                print(f"验证完成 - 作者: {'有' if has_author else '无'}, 封面: {'有' if has_cover else '无'}")

                # 上传到飞书表格
                print("上传到飞书表格...")
                uploader.upload_from_folder(
                    folder_path,
                    skip_existing=False
                )

                success_count += 1
                print(f"成功: {url}")

            else:
                # === 视频处理流程 ===
                # 检查平台处理器是否可用
                if platform not in processors:
                    print(f"跳过: {platform} 处理器不可用")
                    failed_count += 1
                    continue

                processor = processors[platform]

                # 1. 提取视频ID
                video_id = extract_video_id(url, platform)
                if not video_id:
                    print(f"跳过: 无法提取视频ID")
                    failed_count += 1
                    continue

                print(f"视频ID: {video_id}")

                # 1.5. 对于播客，先用 zhipu-cli 提取元数据（作者、嘉宾、封面等）
                zhipu_metadata = {}
                if platform == 'podcast':
                    print("使用 zhipu-cli 提取播客元数据...")
                    zhipu_metadata = extract_podcast_metadata_with_zhipu(url, logger)
                    if zhipu_metadata:
                        print(f"  标题: {zhipu_metadata.get('title', '')}")
                        print(f"  作者/主持人: {zhipu_metadata.get('author', '')}")

                # 2. 获取字幕
                print("获取字幕...")
                processor_result = processor.get_transcript(
                    {"id": video_id, "url": url, "title": ""},
                    output_format="text",
                    include_metadata=True,
                    include_timestamps=True
                )

                if not processor_result:
                    print("跳过: 获取字幕失败")
                    failed_count += 1
                    continue

                # 修正 service/platform 字段以确保正确识别分类
                # 对于播客，确保使用正确的平台名称
                if platform == 'podcast':
                    # 根据URL确定具体播客平台
                    url_lower = url.lower()
                    if 'xiaoyuzhoufm.com' in url_lower:
                        processor_result['service'] = 'xiaoyuzhoufm'
                        processor_result['platform'] = 'xiaoyuzhoufm'
                    elif 'spotify.com' in url_lower:
                        processor_result['service'] = 'spotify'
                        processor_result['platform'] = 'spotify'
                    elif 'podcasts.apple.com' in url_lower:
                        processor_result['service'] = 'apple_podcasts'
                        processor_result['platform'] = 'apple_podcasts'
                    else:
                        processor_result['service'] = 'podcast'
                        processor_result['platform'] = 'podcast'

                    # 合并 zhipu-cli 提取的元数据（优先使用 zhipu-cli 的数据）
                    if zhipu_metadata:
                        if zhipu_metadata.get('title'):
                            processor_result['title'] = zhipu_metadata['title']
                        if zhipu_metadata.get('author'):
                            processor_result['author'] = zhipu_metadata['author']
                        if zhipu_metadata.get('cover_url'):
                            processor_result['cover_url'] = zhipu_metadata['cover_url']

                transcript = processor_result.get("subtitles", "")
                if not transcript or len(transcript.strip()) < 50:
                    print("跳过: 字幕内容过短")
                    failed_count += 1
                    continue

                print(f"字幕长度: {len(transcript)} 字符")

                # 3. 改写内容
                print("AI改写内容...")
                video_config = {
                    "id": video_id,
                    "url": url,
                    "platform": platform,
                    "title": processor_result.get("title", "")
                }

                rewritten = rewriter.rewrite(transcript, video_config, processor_result)

                # 4. 保存文件
                print("保存文件...")
                saved_files = storage.save_all(
                    video_config,
                    processor_result,
                    transcript,
                    rewritten
                )

                # 获取保存的文件夹路径
                folder_name = list(saved_files.values())[0].split(os.sep)[-2] if saved_files else None
                if folder_name:
                    folder_path = os.path.join(output_dir, folder_name)
                else:
                    # 使用视频ID作为文件夹名
                    folder_path = os.path.join(output_dir, video_id)

                print(f"内容已保存到: {folder_path}")

                # 5. 验证 metadata.md 是否包含必要信息
                print("验证 metadata.md...")
                metadata_file = os.path.join(folder_path, "metadata.md")
                if not os.path.exists(metadata_file):
                    print("跳过: metadata.md 不存在")
                    failed_count += 1
                    continue

                # 读取并验证 metadata.md
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_content = f.read()

                # 检查是否包含作者信息
                has_author = False
                author_lines = [
                    '| 作者/UP主 |',
                    '| 作者 |',
                    '| 作者: |'
                ]
                for line in author_lines:
                    if line in metadata_content:
                        # 检查该行是否有内容（不只是标题）
                        idx = metadata_content.find(line)
                        if idx != -1:
                            # 获取该行完整内容
                            end_idx = metadata_content.find('\n', idx)
                            full_line = metadata_content[idx:end_idx]
                            # 检查是否有值（不只是 | 或空格）
                            parts = full_line.split('|')
                            if len(parts) >= 3 and parts[2].strip() and parts[2].strip() != '':
                                has_author = True
                                break

                # 检查是否包含封面图
                has_cover = 'cover.jpg' in metadata_content.lower() or 'http' in metadata_content and '封面图' in metadata_content

                if not has_author:
                    print("警告: metadata.md 缺少作者信息，但仍会上传")
                    logger.warning(f"metadata.md 缺少作者信息: {metadata_file}")

                if not has_cover:
                    print("警告: metadata.md 缺少封面图，但仍会上传")
                    logger.warning(f"metadata.md 缺少封面图: {metadata_file}")

                print(f"验证完成 - 作者: {'有' if has_author else '无'}, 封面: {'有' if has_cover else '无'}")

                # 6. 上传到飞书表格
                print("上传到飞书表格...")
                uploader.upload_from_folder(
                    folder_path,
                    skip_existing=False
                )

                success_count += 1
                print(f"成功: {url}")

        except Exception as e:
            print(f"失败: {e}")
            logger.error(f"处理失败 {url}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1

        # 避免请求过快
        if i < len(incomplete_records):
            time.sleep(2)

    # 打印摘要
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
