#!/usr/bin/env python3
"""
western_intelligence_summary.py - 汇总所有 Agent 的国外情报

由 musk-orchestrator 调用，生成每日国外情报简报
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
DATA_DIR = WORKSPACE / "data/agent-intelligence"
AGENTS = ["quant-munger", "product-engineer", "socratic-mentor", "growthclaw"]

def collect_agent_intelligence(agent_name):
    """收集单个 Agent 的国外情报"""
    agent_dir = DATA_DIR / agent_name
    if not agent_dir.exists():
        return None
    
    today = datetime.now().strftime("%Y%m%d")
    intel_file = agent_dir / f"western_{today}.json"
    
    if not intel_file.exists():
        return None
    
    try:
        with open(intel_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def main():
    """主函数"""
    print("=" * 70)
    print("🌍 国外情报汇总 - Western Intelligence Summary")
    print("   信息差优势：国外高质量 → 国内应用")
    print("=" * 70)
    print()
    
    all_intelligence = {}
    
    for agent in AGENTS:
        intel = collect_agent_intelligence(agent)
        if intel:
            all_intelligence[agent] = intel
    
    if not all_intelligence:
        print("⚠️ 暂无国外情报数据")
        print("   提示：各 Agent 需运行 scripts/western_intelligence.py")
        return
    
    # 输出汇总
    for agent, intel in all_intelligence.items():
        emoji = {
            "quant-munger": "📊",
            "product-engineer": "⚡",
            "socratic-mentor": "🧠",
            "growthclaw": "🚀"
        }.get(agent, "📌")
        
        print(f"{emoji} @{agent}")
        print("-" * 70)
        
        sources = intel.get('sources', {})
        if not sources:
            print("   暂无数据\n")
            continue
        
        for source_name, items in sources.items():
            if isinstance(items, list):
                print(f"   📌 {source_name}: {len(items)} 条")
                for i, item in enumerate(items[:3], 1):
                    title = item.get('title', '')
                    if title:
                        title = title[:50] + '...' if len(title) > 50 else title
                        print(f"      {i}. {title}")
        
        print()
    
    print("=" * 70)
    print("💡 信息差分析建议：")
    print("   1. 对比国内外对同一技术的关注度差异")
    print("   2. 识别国外热门但国内尚未关注的机会点")
    print("   3. 评估国外策略/工具在国内的适用性")
    print("=" * 70)

if __name__ == "__main__":
    main()
