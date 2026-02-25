#!/usr/bin/env python3
"""获取Notion页面内容"""
import requests
import json
import sys

NOTION_KEY = open('/Users/linweihao/.config/notion/api_key').read().strip()
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_page_content(page_id):
    """获取页面内容"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def get_page_info(page_id):
    """获取页面信息"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def extract_text(block):
    """提取文本内容"""
    block_type = block.get('type', '')
    
    if block_type == 'paragraph':
        texts = block.get('paragraph', {}).get('rich_text', [])
        return ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'heading_1':
        texts = block.get('heading_1', {}).get('rich_text', [])
        return '# ' + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'heading_2':
        texts = block.get('heading_2', {}).get('rich_text', [])
        return '## ' + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'heading_3':
        texts = block.get('heading_3', {}).get('rich_text', [])
        return '### ' + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'bulleted_list_item':
        texts = block.get('bulleted_list_item', {}).get('rich_text', [])
        return '- ' + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'numbered_list_item':
        texts = block.get('numbered_list_item', {}).get('rich_text', [])
        return '1. ' + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'to_do':
        texts = block.get('to_do', {}).get('rich_text', [])
        checked = block.get('to_do', {}).get('checked', False)
        return f"{'[x]' if checked else '[ ]'} " + ''.join([t.get('plain_text', '') for t in texts])
    
    elif block_type == 'child_page':
        return f"📄 子页面: {block.get('child_page', {}).get('title', '')}"
    
    elif block_type == 'quote':
        texts = block.get('quote', {}).get('rich_text', [])
        return '> ' + ''.join([t.get('plain_text', '') for t in texts])
    
    else:
        return f"[{block_type}]"

def fetch_all_content(page_id, depth=0):
    """递归获取所有内容"""
    content = get_page_content(page_id)
    results = []
    
    for block in content.get('results', []):
        text = extract_text(block)
        if text:
            results.append('  ' * depth + text)
        
        # 如果有子内容，递归获取
        if block.get('has_children', False) and block.get('type') not in ['child_page']:
            child_content = fetch_all_content(block['id'], depth + 1)
            results.extend(child_content)
    
    return results

# 5个主页面
pages = [
    ("2fc7f3b0-5d4c-8008-8eaf-df549eac1dbc", "年度计划以及总结"),
    ("2c87f3b0-5d4c-80ca-bdc4-f8c12b4c8879", "投资记录"),
    ("2a57f3b0-5d4c-801a-a264-c9a2b0285517", "奇思妙想工作组"),
    ("2637f3b0-5d4c-8044-a40f-fa2ce8c83278", "读书笔记"),
    ("25f7f3b0-5d4c-8083-8bed-ef0833657575", "观影笔记")
]

# 获取并保存所有内容
output = []
for page_id, title in pages:
    output.append(f"\n{'='*60}")
    output.append(f"📄 {title}")
    output.append(f"{'='*60}\n")
    
    content = fetch_all_content(page_id)
    output.extend(content)
    
    # 获取子页面
    page_content = get_page_content(page_id)
    for block in page_content.get('results', []):
        if block.get('type') == 'child_page':
            child_title = block.get('child_page', {}).get('title', '')
            child_id = block['id']
            output.append(f"\n{'─'*40}")
            output.append(f"📑 子页面: {child_title}")
            output.append(f"{'─'*40}\n")
            
            child_content = fetch_all_content(child_id)
            output.extend(child_content)

# 输出到文件
output_text = '\n'.join(output)
print(output_text)

# 保存到文件
output_path = '/Users/linweihao/.openclaw/workspace/knowledge/notion_2025_2026/notion_raw_content.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output_text)

print(f"\n\n✅ 内容已保存到: {output_path}")
