"""
网站数据构建脚本
从飞书多维表格获取数据，生成网站所需的数据文件
"""

import os
import sys
import json
import re
from datetime import datetime

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# 添加skill的script目录到路径
skill_script_dir = os.path.join(project_root, 'skills', 'content-curator-skill', 'script')
sys.path.insert(0, skill_script_dir)

from modules.feishu import FeishuTableUploader
from modules.logger import setup_logger


def extract_tags_from_content(rewritten_content: str) -> list:
    """从深度摘要内容中提取主题标签"""
    import re
    tags = []

    if not rewritten_content:
        return tags

    # 查找 "### 主题标签" 部分
    tags_section_match = re.search(
        r'###\s*主题标签\s*\n([\s\S]+?)(?=\n###|\n---|\n#|$)',
        rewritten_content,
        re.IGNORECASE
    )

    if tags_section_match:
        section = tags_section_match[1]
        # 提取列表项 (支持 "- " 格式)
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                tag = line.lstrip('-').strip()
                # 移除可能的 # 前缀（如果有的话）
                tag = tag.lstrip('#').strip()
                if tag:
                    # 添加 # 前缀
                    tags.append(f"#{tag}")

    return tags


def extract_golden_quotes(rewritten_content: str) -> list:
    """从rewritten内容中提取金句"""
    nuggets = []

    # 查找 "核心金句" 部分
    import re
    golden_section_match = re.search(
        r'###\s*核心金句\s*\n([\s\S]+?)(?=\n###|\n---|$)',
        rewritten_content,
        re.IGNORECASE
    )

    if golden_section_match:
        section = golden_section_match[1]
        # 提取列表项 (支持 "1. " 和 "- " 格式)
        items = re.split(r'^[\s]*[\d]*[-*.]\s*', section, flags=re.MULTILINE)
        nuggets = [item.strip() for item in items if item.strip()]

    return nuggets


def extract_preview_quote(rewritten_content: str, golden_quotes: list) -> str:
    """提取预览金句（优先使用第一条金句）"""
    if golden_quotes:
        # 移除序号，返回纯文本
        first = golden_quotes[0]
        return re.sub(r'^[\d]+[、.\s]*', '', first).strip()
    return ""


def clean_content_for_website(rewritten_content: str) -> str:
    """
    清理深度摘要内容，删除与页面其他部分重复的信息

    删除：
    1. 深度摘要标题（# xxx - 深度摘要）
    2. 副标题（# xxx）
    3. 来源信息（*来源: xxx*）
    4. 核心金句部分（### 核心金句 及其内容）
    5. 正文内容标题（### 正文内容）
    6. 主题标签部分（### 主题标签 及其内容）
    7. 摘要生成时间（*摘要生成时间: xxx*）

    保留：
    - 正文内容
    """
    if not rewritten_content:
        return ""

    content = rewritten_content

    # 删除开头的标题部分（匹配到来源信息之后）
    # 模式：标题 + 分隔线 + 副标题 + 来源 + 分隔线
    content = re.sub(
        r'^#[\s\S]*?来源:[^\n]*\n\s*\n---\n\n',
        '',
        content,
        flags=re.DOTALL
    )

    # 删除"核心金句"部分（包括标题到下一个分隔线或"正文内容"之前）
    content = re.sub(
        r'###\s*核心金句\s*\n[\s\S]*?(?=\n---\n\n###\s*正文内容)',
        '',
        content,
        flags=re.DOTALL
    )

    # 删除"正文内容"标题
    content = re.sub(
        r'---\n\n###\s*正文内容\s*\n\n',
        '',
        content,
        flags=re.DOTALL
    )

    # 删除"主题标签"部分及其内容（直到文件结尾或下一个分隔线）
    content = re.sub(
        r'---\n\n###\s*主题标签\s*\n[\s\S]*?(?=\n---\s*\n\*|$)',
        '',
        content,
        flags=re.DOTALL
    )

    # 删除摘要生成时间（在文件末尾）
    content = re.sub(
        r'\n---\n\n\*摘要生成时间:[^\n]*\*',
        '',
        content,
        flags=re.DOTALL
    )

    return content.strip()


