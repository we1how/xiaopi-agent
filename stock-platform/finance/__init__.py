"""
Finance模块 - 财经新闻聚合与AI分析

包含：
- rss_manager: RSS路由管理
- news_fetcher: 新闻获取
- prompt_templates: Prompt模板管理
- ai_chat: AI聊天组件
- finance_page: 主页面
"""

from finance.rss_manager import RSSManager
from finance.news_fetcher import NewsFetcher
from finance.prompt_templates import PromptManager
from finance.ai_chat import AIChatComponent
from finance.finance_page import render_finance_page

__all__ = [
    'RSSManager',
    'NewsFetcher',
    'PromptManager',
    'AIChatComponent',
    'render_finance_page'
]
