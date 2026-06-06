#!/usr/bin/env python
# coding: utf-8
"""
获取最新期号。
抓取顺序：Jina AI Reader（绕过 Cloudflare）→ 退出并报警。
解析基准：last_issue.txt，成功后写回供 CI commit。
"""

import re
import sys
import os
import requests
from pathlib import Path

ISSUE_URL_TEMPLATE = "https://www.deeplearning.ai/the-batch/issue-{}/"
JINA_BASE = "https://r.jina.ai/https://www.deeplearning.ai/the-batch/"
LAST_ISSUE_FILE = Path(__file__).parent / "last_issue.txt"


def _read_last_known() -> int:
    if LAST_ISSUE_FILE.exists():
        return int(LAST_ISSUE_FILE.read_text().strip())
    env_val = os.getenv("LAST_ISSUE_NUMBER", "").strip()
    if env_val:
        return int(env_val)
    raise ValueError("未找到 last_issue.txt，且未设置 LAST_ISSUE_NUMBER 环境变量")


def _fetch_via_jina(last_known: int) -> tuple[int, str] | None:
    """通过 Jina AI Reader 抓取首页，解析最新期号。"""
    try:
        print("🌐 通过 Jina AI Reader 抓取首页...", file=sys.stderr)
        resp = requests.get(
            JINA_BASE,
            timeout=30,
            headers={"Accept": "text/plain", "X-No-Cache": "true"},
        )
        resp.raise_for_status()

        matches = re.findall(r"issue-(\d+)", resp.text)
        if not matches:
            raise ValueError("Jina 返回内容中未找到任何 issue-XXX 链接")

        candidates = sorted(set(int(m) for m in matches), reverse=True)
        # 只取比上次期号更新或相同的期号
        candidates = [c for c in candidates if c >= last_known]
        if not candidates:
            raise ValueError(f"Jina 返回的期号均早于上次期号 {last_known}")

        latest = candidates[0]
        return latest, ISSUE_URL_TEMPLATE.format(latest)

    except Exception as e:
        print(f"⚠️  Jina 失败：{e}", file=sys.stderr)
        return None


def get_latest_issue():
    try:
        last_known = _read_last_known()
    except Exception as e:
        msg = f"❌ 读取上次期号失败：{e}"
        print(msg, file=sys.stderr)
        _notify_feishu(msg)
        sys.exit(1)

    result = _fetch_via_jina(last_known)

    if result is None:
        msg = f"❌ 无法获取最新期号（上次：{last_known}），Jina AI Reader 请求失败"
        print(msg, file=sys.stderr)
        _notify_feishu(msg)
        sys.exit(1)

    issue_number, issue_url = result
    LAST_ISSUE_FILE.write_text(f"{issue_number}\n")
    print(f"✅ 找到期号: {issue_number}", file=sys.stderr)
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
