# 飞书应用权限配置指南

## 当前问题

诊断显示应用无法访问多维表格 API，返回 "404 page not found" 错误。这是因为应用缺少必要的权限配置。

## 解决方案

### 方法 1: 配置应用权限（推荐）

1. **登录飞书开放平台**
   - 访问: https://open.feishu.cn/app
   - 找到你的应用 (App ID: cli_a9c012fde9b81bd5)

2. **添加权限范围**
   进入 "权限管理" -> "权限配置"，添加以下权限：

   **多维表格权限:**
   - `bitable:app` - 查看、评论和分享多维表格
   - `bitable:app:readonly` - 获取多维表格（只读）
   - `bitable:app:write` - 编辑多维表格

   **知识库权限（如需要访问知识库中的表格）:**
   - `wiki:wiki:readonly` - 获取知识库（只读）
   - `wiki:wiki` - 查看知识库

3. **发布权限**
   - 添加权限后，需要点击 "发布" 或 "创建版本" 使权限生效
   - 发布后可能需要等待几分钟才能生效

4. **获取正确的 app_token**

   **对于知识库中的表格:**
   - 打开你的知识库链接
   - 浏览器开发者工具 (F12) -> Network 标签
   - 刷新页面，查找包含 "node" 或 "obj_token" 的 API 请求
   - 从响应中找到表格节点的 `obj_token`

   **对于独立的多维表格:**
   - 打开多维表格
   - URL 格式通常是: `https://xxx.feishu.cn/base/bascnXXXXXX`
   - `bascnXXXXXX` 就是 app_token

5. **更新配置文件**

   将获取的 app_token 更新到 `reference/feishu.txt`:

   ```
   BASE_ID="<获取到的 app_token>"
   TABLE_ID="tbll3Kgm6b2czc3j"
   ```

### 方法 2: 使用独立的多维表格（更简单）

1. **创建新的多维表格**
   - 在飞书中创建一个新的独立多维表格（不是知识库中的）
   - 添加以下字段: 原链接、平台、标题、作者、封面、完整内容、深度摘要、金句

2. **获取 ID**
   - 打开新建的多维表格
   - 从 URL 中获取 app_token (格式: bascnXXXXXX)
   - 从浏览器开发者工具或 API 中获取 table_id

3. **分享给应用**
   - 点击表格右上角的 "分享"
   - 添加你的应用（通过 App ID 或应用名称）
   - 给予编辑权限

4. **更新配置文件**
   ```
   BASE_ID="<从 URL 获取的 app_token>"
   TABLE_ID="<从开发者工具获取的 table_id>"
   ```

### 方法 3: 使用飞书机器人 Webhook（备选）

如果 API 权限配置困难，可以考虑：
1. 创建飞书自定义机器人
2. 使用 Webhook 发送消息到群聊
3. 不直接操作表格，而是以消息形式通知

## 验证配置

配置完成后，运行诊断脚本验证：

```bash
cd script
python diagnose_feishu_table.py
```

如果看到 "访问成功!" 和 "找到正确的配置!"，说明配置正确。

## 常见错误

| 错误码 | 错误信息 | 解决方案 |
|--------|----------|----------|
| 91402  | NOTEXIST | app_token 不正确或应用没有权限访问 |
| 99991663 | no permission | 应用缺少必要权限，需在开放平台添加 |
| 404    | page not found | API 端点不可用，检查权限配置 |

## 联系支持

如果以上方法都无法解决，可以：
1. 查看飞书开放平台文档: https://open.feishu.cn/document
2. 检查应用日志看具体错误信息
3. 确认应用类型（自建应用 vs 企业应用）
