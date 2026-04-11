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
        print(f"⚠️ 抓取最新期号失败: {e}", file=sys.stderr)

        fallback = os.getenv("LAST_ISSUE_NUMBER", "").strip()
        if fallback and fallback.isdigit():
            print(f"⚠️ 回退到 LAST_ISSUE_NUMBER: {fallback}", file=sys.stderr)
            print(f"issue_number={fallback}")
            print(f"issue_url={ISSUE_URL_TEMPLATE.format(fallback)}")
        else:
            print("❌ 无可用回退值，请在 GitHub Variables 中设置 LAST_ISSUE_NUMBER", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    get_latest_issue()
