# The Batch Newsletter Summarizer

自动化抓取 [The Batch Newsletter](https://www.deeplearning.ai/the-batch/) 并生成 AI 摘要的工具。支持本地网页模式和 GitHub Actions 自动任务模式。

> ⚠️ **注意**：此工具专为 The Batch Newsletter 设计，其他网站的抓取逻辑可能需要调整。

## ✨ 功能特点

- **自动抓取**：定时或手动抓取 The Batch Newsletter 文章
- **AI 摘要**：使用 OpenAI 生成中英文双语摘要
- **Notion 存储**：自动写入 Notion 数据库
- **飞书通知**：任务完成后通过飞书推送结果
- **零成本托管**：GitHub Actions 免费运行，无需服务器

## 📁 目录结构

```
├── newsletter_tool.py       # 核心逻辑库
├── app_launch.py           # Gradio 网页入口（本地使用）
├── run_newsletter.py       # GitHub Actions 自动任务入口
├── test_fetch.py          # 抓取测试脚本
├── test_newsletter.py     # pytest 单元测试
├── requirements.txt       # Python 依赖
└── .github/
    └── workflows/
        └── weekly_newsletter.yml  # GitHub Actions 工作流
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/KureMaki/ai-newsletter-bot.git
cd ai-newsletter-bot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# OpenAI API（必需）
OPENAI_API_KEY=sk-your-openai-api-key

# Notion（必需）
NOTION_TOKEN=secret-your-notion-token
NOTION_DATABASE_ID=your-database-id

# 飞书通知（可选，不填则跳过通知）
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

### 4. 配置 Notion 数据库

创建 Notion 数据库，包含以下字段（区分大小写）：

| 字段名 | 类型 |
|--------|------|
| `名称` | Title |
| `期号` | Rich Text |
| `链接` | URL |

### 5. 本地运行

```bash
python app_launch.py
```

浏览器打开 `http://127.0.0.1:7860`，输入 Newsletter 链接即可。

## 🤖 GitHub Actions 自动任务

### 部署步骤

#### 1. Fork 本仓库

#### 2. 添加 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI API Key |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook URL（可选） |

#### 3. 配置起始 Issue 号

在 Settings → Variables → Actions 中添加：

| Variable | 值 | 说明 |
|----------|-----|------|
| `LAST_ISSUE_NUMBER` | 当前最新一期号 | 下次会自动抓 `值+1` |

#### 4. 完成！

工作流会在每周六自动执行。你也可以手动触发：
- 进入 Actions 页面 → 点击 "Weekly Newsletter Automation" → "Run workflow"

### 自定义执行时间

编辑 `.github/workflows/weekly_newsletter.yml`：

```yaml
schedule:
  - cron: '0 1 * * 6'  # UTC 时间，改为你的时区
```

例如要改成北京时间周六 10:00：
- 北京时间 = UTC+8，所以 `10-8=2`，填 `'0 2 * * 6'`

### 调试模式

手动触发时设置 `debug_mode: true`，可跳过 AI 摘要生成，节省 token。

## 🔧 依赖

- `openai>=1.0.0`
- `gradio>=4.0.0`
- `notion-client>=2.0.0`
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.2`
- `python-dotenv>=1.0.0`

## ⚠️ 注意事项

- 脚本会自动忽略系统代理环境变量
- 默认使用 `gpt-4o` 模型，可在 `newsletter_tool.py` 中修改
- 如果 Notion 写入失败，已生成的摘要会通过飞书通知显示

## 📝 License

MIT License
