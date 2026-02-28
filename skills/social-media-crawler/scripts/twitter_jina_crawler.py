#!/usr/bin/env python3
"""
twitter_jina_crawler.py - 使用 Jina Reader 获取 Twitter/X 内容

无需登录，无封号风险！
API: https://r.jina.ai/http://x.com/{username}

使用系统 curl 命令绕过 SSL 问题
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/social-media"

# 关注的 Twitter 账号列表（精简版）
TWITTER_SOURCES = [
    "sama",         # Sam Altman (OpenAI)
    "ylecun",       # Yann LeCun (Meta AI)
    "elonmusk",     # Elon Musk (xAI/Tesla)
    "naval",        # Naval Ravikant
    "paulg",        # Paul Graham (YC)
]

def fetch_twitter_user(username):
    """使用 curl 获取 Twitter 用户时间线"""
    url = f"https://r.jina.ai/http://x.com/{username}"
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "30", url],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def parse_tweets(content, username):
    """解析 Jina Reader 返回的内容，提取推文"""
    tweets = []
    
    # 检查是否是错误页面
    if "Something went wrong" in content or len(content) < 200:
        return tweets
    
    # 分割推文
    lines = content.split('\n')
    
    current_tweet = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行和标记
        if not line or line.startswith('![') or line.startswith('['):
            i += 1
            continue
        
        # 检测推文开始（日期格式）
        date_patterns = [
            r'\w{3}\s+\d{1,2},?\s+\d{4}',  # Jan 15, 2024
            r'\d{1,2}\s+\w+',                # 15 Jan
            r'\w+\s+\d{1,2}',                # Jan 15
        ]
        
        is_date = any(re.match(pattern, line) for pattern in date_patterns)
        
        if is_date and len(line) < 30:
            # 保存之前的推文
            if current_tweet and current_tweet.get('content'):
                tweets.append(current_tweet)
            
            # 开始新推文
            current_tweet = {
                'date': line,
                'content': '',
                'username': username
            }
            i += 1
            continue
        
        # 如果是推文内容，添加到当前推文
        if current_tweet is not None:
            # 过滤掉一些不需要的内容
            skip_prefixes = ['http', '@', 'Replying to', 'Quote', '---']
            if not any(line.startswith(p) for p in skip_prefixes) and len(line) > 5:
                if current_tweet['content']:
                    current_tweet['content'] += ' ' + line
                else:
                    current_tweet['content'] = line
        
        i += 1
    
    # 保存最后一条推文
    if current_tweet and current_tweet.get('content'):
        tweets.append(current_tweet)
    
    return tweets

def crawl_twitter_jina():
    """主爬取函数"""
    print("🐦 使用 Jina Reader 爬取 Twitter/X...")
    print("   优势: 无需登录，无封号风险\n")
    
    all_tweets = []
    sources_crawled = []
    
    for username in TWITTER_SOURCES:
        print(f"   获取 @{username}...", end=' ', flush=True)
        
        try:
            content = fetch_twitter_user(username)
            
            if content.startswith('Error') or len(content) < 500:
                print(f"❌ 失败")
                continue
            
            tweets = parse_tweets(content, username)
            
            # 过滤有效推文
            valid_tweets = [t for t in tweets if len(t['content']) > 30]
            
            print(f"✅ {len(valid_tweets)} 条")
            all_tweets.extend(valid_tweets[:3])  # 每个用户取前3条
            sources_crawled.append(username)
            
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
    
    # 保存结果
    today = datetime.now().strftime("%Y%m%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "twitter").mkdir(exist_ok=True)
    
    result = {
        "date": today,
        "platform": "twitter",
        "method": "jina_reader",
        "status": "success" if all_tweets else "no_data",
        "sources": sources_crawled,
        "tweets_count": len(all_tweets),
        "tweets": all_tweets
    }
    
    output_file = OUTPUT_DIR / f"twitter/trending_{today}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Twitter 数据已保存: {len(all_tweets)} 条推文")
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Twitter/X Crawler - Jina Reader 版")
    print("=" * 60)
    print()
    
    result = crawl_twitter_jina()
    
    # 显示热门推文
    if result.get('tweets'):
        print("\n🔥 热门推文 Top 5:")
        for i, tweet in enumerate(result['tweets'][:5], 1):
            content = tweet['content'][:70] + '...' if len(tweet['content']) > 70 else tweet['content']
            print(f"   {i}. @{tweet['username']}: {content}")
    else:
        print("\n⚠️ 未获取到推文，可能网络受限")
    
    print("\n" + "=" * 60)
    return result

if __name__ == "__main__":
    main()
