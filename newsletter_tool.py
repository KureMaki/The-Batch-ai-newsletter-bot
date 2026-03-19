#!/usr/bin/env python
# coding: utf-8

# The Batch Newsletter Summarizer with OpenAI

import requests
from bs4 import BeautifulSoup
import datetime
import sys
import re
import os
from urllib.parse import urlparse


def send_feishu_notification(success, issue_number, content):
    """发送飞书通知"""
    import os
    
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ 未配置 FEISHU_WEBHOOK_URL，跳过通知")
        return
    
    if success:
        title = "✅ Newsletter 更新完成"
        template = "green"
        extra_text = f"Issue {issue_number} 已成功抓取并写入 Notion"
    else:
        title = "❌ Newsletter 更新失败"
        template = "red"
        extra_text = content
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": template
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**Issue {issue_number}**\n\n{extra_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"执行时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ 飞书通知已发送")
        else:
            print(f"⚠️ 飞书通知发送失败: {response.text}")
    except Exception as e:
        print(f"⚠️ 飞书通知发送异常: {str(e)}")


def _configure_stdout_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


_configure_stdout_utf8()


# --- Lazy-initialized clients (no network I/O at import time) ---
_openai_client = None
_notion_client = None
_database_id = None
_env_loaded = False


def _ensure_env():
    """Load .env file once on first use."""
    global _env_loaded
    if not _env_loaded:
        from dotenv import load_dotenv

        load_dotenv()
        _env_loaded = True


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _ensure_env()
        from openai import OpenAI

        _openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=120.0,
        )
    return _openai_client


def _get_notion_client():
    global _notion_client
    if _notion_client is None:
        _ensure_env()
        from notion_client import Client

        _notion_client = Client(
            auth=os.getenv("NOTION_TOKEN"),
            timeout_ms=30000,
        )
    return _notion_client


def _get_database_id():
    global _database_id
    if _database_id is None:
        _ensure_env()
        _database_id = os.getenv("NOTION_DATABASE_ID")
    return _database_id


def fetch_newsletter_text(url):
    """抓取网站文章主体文本"""
    # URL 验证：仅允许 http/https
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return "⚠️ 无效的 URL：仅支持 http/https 协议"
    except Exception:
        return "⚠️ 无效的 URL 格式"

    headers = {"User-Agent": "Mozilla/5.0"}
    # 使用独立 Session 绕过本地代理设置，不污染全局环境变量
    session = requests.Session()
    session.trust_env = False
    try:
        r = session.get(
            url,
            headers=headers,
            timeout=(10, 30),
            proxies={"http": None, "https": None},
        )
    except requests.exceptions.Timeout:
        return "⚠️ 抓取超时，请检查网络连接或稍后重试"
    except requests.exceptions.RequestException as e:
        return f"⚠️ 抓取失败：{str(e)}"

    soup = BeautifulSoup(r.text, "html.parser")

    content = soup.find("article") or soup.find("div", class_="prose")
    if not content:
        return "⚠️ 抓取失败，找不到文章主体"

    paragraphs = content.find_all(["p", "h2", "li"])
    texts = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text:
            texts.append(text)
    return "\n".join(texts)


def gpt_summary_and_translation(text):
    """用 OpenAI 生成英文摘要与中文翻译"""
    # 截断过长文本防止 token 溢出
    max_chars = 15000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n...[内容已截断]"

    prompt = f"""\
你是一位资深的 AI 研究摘要与翻译助手。请你分阶段完成以下任务，对下方 Newsletter 英文内容进行总结与翻译，要求：
---
## 第一阶段：英文摘要（English Summary）
1. 使用简明扼要的英语，总结文章的主要内容。
2. 用 Bullet Points 的形式，段落长度自行判断，关键是容易理解重点。
3. 突出关键模型、算法、研究成果、趋势判断。
4. 若提到专业术语（如 diffusion model、retriever、pretraining 等），请：
   - 保留英文本文
   - 并在括号中简要解释，如：
     `transformer (a type of neural network architecture for sequence modeling)`
---
## 第二阶段：中文翻译（Chinese Translation）
1. 请将以上所有英文摘要翻译为中文
2. 每条与英文段落编号对应（如 1. → 【1】）
3. 中文语言应通顺自然，适合科技爱好者阅读
4. 对原文中解释的术语，中文中也应保留原英文本文及括号说明
---

## 输出格式要求（Markdown）
请按如下结构输出：
- 一级标题：`## 🧠 English Summary`
- 接下来是英文段落（1. ... 换行 2. ...）
- 然后加一级标题：`## 🌏 中文翻译`
- 接下来是中文段落（【1】... 换行【2】...）

以下是正文内容：

{text}
"""
    client = _get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": "You are a bilingual AI summarizer and translator.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def save_to_notion(summary_markdown, url):
    """将摘要写入 Notion 数据库"""
    # 从 URL 提取期号
    issue_match = re.search(r"issue-(\d+)", url)
    issue_number = issue_match.group(1) if issue_match else "Unknown"

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    title = f"The Batch - Issue {issue_number} ({today})"

    # 将 markdown 拆分为结构化 block
    children_blocks = []
    lines = summary_markdown.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            children_blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": line.replace("## ", "").strip()},
                            }
                        ]
                    },
                }
            )
        else:
            children_blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": line[:2000]}}
                        ]
                    },
                }
            )

    notion = _get_notion_client()
    database_id = _get_database_id()

    try:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "名称": {"title": [{"text": {"content": title}}]},
                "期号": {"rich_text": [{"text": {"content": f"{issue_number}"}}]},
                "链接": {"url": url},
            },
            children=children_blocks,
        )
    except Exception as e:
        raise RuntimeError(f"Notion 写入失败：{str(e)}") from e
    print(f"Wrote to Notion: {title}, blocks={len(children_blocks)}")
