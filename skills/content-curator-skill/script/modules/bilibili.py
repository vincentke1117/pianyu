"""
Bilibili Processor Module
处理Bilibili视频获取、字幕提取等功能
"""

import os
import re
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional


class BilibiliProcessor:
    """Bilibili视频处理器"""

    def __init__(self, logger):
        self.logger = logger
        self.api_key = os.environ.get("BIBIGPT_API_KEY")

        if not self.api_key:
            self.logger.warning("未设置BIBIGPT_API_KEY环境变量，Bilibili功能将不可用")

        self.base_url = "https://api.bibigpt.co/api/v1"
        self.rate_limit_delay = 1000  # 默认延迟1秒
        self.max_retries = 3

    def fetch_videos(self, up_config: Dict, target_date) -> List[Dict]:
        """获取指定UP主的视频列表

        Args:
            up_config: UP主配置
            target_date: 目标日期

        Returns:
            List[Dict]: 视频列表
        """
        if not self.api_key:
            self.logger.warning("Bilibili功能不可用: 缺少API密钥")
            return []

        uid = up_config.get("uid")
        up_name = up_config.get("name", "未知")
        min_duration = up_config.get("filters", {}).get("min_duration", 0)

        logger = self.logger
        logger.info(f"获取Bilibili UP主: {up_name} (UID: {uid})")

        videos = []

        try:
            # 获取UP主视频列表
            page = 1
            ps = 30  # 每页数量

            while len(videos) < 50:  # 最多获取50个
                try:
                    # Bilibili API需要WBI签名验证
                    # 这里使用更简单的版本
                    url = f"https://api.bilibili.com/x/space/arc/search?mid={uid}&ps={ps}&tid=0&pn={page}&order=pubdate"

                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    data = response.json()

                    if data.get("code") != 0:
                        logger.error(f"获取视频列表失败: {data.get('message')}")
                        break

                    vlist = data["data"]["list"]["vlist"]

                    if not vlist:
                        break

                    for video in vlist:
                        # 解析发布时间
                        publish_time = datetime.fromtimestamp(video["created"])

                        if publish_time.date() != target_date:
                            continue

                        # 解析时长（格式: "MM:SS" 或 "HH:MM:SS"）
                        duration_str = video["length"]
                        duration = self._parse_bilibili_duration(duration_str)

                        # 时长过滤
                        if duration and duration < min_duration:
                            logger.debug(f"跳过短视频: {video['bvid']} ({duration}s < {min_duration}s)")
                            continue

                        videos.append({
                            "id": video["bvid"],
                            "title": video["title"],
                            "description": "",  # Bilibili API不直接提供描述
                            "duration": duration,
                            "published_at": publish_time.strftime("%Y-%m-%d"),
                            "thumbnail_url": video["pic"],
                            "url": f"https://www.bilibili.com/video/{video['bvid']}",
                            "aid": video.get("aid"),
                            "cid": video.get("cid")
                        })

                    page += 1

                    # B站也有请求频率限制
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"获取视频列表页 {page} 失败: {e}")
                    break

            logger.info(f"获取到 {len(videos)} 个符合条件的视频")
            return videos

        except Exception as e:
            logger.error(f"获取Bilibili视频失败: {e}")
            return []

    def get_transcript(
        self,
        video: Dict,
        output_format: str = "text",
        include_timestamps: bool = False,
        include_metadata: bool = True,
        **kwargs
    ) -> Optional[Dict]:
        """获取Bilibili视频完整字幕和元数据

        Args:
            video: 视频信息字典
            output_format: 输出格式 - "text" (纯文本), "json" (带时间戳的JSON), "srt" (SRT格式)
            include_timestamps: 是否在text格式中包含时间戳
            include_metadata: 是否在结果中包含视频元数据
            **kwargs: 其他参数（为了兼容性）

        Returns:
            Dict: 包含视频信息和字幕的字典，失败返回None
            {
                "id": 视频ID,
                "title": 视频标题,
                "author": UP主名称,
                "author_id": UP主ID,
                "cover_url": 封面图URL,
                "duration": 时长,
                "publish_date": 发布日期,
                "source_url": 源URL,
                "service": 服务类型,
                "subtitles": 字幕内容（根据output_format格式化),
                "raw_response": 原始API响应
            }
        """
        if not self.api_key:
            self.logger.error("无法获取字幕: 缺少BIBIGPT_API_KEY")
            return None

        video_url = video["url"]
        video_id = video["id"]

        try:
            self.logger.info(f"获取Bilibili字幕: {video['title']}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }

            params = {
                "url": video_url,
                "enabledSpeaker": True
            }

            # 指数退避重试
            for attempt in range(self.max_retries):
                try:
                    # 内置延迟防止限流
                    time.sleep(self.rate_limit_delay / 1000)

                    # 使用 getSubtitle 端点获取完整字幕
                    # 播客可能需要更长时间处理，增加超时到 180 秒
                    response = requests.get(
                        f"{self.base_url}/getSubtitle",
                        headers=headers,
                        params=params,
                        timeout=180
                    )

                    # 检查HTTP状态码
                    if response.status_code == 401:
                        self.logger.error("Bibigpt API认证失败 - 请检查API密钥")
                        return None
                    elif response.status_code in [429, 503]:
                        raise Exception("API限流或服务不可用，请稍后再试")
                    elif response.status_code != 200:
                        raise Exception(f"API错误 - 状态码: {response.status_code}")

                    data = response.json()
                    self.logger.debug(f"API 响应: {data}")

                    # 检查响应结构
                    if not data.get("success"):
                        raise Exception(f"API调用失败: {data}")

                    # 获取字幕数组
                    detail = data.get("detail", {})
                    subtitles_array = detail.get("subtitlesArray", [])

                    if not subtitles_array:
                        raise Exception("API返回的字幕数组为空")

                    self.logger.info(f"成功获取 {len(subtitles_array)} 个字幕片段")

                    # 格式化字幕内容
                    formatted_subtitles = self._format_subtitles(subtitles_array, output_format, include_timestamps)

                    # 如果不包含元数据，只返回字幕文本
                    if not include_metadata:
                        return formatted_subtitles

                    # 构建包含元数据的完整结果
                    result = {
                        "id": detail.get("id", video_id),
                        "title": detail.get("title", video.get("title", "")),
                        "author": detail.get("author", ""),
                        "author_id": detail.get("authorId", ""),
                        "cover_url": detail.get("cover", ""),
                        "duration": detail.get("duration", 0),
                        "publish_date": detail.get("publishedDate", ""),
                        "source_url": detail.get("url", video_url),
                        "service": detail.get("type", "bilibili"),
                        "subtitles": formatted_subtitles,
                        "raw_response": data
                    }

                    self.logger.info(f"视频信息: {result['title']} by {result['author']}")
                    self.logger.info(f"时长: {result['duration']}秒, 封面图: {result['cover_url']}")

                    return result

                except requests.exceptions.Timeout:
                    if attempt == self.max_retries - 1:
                        raise Exception("请求超时，已达到最大重试次数")

                    # 指数退避
                    wait_time = min(2 ** attempt, 30)  # 最大等待30秒
                    self.logger.warning(f"请求超时，{wait_time}s后重试 ({attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)

                except requests.exceptions.ConnectionError:
                    raise Exception("网络连接错误")

                except requests.exceptions.RequestException as e:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"请求异常: {str(e)}")

                    wait_time = min(2 ** attempt, 30)
                    self.logger.warning(f"请求失败: {e}，{wait_time}s后重试")
                    time.sleep(wait_time)

        except Exception as e:
            self.logger.error(f"获取Bilibili字幕失败 {video_id}: {str(e)}")
            return None

    def _format_subtitles(self, subtitles_array: List[Dict], output_format: str, include_timestamps: bool) -> str:
        """格式化字幕数组

        Args:
            subtitles_array: 字幕数组
            output_format: 输出格式
            include_timestamps: 是否包含时间戳

        Returns:
            str: 格式化后的字幕文本
        """
        if output_format == "json":
            import json
            return json.dumps(subtitles_array, ensure_ascii=False, indent=2)

        elif output_format == "srt":
            return self._convert_to_srt(subtitles_array)

        else:  # text format
            return self._convert_to_text(subtitles_array, include_timestamps)

    def _convert_to_srt(self, subtitles_array: List[Dict]) -> str:
        """转换为 SRT 格式

        Args:
            subtitles_array: 字幕数组

        Returns:
            str: SRT格式的字幕
        """
        srt_lines = []

        for index, subtitle in enumerate(subtitles_array, 1):
            start_time = self._format_srt_time(subtitle.get("startTime", 0))
            end_time = self._format_srt_time(subtitle.get("end", 0))
            text = subtitle.get("text", "").strip()

            srt_lines.append(str(index))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # 空行

        return "\n".join(srt_lines).strip()

    def _convert_to_text(self, subtitles_array: List[Dict], include_timestamps: bool) -> str:
        """转换为纯文本格式

        Args:
            subtitles_array: 字幕数组
            include_timestamps: 是否包含时间戳

        Returns:
            str: 纯文本格式的字幕
        """
        text_lines = []

        for subtitle in subtitles_array:
            text = subtitle.get("text", "").strip()

            if include_timestamps:
                start_time = subtitle.get("startTime", 0)
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                text_lines.append(f"{timestamp} {text}")
            else:
                text_lines.append(text)

        return "\n".join(text_lines).strip()

    def _format_srt_time(self, seconds: float) -> str:
        """格式化时间为 SRT 格式

        Args:
            seconds: 秒数

        Returns:
            str: SRT时间格式 (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _parse_bilibili_duration(self, duration_str: str) -> int:
        """解析Bilibili时长格式

        Args:
            duration_str: 时长字符串，如"40:15"或"1:20:30"

        Returns:
            int: 秒数
        """
        try:
            # 分割时间字符串
            parts = duration_str.split(':')

            if len(parts) == 3:
                # HH:MM:SS 格式
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS 格式
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                # 未知格式
                self.logger.warning(f"无法解析B站时长格式: {duration_str}")
                return 0

        except Exception as e:
            self.logger.warning(f"解析B站时长失败 '{duration_str}': {e}")
            return 0

    @staticmethod
    def extract_video_id(video_url: str) -> Optional[str]:
        """从B站视频链接提取视频ID

        Args:
            video_url: 视频链接

        Returns:
            str: BV号，提取失败返回None
        """
        # 标准格式: https://www.bilibili.com/video/BV1xx411c7mD
        match = re.search(r'video/(BV\w+)', video_url)
        if match:
            return match.group(1)

        # 移动端格式: https://m.bilibili.com/video/BV1xx411c7mD
        match = re.search(r'bilibili\.com/video/(BV\w+)', video_url)
        if match:
            return match.group(1)

        # 短链接格式: https://b23.tv/BV1xx411c7mD
        match = re.search(r'b23\.tv/(BV\w+)', video_url)
        if match:
            return match.group(1)

        return None

    def get_user_info(self, uid: int) -> Optional[Dict]:
        """获取UP主信息

        Args:
            uid: UP主UID

        Returns:
            Dict: UP主信息
        """
        try:
            url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("code") != 0:
                return None

            info = data["data"]
            return {
                "uid": info["mid"],
                "name": info["name"],
                "avatar": info["face"],
                "fans": info["fans"]
            }

        except Exception as e:
            self.logger.error(f"获取UP主信息失败: {e}")
            return None


if __name__ == "__main__":
    # 简单测试
    import logging

    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    processor = BilibiliProcessor(logger)

    # 测试配置
    config = {
        "uid": 517898783,
        "name": "小Lin说",
        "filters": {
            "min_duration": 1800
        }
    }

    target_date = datetime.now().date() - datetime.timedelta(days=1)
    videos = processor.fetch_videos(config, target_date)
    print(f"找到 {len(videos)} 个视频")
