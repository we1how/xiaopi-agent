#!/usr/bin/env python3
"""
growthclaw_western.py - GrowthClaw 国外增长/营销情报获取

信息差来源：
- Indie Hackers（独立开发者案例）
- Hacker News "Show HN"（产品发布）
- Substack（Newsletter趋势）

价值：国外增长案例在国内的复刻机会
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/agent-intelligence/growthclaw"

def fetch_indie_hackers():
    """获取 Indie Hackers 热门案例"""
    print("🚀 Indie Hackers...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "https://www.indiehackers.com/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        html = result.stdout
        
        # 提取案例
        cases = []
        
        # 匹配案例标题
        pattern = r'<a[^>]*href="(/product/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</a>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:8]:
            url_path = match[0]
            title = re.sub(r'<[^>]+>', '', match[1]).strip()
            title = ' '.join(title.split())
            
            if title:
                cases.append({
                    'title': title,
                    'url': f"https://www.indiehackers.com{url_path}",
                    'source': 'indie_hackers'
                })
        
        print(f"   ✅ {len(cases)} 个案例")
        return cases
        
    except Exception as e:
        print(f"   ❌ {e}")
        return []

def fetch_hn_show():
    """获取 Hacker News Show HN"""
    print("📰 Hacker News Show...")
    
    try:
        import urllib.request
        import ssl
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        url = "https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            projects = []
            for hit in data.get('hits', []):
                projects.append({
                    'title': hit.get('title', ''),
                    'url': hit.get('url', ''),
                    'points': hit.get('points', 0),
                    'comments': hit.get('num_comments', 0),
                    'source': 'hn_show'
                })
            
            print(f"   ✅ {len(projects)} 个项目")
            return projects
            
    except Exception as e:
        print(f"   ❌ {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 GrowthClaw Western Intelligence")
    print("   国外增长案例 → 国内复刻机会")
    print("=" * 60)
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_data = {
        'date': datetime.now().strftime("%Y%m%d"),
        'agent': 'growthclaw',
        'sources': {}
    }
    
    # 获取数据
    ih_cases = fetch_indie_hackers()
    if ih_cases:
        all_data['sources']['indie_hackers'] = ih_cases
    
    hn_projects = fetch_hn_show()
    if hn_projects:
        all_data['sources']['hn_show'] = hn_projects
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"western_{today}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    total = len(ih_cases) + len(hn_projects)
    print(f"\n✅ 已保存: {output_file}")
    print(f"   总计: {total} 条情报")
    
    # 输出洞察
    if ih_cases:
        print("\n💰 Indie Hackers 热门案例:")
        for i, case in enumerate(ih_cases[:3], 1):
            title = case['title'][:60] + '...' if len(case['title']) > 60 else case['title']
            print(f"   {i}. {title}")
    
    if hn_projects:
        print("\n🚀 Show HN 热门项目:")
        for i, proj in enumerate(hn_projects[:3], 1):
            title = proj['title'][:60] + '...' if len(proj['title']) > 60 else proj['title']
            print(f"   {i}. {title} (▲ {proj['points']})")

if __name__ == "__main__":
    main()
