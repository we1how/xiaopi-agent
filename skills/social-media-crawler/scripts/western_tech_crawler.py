#!/usr/bin/env python3
"""
western_tech_crawler.py - 国外高质量科技信息源爬取

聚焦信息差优势：国外优质内容 → 国内洞察

数据源：
1. Hacker News (API) - 技术圈风向标
2. GitHub Trending - 开源趋势
3. Arxiv (cs.AI) - 前沿论文

优势：
- 无需登录
- 高质量、高浓度信息
- 与国内形成信息差
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/social-media"

def fetch_hackernews():
    """
    获取 Hacker News 首页热点
    
    API: https://hn.algolia.com/api/v1/search?tags=front_page
    
    特点：
    - 技术圈最权威的风向标
    - 评论区质量极高
    - 比国内技术社区领先1-3天
    """
    print("📰 获取 Hacker News 热点...")
    
    try:
        import urllib.request
        import ssl
        
        # 禁用 SSL 验证（某些环境需要）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            stories = []
            for hit in data.get('hits', []):
                stories.append({
                    'title': hit.get('title', ''),
                    'url': hit.get('url', ''),
                    'author': hit.get('author', ''),
                    'points': hit.get('points', 0),
                    'comments': hit.get('num_comments', 0),
                    'created_at': hit.get('created_at', ''),
                    'source': 'hackernews'
                })
            
            print(f"   ✅ 获取 {len(stories)} 条热点")
            return stories
            
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_github_trending():
    """
    获取 GitHub Python 趋势项目
    
    特点：
    - 开源技术风向标
    - 发现新工具、新框架
    - 比国内技术媒体早1-2周
    """
    print("⭐ 获取 GitHub Trending...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "https://github.com/trending/python"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        html = result.stdout
        
        # 使用更可靠的解析
        import re
        repos = []
        
        # 匹配文章/仓库卡片
        # GitHub trending 页面结构：article > h2 > a[href="/owner/repo"]
        article_pattern = r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>.*?<h2[^>]*>.*?<a[^>]*href="(/[^/"]+/[^/"]+)"[^>]*>.*?</a>.*?</h2>.*?<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>.*?</article>'
        matches = re.findall(article_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:10]:
            repo_path = match[0].strip()
            # 清理描述文字
            desc = re.sub(r'<[^>]+>', '', match[1]).strip() if match[1] else ''
            desc = ' '.join(desc.split())[:100]  # 清理空白，限制长度
            
            repos.append({
                'name': repo_path.strip('/'),
                'url': f"https://github.com{repo_path}",
                'description': desc,
                'source': 'github'
            })
        
        # 如果没匹配到，尝试备用模式
        if not repos:
            # 简单的 href 匹配
            simple_pattern = r'href="(/[\w-]+/[\w.-]+)"'
            paths = re.findall(simple_pattern, html)
            seen = set()
            for path in paths:
                if path not in seen and not any(x in path for x in ['github.com', '/site/']):
                    seen.add(path)
                    repos.append({
                        'name': path.strip('/'),
                        'url': f"https://github.com{path}",
                        'description': '',
                        'source': 'github'
                    })
                    if len(repos) >= 10:
                        break
        
        print(f"   ✅ 获取 {len(repos)} 个趋势项目")
        return repos
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_arxiv_ai():
    """
    获取 Arxiv AI 领域最新论文
    
    特点：
    - 比正式发表早6-12个月
    - 顶级研究机构首选发布渠道
    - 国内很少系统跟踪
    """
    print("📄 获取 Arxiv AI 论文...")
    
    try:
        import urllib.request
        import ssl
        from xml.etree import ElementTree as ET
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Arxiv API: 获取最近3天的 cs.AI 论文
        url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            xml_data = response.read().decode('utf-8')
            
            # 解析 XML
            root = ET.fromstring(xml_data)
            
            # Arxiv 使用命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:link[@type="text/html"]', ns)
                published = entry.find('atom:published', ns)
                
                if title is not None:
                    papers.append({
                        'title': title.text.strip() if title.text else '',
                        'summary': summary.text[:200] + '...' if summary is not None and summary.text else '',
                        'url': link.get('href', '') if link is not None else '',
                        'published': published.text[:10] if published is not None else '',
                        'source': 'arxiv'
                    })
            
            print(f"   ✅ 获取 {len(papers)} 篇论文")
            return papers
            
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("🌍 Western Tech Intelligence - 国外科技情报")
    print("=" * 60)
    print("   聚焦信息差优势：国外高质量 → 国内洞察\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "western").mkdir(exist_ok=True)
    
    # 收集所有数据
    all_data = {
        'date': datetime.now().strftime("%Y%m%d"),
        'collected_at': datetime.now().isoformat(),
        'sources': {}
    }
    
    # 1. Hacker News
    hn_stories = fetch_hackernews()
    if hn_stories:
        all_data['sources']['hackernews'] = {
            'count': len(hn_stories),
            'items': hn_stories
        }
    print()
    
    # 2. GitHub Trending
    gh_repos = fetch_github_trending()
    if gh_repos:
        all_data['sources']['github'] = {
            'count': len(gh_repos),
            'items': gh_repos
        }
    print()
    
    # 3. Arxiv AI
    arxiv_papers = fetch_arxiv_ai()
    if arxiv_papers:
        all_data['sources']['arxiv'] = {
            'count': len(arxiv_papers),
            'items': arxiv_papers
        }
    print()
    
    # 保存数据
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"western/intelligence_{today}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    # 输出摘要
    print("=" * 60)
    print("📊 采集完成")
    print(f"   Hacker News: {len(hn_stories)} 条")
    print(f"   GitHub: {len(gh_repos)} 个")
    print(f"   Arxiv: {len(arxiv_papers)} 篇")
    print(f"   保存位置: {output_file}")
    print("=" * 60)
    
    # 输出热门内容
    if hn_stories:
        print("\n🔥 Hacker News Top 3:")
        for i, story in enumerate(hn_stories[:3], 1):
            print(f"   {i}. {story['title'][:50]}... (▲ {story['points']})")
    
    if gh_repos:
        print("\n⭐ GitHub Trending Top 3:")
        for i, repo in enumerate(gh_repos[:3], 1):
            print(f"   {i}. {repo['name']}")
    
    return all_data

if __name__ == "__main__":
    main()
