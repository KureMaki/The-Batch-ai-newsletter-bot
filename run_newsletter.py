import os
from newsletter_tool import fetch_newsletter_text, generate_summary, save_to_notion, send_notification

url = os.environ['ISSUE_URL']
issue = os.environ['ISSUE_NUMBER']

print(f'抓取 Issue {issue}...')
text = fetch_newsletter_text(url)

if text.startswith('⚠️'):
    msg = f'❌ 抓取失败：{text}'
    print(msg)
    send_notification(False, issue, msg)
    exit(1)

print('生成摘要...')
summary = generate_summary(text)

print('写入 Notion...')
try:
    save_to_notion(summary, url)
    send_notification(True, issue, None, summary)
    print('✅ 完成！')
except Exception as e:
    msg = f'⚠️ Notion 写入失败：{str(e)}'
    print(msg)
    send_notification(False, issue, msg)
    exit(1)
