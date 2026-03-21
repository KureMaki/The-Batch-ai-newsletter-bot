#!/usr/bin/env python
# coding: utf-8

"""
The Batch Newsletter Summarizer
支持多种 LLM 和多种通知方式
"""

import requests
from bs4 import BeautifulSoup
import datetime
import sys
import re
import os
from urllib.parse import urlparse


def _configure_stdout_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


_configure_stdout_utf8()


# --- Lazy-initialized clients ---
_llm_client = None
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


# ==================== LLM 支持 ====================

def _get_llm_client():
    """根据 LLM_PROVIDER 获取对应的 LLM 客户端"""
    global _llm_client
    if _llm_client is None:
        _ensure_env()
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "openai":
            from openai import OpenAI
            _llm_client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=120.0,
            )
        elif provider == "anthropic":
            from anthropic import Anthropic
            _llm_client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                timeout=120.0,
            )
        elif provider == "deepseek":
            from openai import OpenAI
            _llm_client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                timeout=120.0,
            )
        else:
            raise ValueError(f"不支持的 LLM_PROVIDER: {provider}")
    
    return _llm_client


def _get_llm_model():
    """获取 LLM 模型名"""
    _ensure_env()
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o")
    elif provider == "anthropic":
        return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    elif provider == "deepseek":
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    else:
        return "gpt-4o"


def generate_summary(text):
    """使用配置的 LLM 生成英文摘要与中文翻译"""
    _ensure_env()
    
    # 截断过长文本
    max_chars = 60000
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
    
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        client = _get_llm_client()
        model = _get_llm_model()
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a bilingual AI summarizer and translator."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    
    elif provider == "anthropic":
        client = _get_llm_client()
        model = _get_llm_model()
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0.3,
            system="You are a bilingual AI summarizer and translator.",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response.content[0].text.strip()
    
    elif provider == "deepseek":
        client = _get_llm_client()
        model = _get_llm_model()
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a bilingual AI summarizer and translator."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    
    else:
        raise ValueError(f"不支持的 LLM_PROVIDER: {provider}")


# ==================== 通知支持 ====================

def send_notification(success, issue_number, content, summary=None):
    """发送通知（支持多种渠道）
    
    根据配置自动选择通知渠道：飞书 > Telegram > Discord
    """
    _ensure_env()
    
    # 尝试各种通知方式
    sent = False
    
    # 飞书
    feishu_url = os.getenv("FEISHU_WEBHOOK_URL")
    if feishu_url:
        _send_feishu(feishu_url, success, issue_number, content, summary)
        sent = True
    
    # Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat_id:
        _send_telegram(telegram_token, telegram_chat_id, success, issue_number, content, summary)
        sent = True
    
    # Discord
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook:
        _send_discord(discord_webhook, success, issue_number, content, summary)
        sent = True
    
    if not sent:
        print("⚠️ 未配置任何通知渠道，跳过通知")


def _send_feishu(webhook_url, success, issue_number, content, summary):
    """发送飞书通知"""
    if success:
        title = "✅ Newsletter 更新完成"
        template = "green"
        display_content = f"**Issue {issue_number}**\n\n{summary[:4000]}" if summary else f"**Issue {issue_number}**\n\n已成功抓取并写入 Notion"
    else:
        title = "❌ Newsletter 更新失败"
        template = "red"
        display_content = f"**Issue {issue_number}**\n\n{content}"
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": display_content}},
                {"tag": "hr"},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"执行时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}]}
            ]
        }
    }
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ 飞书通知已发送")
        else:
            print(f"⚠️ 飞书通知发送失败: {resp.text}")
    except Exception as e:
        print(f"⚠️ 飞书通知发送异常: {str(e)}")


def _send_telegram(token, chat_id, success, issue_number, content, summary):
    """发送 Telegram 通知"""
    if success:
        title = f"✅ Newsletter 更新完成 - Issue {issue_number}"
        msg = f"{title}\n\n{summary[:4000]}" if summary else f"{title}\n\n已成功抓取并写入 Notion"
    else:
        title = f"❌ Newsletter 更新失败 - Issue {issue_number}"
        msg = f"{title}\n\n{content}"
    
    msg += f"\n\n⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        if resp.json().get("ok"):
            print("✅ Telegram 通知已发送")
        else:
            print(f"⚠️ Telegram 通知发送失败: {resp.text}")
    except Exception as e:
        print(f"⚠️ Telegram 通知发送异常: {str(e)}")


def _send_discord(webhook_url, success, issue_number, content, summary):
    """发送 Discord Webhook 通知"""
    if success:
        title = f"✅ Newsletter 更新完成 - Issue {issue_number}"
        description = summary[:4000] if summary else "已成功抓取并写入 Notion"
        color = 3066993  # 绿色
    else:
        title = f"❌ Newsletter 更新失败 - Issue {issue_number}"
        description = content
        color = 15158332  # 红色
    
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": f"执行时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            print("✅ Discord 通知已发送")
        else:
            print(f"⚠️ Discord 通知发送失败: {resp.text}")
    except Exception as e:
        print(f"⚠️ Discord 通知发送异常: {str(e)}")


# ==================== 抓取 ====================

def fetch_newsletter_text(url):
    """抓取网站文章主体文本"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return "⚠️ 无效的 URL：仅支持 http/https 协议"
    except Exception:
        return "⚠️ 无效的 URL 格式"

    headers = {"User-Agent": "Mozilla/5.0"}
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
    texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    return "\n".join(texts)


# ==================== Notion 写入 ====================

def _get_notion_client():
    global _notion_client
    if _notion_client is None:
        _ensure_env()
        from notion_client import Client
        _notion_client = Client(auth=os.getenv("NOTION_TOKEN"), timeout_ms=30000)
    return _notion_client


def _get_database_id():
    global _database_id
    if _database_id is None:
        _ensure_env()
        _database_id = os.getenv("NOTION_DATABASE_ID")
    return _database_id


def save_to_notion(summary_markdown, url):
    """将摘要写入 Notion 数据库"""
    issue_match = re.search(r"issue-(\d+)", url)
    issue_number = issue_match.group(1) if issue_match else "Unknown"

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    newsletter_name = os.getenv("NEWSLETTER_NAME", "The Batch")
    title = f"{newsletter_name} - Issue {issue_number} ({today})"

    children_blocks = []
    for line in summary_markdown.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            children_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line.replace("## ", "").strip()}}]},
            })
        else:
            children_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]},
            })

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

