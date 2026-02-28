#!/usr/bin/env python3
"""
twitter_crawler.py - Twitter/X 数据爬取

使用 Playwright 浏览器自动化登录并获取趋势话题
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/social-media"
CREDENTIALS_FILE = WORKSPACE / ".credentials/platform-accounts.json"

async def crawl_twitter_trending():
    """
    爬取 Twitter/X 趋势话题
    
    需要: 账号 weHow27844 / 密码 13580lwh
    """
    print("🐦 开始爬取 Twitter/X 趋势话题...")
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("   安装 playwright...")
        os.system("pip install playwright -q")
        os.system("playwright install chromium")
        from playwright.async_api import async_playwright
    
    trending_topics = []
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # 访问 Twitter
            print("   访问 Twitter/X...")
            await page.goto("https://x.com", wait_until="networkidle", timeout=30000)
            
            # 检查是否已经登录
            if await page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                print("   已检测到登录状态")
            else:
                print("   需要登录...")
                # 点击登录按钮
                await page.click("text=Sign in")
                await page.wait_for_selector("input[name='text']", timeout=10000)
                
                # 输入用户名
                await page.fill("input[name='text']", "weHow27844")
                await page.click("text=Next")
                
                # 输入密码
                await page.wait_for_selector("input[name='password']", timeout=10000)
                await page.fill("input[name='password']", "13580lwh")
                await page.click("text=Log in")
                
                # 等待登录完成
                await page.wait_for_load_state("networkidle", timeout=30000)
                print("   登录成功")
            
            # 获取趋势话题
            print("   获取趋势话题...")
            await page.goto("https://x.com/explore/tabs/trending", wait_until="networkidle", timeout=30000)
            
            # 等待趋势加载
            await page.wait_for_timeout(3000)
            
            # 提取趋势话题
            trend_elements = await page.query_selector_all("[data-testid='trend']")
            
            for i, elem in enumerate(trend_elements[:10]):  # 取前10个
                try:
                    # 获取话题名称
                    name_elem = await elem.query_selector("span")
                    if name_elem:
                        name = await name_elem.inner_text()
                        
                        # 获取帖子数量（如果有）
                        count_elem = await elem.query_selector("span:nth-child(2)")
                        tweet_count = await count_elem.inner_text() if count_elem else ""
                        
                        trending_topics.append({
                            "rank": i + 1,
                            "name": name,
                            "tweet_count": tweet_count,
                            "category": "Trending"
                        })
                except Exception as e:
                    print(f"   提取趋势失败: {e}")
            
            await browser.close()
            
        except Exception as e:
            print(f"   爬取过程出错: {e}")
            await browser.close()
    
    # 保存结果
    today = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"twitter/trending_{today}.json"
    
    result = {
        "date": today,
        "platform": "twitter",
        "status": "success" if trending_topics else "no_data",
        "trending_count": len(trending_topics),
        "trending_topics": trending_topics
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Twitter 数据已保存: {len(trending_topics)} 个趋势话题")
    return result

def main():
    """主函数"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "twitter").mkdir(exist_ok=True)
    
    # 运行异步爬取
    result = asyncio.run(crawl_twitter_trending())
    
    # 显示结果
    if result.get("trending_topics"):
        print("\n🔥 Twitter/X 热门趋势 Top 5:")
        for trend in result["trending_topics"][:5]:
            print(f"   {trend['rank']}. {trend['name']}")
    
    return result

if __name__ == "__main__":
    main()
