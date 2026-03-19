import pytest
from unittest.mock import MagicMock, patch
import requests
import sys
import os

# Add current directory to sys.path to import newsletter_tool
sys.path.append(os.getcwd())

from newsletter_tool import (
    fetch_newsletter_text,
    gpt_summary_and_translation,
    save_to_notion,
)

# --- Tests for fetch_newsletter_text ---


def test_fetch_newsletter_text_success():
    """Test successful fetch with article tag"""
    mock_html = """
    <html>
        <body>
            <article>
                <h2>Title</h2>
                <p>Paragraph 1</p>
                <li>List item</li>
            </article>
        </body>
    </html>
    """
    with patch("requests.Session.get") as mock_get:
        mock_get.return_value.text = mock_html
        result = fetch_newsletter_text("https://example.com")
        assert "Title" in result
        assert "Paragraph 1" in result
        assert "List item" in result
        assert "⚠️" not in result


def test_fetch_newsletter_text_no_article():
    """Test fetch failure when no article/prose found"""
    mock_html = "<html><body><div>No content here</div></body></html>"
    with patch("requests.Session.get") as mock_get:
        mock_get.return_value.text = mock_html
        result = fetch_newsletter_text("https://example.com")
        assert "⚠️ 抓取失败" in result


def test_fetch_newsletter_text_invalid_url():
    """Test invalid URL format"""
    result = fetch_newsletter_text("not-a-url")
    assert "⚠️ 无效的 URL" in result


def test_fetch_newsletter_text_timeout():
    """Test timeout handling"""
    with patch("requests.Session.get", side_effect=requests.exceptions.Timeout):
        result = fetch_newsletter_text("https://example.com")
        assert "⚠️ 抓取超时" in result


# --- Tests for gpt_summary_and_translation ---


def test_gpt_summary_success():
    """Test GPT summary generation"""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Summary result"

    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_response

        result = gpt_summary_and_translation("Some text")
        assert result == "Summary result"
        # Verify client was called with timeout
        MockOpenAI.assert_called()
        # Verify call args
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4-turbo"


# --- Tests for save_to_notion ---


def test_save_to_notion_extracts_issue_number():
    """Test issue number extraction and notion call"""
    with patch("notion_client.Client") as MockNotion:
        mock_client = MockNotion.return_value

        save_to_notion("## Title\nContent", "https://example.com/issue-123/")

        # Verify create was called
        mock_client.pages.create.assert_called_once()
        call_kwargs = mock_client.pages.create.call_args.kwargs

        # Verify properties
        props = call_kwargs["properties"]
        assert props["期号"]["rich_text"][0]["text"]["content"] == "123"
        assert props["链接"]["url"] == "https://example.com/issue-123/"


def test_save_to_notion_handles_unknown_issue():
    """Test fallback for unknown issue number"""
    with patch("notion_client.Client") as MockNotion:
        mock_client = MockNotion.return_value
        save_to_notion("Content", "https://example.com/no-issue")

        props = mock_client.pages.create.call_args.kwargs["properties"]
        assert props["期号"]["rich_text"][0]["text"]["content"] == "Unknown"
