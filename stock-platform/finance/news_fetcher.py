"""
新闻获取模块
基于 newsRss.py 封装，支持多种RSS源
"""

import os
import json
import requests
import feedparser
import uuid
import re
import html
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def get_random_user_agent():
    """获取随机用户代理"""
    return random.choice(USER_AGENTS)


def clean_html_content(html_content: str) -> str:
    """使用BeautifulSoup清理HTML内容并提取纯文本"""
    if not html_content:
        return ""

    try:
        # 先解码HTML实体
        decoded_content = html.unescape(html_content)

        # 使用BeautifulSoup解析
        soup = BeautifulSoup(decoded_content, 'html.parser')

        # 移除不需要的元素
        for element in soup(['script', 'style', 'img', 'a', 'br', 'iframe', 'object']):
            element.decompose()

        # 获取纯净文本
        text = soup.get_text(separator='\n', strip=True)

        # 清理多余空格和空行
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)

        return text.strip()

    except Exception as e:
        print(f"HTML清理错误: {str(e)}")
        # 回退方法：使用正则表达式移除HTML标签
        return re.sub(r'<[^>]+>', '', html_content)


def fetch_rss_content(rss_url: str, max_retries: int = 3) -> Optional[str]:
    """直接获取RSS内容"""
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'application/rss+xml, application/xml; q=0.9, */*; q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
            }

            # 添加随机延迟
            time.sleep(random.uniform(0.5, 1.5))

            response = requests.get(rss_url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"HTTP错误: {response.status_code}")
                continue

            # 检查内容是否是RSS
            content = response.text.strip()
            if not content.startswith('<?xml') and '<rss' not in content and '<feed' not in content:
                print("响应内容不是有效的RSS XML")
                continue

            return content

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    return None


def parse_rss_feed(xml_content: str) -> Optional[feedparser.FeedParserDict]:
    """解析RSS XML内容"""
    try:
        feed = feedparser.parse(xml_content)

        if feed.bozo:
            print(f"解析警告: {feed.bozo_exception}")

            # 尝试修复常见实体问题
            if 'undefined entity' in str(feed.bozo_exception):
                fixed_content = xml_content.replace('&nbsp;', ' ')
                fixed_content = fixed_content.replace('&amp;', '&')
                fixed_content = fixed_content.replace('&lt;', '<')
                fixed_content = fixed_content.replace('&gt;', '>')
                feed = feedparser.parse(fixed_content)

        return feed

    except Exception as e:
        print(f"解析RSS失败: {str(e)}")
        return None


def parse_cls_entry(entry) -> Optional[Dict]:
    """解析财联社特定格式的新闻条目"""
    try:
        title = entry.get('title', '无标题')
        pub_date = entry.get('published', '未知时间')
        author = entry.get('author', '未知作者')
        link = entry.get('link', '')

        # 特殊处理description字段
        raw_description = entry.get('description', '')
        clean_description = clean_html_content(raw_description)

        # 提取新闻来源（财联社特定格式）
        source_match = re.search(r'财联社(\d+月\d+日)?[讯|电]', clean_description)
        source = source_match.group(0) if source_match else "财联社"

        # 提取新闻正文（去除来源行）
        content = re.sub(r'^财联社.*?[讯|电]', '', clean_description, count=1).strip()

        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'source': source,
            'pub_date': pub_date,
            'author': author,
            'link': link,
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        print(f"解析财联社条目失败: {e}")
        return None


def parse_generic_entry(entry) -> Optional[Dict]:
    """解析通用RSS新闻条目"""
    try:
        title = entry.get('title', '无标题')
        pub_date = entry.get('published', entry.get('updated', '未知时间'))
        author = entry.get('author', entry.get('creator', '未知作者'))
        link = entry.get('link', '')

        # 获取内容（优先使用content，其次description，最后summary）
        content = ''
        if 'content' in entry:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif 'description' in entry:
            content = entry.description
        elif 'summary' in entry:
            content = entry.summary

        clean_content = clean_html_content(content)

        # 提取摘要（前200字符）
        summary = clean_content[:200] + '...' if len(clean_content) > 200 else clean_content

        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': clean_content,
            'summary': summary,
            'source': entry.get('source', {}).get('title', '未知来源') if isinstance(entry.get('source'), dict) else '未知来源',
            'pub_date': pub_date,
            'author': author,
            'link': link,
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        print(f"解析通用条目失败: {e}")
        return None


class NewsFetcher:
    """新闻获取器"""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news_cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_from_url(self, url: str, parser: str = "generic", limit: int = 20) -> List[Dict]:
        """从URL获取新闻"""
        xml_content = fetch_rss_content(url)
        if not xml_content:
            return []

        feed = parse_rss_feed(xml_content)
        if not feed or not hasattr(feed, 'entries'):
            return []

        news_list = []
        for entry in feed.entries[:limit]:
            if parser == "cls":
                news = parse_cls_entry(entry)
            else:
                news = parse_generic_entry(entry)

            if news:
                news_list.append(news)

        return news_list

    def fetch_from_route(self, route: Dict, limit: int = 20) -> List[Dict]:
        """从路由配置获取新闻"""
        url = route.get("url", "")
        parser = route.get("parser", "generic")
        route_id = route.get("id", "unknown")

        news_list = self.fetch_from_url(url, parser=parser, limit=limit)

        # 添加路由ID
        for news in news_list:
            news['route_id'] = route_id

        return news_list

    def get_cache_file(self, route_id: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{route_id}_news.json")

    def load_cached_news(self, route_id: str, max_age_minutes: int = 5) -> List[Dict]:
        """加载缓存的新闻"""
        cache_file = self.get_cache_file(route_id)

        if not os.path.exists(cache_file):
            return []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # 检查缓存是否过期
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            age = (datetime.now(timezone.utc) - cached_time).total_seconds() / 60

            if age > max_age_minutes:
                return []

            return cached.get('news', [])

        except Exception as e:
            print(f"加载缓存失败: {e}")
            return []

    def save_cached_news(self, route_id: str, news: List[Dict]):
        """保存新闻到缓存"""
        cache_file = self.get_cache_file(route_id)

        try:
            cache_data = {
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'news': news
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def fetch_with_cache(self, route: Dict, limit: int = 20, use_cache: bool = True) -> List[Dict]:
        """带缓存的新闻获取"""
        route_id = route.get("id", "")

        if use_cache:
            cached = self.load_cached_news(route_id)
            if cached:
                return cached

        news = self.fetch_from_route(route, limit=limit)
        self.save_cached_news(route_id, news)
        return news

    def clear_cache(self, route_id: str = None):
        """清除缓存"""
        if route_id:
            cache_file = self.get_cache_file(route_id)
            if os.path.exists(cache_file):
                os.remove(cache_file)
        else:
            # 清除所有缓存
            for f in os.listdir(self.cache_dir):
                if f.endswith('_news.json'):
                    os.remove(os.path.join(self.cache_dir, f))
