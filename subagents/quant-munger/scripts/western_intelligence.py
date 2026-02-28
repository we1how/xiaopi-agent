#!/usr/bin/env python3
"""
quant_munger_western.py - Quant-Munger 国外量化情报获取

信息差来源：
- Arxiv q-fin（学术前沿）
- SSRN（工作论文）
- Quantpedia（策略库）

价值：国外量化策略在国内市场的应用机会
"""

import json
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/agent-intelligence/quant-munger"

def fetch_arxiv_qfin():
    """获取 Arxiv 量化金融最新论文"""
    print("📊 Arxiv q-fin 最新论文...")
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.CP+OR+cat:q-fin.PM+OR+cat:q-fin.ST&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            xml_data = response.read().decode('utf-8')
            
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:id', ns)
                published = entry.find('atom:published', ns)
                
                if title is not None:
                    papers.append({
                        'title': title.text.strip() if title.text else '',
                        'summary': summary.text[:300] + '...' if summary is not None and summary.text else '',
                        'url': link.text if link is not None else '',
                        'published': published.text[:10] if published is not None else '',
                        'source': 'arxiv_qfin'
                    })
            
            print(f"   ✅ {len(papers)} 篇论文")
            return papers
            
    except Exception as e:
        print(f"   ❌ {e}")
        return []

def fetch_quantpedia_strategies():
    """获取 Quantpedia 最新策略（通过页面抓取）"""
    print("📈 Quantpedia 策略...")
    # Quantpedia 需要登录或 API Key，这里记录待实现
    print("   ⏸️ 需要 API Key")
    return []

def main():
    """主函数"""
    print("=" * 60)
    print("📊 Quant-Munger Western Intelligence")
    print("   国外量化金融情报 → 国内市场机会")
    print("=" * 60)
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_data = {
        'date': datetime.now().strftime("%Y%m%d"),
        'agent': 'quant-munger',
        'sources': {}
    }
    
    # 获取数据
    arxiv_papers = fetch_arxiv_qfin()
    if arxiv_papers:
        all_data['sources']['arxiv'] = arxiv_papers
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"western_{today}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存: {output_file}")
    print(f"   总计: {len(arxiv_papers)} 条情报")
    
    # 输出洞察
    if arxiv_papers:
        print("\n🔥 今日量化论文 Top 3:")
        for i, paper in enumerate(arxiv_papers[:3], 1):
            title = paper['title'][:60] + '...' if len(paper['title']) > 60 else paper['title']
            print(f"   {i}. {title}")

if __name__ == "__main__":
    main()
