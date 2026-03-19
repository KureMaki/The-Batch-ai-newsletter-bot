import os
from newsletter_tool import fetch_newsletter_text, save_to_notion, send_feishu_notification

url = os.environ['ISSUE_URL']
issue = os.environ['ISSUE_NUMBER']

print(f'抓取 Issue {issue}...')
text = fetch_newsletter_text(url)

if text.startswith('⚠️'):
    msg = f'❌ 抓取失败：{text}'
    print(msg)
    send_feishu_notification(False, issue, msg)
    exit(1)

summary = f'[调试模式] 测试摘要\n\n{text[:500]}...\n\n(这是调试模式生成的测试摘要)'

print('写入 Notion（调试模式）...')
try:
    save_to_notion(summary, url)
    send_feishu_notification(True, issue, '✅ 调试模式测试成功！')
    print('✅ 完成！')
except Exception as e:
    msg = f'⚠️ Notion 写入失败：{str(e)}'
    print(msg)
    send_feishu_notification(False, issue, msg)
    exit(1)
