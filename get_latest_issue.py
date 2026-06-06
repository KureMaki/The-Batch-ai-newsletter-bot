#!/usr/bin/env python
# coding: utf-8
"""
从 last_issue.txt 读取上次期号，向后探测新期号（不抓首页，规避 Cloudflare IP 封锁）。
探测成功后将新期号写回 last_issue.txt（由 CI 负责 commit）。
"""

import sys
import os
import requests
from pathlib import Path

ISSUE_URL_TEMPLATE = "https://www.deeplearning.ai/the-batch/issue-{}/"
LAST_ISSUE_FILE = Path(__file__).parent / "last_issue.txt"

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def _read_last_known() -> int:
    if LAST_ISSUE_FILE.exists():
        return int(LAST_ISSUE_FILE.read_text().strip())
    env_val = os.getenv("LAST_ISSUE_NUMBER", "").strip()
    if env_val:
        return int(env_val)
    raise ValueError("未找到 last_issue.txt，且未设置 LAST_ISSUE_NUMBER 环境变量")


def _is_accessible(url: str) -> bool:
    try:
        r = requests.get(url, timeout=10, headers=_BROWSER_HEADERS, allow_redirects=True)
        return r.status_code == 200 and "issue-" in r.url
    except Exception:
        return False


def get_latest_issue():
    try:
        last_known = _read_last_known()
    except Exception as e:
        msg = f"❌ 读取上次期号失败：{e}"
        print(msg, file=sys.stderr)
        _notify_feishu(msg)
        sys.exit(1)

    # 向后探测最多 3 期新期号
    found = None
    for offset in range(1, 4):
        candidate = last_known + offset
        url = ISSUE_URL_TEMPLATE.format(candidate)
        print(f"🔍 探测 issue-{candidate} ...", file=sys.stderr)
        if _is_accessible(url):
            found = (candidate, url)
            break

    # 没有新期号时，验证上次期号本身是否可访问（防止重复处理时静默失败）
    if found is None:
        url = ISSUE_URL_TEMPLATE.format(last_known)
        print(f"🔍 探测 issue-{last_known} (上次期号) ...", file=sys.stderr)
        if _is_accessible(url):
            found = (last_known, url)

    if found is None:
        msg = f"❌ 无法访问任何期号页面（从 issue-{last_known} 开始探测），网站可能已封锁 CI IP"
        print(msg, file=sys.stderr)
        _notify_feishu(msg)
        sys.exit(1)

    issue_number, issue_url = found
    print(f"✅ 找到期号: {issue_number}", file=sys.stderr)
    # 更新 last_issue.txt 供 CI commit
    LAST_ISSUE_FILE.write_text(f"{issue_number}\n")
    print(f"issue_number={issue_number}")
    print(f"issue_url={issue_url}")


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
