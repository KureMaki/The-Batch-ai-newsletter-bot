from newsletter_tool import fetch_newsletter_text

# 测试
url = "https://www.deeplearning.ai/the-batch/issue-323/"
text = fetch_newsletter_text(url)
print("=== 抓取结果预览 ===\n")
print(text[:3000])
