# The Batch Newsletter Summarizer

自动化抓取 [The Batch Newsletter](https://www.deeplearning.ai/the-batch/) 并生成 AI 摘要的工具。支持本地网页模式和 GitHub Actions 自动任务模式。

> ⚠️ **注意**：此工具专为 The Batch Newsletter 设计，其他网站的抓取逻辑可能需要调整。

## ✨ 功能特点

- **自动抓取**：定时或手动抓取 The Batch Newsletter 文章
- **AI 摘要**：支持多种 LLM（OpenAI、Claude、DeepSeek 等）生成摘要
- **Notion 存储**：自动写入 Notion 数据库
- **多平台通知**：支持飞书、Telegram、Discord 等 Webhook 通知
- **零成本托管**：GitHub Actions 免费运行，无需服务器

## 📁 目录结构

```
├── newsletter_tool.py       # 核心逻辑库
├── app_launch.py           # Gradio 网页入口（本地使用）
├── get_latest_issue.py     # 获取最新期号（通过 Jina AI Reader 绕过 Cloudflare）
├── last_issue.txt          # 上次成功处理的期号（由 CI 自动维护）
├── run_newsletter.py       # GitHub Actions 自动任务入口
├── test_fetch.py           # 抓取测试脚本
├── test_newsletter.py      # pytest 单元测试
├── requirements.txt         # Python 依赖
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
# LLM API（必需，支持 OpenAI/Claude/DeepSeek 等）
LLM_PROVIDER=openai                    # 可选: openai, anthropic, deepseek
OPENAI_API_KEY=sk-xxx                  # OpenAI（LLM_PROVIDER=openai 时）
# ANTHROPIC_API_KEY=sk-ant-xxx         # Claude（LLM_PROVIDER=anthropic 时）
# DEEPSEEK_API_KEY=sk-xxx               # DeepSeek（LLM_PROVIDER=deepseek 时）

# Notion（必需）
NOTION_TOKEN=secret-xxx
NOTION_DATABASE_ID=xxx

# 通知 Webhook（可选）
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
# TELEGRAM_BOT_TOKEN=xxx                # Telegram Bot Token
# TELEGRAM_CHAT_ID=xxx                  # Telegram Chat ID
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
| `OPENAI_API_KEY` | 你的 LLM API Key（根据 LLM_PROVIDER 选择） |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook URL（可选） |

#### 3. 完成！

工作流会在每周六自动执行。你也可以手动触发：
- 进入 Actions 页面 → 点击 "Weekly Newsletter Automation" → "Run workflow"
- `issue_number`（可选）：手动填写期号（如 `356`）可跳过自动检测，直接处理指定期
- `debug_mode`（可选）：设为 `true` 跳过 AI 摘要，节省 token

### 自定义 LLM

编辑 `newsletter_tool.py` 中的 `_get_llm_client()` 函数，支持：

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- **Claude**: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- **DeepSeek**: `deepseek-chat`, `deepseek-coder`

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

### 关于抓取方式

期号检测和文章内容均通过 [Jina AI Reader](https://jina.ai/reader/)（`r.jina.ai`）中转请求，无需额外账号，可绕过 GitHub Actions IP 被 Cloudflare 封锁的问题。`last_issue.txt` 记录上次成功处理的期号，每次运行成功后由 CI 自动更新并提交。

## 🔧 依赖

- `openai>=1.0.0`
- `anthropic>=0.18.0` （如使用 Claude）
- `gradio>=4.0.0`
- `notion-client>=2.0.0`
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`

## ⚠️ 注意事项

- 脚本会自动忽略系统代理环境变量
- 如果 Notion 写入失败，已生成的摘要会通过通知显示

## 📝 License

MIT License
