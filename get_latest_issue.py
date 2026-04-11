#!/usr/bin/env python
# coding: utf-8
"""
从 deeplearning.ai/the-batch/ 首页抓取最新期号。
解析失败时自动回退到 LAST_ISSUE_NUMBER 环境变量。
"""

import re
import sys
import os
import requests

BASE_URL = "https://www.deeplearning.ai/the-batch/"
ISSUE_URL_TEMPLATE = "https://www.deeplearning.ai/the-batch/issue-{}/"


def get_latest_issue():
    try:
        resp = requests.get(
            BASE_URL,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; newsletter-bot/1.0)"},
        )
        resp.raise_for_status()

        matches = re.findall(r"issue-(\d+)", resp.text)
        if not matches:
            raise ValueError("页面中未找到任何 issue-XXX 链接，网站结构可能已变更")

        latest = max(int(m) for m in matches)
        issue_url = ISSUE_URL_TEMPLATE.format(latest)

        print(f"✅ 找到最新期号: {latest}", file=sys.stderr)
        print(f"issue_number={latest}")
        print(f"issue_url={issue_url}")

    except Exception as e:
        msg = f"❌ 无法获取最新期号，请检查网站结构是否变更：{e}"
        print(msg, file=sys.stderr)
        _notify_feishu(msg)
        sys.exit(1)


def _notify_feishu(msg):
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return
    try:
        import requests as _requests
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "⚠️ Newsletter 自动化异常"},
                    "template": "red",
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": msg}},
                ],
            },
        }
        _requests.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass


if __name__ == "__main__":
    get_latest_issue()
