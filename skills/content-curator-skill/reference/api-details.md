# API Details Reference

## YouTube Data API v3

### 获取频道视频
**Endpoint**: `GET https://www.googleapis.com/youtube/v3/search`

**Parameters**:
```
part: snippet
channelId: {channel_id}
order: date
maxResults: 50
type: video
```

**Response Structure**:
```json
{
  "items": [
    {
      "id": {"videoId": "abc123"},
      "snippet": {
        "title": "视频标题",
        "publishedAt": "2024-01-15T10:00:00Z",
        "thumbnails": {
          "high": {"url": "https://..."}
        }
      }
    }
  ]
}
```

**Rate Limits**: 10,000 units/day (免费层)

---

## youtube-transcript-api

### Installation
```bash
pip install youtube-transcript-api
```

### Usage
```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# 获取字幕
transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

# 优先选择: 人工字幕 > 自动字幕
transcript = None
for lang in ["zh-CN", "zh-TW", "en"]:
    try:
        transcript = transcript_list.find_transcript([lang])
        break
    except:
        continue

# 回退到自动生成的字幕
if not transcript:
    try:
        transcript = transcript_list.find_generated_transcript(["zh-CN", "zh-TW", "en"])
    except:
        raise Exception("No transcript found")

# 格式化为文本
formatter = TextFormatter()
text = formatter.format_transcript(transcript.fetch())
```

**Error Handling**:
- `TranscriptsDisabled`: 视频禁用字幕 → 跳过
- `NoTranscriptFound`: 无指定语言字幕 → 尝试其他语言
- `VideoUnavailable`: 视频不可访问 → 跳过
- `TooManyRequests`: 请求过多 → 指数退避重试

**Rate Limits**: YouTube未明确限制，建议请求间隔≥100ms

---

## Bilibili API

### 获取UP主视频列表
**Endpoint**: `GET https://api.bilibili.com/x/space/wbi/arc/search`

**Parameters**:
```
mid: {uid}          # UP主ID
ps: 50              # 每页数量
tid: 0              # 分区ID (0=全部)
pn: 1               # 页码
order: pubdate       # 排序方式
dm_img_list: []     # WBI签名参数
dm_img_str: V2ViNA..# WBI签名
```

**Response Structure**:
```json
{
  "code": 0,
  "data": {
    "list": {
      "vlist": [
        {
          "bvid": "BV1xx411c7mD",
          "title": "视频标题",
          "length": "40:15",     // 时长字符串
          "created": 1705276800, // Unix时间戳
          "pic": "http://..."   // 封面图
        }
      ]
    }
  }
}
```

**NOTE**: Bilibili API需要WBI签名验证，建议使用现有库如`bilibili-api-python`

---

## Bibigpt.co API

### Authentication
```bash
curl --request GET \
  --url "https://api.bibigpt.co/api/v1/summarize?url={video_url}" \
  --header "Authorization: Bearer YOUR_API_KEY"
```

**Python Implementation**:
```python
import requests
import time

def fetch_bilibili_transcript(video_url, api_key, delay=1000):
    """获取B站视频字幕"""

    # 内置延时防止限流
    time.sleep(delay / 1000)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    params = {
        "url": video_url,
        "format": "text"  # 纯文本格式
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://api.bibigpt.co/api/v1/summarize",
                headers=headers,
                params=params,
                timeout=30
            )

            # 检查HTTP状态码
            if response.status_code == 401:
                raise Exception("API认证失败 - 请检查API密钥")
            elif response.status_code == 429:
                raise Exception("API限流 - 请稍后再试")
            elif response.status_code != 200:
                raise Exception(f"API错误 - 状态码: {response.status_code}")

            # 解析JSON响应
            data = response.json()

            if data.get("code") != 0:
                raise Exception(f"API返回错误: {data.get('message')}")

            transcript = data.get("data", {}).get("transcript")

            if not transcript:
                raise Exception("获取到空字幕内容")

            return {
                "transcript": transcript,
                "summary": data.get("data", {}).get("summary"),
                "metadata": data.get("data", {}).get("metadata")
            }

        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise Exception("请求超时，已达到最大重试次数")
            wait_time = 2 ** attempt  # 指数退避: 1, 2, 4秒
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError:
            raise Exception("网络连接错误")

        except Exception as e:
            raise e

    return None
```

