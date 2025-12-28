# Content Curator Skill

## 项目结构
```
content-curator-skill/
├── SKILL.md                      # 主技能文件 (226行)
├── README.md                     # 本文件
├── reference/
│   ├── api-details.md           # API调用详情
│   └── configuration.md         # 配置指南
├── script/
│   ├── main.py                  # 入口程序 (300+行)
│   └── modules/
│       ├── __init__.py
│       ├── logger.py            # 日志配置 (150行)
│       ├── storage.py           # 存储管理 (300+行)
│       ├── youtube.py           # YouTube处理 (300+行)
│       ├── bilibili.py          # Bilibili处理 (350+行)
│       └── transcript.py        # 内容改写 (250行)
└── output/                      # 输出目录 (运行时创建)
    ├── YYYY-MM-DD/
    │   ├── youtube_xxx.md
    │   ├── bilibili_xxx.md
    │   └── _report.json
    └── processed.json           # 已处理视频日志
```

## 模块化设计

### 主文件 (SKILL.md)
- **目标行数**: < 500行
- **当前**: 226行 ✓
- **内容**: 执行协议、调用说明、错误映射、使用方式
- **职责**: 定义行为，不实现细节

### 程序脚本

#### 入口程序 (main.py)
```python
ContentCurator
├── _load_config()          # 加载channels.yaml
├── _load_prompt()          # 加载/创建prompt.md
├── process_date()          # 处理指定日期
│   ├── YouTubeProcessor.fetch_videos()
│   ├── BilibiliProcessor.fetch_videos()
│   └── storage.save_content()
└── _generate_report()      # 生成报告
```

#### 模块化组件

**logger.py** (150行)
- 统一日志配置
- 日志模板系统
- 频道专用日志适配器

**storage.py** (300+行)
- 文件存储管理
- 已处理视频追踪 (幂等性)
- Markdown文件生成
- YAML转义处理

**youtube.py** (300+行)
- YouTube Data API v3调用
- youtube-transcript-api集成
- ISO 8601时长解析
- RSS备用方案

**bilibili.py** (350+行)
- Bilibili API调用
- Bibigpt.co API集成
- 指数退避重试
- 限流处理

**transcript.py** (250行)
- Claude API调用
- Prompt模板渲染
- 内容长度优化
- 错误处理

## 自动调用机制

### 主流程调用
```
SKILL.md (Claude Skill)
    ↓ 调用
python script/main.py
    ↓ 初始化
├─ ContentCurator
│   ├─ modules/logger.py (setup_logger)
│   ├─ modules/storage.py (StorageManager)
│   ├─ modules/youtube.py (YouTubeProcessor)
│   └─ modules/bilibili.py (BilibiliProcessor)
│
│   ↓ 执行
└─ process_date()
    ├─ youtube.fetch_videos()     → modules/youtube.py
    ├─ bilibili.fetch_videos()    → modules/bilibili.py
    ├─ transcript.rewrite()       → modules/transcript.py
    └─ storage.save_content()     → modules/storage.py
```

### 错误传递与静默处理
```
错误发生 → 记录日志 → 选择策略 → 继续执行
    ↓
策略映射 (参考错误处理矩阵)
    ├─ FATAL: 退出(1)
    ├─ SKIP_PLATFORM: 标记不可用，继续
    ├─ SKIP_VIDEO: 跳过当前视频，继续
    ├─ DEFAULT_VALUE: 使用默认值，继续
    └─ RETRY: 重试3次，失败则跳过
```

## 配置文件结构

### channels.yaml (必需)
```yaml
youtube:
  - channel_id: "UCxxx"
    name: "频道名"
    filters:
      min_duration: 1800

bilibili:
  - uid: 123456
    name: "UP主名"
    filters:
      min_duration: 1800
```

### Environment Variables (必需)
```bash
export BIBIGPT_API_KEY="your_bibigpt_key"
export ANTHROPIC_API_KEY="your_claude_key"
```

### Optional Files
- `prompt.md` - 自定义改写prompt
- `config.yaml` - 高级配置

## 零中断保证

所有错误场景均已预设处理策略：
- ❌ **绝不询问确认**
- ❌ **绝不暂停等待输入**
- ✅ **所有缺失数据都有默认值**
- ✅ **所有错误都有定义好的恢复路径**
- ✅ **重复执行幂等**

## 使用示例

### 基本用法
```bash
cd content-curator-skill

# 安装依赖
pip install -r requirements.txt

# 设置密钥
export BIBIGPT_API_KEY="xxx"
export ANTHROPIC_API_KEY="xxx"

# 创建channels.yaml
cp examples/channels.yaml .

# 运行
python script/main.py
```

### 作为Claude Skill使用
```bash
# 在Claude Code中
claude /content-curator

# 等同于执行
python script/main.py
```

## 测试

### 配置检查
```bash
python script/main.py --check-config
```

### 单个平台测试
```bash
python script/main.py --platform youtube
python script/main.py --platform bilibili
```

### 指定日期测试
```bash
python script/main.py --date 2024-01-15
```

## 扩展性

### 添加新平台
1. 创建 `modules/new_platform.py`
2. 实现:
   - `fetch_videos()` - 获取视频列表
   - `get_transcript()` - 获取字幕
3. 在 `main.py` 中注册处理器

### 自定义改写
编辑 `prompt.md` 调整改写风格

### 修改输出格式
编辑 `modules/storage.py` 的 `_generate_markdown()`

## 许可证

MIT License

## 最后更新

2024-01-15