def get_article_type(platform: str) -> str:
    """根据平台确定文章类型"""
    platform_lower = platform.lower()
    if 'youtube' in platform_lower or 'bilibili' in platform_lower:
        return 'video'
    elif 'podcast' in platform_lower or 'xiaoyuzhoufm' in platform_lower or 'spotify' in platform_lower or 'apple_podcasts' in platform_lower:
        return 'podcast'
    else:
        return 'article'


def convert_feishu_to_articles(records: list) -> list:
    """将飞书记录转换为网站Article格式"""
    articles = []

    for record in records:
        fields = record.get('fields', {})

        # 提取字段
        title = fields.get('标题', '')
        author = fields.get('作者', '')
        platform = fields.get('平台', '')
        source_link = fields.get('源链接', '')
        rewritten = fields.get('深度摘要', '')
        golden_quotes = fields.get('金句', '')

        # 封面处理
        cover_url = ''
        cover = fields.get('封面')
        if cover:
            if isinstance(cover, list) and len(cover) > 0:
                token = cover[0] if isinstance(cover[0], str) else cover[0].get('token', '')
                if token:
                    cover_url = f"https://open.feishu.cn/open-apis/drive/v1/preview/{token}?format=jpg"
            elif isinstance(cover, str):
                cover_url = cover

        # 日期：优先使用发布日期，否则使用创建时间
        publish_date_ms = fields.get('发布日期')
        created_time = record.get('created_time', 0)

        if publish_date_ms:
            # 使用发布日期（毫秒时间戳）
            date = datetime.fromtimestamp(publish_date_ms / 1000).strftime('%Y.%m.%d')
        elif created_time:
            # 使用创建时间
            date = datetime.fromtimestamp(created_time / 1000).strftime('%Y.%m.%d')
        else:
            date = datetime.now().strftime('%Y.%m.%d')

        # 确定文章类型（需要在解析 author 之前，因为播客需要特殊处理）
        article_type = fields.get('分类', '')
        if not article_type:
            article_type = get_article_type(platform)

        # 确保类型是有效值
        valid_types = ['video', 'podcast', 'article']
        if article_type not in valid_types:
            article_type = get_article_type(platform)

        # 解析主播和嘉宾信息
        host = ''
        guest = ''
        if author:
            import re
            # 检查是否是 "嘉宾: xxx" 或 "主播: xxx" 格式
            guest_match = re.match(r'^嘉宾[:：]\s*(.+)$', author)
            if guest_match:
                guest = guest_match.group(1).strip()
            else:
                host_match = re.match(r'^主播[:：]\s*(.+)$', author)
                if host_match:
                    host = host_match.group(1).strip()
        elif article_type in ('podcast', 'video'):
            # 对于播客和视频，如果 author 为空，尝试从深度摘要中提取人名
            import re
            if rewritten:
                # 查找常见的人名标注模式
                patterns = [
                    r'嘉宾[：:]\s*([^\s,。]{2,6})',
                    r'主讲[：:]\s*([^\s,。]{2,6})',
                    r'与\s*([^\s,。]{2,6})\s*对话',
                    r'([^\s,。]{2,6})\s*老师',
                    r'([^\s,。]{2,6})\s*教授',
                    # 英文人名模式 (如 "with John Doe")
                    r'(?:with|对话|访谈)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, rewritten)
                    if match:
                        guest = match.group(1).strip()
                        # 根据类型设置不同的前缀
                        if article_type == 'podcast':
                            author = f"嘉宾: {guest}"
                        else:
                            author = guest
                        break

        # 金句提取
        nuggets = []
        if golden_quotes:
            # 分割金句并去除序号
            import re
            # 先按换行符分割
            items = golden_quotes.strip().split('\n')
            # 去除每条金句开头的序号（如 "1." "1、" "1 " 等）
            nuggets = [re.sub(r'^[\d]+[、.\s]+', '', item).strip() for item in items if item.strip()]

        # 如果没有金句字段，从深度摘要中提取
        if not nuggets and rewritten:
            nuggets = extract_golden_quotes(rewritten)

        # 预览金句
        preview_quote = extract_preview_quote(rewritten, nuggets)

        # 清理内容：删除与页面其他部分重复的信息
        cleaned_content = clean_content_for_website(rewritten)

        # 生成标签 - 从深度摘要内容中提取 + 自动生成
        tags = []

        # 从深度摘要内容中提取标签
        content_tags = extract_tags_from_content(rewritten)
        tags.extend(content_tags)

        # 添加平台标签
        if platform:
            platform_tag = f"#{platform.upper()}"
            if platform_tag not in tags:
                tags.append(platform_tag)

        # 添加访谈标签
        if author and '嘉宾' in author and '#访谈' not in tags:
            tags.append('#访谈')

        article = {
            'id': record.get('record_id', ''),
            'title': title,
            'author': author,
            'date': date,
            'coverUrl': cover_url,
            'tags': tags,
            'type': article_type,
            'previewQuote': preview_quote,
            'nuggets': nuggets,
            'content': cleaned_content,
            'sourceLink': source_link,
        }

        # 添加主播和嘉宾字段（如果有）
        if host:
            article['host'] = host
        if guest:
            article['guest'] = guest

        # 只添加有内容的文章
        if title and rewritten:
            articles.append(article)

    return articles


def load_existing_articles(json_path: str) -> tuple:
    """加载现有 articles.json，返回 (articles_list, existing_ids)

    Args:
        json_path: articles.json 文件路径

    Returns:
        tuple: (现有文章列表, 已存在的 record_id 集合)
    """
    if not os.path.exists(json_path):
        return [], set()

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        existing_ids = {article.get('id', '') for article in articles if article.get('id')}
        return articles, existing_ids
    except Exception as e:
        return [], set()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='构建网站数据')
    parser.add_argument('--full', action='store_true', help='完全重新构建（不使用增量更新）')
    args = parser.parse_args()

    logger = setup_logger("build_website")

    logger.info("开始构建网站数据...")

    # 初始化飞书上传器（复用配置）
    try:
        uploader = FeishuTableUploader(logger=logger)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return 1

    # 获取所有记录
    logger.info("从飞书获取数据...")
    records = uploader.get_existing_records(force_refresh=True)
    logger.info(f"获取到 {len(records)} 条记录")

    # 确定输出目录
    output_dir = os.path.join(project_root, 'public', 'data')
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, 'articles.json')

    # 增量更新逻辑
    if args.full:
        # 完全重新构建
        logger.info("模式: 完全重新构建")
        articles = convert_feishu_to_articles(records)
        new_count = len(articles)
    else:
        # 增量更新
        existing_articles, existing_ids = load_existing_articles(json_path)
        logger.info(f"模式: 增量更新 (现有 {len(existing_articles)} 篇文章)")

        # 找出需要新增的记录
        new_records = [r for r in records if r.get('record_id') not in existing_ids]
        logger.info(f"发现 {len(new_records)} 条新记录")

        if new_records:
            # 只转换新记录
            new_articles = convert_feishu_to_articles(new_records)
            # 合并新旧文章
            articles = existing_articles + new_articles
            new_count = len(new_articles)
        else:
            # 没有新记录，保持现有文章不变
            articles = existing_articles
            new_count = 0

    # 按日期排序（最新的在前）
    articles.sort(key=lambda x: x['date'], reverse=True)

    logger.info(f"转换后有效文章: {len(articles)} 篇 (新增: {new_count})")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 保存JSON文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存: {json_path}")

    # 生成TypeScript常量文件（可选）
    src_dir = os.path.join(project_root, 'src', 'data')
    os.makedirs(src_dir, exist_ok=True)

    typescript_path = os.path.join(src_dir, 'articles.ts')

    with open(typescript_path, 'w', encoding='utf-8') as f:
        f.write("// 自动生成，请勿手动修改\n")
        f.write("// 生成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        f.write("import { Article } from '../types';\n\n")
        f.write("export const ARTICLES: Article[] = ")
        json.dump(articles, f, ensure_ascii=False, indent=2)
        f.write(" as const;\n")
    logger.info(f"已保存: {typescript_path}")

    logger.info("=" * 50)
    logger.info("构建完成!")
    logger.info(f"  文章总数: {len(articles)}")
    logger.info(f"  JSON: {json_path}")
    logger.info(f"  TypeScript: {typescript_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
