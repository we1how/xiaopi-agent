#!/usr/bin/env python3
"""
twitter_api_test.py - 测试 Twitter API Client

使用账号密码获取趋势话题
"""

import json
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw/workspace"
OUTPUT_DIR = WORKSPACE / "data/social-media"

def test_twitter_login():
    """测试 Twitter 登录"""
    print("🐦 测试 Twitter/X API...")
    
    try:
        from twitter.account import Account
        
        # 使用账号密码登录
        # 注意：首次登录可能需要验证码
        print("   尝试登录...")
        print("   账号: weHow27844")
        
        # 尝试不同方式登录
        # 方式1: 仅用用户名密码
        account = Account(
            username="weHow27844",
            password="13580lwh"
        )
        
        print("   登录成功!")
        
        # 获取趋势话题
        print("   获取趋势话题...")
        trends = account.trends()
        
        print(f"   获取到 {len(trends)} 个趋势")
        
        # 保存结果
        today = datetime.now().strftime("%Y%m%d")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "twitter").mkdir(exist_ok=True)
        
        result = {
            "date": today,
            "platform": "twitter",
            "status": "success",
            "trending_topics": trends
        }
        
        output_file = OUTPUT_DIR / f"twitter/trending_{today}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存: {output_file}")
        return result
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        
        # 保存错误状态
        today = datetime.now().strftime("%Y%m%d")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "twitter").mkdir(exist_ok=True)
        
        result = {
            "date": today,
            "platform": "twitter",
            "status": "error",
            "error": str(e)
        }
        
        output_file = OUTPUT_DIR / f"twitter/trending_{today}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result

if __name__ == "__main__":
    test_twitter_login()
