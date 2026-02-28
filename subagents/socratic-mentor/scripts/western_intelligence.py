#!/usr/bin/env python3
"""
socratic_mentor_western.py - Socratic-Mentor 国外成长/思维情报获取

信息差来源：
- Farnam Street（决策/思维模型）
- Wait But Why（深度长文）
- LessWrong（理性思维）

价值：国外前沿思维模型的本土化应用
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/agent-intelligence/socratic-mentor"

def fetch_farnam_street():
    """获取 Farnam Street 最新文章"""
    print("🧠 Farnam Street...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "https://fs.blog/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        html = result.stdout
        
        # 提取文章标题和链接
        import re
        articles = []
        
        # 匹配文章卡片
        pattern = r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?</h2>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:5]:
            url = match[0]
            title = re.sub(r'<[^>]+>', '', match[1]).strip()
            title = ' '.join(title.split())
            
            if title and url:
                articles.append({
                    'title': title,
                    'url': url if url.startswith('http') else f"https://fs.blog{url}",
                    'source': 'farnam_street'
                })
        
        print(f"   ✅ {len(articles)} 篇文章")
        return articles
        
    except Exception as e:
        print(f"   ❌ {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("🧠 Socratic-Mentor Western Intelligence")
    print("   国外思维模型 → 个人成长应用")
    print("=" * 60)
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_data = {
        'date': datetime.now().strftime("%Y%m%d"),
        'agent': 'socratic-mentor',
        'sources': {}
    }
    
    # 获取数据
    fs_articles = fetch_farnam_street()
    if fs_articles:
        all_data['sources']['farnam_street'] = fs_articles
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"western_{today}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存: {output_file}")
    print(f"   总计: {len(fs_articles)} 条情报")
    
    # 输出洞察
    if fs_articles:
        print("\n📝 今日思维模型文章:")
        for i, article in enumerate(fs_articles[:3], 1):
            title = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
            print(f"   {i}. {title}")

if __name__ == "__main__":
    main()
