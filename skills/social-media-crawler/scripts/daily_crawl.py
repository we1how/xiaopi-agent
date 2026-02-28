#!/usr/bin/env python3
"""
daily_crawl.py - 每日社交媒体数据爬取

支持平台:
- xhs (小红书): 热门笔记、关键词搜索

输出格式: JSON，供 GrowthClaw 分析使用
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# 配置路径
WORKSPACE = Path.home() / ".openclaw/workspace"
CRAWLER_DIR = WORKSPACE / "tools/MediaCrawler"
OUTPUT_DIR = WORKSPACE / "data/social-media"

def ensure_dirs():
    """确保目录存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "xiaohongshu").mkdir(exist_ok=True)
    (OUTPUT_DIR / "twitter").mkdir(exist_ok=True)

def crawl_xiaohongshu():
    """
    爬取小红书热门数据
    """
    print("📕 开始爬取小红书...")
    
    if not CRAWLER_DIR.exists():
        print("❌ MediaCrawler 未安装")
        return None
    
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"xiaohongshu/hot_notes_{today}.json"
    
    # 切换目录并运行 MediaCrawler
    os.chdir(CRAWLER_DIR)
    
    # 关键词列表（从配置文件读取）
    keywords = ["投资", "理财", "AI", "人工智能", "科技", "副业", "赚钱", "读书", "成长", "效率", "编程", "Python", "量化"]
    
    all_notes = []
    
    for keyword in keywords[:3]:  # 限制前3个关键词，避免请求过多
        print(f"   搜索关键词: {keyword}")
        
        try:
            # 运行 MediaCrawler
            result = subprocess.run(
                ["uv", "run", "main.py", "--platform", "xhs", "--lt", "qrcode", "--type", "search"],
                timeout=120,
                capture_output=True,
                text=True,
                env={**os.environ, "KEYWORDS": keyword}
            )
            
            # 检查输出目录是否有新数据
            # MediaCrawler 默认输出到 data/xhs/ 目录
            crawler_output = CRAWLER_DIR / "data" / "xhs"
            if crawler_output.exists():
                # 读取最新生成的数据文件
                json_files = sorted(crawler_output.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                if json_files:
                    try:
                        with open(json_files[0], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for note in data[:5]:  # 每个关键词取前5条
                                    note['keyword'] = keyword
                                    all_notes.append(note)
                    except Exception as e:
                        print(f"   读取数据失败: {e}")
                        
        except subprocess.TimeoutExpired:
            print(f"   关键词 '{keyword}' 爬取超时")
        except Exception as e:
            print(f"   关键词 '{keyword}' 爬取失败: {e}")
    
    # 构建结果
    result = {
        "date": today,
        "platform": "xiaohongshu",
        "keywords": keywords[:3],
        "notes_count": len(all_notes),
        "notes": all_notes[:20],  # 限制总条数
        "status": "success" if all_notes else "partial"
    }
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 小红书数据已保存: {len(all_notes)} 条笔记")
    return result

def crawl_xiaohongshu_simple():
    """
    简化版：直接读取 MediaCrawler 已有的数据结构
    """
    print("📕 整理小红书数据...")
    
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"xiaohongshu/hot_notes_{today}.json"
    
    # 检查 MediaCrawler 输出目录 (实际在 data/xhs/json/ 下)
    crawler_output = CRAWLER_DIR / "data" / "xhs" / "json"
    
    all_notes = []
    keywords_searched = []
    
    if crawler_output.exists():
        # 读取所有 JSON 文件（最近24小时内）
        for json_file in crawler_output.glob("*.json"):
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            if (datetime.now() - mtime).days < 1:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            # 从 source_keyword 字段读取关键词，或从文件名推断
                            keyword = "未知"
                            # 获取第一条数据的 source_keyword
                            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                keyword = data[0].get('source_keyword', '未知')
                            keywords_searched.append(keyword)
                            
                            for note in data[:10]:  # 每个文件取前10条
                                if isinstance(note, dict):
                                    # 跳过评论数据（有 comment_id 字段的是评论）
                                    if 'comment_id' in note:
                                        continue
                                    note['keyword'] = keyword
                                    note['source_file'] = json_file.name
                                    all_notes.append(note)
                except Exception as e:
                    print(f"   读取文件失败 {json_file}: {e}")
    
    # 去重（按 note_id）
    seen_ids = set()
    unique_notes = []
    for note in all_notes:
        note_id = note.get('note_id') or note.get('id') or str(hash(str(note)))
        if note_id not in seen_ids:
            seen_ids.add(note_id)
            unique_notes.append(note)
    
    # 按点赞数排序（转换为整数）
    def get_likes(note):
        likes = note.get('liked_count', 0) or note.get('likes', 0) or 0
        try:
            return int(likes)
        except (ValueError, TypeError):
            return 0
    
    sorted_notes = sorted(unique_notes, key=get_likes, reverse=True)[:30]
    
    result = {
        "date": today,
        "platform": "xiaohongshu",
        "keywords": list(set(keywords_searched)),
        "notes_count": len(sorted_notes),
        "notes": sorted_notes,
        "status": "success" if sorted_notes else "no_data"
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 小红书数据已整理: {len(sorted_notes)} 条笔记 (来源: {len(set(keywords_searched))} 个关键词)")
    return result

def crawl_twitter():
    """
    Twitter/X 使用 Jina Reader 获取（无需登录）
    """
    print("🐦 Twitter/X 使用 Jina Reader 爬取...")
    
    # 调用 twitter_jina_crawler.py
    import subprocess
    
    script_path = WORKSPACE / "skills/social-media-crawler/scripts/twitter_jina_crawler.py"
    
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=WORKSPACE / "skills/social-media-crawler"
        )
        
        # 读取生成的结果文件
        today = datetime.now().strftime("%Y%m%d")
        output_file = OUTPUT_DIR / f"twitter/trending_{today}.json"
        
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "date": today,
                "platform": "twitter",
                "status": "error",
                "message": "输出文件未生成"
            }
            
    except Exception as e:
        today = datetime.now().strftime("%Y%m%d")
        return {
            "date": today,
            "platform": "twitter",
            "status": "error",
            "error": str(e)
        }

def generate_report(xhs_data, tw_data):
    """生成每日爬取报告"""
    report = {
        "date": datetime.now().isoformat(),
        "summary": {
            "xiaohongshu": {
                "status": xhs_data.get("status", "unknown"),
                "notes_count": xhs_data.get("notes_count", 0)
            },
            "twitter": tw_data.get("status", "unknown")
        },
        "output_dir": str(OUTPUT_DIR)
    }
    
    report_file = OUTPUT_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Social Media Daily Crawl")
    print("=" * 60)
    
    ensure_dirs()
    
    # 检查 MediaCrawler 目录
    if not CRAWLER_DIR.exists():
        print("❌ MediaCrawler 未安装，请先运行 install.sh")
        return
    
    # 爬取小红书（简化版：读取已有数据）
    xhs_data = crawl_xiaohongshu_simple()
    print()
    
    # Twitter 占位
    tw_data = crawl_twitter()
    print()
    
    # 生成报告
    report = generate_report(xhs_data, tw_data)
    
    print("=" * 60)
    print("📊 爬取完成")
    print(f"   小红书: {report['summary']['xiaohongshu']['status']} ({report['summary']['xiaohongshu']['notes_count']} 条)")
    print(f"   Twitter: {report['summary']['twitter']}")
    print(f"   数据目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 输出今日热门（如果有数据）
    if xhs_data.get('notes'):
        print("\n🔥 今日小红书热门笔记 Top 3:")
        for i, note in enumerate(xhs_data['notes'][:3], 1):
            title = note.get('title', '')[:30] + '...' if len(note.get('title', '')) > 30 else note.get('title', '')
            likes = note.get('liked_count', 0) or note.get('likes', 0)
            print(f"   {i}. {title} (❤️ {likes})")
    
    return report

if __name__ == "__main__":
    main()
