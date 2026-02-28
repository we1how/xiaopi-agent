#!/usr/bin/env python3
"""
setup_credentials.py - 配置平台登录凭证

从 .credentials/platform-accounts.md 读取账号密码
生成 MediaCrawler 可用的配置文件
"""

import os
import re
import json
from pathlib import Path

def read_credentials():
    """从凭证文件读取账号密码"""
    cred_file = Path.home() / ".openclaw/workspace/.credentials/platform-accounts.md"
    
    if not cred_file.exists():
        print(f"❌ 凭证文件不存在: {cred_file}")
        return None
    
    content = cred_file.read_text()
    
    # 解析小红书
    xhs_phone = re.search(r'小红书.*?手机号.*?([\d]+)', content, re.DOTALL)
    xhs_pass = re.search(r'小红书.*?密码.*?([\w]+)', content, re.DOTALL)
    
    # 解析 Twitter
    tw_user = re.search(r'Twitter / X.*?用户名.*?([\w]+)', content, re.DOTALL)
    tw_pass = re.search(r'Twitter / X.*?密码.*?([\w]+)', content, re.DOTALL)
    
    creds = {
        "xiaohongshu": {
            "phone": xhs_phone.group(1) if xhs_phone else None,
            "password": xhs_pass.group(1) if xhs_pass else None
        },
        "twitter": {
            "username": tw_user.group(1) if tw_user else None,
            "password": tw_pass.group(1) if tw_pass else None
        }
    }
    
    return creds

def setup_mediacrawler_config():
    """配置 MediaCrawler"""
    creds = read_credentials()
    if not creds:
        return False
    
    workspace = Path.home() / ".openclaw/workspace"
    crawler_dir = workspace / "tools/MediaCrawler"
    
    if not crawler_dir.exists():
        print("❌ MediaCrawler 未安装，请先运行 install.sh")
        return False
    
    # 创建本地配置文件
    config = {
        "xhs": {
            "login_type": "qrcode",  # 小红书推荐二维码登录
            "phone": creds["xiaohongshu"]["phone"],
            "password": creds["xiaohongshu"]["password"]
        },
        "twitter": {
            "login_type": "password",  # Twitter 使用账号密码
            "username": creds["twitter"]["username"],
            "password": creds["twitter"]["password"]
        }
    }
    
    # 保存配置
    config_file = workspace / "skills/social-media-crawler/config/credentials.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ 凭证已配置: {config_file}")
    print(f"   小红书: {creds['xiaohongshu']['phone']}")
    print(f"   Twitter: {creds['twitter']['username']}")
    
    return True

if __name__ == "__main__":
    setup_mediacrawler_config()
