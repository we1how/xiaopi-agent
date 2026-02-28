#!/usr/bin/env python3
"""
test_login.py - 测试平台登录

用法:
    python test_login.py --platform xhs      # 测试小红书
    python test_login.py --platform twitter  # 测试 Twitter
"""

import argparse
import sys
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
CRAWLER_DIR = WORKSPACE / "tools/MediaCrawler"

def test_xiaohongshu():
    """测试小红书登录"""
    print("📕 测试小红书登录...")
    print("   登录方式: 二维码")
    print("   首次登录需要手动扫码")
    
    if not CRAWLER_DIR.exists():
        print("❌ MediaCrawler 未安装")
        return False
    
    import subprocess
    import os
    
    os.chdir(CRAWLER_DIR)
    
    # 运行 MediaCrawler 的登录测试
    try:
        result = subprocess.run(
            ["uv", "run", "main.py", "--platform", "xhs", "--lt", "qrcode", "--type", "search"],
            timeout=60,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✅ 小红书登录成功")
            return True
    except subprocess.TimeoutExpired:
        print("⏱️  登录超时（可能需要扫码）")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
    
    return False

def test_twitter():
    """测试 Twitter 登录"""
    print("🐦 测试 Twitter 登录...")
    print("   登录方式: 账号密码")
    
    # 读取凭证
    cred_file = WORKSPACE / ".credentials/platform-accounts.md"
    if not cred_file.exists():
        print("❌ 凭证文件不存在")
        return False
    
    print("✅ 凭证文件存在")
    print("   注意: Twitter 需要额外的 API 配置")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="测试社交媒体平台登录")
    parser.add_argument("--platform", choices=["xhs", "twitter", "all"], 
                       default="all", help="测试平台")
    args = parser.parse_args()
    
    if args.platform in ["xhs", "all"]:
        test_xiaohongshu()
        print()
    
    if args.platform in ["twitter", "all"]:
        test_twitter()

if __name__ == "__main__":
    main()
