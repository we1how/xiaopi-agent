#!/usr/bin/env python3
"""
Tavily Search Skill - 专为LLM优化的搜索引擎
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional

TAVILY_API_URL = "https://api.tavily.com/search"

def get_api_key() -> str:
    """获取Tavily API Key"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        # 尝试从credentials文件读取
        cred_path = os.path.expanduser("~/.openclaw/workspace/.credentials/tavily-api-key")
        if os.path.exists(cred_path):
            with open(cred_path) as f:
                for line in f:
                    if line.startswith("TAVILY_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
    
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found. Please set it in environment or .credentials/tavily-api-key")
    
    return api_key

def search(
    query: str,
    max_results: int = 5,
    include_answer: bool = True,
    include_raw_content: bool = False,
    search_depth: str = "basic"  # "basic" or "advanced"
) -> Dict:
    """
    使用Tavily API搜索
    
    Args:
        query: 搜索查询
        max_results: 最大结果数（默认5）
        include_answer: 是否包含AI生成的回答
        include_raw_content: 是否包含原始网页内容
        search_depth: 搜索深度（basic/advanced）
    
    Returns:
        Tavily API响应字典
    """
    api_key = get_api_key()
    
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "search_depth": search_depth
    }
    
    try:
        response = requests.post(TAVILY_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Tavily API request failed: {str(e)}",
            "fallback": "Consider using web_search as alternative"
        }

def format_results(results: Dict) -> str:
    """格式化搜索结果为可读文本"""
    if results.get("error"):
        return f"❌ Search failed: {results.get('message')}"
    
    output = []
    
    # AI生成的回答
    if results.get("answer"):
        output.append("## 🤖 AI Summary")
        output.append(results["answer"])
        output.append("")
    
    # 搜索结果
    if results.get("results"):
        output.append("## 🔍 Search Results")
        for i, result in enumerate(results["results"], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "")[:300]  # 限制长度
            
            output.append(f"\n{i}. **{title}**")
            output.append(f"   URL: {url}")
            output.append(f"   {content}...")
    
    # 使用统计
    if "query" in results:
        output.append(f"\n---")
        output.append(f"📊 Query: {results.get('query', 'N/A')}")
    
    return "\n".join(output)

def main():
    """CLI入口"""
    if len(sys.argv) < 2:
        print("Usage: python tavily_search.py 'your search query'")
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"🔍 Searching: {query}\n")
    
    results = search(query, max_results=max_results)
    print(format_results(results))

if __name__ == "__main__":
    main()
