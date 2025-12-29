<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Content Collector

一个静态网站，展示从飞书多维表格同步来的「文章/播客/视频」深度摘要与金句。

## ✨ 特性

- 📚 **多类型内容**：支持文章、播客、视频三种内容类型
- 🔄 **自动同步**：通过 GitHub Actions 从飞书多维表格自动获取最新数据
- 🔍 **全文搜索**：侧边栏抽屉式搜索，支持按关键词、标签、类型、作者筛选（快捷键 `Cmd+K` / `Ctrl+K`）
- 🎨 **优雅阅读**：沉浸式阅读体验，支持目录导航、金句高亮
- 🤖 **智能提取**：自动从内容中提取嘉宾、主播、标签等信息
- 📱 **响应式设计**：完美适配桌面和移动设备
- 🌙 **深色模式**：支持明暗主题切换

## 🚀 本地运行

**前置要求：** Node.js 20+

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## ⚙️ 环境变量配置

在 GitHub 仓库的 Secrets 中配置以下变量：

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `FEISHU_APP_ID` | 飞书应用 ID | [飞书开放平台](https://open.feishu.cn/) |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 飞书开放平台 |
| `FEISHU_BASE_ID` | 多维表格 Base ID | 飞书多维表格 URL |
| `FEISHU_TABLE_ID` | 表格 ID | 飞书多维表格 URL |
| `VERCEL_TOKEN` | Vercel 部署令牌 | [Vercel Dashboard](https://vercel.com/) |
| `VERCEL_ORG_ID` | Vercel 组织 ID | Vercel Dashboard |
| `VERCEL_PROJECT_ID` | Vercel 项目 ID | Vercel 项目设置 |

## 📦 项目结构

```
content_extractor/
├── public/
│   └── data/
│       └── articles.json      # 网站数据（从飞书同步）
├── scripts/
│   └── build_website_data.py   # 数据构建脚本
├── skills/
│   └── content-curator-skill/
│       └── script/
│           └── modules/
│               ├── feishu.py   # 飞书 API 模块
│               └── logger.py   # 日志模块
├── src/
│   ├── components/             # React 组件
│   ├── data/
│   │   └── articles.ts         # TypeScript 数据文件
│   └── types.ts                # 类型定义
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 配置
└── README.md
```

## 🔄 自动更新流程

```
推送代码到 main 分支
         ↓
   GitHub Actions 触发
         ↓
1. 从飞书获取最新数据
2. 生成 articles.json
3. 构建 React 网站
4. 部署到 Vercel
```

### 手动触发

在 GitHub 仓库的 Actions 页面，选择 "Build and Deploy" workflow，点击 "Run workflow" 按钮。

## 📊 数据格式

每篇文章包含以下字段：

```typescript
{
  id: string;          // 唯一标识
  title: string;       // 标题
  author: string;      // 作者/UP主
  guest?: string;      // 嘉宾（播客/视频）
  host?: string;       // 主播（播客）
  date: string;        // 发布日期
  coverUrl: string;    // 封面图片
  tags: string[];      // 标签
  type: 'video' | 'podcast' | 'article';  // 内容类型
  previewQuote: string; // 预览金句
  nuggets: string[];   // 金句列表
  content: string;     // Markdown 内容
  sourceLink?: string; // 原文链接
}
```

## 🛠️ 技术栈

- **前端框架**：React + TypeScript + Vite
- **样式**：Tailwind CSS
- **部署**：Vercel
- **自动化**：GitHub Actions
- **数据源**：飞书多维表格 API

## 📄 许可证

MIT
