import os
from newsletter_tool import fetch_newsletter_text, gpt_summary_and_translation, save_to_notion, send_feishu_notification

url = os.environ['ISSUE_URL']
issue = os.environ['ISSUE_NUMBER']

print(f'抓取 Issue {issue}...')
text = fetch_newsletter_text(url)

if text.startswith('⚠️'):
    msg = f'❌ 抓取失败：{text}'
    print(msg)
    send_feishu_notification(False, issue, msg)
    exit(1)

print('生成摘要...')
summary = gpt_summary_and_translation(text)

print('写入 Notion...')
try:
    save_to_notion(summary, url)
    send_feishu_notification(True, issue, summary[:500])
    print('✅ 完成！')
except Exception as e:
    msg = f'⚠️ Notion 写入失败：{str(e)}'
    print(msg)
    send_feishu_notification(False, issue, msg)
    exit(1)
