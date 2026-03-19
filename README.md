# AI Newsletter Summarizer

这是一个针对 The Batch Newsletter 的自动化工具：抓取文章正文，使用 OpenAI 生成英文摘要并翻译成中文，然后写入 Notion 数据库。提供了 Gradio 网页版入口，方便本地一键使用。

## ✨ 功能模式

### 本地网页模式
手动访问网页，输入 Newsletter 链接，一键完成抓取→摘要→写入 Notion。

### 自动任务模式（GitHub Actions）
每周六 10:00 自动抓取最新 Newsletter，结果写入 Notion 并通过飞书通知。

## 📁 目录结构
- `app_launch.py`：Gradio 网页入口（**主要运行文件**）
- `newsletter_tool.py`：核心逻辑库（抓取、GPT、Notion）
- `Ai Newsletter Openai.ipynb`：Jupyter Notebook 版本（已同步核心逻辑）
- `test_fetch.py`：简单的单篇抓取测试脚本
- `test_newsletter.py`：基于 pytest 的单元测试
- `requirements.txt`：项目依赖列表

## 🛠️ 环境准备

### 1. Python 环境
项目已内置 `.venv/` 虚拟环境（推荐），也可用 conda 或其他虚拟环境。

**使用 .venv/（推荐）：**
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# CMD
.\.venv\Scripts\activate.bat
```

**使用 conda：**
```powershell
conda activate ai-newsletter
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
在项目根目录创建 `.env` 文件，填入以下信息：
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Notion 数据库字段要求（区分大小写）：**
- `名称` (Title)
- `期号` (Rich text)
- `链接` (URL)

## 🚀 运行方式

### 1) 启动 Gradio 网页版 (推荐)
```bash
python app_launch.py
```
启动后，终端会显示本地 URL（通常是 `http://127.0.0.1:7860`）。在浏览器打开该链接，输入 Newsletter 文章网址即可。

### 2) 运行单元测试
验证核心逻辑是否正常（离线 Mock 测试，需先安装 pytest）：
```bash
pip install pytest
pytest test_newsletter.py
```

### 3) 简单抓取测试
仅测试文章抓取功能，不调用 OpenAI/Notion：
```bash
python test_fetch.py
```

### 4) Jupyter Notebook
启动 Jupyter Lab 或 Notebook 打开 `Ai Newsletter Openai.ipynb`，按顺序运行单元格即可。现在 Notebook 直接复用 `newsletter_tool.py` 的逻辑，维护更方便。

## ⚠️ 注意事项
- **网络代理**：脚本会自动忽略系统代理环境变量（HTTP_PROXY 等），直接连接。如果需要通过代理访问，请在 `newsletter_tool.py` 的 `fetch_newsletter_text` 函数中修改 `session.proxies` 设置。
- **OpenAI 模型**：默认使用 `gpt-4o`。如需更改，请修改 `newsletter_tool.py` 中的 `model` 参数。
- **Notion 写入**：如果 Notion 写入失败（如网络波动），程序会**保留并显示**已生成的 GPT 摘要，避免重复扣费。

---

## 🤖 自动任务模式（GitHub Actions）

### 功能
- 每周六早上 10:00（北京时间）自动执行
- 抓取最新 Newsletter → 生成摘要 → 写入 Notion
- 通过飞书发送执行结果通知

### 部署步骤

#### 1. GitHub Secrets 配置
在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 值 |
|-------------|-----|
| `OPENAI_API_KEY` | 你的 OpenAI API Key |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook URL |

#### 2. GitHub Variables 配置
在 Settings → Secrets and variables → Actions → Variables 中添加：

| Variable 名称 | 值 |
|--------------|-----|
| `LAST_ISSUE_NUMBER` | `323`（起始 issue 号，下次会自动 +1）|

#### 3. 手动触发测试
在 GitHub 仓库 Actions 页面，选择 "Weekly Newsletter Automation" → Run workflow

#### 4. 飞书机器人配置
1. 在飞书群中添加自定义机器人
2. 复制 Webhook URL 到 GitHub Secrets
