# Configuration Guide

## 配置文件结构

### 1. channels.yaml (必需)

定义需要监控的YouTube频道和Bilibili UP主。

**文件位置**: `./channels.yaml`

**示例配置**:
```yaml
# YouTube频道配置
youtube:
  - channel_id: "UCBa659QWEk1AI4Tg--mrJ2A"  # 频道ID（从URL中获取）
    name: "李永乐老师"  # 频道名称（用于标识）
    filters:
      min_duration: 1800  # 最小时长（秒），30分钟=1800秒
      transcript_languages: # 字幕语言优先级
        - "zh-CN"  # 简体中文
        - "zh-TW"  # 繁体中文
        - "en"     # 英文

  - channel_id: "UCIkQ2UG0gtmsr6XzIjygFnw"
    name: "回形针PaperClip"
    filters:
      min_duration: 900   # 15分钟
      transcript_languages: ["zh-CN"]

# Bilibili UP主配置
bilibili:
  - uid: 517898783  # UP主UID
    name: "小Lin说"
    filters:
      min_duration: 1800

  - uid: 436193060
    name: "老师好我叫何同学"
    filters:
      min_duration: 900
```

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `channel_id` | string | 是 | YouTube频道ID（格式: UC...） |
| `uid` | integer | 是 | Bilibili UP主ID |
| `name` | string | 是 | 频道/UP主名称（用于日志和输出） |
| `filters.min_duration` | integer | 否 | 最小时长（秒），默认YouTube=1800, B站无限制 |
| `filters.transcript_languages` | array | 否 | 字幕语言优先级，默认["zh-CN", "zh-TW", "en"] |

**如何获取ID**:
- **YouTube Channel ID**: 访问频道主页 → 查看页面源代码 → 搜索 `channelId` 或从URL中提取（如果是自定义URL，需要用API转换）
- **Bilibili UID**: 访问UP主空间 → URL中的数字就是UID（如 `https://space.bilibili.com/517898783`）

---

### 2. prompt.md (自动生成)

**首次运行**: 自动生成默认模板

**文件位置**: `./prompt.md`

**默认内容**:
```markdown
你是一名专业的内容策展人和知识传播者。请基于以下视频信息，将其改写成一篇结构清晰、易于理解的文章。

视频信息:
- 标题: {title}
- 时长: {duration}
- 频道: {channel_name}
- 发布日期: {publish_date}
- 平台: {platform}

原始字幕内容:
{transcript}

请按照以下结构组织内容：
1. **核心概念/要点**: 用一句话概括本期核心内容
2. **详细解释**: 展开讲解核心概念，使用通俗易懂的语言
3. **实际应用/案例**: 提供具体例子帮助理解
4. **延伸思考**: 引导读者进一步思考
5. **关键术语**: 列出重要概念并解释

写作要求：
- 使用清晰的标题层级（##, ###）
- 保持客观、专业的语气
- 避免直接复制字幕中的口语化表达
- 适当分段，每段不超过5行
- 如有必要，可以使用列表和表格

请直接输出改写后的内容，不要包含原始字幕。
```

**自定义指南**:

你可以修改prompt来定制改写风格，可用变量:
- `{title}`: 视频标题
- `{duration}`: 格式化时长（HH:MM:SS）
- `{channel_name}`: 频道/UP主名称
- `{publish_date}`: 发布日期
- `{platform}`: 平台名称（youtube/bilibili）
- `{transcript}`: 原始字幕内容
- `{video_url}`: 视频链接（可选）

---

### 3. config.yaml (可选)

全局配置和API设置。

**文件位置**: `./config.yaml`