**Response Format**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "transcript": "完整字幕文本...",
    "summary": "AI生成的视频摘要...",
    "metadata": {
      "duration": 2456,
      "title": "视频标题",
      "quality": "high"
    }
  }
}
```

**Error Codes**:
- `code: 0` - 成功
- `code: 401` - API密钥无效
- `code: 429` - 请求频率过高
- `code: 500` - 服务器错误

**Rate Limiting**:
- 免费版: 100次/天
- 付费版: 根据套餐不同
- **推荐延时**: 1000ms（1秒）

---

## Claude API

### Content Rewriting
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def rewrite_content(transcript, video_info, prompt_template):
    """使用Claude API改写内容"""

    # 构建完整的prompt
    full_prompt = prompt_template.format(
        title=video_info.title,
        duration=format_duration(video_info.duration),
        channel_name=video_info.channel_name,
        publish_date=video_info.published_at,
        transcript=transcript[:50000]  # 限制长度避免token超限
    )

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )

        return response.content[0].text

    except anthropic.AuthenticationError:
        raise Exception("Claude API认证失败")
    except anthropic.RateLimitError:
        raise Exception("Claude API限流")
    except anthropic.APIError as e:
        raise Exception(f"Claude API错误: {str(e)}")
```

**Token Limitations**:
- Claude 3 Sonnet: 200K tokens context
- 建议字幕长度控制在50K字符内（约12.5K tokens）

**Rate Limits**:
- 标准版: 50 requests/minute
- 建议请求间隔: 1200ms

---

## 工具函数

### 时长解析
```python
def parse_duration(duration_str):
    """将时长字符串转换为秒数

    Args:
        duration_str: ISO 8601格式 (如 "PT40M15S") 或 "40:15"

    Returns:
        int: 秒数，解析失败返回None
    """
    import re
    from isodate import parse_duration as iso_parse

    try:
        # ISO 8601格式 (YouTube API)
        if duration_str.startswith('PT'):
            duration = iso_parse(duration_str)
            return int(duration.total_seconds())

        # HH:MM:SS或MM:SS格式
        parts = duration_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s

    except Exception as e:
        log_warning(f"时长解析失败 '{duration_str}': {e}")
        return None

def format_duration(seconds):
    """将秒数格式化为HH:MM:SS"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
```

### 文件操作
```python
def save_markdown_file(content, transcript, video_info, output_dir):
    """生成Markdown文件"""

    filename = f"{video_info.platform}_{video_info.id}_{video_info.published_at}.md"
    filepath = os.path.join(output_dir, filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # 生成文件内容
    markdown_content = f"""---
video_id: "{video_info.id}"
title: "{escape_yaml(video_info.title)}"
duration: {video_info.duration}
thumbnail_url: "{video_info.thumbnail_url}"
published_at: "{video_info.published_at}"
channel: "{video_info.channel_name}"
platform: "{video_info.platform}"
---

# {video_info.title}

## 内容摘要

{content or "_改写失败，见原始字幕_"}

## 原始字幕

\`\`\`
{transcript}
\`\`\`
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return filepath
```

### 幂等性处理
```python
def is_video_processed(video_id, processed_log="processed.json"):
    """检查视频是否已处理"""
    try:
        with open(processed_log, 'r') as f:
            processed = json.load(f)
        return video_id in processed
    except:
        return False

def mark_processed(video_id, processed_log="processed.json"):
    """标记视频为已处理"""
    try:
        with open(processed_log, 'r') as f:
            processed = json.load(f)
    except:
        processed = []

    processed.append({
        "id": video_id,
        "processed_at": datetime.now().isoformat()
    })

    with open(processed_log, 'w') as f:
        json.dump(processed, f)
```

---

## API调用最佳实践

### Rate Limiting策略
```python
class RateLimiter:
    def __init__(self, calls_per_minute):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.time()

# 使用示例
limiter = RateLimiter(50)  # 50次/分钟

for video in videos:
    limiter.wait()  # 自动延时
    process_video(video)
```

### 错误重试策略
```python
def retry_with_backoff(func, max_retries=3, base_delay=1):
    """指数退避重试"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            delay = base_delay * (2 ** attempt)
            log_warning(f"操作失败，{delay}s后重试 ({attempt+1}/{max_retries})")
            time.sleep(delay)
```

---

**Last Updated**: 2024-01-15
**API Versions**: YouTube Data API v3, Bibigpt API v1
