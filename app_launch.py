# ✨ Newsletter 网页版入口
# 你只需要安装 gradio 后运行这个脚本，就能打开本地网页界面

import gradio as gr
import sys

# 导入核心函数
from newsletter_tool import (
    fetch_newsletter_text,
    generate_summary,
    save_to_notion,
)


def handle_newsletter(url):
    yield "⏳ 正在抓取文章内容..."
    full_text = fetch_newsletter_text(url)

    # 检查 fetch 是否返回错误（以 ⚠️ 开头）
    if full_text.startswith("⚠️"):
        yield f"❌ 抓取失败：{full_text}"
        return

    yield "🤖 正在生成 AI 摘要与翻译（预计 30-120 秒）..."
    try:
        summary_result = generate_summary(full_text)
    except Exception as e:
        yield f"❌ GPT 生成失败：{str(e)}"
        return

    yield "📝 正在写入 Notion..."
    try:
        save_to_notion(summary_result, url)
    except Exception as e:
        # Notion 失败不应丢失已生成的摘要
        yield f"⚠️ Notion 写入失败，但摘要已生成：\n\n{summary_result}\n\n---\n错误信息：{str(e)}"
        return

    yield summary_result


with gr.Blocks(title="The Batch 自动摘要工具") as demo:
    gr.Markdown("""
    # 📰 The Batch 自动摘要工具
    
    输入 Newsletter 链接，一键生成中英文摘要并写入 Notion。
    """)

    with gr.Row():
        with gr.Column(scale=3):
            url_input = gr.Textbox(
                label="Newsletter URL",
                placeholder="请输入链接，例如：https://www.deeplearning.ai/the-batch/issue-323/",
            )
            submit_btn = gr.Button("📥 提交并写入 Notion")
        with gr.Column(scale=5):
            output_md = gr.Markdown(label="🧠 AI 摘要与中文翻译")

    submit_btn.click(fn=handle_newsletter, inputs=url_input, outputs=output_md)

if __name__ == "__main__":
    demo.launch()