**默认配置**:
```yaml
# API配置
apis:
  youtube:
    enabled: true  # 如果设为false，跳过YouTube处理
    rate_limit_delay: 100  # 请求间隔（毫秒）

  bibigpt:
    enabled: true
    base_url: "https://api.bibigpt.co/api/v1"
    rate_limit_delay: 1000  # 请求间隔，默认1秒
    max_retries: 3          # 失败重试次数
    timeout: 30             # 请求超时（秒）

# 输出配置
output:
  directory: "./output"   # 输出根目录
  date_format: "%Y-%m-%d" # 日期子目录格式
  filename_format: "{platform}_{id}_{date}"  # 文件名格式

# 处理配置
processing:
  max_videos_per_channel: 50  # 每个频道最多处理视频数
  skip_short_videos: true     # 是否跳过短视频
  skip_processed: true        # 是否跳过已处理视频

# 日志配置
logging:
  level: "INFO"               # DEBUG, INFO, WARNING, ERROR
  file: "./logs/content-curator.log"  # 日志文件路径
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

**配置项说明**:

#### API配置

**YouTube**:
- `enabled`: 是否启用YouTube处理
- `rate_limit_delay`: YouTube API请求间隔（毫秒），默认100ms

**Bibigpt** (Bilibili):
- `enabled`: 是否启用Bilibili处理
- `base_url`: Bibigpt API基础URL
- `rate_limit_delay`: 请求间隔（毫秒），默认1000ms（1秒）
- `max_retries`: 失败重试次数，默认3次
- `timeout`: 请求超时时间（秒），默认30秒

#### 输出配置

- `directory`: 输出文件根目录，默认`./output`
- `date_format`: 日期子目录格式，支持strftime格式
- `filename_format`: 文件名模板，支持变量:
  - `{platform}`: 平台名称
  - `{id}`: 视频ID
  - `{date}`: 发布日期
  - `{title}`: 视频标题（会清理特殊字符）

#### 处理配置

- `max_videos_per_channel`: 每个频道最多获取视频数（API限制最大50）
- `skip_short_videos`: 是否启用时长过滤
- `skip_processed`: 是否跳过已处理视频（基于processed.json）

#### 日志配置

- `level`: 日志级别
  - `DEBUG`: 最详细，包含所有调试信息
  - `INFO`: 标准信息
  - `WARNING`: 警告信息
  - `ERROR`: 仅错误信息
- `file`: 日志文件路径（如果不设置则只输出到控制台）
- `format`: 日志格式

---

## 环境变量

### 必需环境变量

```bash
# Bilibili字幕获取（必需）
export BIBIGPT_API_KEY="your_bibigpt_api_key_here"

# Claude API改写（必需）
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

### 可选环境变量

```bash
# 代理配置（如果需要）
export HTTP_PROXY="http://127.0.0.1:1080"
export HTTPS_PROXY="http://127.0.0.1:1080"

# 自定义配置路径
export CONTENT_CURATOR_CONFIG_PATH="/path/to/config.yaml"
export CONTENT_CURATOR_CHANNELS_PATH="/path/to/channels.yaml"
```

---

## 配置验证

运行配置检查:

```bash
claude /content-curator --check-config
```

**验证内容**:
- ✅ channels.yaml 存在且格式正确
- ✅ prompt.md 存在（不存在会提示自动生成）
- ✅ BIBIGPT_API_KEY 环境变量已设置
- ✅ ANTHROPIC_API_KEY 环境变量已设置
- ✅ youtube-transcript-api 库已安装
- ✅ 网络连接正常（可选）

**输出示例**:
```
=== 配置检查 ===
✅ channels.yaml: 找到2个YouTube频道，2个Bilibili UP主
✅ prompt.md: 存在
✅ BIBIGPT_API_KEY: 已设置
✅ ANTHROPIC_API_KEY: 已设置
✅ youtube-transcript-api: 已安装
⚠️  YouTube Data API: 未配置（不影响字幕获取）

配置检查通过！
```

---

## 最佳实践

### 1. 频道选择

- **质量优先**: 选择内容质量高、更新频率适中的频道
- **时长筛选**: 根据内容深度设置合理的`min_duration`
  - 知识类: 20-30分钟 (1200-1800秒)
  - 访谈类: 40-60分钟 (2400-3600秒)
  - 课程类: 60分钟以上

### 2. Prompt优化

- **明确结构**: 在prompt中指定清晰的输出结构
- **控制长度**: 使用`{transcript[:20000]}`限制输入长度
- **风格定制**: 根据目标读者调整语气和用词

### 3. 性能调优

- **API延迟**: 如果对方API有严格限流，适当增大`rate_limit_delay`
- **批量处理**: 首次处理大量历史内容时，可临时增大`max_videos_per_channel`
- **错误处理**: 对于不稳定网络，增大`max_retries`和`timeout`

### 4. 监控与维护

- **定期检查**: 每周运行一次配置检查
- **日志分析**: 定期查看日志，识别频繁失败的原因
- **更新prompt**: 根据改写效果持续优化prompt

---

## 常见问题

**Q: 如何添加新的YouTube频道？**
A: 编辑`channels.yaml`，在`youtube`数组中添加新频道信息。

**Q: 可以只处理特定日期范围的内容吗？**
A: 当前版本支持指定单个日期，如需日期范围可多次运行或修改代码。

**Q: 处理过的视频如何重新处理？**
A: 删除`processed.json`中的对应记录，或删除整个文件。

**Q: 字幕语言如何设置优先级？**
A: 在`channels.yaml`中配置`transcript_languages`数组，按优先级排序。

**Q: API配额用完了怎么办？**
A: 等待配额重置（通常24小时），或升级API套餐。

---

**Last Updated**: 2024-01-15
