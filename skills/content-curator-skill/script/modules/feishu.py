"""
飞书多维表格上传模块
将提取的视频内容上传到飞书多维表格，支持去重处理
"""

import os
import json
import requests
from typing import Dict, List, Optional
import mimetypes
from datetime import datetime


class FeishuTableUploader:
    """飞书多维表格上传器"""

    # API 端点
    TENANT_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    # 表格 API
    TABLE_GET_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_id}/tables/{table_id}/records"
    TABLE_CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_id}/tables/{table_id}/records"
    TABLE_BATCH_CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_id}/tables/{table_id}/records/batch_create"
    TABLE_UPDATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_id}/tables/{table_id}/records/{record_id}"

    # 图片上传 API
    IMAGE_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"

    def __init__(self, config_path: str = None, logger=None):
        self.logger = logger
        self.config = self._load_config(config_path)
        self.tenant_token = None
        self._existing_records_cache = None

    def _load_config(self, config_path: str = None) -> Dict:
        """加载飞书配置"""
        config = {}

        # 从环境变量读取
        config['app_id'] = os.environ.get('FEISHU_APP_ID')
        config['app_secret'] = os.environ.get('FEISHU_APP_SECRET')
        config['base_id'] = os.environ.get('FEISHU_BASE_ID')
        config['table_id'] = os.environ.get('FEISHU_TABLE_ID')

        # 如果环境变量没有，尝试从文件读取
        if not all([config['app_id'], config['app_secret'], config['base_id'], config['table_id']]):
            if config_path is None:
                script_dir = os.path.dirname(os.path.dirname(__file__))
                config_path = os.path.join(script_dir, '..', 'reference', 'feishu.txt')

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            if key == 'FEISHU_APP_ID' and not config['app_id']:
                                config['app_id'] = value
                            elif key == 'FEISHU_APP_SECRET' and not config['app_secret']:
                                config['app_secret'] = value
                            elif key == 'BASE_ID' and not config['base_id']:
                                config['base_id'] = value
                            elif key == 'TABLE_ID' and not config['table_id']:
                                config['table_id'] = value

        # 验证必需配置
        required = ['app_id', 'app_secret', 'base_id', 'table_id']
        missing = [k for k in required if not config.get(k)]
        if missing:
            raise ValueError(f"缺少飞书配置: {', '.join(missing)}")

        if self.logger:
            self.logger.info(f"飞书配置加载成功: app_id={config['app_id'][:10]}..., table_id={config['table_id']}")

        return config

    def get_tenant_token(self) -> str:
        """获取租户访问令牌"""
        if self.tenant_token:
            return self.tenant_token

        payload = {
            "app_id": self.config['app_id'],
            "app_secret": self.config['app_secret']
        }

        response = requests.post(
            self.TENANT_TOKEN_URL,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

        data = response.json()

        if data.get('code') != 0:
            raise Exception(f"获取租户令牌失败: {data.get('msg')}")

        self.tenant_token = data.get('tenant_access_token')

        if self.logger:
            self.logger.info("租户令牌获取成功")

        return self.tenant_token

    def upload_image(self, image_path: str) -> Optional[Dict]:
        """上传图片到飞书多维表格

        Args:
            image_path: 图片文件路径

        Returns:
            Dict: 包含 file_token 和 name 的字典，失败返回 None
                    格式: {"file_token": "xxx", "name": "文件名.jpg"}
        """
        if not image_path or not os.path.exists(image_path):
            return None

        token = self.get_tenant_token()

        file_name = os.path.basename(image_path)
        app_token = self.config['base_id']

        # 使用 drive/media upload_all API
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"

        # 获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'

        # 读取图片数据
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # 手动构建 multipart/form-data
        boundary = f"----WebKitFormBoundary{app_token[:8]}"

        # 构建表单部分
        form_parts = []

        # file_name 字段
        form_parts.append(f"--{boundary}\r\n")
        form_parts.append('Content-Disposition: form-data; name="file_name"\r\n\r\n')
        form_parts.append(f"{file_name}\r\n")

        # parent_type 字段
        form_parts.append(f"--{boundary}\r\n")
        form_parts.append('Content-Disposition: form-data; name="parent_type"\r\n\r\n')
        form_parts.append("bitable_image\r\n")

        # parent_node 字段
        form_parts.append(f"--{boundary}\r\n")
        form_parts.append('Content-Disposition: form-data; name="parent_node"\r\n\r\n')
        form_parts.append(f"{app_token}\r\n")

        # size 字段
        form_parts.append(f"--{boundary}\r\n")
        form_parts.append('Content-Disposition: form-data; name="size"\r\n\r\n')
        form_parts.append(f"{len(image_data)}\r\n")

        # file 字段
        form_parts.append(f"--{boundary}\r\n")
        form_parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n')
        form_parts.append(f"Content-Type: {mime_type}\r\n\r\n")

        # 组装请求体
        body = "".join(form_parts)
        body_bytes = body.encode('utf-8')
        body_bytes += image_data
        body_bytes += f"\r\n--{boundary}--\r\n".encode('utf-8')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }

        try:
            response = requests.post(url, data=body_bytes, headers=headers)

            if self.logger:
                self.logger.debug(f"图片上传响应: {response.status_code}, {response.text[:500]}")

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_token = result.get('data', {}).get('file_token')
                    if self.logger:
                        self.logger.info(f"图片上传成功: {file_name}, token: {file_token}")
                    return {"file_token": file_token, "name": file_name}
                else:
                    if self.logger:
                        self.logger.warning(f"图片上传失败: {result.get('msg')}")
            else:
                if self.logger:
                    self.logger.warning(f"图片上传失败: HTTP {response.status_code}, {response.text[:200]}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"图片上传异常: {e}")

        return None

    def get_existing_records(self, force_refresh: bool = False) -> List[Dict]:
        """获取现有记录（用于去重）

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            List[Dict]: 现有记录列表
        """
        if self._existing_records_cache is not None and not force_refresh:
            return self._existing_records_cache

        token = self.get_tenant_token()
        app_id = self.config['base_id']
        table_id = self.config['table_id']

        # 分页获取所有记录
        all_records = []
        page_token = None

        while True:
            url = self.TABLE_GET_URL.format(app_id=app_id, table_id=table_id)

            params = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }

            response = requests.get(url, params=params, headers=headers)
            data = response.json()

            if data.get('code') != 0:
                if self.logger:
                    self.logger.warning(f"获取现有记录失败: {data.get('msg')}")
                break

            data_content = data.get('data')
            if not data_content or not isinstance(data_content, dict):
                break

            items = data_content.get('items', [])
            if items is None:
                items = []
            all_records.extend(items)

            # 检查是否有更多页
            has_more = data.get('data', {}).get('has_more', False)
            if not has_more:
                break
            page_token = data.get('data', {}).get('page_token')

        self._existing_records_cache = all_records

        if self.logger:
            self.logger.info(f"获取到 {len(all_records)} 条现有记录")

        return all_records

    def find_existing_record(self, unique_field: str, unique_value: str) -> Optional[Dict]:
        """查找已存在的记录

        Args:
            unique_field: 用于去重的字段名（如 "源链接"）
            unique_value: 字段值

        Returns:
            Dict: 找到的记录，如果不存在返回 None
        """
        existing_records = self.get_existing_records()

        for record in existing_records:
            fields = record.get('fields', {})
            if fields.get(unique_field) == unique_value:
                return record

        return None

    def upload_video(
        self,
        video_url: str,
        platform: str,
        title: str,
        author: str,
        cover_url: str,
        cover_path: str,
        transcript_path: str,
        rewritten_path: str,
        unique_field: str = "源链接",
        skip_existing: bool = True,
        publish_date: int = None,
        content_type: str = None
    ) -> Dict:
        """上传单个视频数据到飞书表格

        Args:
            video_url: 视频原链接
            platform: 平台 (YOUTUBE/BILIBILI)
            title: 标题
            author: 作者
            cover_url: 封面图URL
            cover_path: 封面图片文件路径
            transcript_path: 字幕文件路径
            rewritten_path: 改写文件路径
            unique_field: 用于去重的字段名（默认 "源链接"）
            skip_existing: 如果已存在是否跳过（True）或更新（False）
            publish_date: 发布日期（毫秒时间戳），默认为当前时间
            content_type: 内容分类 (video/podcast/article)

        Returns:
            Dict: 上传结果
        """
        # 读取改写内容和完整内容
        rewritten_content = self._read_file(rewritten_path)
        transcript_content = self._read_file(transcript_path)

        # 分割超长内容
        transcript_parts = self._split_content(transcript_content, max_length=30000)
        rewritten_parts = self._split_content(rewritten_content, max_length=30000)

        # 记录分片信息
        total_transcript_parts = len(transcript_parts)
        total_rewritten_parts = len(rewritten_parts)

        if total_transcript_parts > 1:
            if self.logger:
                self.logger.info(f"完整内容分为 {total_transcript_parts} 部分上传")
        if total_rewritten_parts > 1:
            if self.logger:
                self.logger.info(f"深度摘要分为 {total_rewritten_parts} 部分上传")

        # 提取金句（使用第一部分摘要）
        golden_quotes = self._extract_golden_quotes(rewritten_parts[0] if rewritten_parts else "")

        # 获取发布日期（如果未提供则使用当前时间）
        if publish_date is None:
            publish_date = int(datetime.now().timestamp() * 1000)

        # 获取上传时间（当前时间）
        upload_date = int(datetime.now().timestamp() * 1000)

        # 检查是否已存在
        existing = self.find_existing_record(unique_field, video_url)

        # 如果需要分片上传，使用特殊处理
        if total_transcript_parts > 1 or total_rewritten_parts > 1:
            return self._upload_chunked_content(
                video_url, platform, title, author, cover_url,
                transcript_parts, rewritten_parts, golden_quotes, publish_date, upload_date,
                unique_field, existing, skip_existing, content_type
            )

        # 单个部分，直接上传
        # 构建记录数据 - 只包含表格中存在的字段
        record = {"fields": {}}
        record["fields"][unique_field] = video_url
        record["fields"]["平台"] = platform
        record["fields"]["标题"] = title
        record["fields"]["作者"] = author
        record["fields"]["发布日期"] = publish_date
        record["fields"]["上传时间"] = upload_date
        record["fields"]["完整内容"] = transcript_content
        record["fields"]["深度摘要"] = rewritten_content
        record["fields"]["金句"] = golden_quotes

        # 分类字段
        if content_type:
            record["fields"]["分类"] = content_type

        # 封面 - 直接使用 URL
        if cover_url:
            record["fields"]["封面"] = cover_url

        if existing:
            if skip_existing:
                if self.logger:
                    self.logger.info(f"记录已存在，跳过: {title}")
                return {"action": "skipped", "existing_record": existing}
            else:
                # 更新现有记录
                return self._update_record(existing, record)

        # 创建新记录
        return self._create_records([record])

    def _upload_chunked_content(
        self,
        video_url: str,
        platform: str,
        title: str,
        author: str,
        cover_url: str,
        transcript_parts: list,
        rewritten_parts: list,
        golden_quotes: str,
        publish_date: int,
        upload_date: int,
        unique_field: str,
        existing: dict,
        skip_existing: bool,
        content_type: str = None
    ) -> Dict:
        """上传分片内容 - 创建多个记录，每个包含一部分内容

        对于超长内容，会创建多个记录：
        - 主记录：包含基本信息、第一部分内容、金句
        - 副记录：包含后续部分内容（标题带分片标记）
        """
        records_to_create = []
        records_to_update = []

        total_transcript = len(transcript_parts)
        total_rewritten = len(rewritten_parts)
        max_parts = max(total_transcript, total_rewritten)

        # 为每个分片创建一个记录
        for i in range(max_parts):
            part_title = title
            if i > 0:
                part_title = f"{title} [{i+1}/{max_parts}]"

            record = {"fields": {}}
            record["fields"][unique_field] = video_url
            record["fields"]["平台"] = platform
            record["fields"]["标题"] = part_title
            record["fields"]["作者"] = author
            record["fields"]["发布日期"] = publish_date
            record["fields"]["上传时间"] = upload_date

            # 添加当前部分的内容
            if i < total_transcript:
                transcript_part = transcript_parts[i]
                if total_transcript > 1:
                    transcript_part = f"[{i+1}/{total_transcript}]\n\n{transcript_part}"
                record["fields"]["完整内容"] = transcript_part

            if i < total_rewritten:
                rewritten_part = rewritten_parts[i]
                if total_rewritten > 1:
                    rewritten_part = f"[{i+1}/{total_rewritten}]\n\n{rewritten_part}"
                record["fields"]["深度摘要"] = rewritten_part

            # 只在第一个记录中添加金句、封面和分类
            if i == 0:
                record["fields"]["金句"] = golden_quotes
                if cover_url:
                    record["fields"]["封面"] = cover_url
                # 添加分类字段
                if content_type:
                    record["fields"]["分类"] = content_type

            records_to_create.append(record)

        # 处理已存在记录的情况
        if existing:
            if skip_existing:
                if self.logger:
                    self.logger.info(f"记录已存在，跳过: {title}")
                return {"action": "skipped", "existing_record": existing}
            else:
                # 检查是否需要扩展为多记录
                # 简单处理：删除旧记录，创建新记录
                return self._recreate_with_chunks(existing, records_to_create, unique_field)

        # 创建新记录
        result = self._create_records(records_to_create)
        result["chunks"] = max_parts
        return result

    def _recreate_with_chunks(self, existing: dict, new_records: list, unique_field: str) -> Dict:
        """删除旧记录并创建新的分片记录"""
        record_id = existing.get('record_id')
        token = self.get_tenant_token()
        app_id = self.config['base_id']
        table_id = self.config['table_id']

        # 删除旧记录
        url = self.TABLE_UPDATE_URL.format(app_id=app_id, table_id=table_id, record_id=record_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # 飞书删除记录需要使用 DELETE 请求
        delete_url = url  # 同样的URL，使用DELETE方法
        response = requests.delete(delete_url, headers=headers)

        if response.json().get('code') == 0:
            if self.logger:
                self.logger.info(f"已删除旧记录 {record_id}，准备创建分片记录")
        else:
            if self.logger:
                self.logger.warning(f"删除旧记录失败: {response.json().get('msg')}")

        # 创建新记录
        result = self._create_records(new_records)
        result["action"] = "recreated"
        result["chunks"] = len(new_records)
        return result

    def _extract_golden_quotes(self, rewritten_content: str) -> str:
        """从改写内容中提取金句，添加序号"""
        lines = rewritten_content.split('\n')
        quotes = []
        in_quotes_section = False

        for line in lines:
            line = line.strip()
            if line.startswith('### 核心金句'):
                in_quotes_section = True
                continue
            if in_quotes_section:
                if line.startswith('---') or line.startswith('##'):
                    break
                if line.startswith('-'):
                    # 移除 - 和 ** 标记
                    quote = line.lstrip('-').strip()
                    quote = quote.replace('**', '').strip()
                    if quote:
                        quotes.append(quote)

        # 添加序号
        if quotes:
            numbered_quotes = [f"{i+1}. {quote}" for i, quote in enumerate(quotes)]
            return '\n'.join(numbered_quotes)
        return ""

    def _extract_tags(self, rewritten_content: str) -> str:
        """从改写内容中提取主题标签"""
        import re
        tags = []

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

        return ', '.join(tags) if tags else ""

    def _read_file(self, file_path: str, max_length: int = 30000) -> str:
        """读取文件内容，限制最大长度（已弃用，请使用_split_content）

        Args:
            file_path: 文件路径
            max_length: 最大字符长度（飞书字段限制）

        Returns:
            str: 文件内容，超过长度会被截断
        """
        if not file_path or not os.path.exists(file_path):
            return ""

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    def _split_content(self, content: str, max_length: int = 30000) -> list:
        """将长内容分割成多个部分

        Args:
            content: 要分割的内容
            max_length: 每部分的最大长度

        Returns:
            list: 分割后的内容列表
        """
        if not content or len(content) <= max_length:
            return [content] if content else []

        parts = []
        remaining = content

        while len(remaining) > max_length:
            # 在max_length位置查找最近的换行符或句子结束
            split_pos = max_length
            # 向后查找换行符（最多100字符）
            for i in range(max_length, min(max_length + 100, len(remaining))):
                if remaining[i] == '\n':
                    split_pos = i + 1
                    break

            # 如果没找到换行符，在句子结束处分割
            if split_pos == max_length:
                for i in range(max_length - 50, max_length):
                    if remaining[i] in '.!?。！？':
                        split_pos = i + 1
                        break

            parts.append(remaining[:split_pos])
            remaining = remaining[split_pos:]

        # 添加剩余部分
        if remaining:
            parts.append(remaining)

        return parts

    def _create_records(self, records: List[Dict]) -> Dict:
        """批量创建记录到飞书表格"""
        token = self.get_tenant_token()
        app_id = self.config['base_id']
        table_id = self.config['table_id']

        url = self.TABLE_BATCH_CREATE_URL.format(app_id=app_id, table_id=table_id)

        payload = {
            "records": records
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if data.get('code') != 0:
            # 获取更详细的错误信息
            error_msg = data.get('msg', '未知错误')
            error_field = data.get('error', {}).get('field', '')
            if error_field:
                raise Exception(f"创建记录失败: {error_msg} (字段: {error_field})")
            raise Exception(f"创建记录失败: {error_msg}")

        # 清除缓存
        self._existing_records_cache = None

        if self.logger:
            self.logger.info(f"成功创建 {len(records)} 条记录")

        return data

    def _update_record(self, existing: Dict, new_record: Dict) -> Dict:
        """更新现有记录（只更新空字段，不覆盖已有内容）

        Args:
            existing: 现有记录
            new_record: 新的记录数据

        Returns:
            Dict: 更新结果
        """
        token = self.get_tenant_token()
        app_id = self.config['base_id']
        table_id = self.config['table_id']
        record_id = existing.get('record_id')

        # 获取现有记录的字段
        existing_fields = existing.get('fields', {})
        new_fields = new_record.get('fields', {})

        # 只更新空字段或缺失字段，不覆盖已有内容
        # 特殊处理：金句字段如果有新版本（带序号），则更新
        fields_to_update = {}
        updated_field_names = []

        for field_name, new_value in new_fields.items():
            existing_value = existing_fields.get(field_name)

            # 判断字段是否为空
            is_empty = False
            if existing_value is None:
                is_empty = True
            elif isinstance(existing_value, str) and existing_value.strip() == '':
                is_empty = True
            elif isinstance(existing_value, list) and len(existing_value) == 0:
                is_empty = True

            # 金句字段特殊处理：如果新值带序号，则更新
            should_update = is_empty
            if field_name == "金句" and new_value and not is_empty:
                # 检查新值是否有编号格式 (如 "1. xxx")
                new_has_number = any(new_value.strip().startswith(f"{i}.") for i in range(1, 20))
                # 检查旧值是否有编号格式
                existing_has_number = any(existing_value.strip().startswith(f"{i}.") for i in range(1, 20)) if existing_value else False
                # 如果新值有编号而旧值没有，则更新
                if new_has_number and not existing_has_number:
                    should_update = True

            # 只有当字段为空、缺失，或金句需要更新序号时才更新
            if should_update:
                fields_to_update[field_name] = new_value
                updated_field_names.append(field_name)

        # 如果没有需要更新的字段，直接返回
        if not fields_to_update:
            if self.logger:
                self.logger.info(f"记录已完整，无需更新: {record_id}")
            return {"action": "no_update", "existing_record": existing}

        # 构建更新数据
        update_record = {"fields": fields_to_update}

        url = self.TABLE_UPDATE_URL.format(app_id=app_id, table_id=table_id, record_id=record_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        response = requests.put(url, json=update_record, headers=headers)
        data = response.json()

        if data.get('code') != 0:
            raise Exception(f"更新记录失败: {data.get('msg')}")

        # 清除缓存
        self._existing_records_cache = None

        if self.logger:
            self.logger.info(f"成功更新记录 {record_id}，更新字段: {', '.join(updated_field_names)}")

        return data

    def upload_from_folder(
        self,
        folder_path: str,
        unique_field: str = "源链接",
        skip_existing: bool = True
    ) -> Dict:
        """从视频文件夹上传数据

        Args:
            folder_path: 视频文件夹路径
            unique_field: 用于去重的字段名（默认 "源链接"）
            skip_existing: 如果已存在是否跳过

        Returns:
            Dict: 上传结果
        """
        # 文件路径
        cover_path = os.path.join(folder_path, "cover.jpg")
        transcript_path = os.path.join(folder_path, "transcript.md")
        rewritten_path = os.path.join(folder_path, "rewritten.md")

        # 解析 metadata
        metadata = self._parse_metadata(os.path.join(folder_path, "metadata.md"))

        # 合并作者和嘉宾信息
        author = metadata.get('作者/UP主', '')
        guest = metadata.get('嘉宾', '')
        if guest:
            if author:
                author = f"{author} (嘉宾: {guest})"
            else:
                author = f"嘉宾: {guest}"

        # 提取发布日期（从metadata中获取，如果没有则使用None）
        publish_date = None
        publish_date_str = metadata.get('发布日期', '')
        if publish_date_str:
            try:
                # 发布日期格式通常是 YYYYMMDD 或 YYYY-MM-DD
                # 尝试解析不同格式
                if len(publish_date_str) == 8:  # YYYYMMDD
                    publish_date = int(datetime.strptime(publish_date_str, '%Y%m%d').timestamp() * 1000)
                elif '-' in publish_date_str:  # YYYY-MM-DD
                    publish_date = int(datetime.strptime(publish_date_str, '%Y-%m-%d').timestamp() * 1000)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"无法解析发布日期 {publish_date_str}: {e}")

        # 提取分类（从metadata中获取）
        content_type = metadata.get('分类', None)

        return self.upload_video(
            video_url=metadata.get('视频链接', ''),
            platform=metadata.get('平台', ''),
            title=metadata.get('标题', ''),
            author=author,
            cover_url=metadata.get('封面图', ''),
            cover_path=cover_path,
            transcript_path=transcript_path,
            rewritten_path=rewritten_path,
            unique_field=unique_field,
            skip_existing=skip_existing,
            publish_date=publish_date,
            content_type=content_type
        )

    def _parse_metadata(self, metadata_path: str) -> Dict:
        """解析 metadata.md 文件"""
        metadata = {}

        if not os.path.exists(metadata_path):
            return metadata

        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析表格格式的字段
        lines = content.split('\n')
        in_table = False
        for line in lines:
            line = line.strip()

            # 跳过分隔线
            if line.startswith('|---') or line.startswith('| ==='):
                continue

            # 检测表格开始
            if line.startswith('|') and line.endswith('|'):
                parts = [p.strip() for p in line.split('|')]
                # 移除首尾空元素（由于 | 开头和结尾）
                parts = [p for p in parts if p]

                if len(parts) >= 2:
                    # 表头行：| 字段 | 内容 |
                    if parts[0] == '字段' or parts[0] == 'Field':
                        in_table = True
                        continue

                    # 数据行：| 标题 | xxx |
                    if len(parts) >= 2 and in_table:
                        key = parts[0]
                        # 如果值包含多个部分（因为标题中有 |），合并后面的部分
                        value = parts[1] if len(parts) > 1 else ''
                        if len(parts) > 2:
                            # 标题可能包含 |，所以合并剩余部分
                            value = '|'.join(parts[1:])

                        # 跳过空值字段
                        if key and value and value not in ['字段', '内容']:
                            metadata[key] = value

        # 解析"源链接"部分
        import re
        video_link_match = re.search(r'视频链接:\s*(.+)', content)
        if video_link_match:
            metadata['视频链接'] = video_link_match.group(1).strip()

        cover_match = re.search(r'封面图:\s*(.+)', content)
        if cover_match:
            metadata['封面图'] = cover_match.group(1).strip()

        # 从视频简介中提取嘉宾信息
        # 查找 "嘉宾:" 或 "Guest:" 或 "ft." 等关键词
        description = ''
        for line in lines:
            if '视频简介' in line:
                # 找到视频简介部分，读取后续内容
                desc_start = lines.index(line) + 1
                desc_lines = []
                for desc_line in lines[desc_start:]:
                    desc_line = desc_line.strip()
                    if desc_line and not desc_line.startswith('#') and not desc_line.startswith('-') and '源链接' not in desc_line:
                        desc_lines.append(desc_line)
                    elif desc_line.startswith('##'):
                        break
                description = '\n'.join(desc_lines)
                break

        # 提取嘉宾信息
        if description:
            # 非人名黑名单
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
                r'嘉宾[:：]\s*([^\n]+?)(?:\n|$)',
                r'Guest[:：]\s*([^\n]+?)(?:\n|$)',
                r'ft\.\s+([^\n,]+?)(?:\n|,)',
                r'featuring\s+([^\n,]+?)(?:\n|,)',
                r'with\s+([A-Z][a-zA-Z\s]+?)(?:\n|,|\.|In this)',
                # 名字开头 + "is the/a/an" 格式 (更严格的模式)
                r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\s+is\s+(?:the|a|an)',
            ]
            for pattern in guest_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    guest_name = match.group(1).strip()
                    # 清理可能的额外字符和标点
                    guest_name = re.sub(r'^\s+|\s+$|[,，。.]*$', '', guest_name)

                    # 检查是否在黑名单中
                    if guest_name in non_name_blacklist:
                        continue

                    # 验证人名格式：2-4个单词，每个单词首字母大写
                    words = guest_name.split()
                    if 2 <= len(words) <= 4:
                        all_proper = all(
                            (word[0].isupper() and word[1:].islower()) or
                            (len(word) <= 4 and word.isupper())
                            for word in words if len(word) > 1
                        )
                        if all_proper and len(guest_name) < 100:
                            metadata['嘉宾'] = guest_name
                            break

                    # 对于明确标记的 Guest/featuring 格式，放宽限制
                    if 'Guest:' in description or 'featuring' in description or 'ft.' in description:
                        if guest_name and len(guest_name) > 1 and len(guest_name) < 100:
                            metadata['嘉宾'] = guest_name
                            break

        return metadata


__all__ = ['FeishuTableUploader']
