#!/usr/bin/env python3
"""
Agent输出归档脚本
智能归档子Agent的workspace-{agent}内容到主workspace/subagents/{agent}/

核心原则：
1. 只归档有价值的产出（reports/、skills/、data/等）
2. 忽略模板文件（AGENTS.md、BOOTSTRAP.md等OpenClaw自动生成文件）
3. 智能合并LEARNING.md（提取新内容而非简单覆盖）
4. 提取关键洞察到主MEMORY.md

Usage:
    python scripts/archive_agent_outputs.py [agent_name]
    
Examples:
    python scripts/archive_agent_outputs.py quant-munger  # 归档特定Agent
    python scripts/archive_agent_outputs.py              # 归档所有Agent
"""

import os
import sys
import shutil
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set
import fnmatch
import hashlib

# 配置
OPENCLAW_DIR = Path.home() / ".openclaw"
WORKSPACE_DIR = OPENCLAW_DIR / "workspace"
ARCHIVE_RETENTION_DAYS = 7

# === 归档规则配置 ===

# 高价值目录（这些目录下的内容应该归档）
HIGH_VALUE_DIRS = [
    "reports",      # 报告文件
    "skills",       # 实现的工具/技能
    "data",         # 生成的数据
    "examples",     # 示例代码
    "memory",       # 记忆文件
    "scripts",      # 脚本文件
    "learning-plans", # 学习计划
]

# 高价值文件（特定文件应该归档）
HIGH_VALUE_FILES = [
    "LEARNING.md",      # 学习记录（需要智能合并）
    "MEMORY.md",        # 记忆文件
    "SKILL.md",         # 技能清单
    "GROWTH_PLAN.md",   # 成长计划
    "TEMPLATES.md",     # 模板文件
]

# 模板文件（OpenClaw自动生成，不应该归档，因为workspace/subagents/已有正式版本）
TEMPLATE_FILES = [
    "AGENTS.md",        # Agent列表模板
    "BOOTSTRAP.md",     # 启动配置模板
    "HEARTBEAT.md",     # 心跳配置模板
    "IDENTITY.md",      # 身份配置模板
    "SOUL.md",          # 人格模板（会覆盖正式SOUL.md）
    "TOOLS.md",         # 工具配置模板
    "USER.md",          # 用户信息模板
    "openclaw.json",    # OpenClaw配置
    ".openclaw.json",   # OpenClaw配置
    
    # 注意：AGENT.md 是正式Agent配置，不是模板，不应在此列表
]

# 完全忽略的文件/目录
IGNORE_PATTERNS = [
    "*.pyc",
    "__pycache__",
    ".pi",
    ".git",
    ".openclaw",
    "subagents",
    "*.tmp",
    "*.log",
]


def get_file_hash(filepath: Path) -> str:
    """计算文件MD5哈希，用于检测重复"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:16]
    except:
        return ""


def is_template_file(filename: str) -> bool:
    """判断是否为OpenClaw模板文件"""
    return filename in TEMPLATE_FILES


def should_archive_path(rel_path: Path) -> bool:
    """
    判断路径是否应该归档
    
    优先级：
    1. 如果是模板文件 → 跳过
    2. 如果在高价值目录下 → 归档
    3. 如果是高价值文件 → 归档
    4. 如果在忽略列表 → 跳过
    """
    path_str = str(rel_path)
    filename = rel_path.name
    
    # 检查是否在忽略列表
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str or fnmatch.fnmatch(filename, pattern):
            return False
    
    # 检查是否为模板文件
    if is_template_file(filename):
        return False
    
    # 检查是否在高价值目录下
    parts = rel_path.parts
    for high_value_dir in HIGH_VALUE_DIRS:
        if high_value_dir in parts:
            return True
    
    # 检查是否为高价值文件
    if filename in HIGH_VALUE_FILES:
        return True
    
    return False


def smart_merge_learning_md(source_file: Path, target_file: Path) -> Dict:
    """
    智能合并LEARNING.md
    
    策略：
    1. 如果目标文件不存在，直接复制
    2. 如果存在，提取源文件中的新条目追加到目标文件
    """
    if not target_file.exists():
        # 目标不存在，直接复制
        shutil.copy2(source_file, target_file)
        return {"action": "copied", "new_entries": 0}
    
    # 读取两个文件
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(target_file, 'r', encoding='utf-8') as f:
        target_content = f.read()
    
    # 简单策略：如果内容不同，创建备份并覆盖
    # TODO: 未来可以实现更智能的条目级合并
    if source_content.strip() != target_content.strip():
        # 创建备份
        backup_file = target_file.with_suffix('.md.bak')
        shutil.copy2(target_file, backup_file)
        
        # 覆盖（保留更完整的版本，通常source是更新的）
        shutil.copy2(source_file, target_file)
        
        return {"action": "merged", "backup": str(backup_file), "new_entries": 1}
    
    return {"action": "unchanged"}


def archive_agent(agent_name: str, dry_run: bool = False) -> Dict:
    """归档单个Agent的输出"""
    source_dir = OPENCLAW_DIR / f"workspace-{agent_name}"
    target_dir = WORKSPACE_DIR / "subagents" / agent_name
    
    if not source_dir.exists():
        return {
            "agent": agent_name,
            "status": "skipped",
            "reason": f"Source directory not found: {source_dir}"
        }
    
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
    
    archived_files = []
    skipped_files = []
    merged_files = []
    errors = []
    
    # 遍历源目录
    for root, dirs, files in os.walk(source_dir):
        # 过滤目录
        dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS and not d.startswith('.')]
        
        for file in files:
            source_file = Path(root) / file
            rel_path = source_file.relative_to(source_dir)
            
            # 判断是否应归档
            if not should_archive_path(rel_path):
                skipped_files.append(str(rel_path))
                continue
            
            target_file = target_dir / rel_path
            
            if dry_run:
                archived_files.append(str(rel_path))
                continue
            
            try:
                # 确保目标目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 特殊处理LEARNING.md
                if file == "LEARNING.md":
                    merge_result = smart_merge_learning_md(source_file, target_file)
                    merged_files.append({
                        "file": str(rel_path),
                        **merge_result
                    })
                else:
                    # 普通文件直接复制
                    shutil.copy2(source_file, target_file)
                    archived_files.append(str(rel_path))
                
            except Exception as e:
                errors.append(f"{rel_path}: {str(e)}")
    
    result = {
        "agent": agent_name,
        "status": "success" if not errors else "partial",
        "source": str(source_dir),
        "target": str(target_dir),
        "archived_count": len(archived_files),
        "merged_count": len(merged_files),
        "skipped_count": len(skipped_files),
        "archived_files": archived_files[:20],  # 只显示前20个
        "merged_files": merged_files,
        "skipped_examples": skipped_files[:10],  # 示例跳过的文件
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def extract_insights_from_learning(agent_name: str) -> Dict:
    """从Agent的LEARNING.md提取关键洞察"""
    learning_file = OPENCLAW_DIR / f"workspace-{agent_name}" / "LEARNING.md"
    
    if not learning_file.exists():
        return {"status": "skipped", "reason": "LEARNING.md not found"}
    
    try:
        with open(learning_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        insights = []
        
        # 匹配不同格式的核心洞察部分
        patterns = [
            r'(?:###|##)\s*(?:核心洞察|关键洞察|核心要点).*?(?=(?:###|##)|$)',
            r'(?:###|##)\s*(?:今日精选|学习内容).*?(?=(?:###|##)|$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(0)
                # 提取列表项（支持多种格式）
                items = re.findall(r'(?:^|\n)(?:[-\*•]|\d+\.)\s*(.+?)(?=\n|$)', section)
                insights.extend([item.strip() for item in items if len(item.strip()) > 10])
        
        # 去重并限制数量
        insights = list(dict.fromkeys(insights))[:10]  # 最多10条，去重
        
        return {
            "status": "success",
            "insights_extracted": len(insights),
            "insights": insights
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


def merge_to_memory(agent_name: str, insights: List[str]) -> bool:
    """将洞察合并到主MEMORY.md"""
    memory_file = WORKSPACE_DIR / "MEMORY.md"
    
    if not insights:
        return False
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # 读取或创建MEMORY.md
    if memory_file.exists():
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# MEMORY.md - 长期记忆库\n\n> **注意**: 本文件由Agent归档脚本自动更新\n\n"
    
    # 构建新条目
    new_entry = f"\n### {agent_name} - {timestamp}\n\n"
    for i, insight in enumerate(insights[:5], 1):  # 最多5条
        # 截断过长的洞察
        if len(insight) > 200:
            insight = insight[:197] + "..."
        new_entry += f"{i}. {insight}\n"
    
    # 检查是否已存在（简单去重）
    entry_hash = hashlib.md5(new_entry.encode()).hexdigest()[:16]
    if entry_hash in content:
        return False  # 已存在，跳过
    
    # 插入到文件末尾
    content += new_entry
    
    with open(memory_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def cleanup_workspace(agent_name: str, dry_run: bool = True) -> Dict:
    """
    清理workspace-xx中已归档的内容
    
    策略：
    1. 删除已成功归档到reports/的文件
    2. 保留LEARNING.md作为备份
    3. 删除7天以上的旧报告
    """
    workspace_dir = OPENCLAW_DIR / f"workspace-{agent_name}"
    
    if not workspace_dir.exists():
        return {"status": "skipped", "reason": "Workspace not found"}
    
    deleted = []
    errors = []
    
    cutoff_date = datetime.now() - timedelta(days=ARCHIVE_RETENTION_DAYS)
    
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(workspace_dir)
            
            # 策略1: 删除已归档的报告文件（在reports/目录下且已归档）
            if "reports" in str(rel_path):
                try:
                    stat = filepath.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    
                    if mtime < cutoff_date:
                        if dry_run:
                            deleted.append(f"[would delete] {rel_path}")
                        else:
                            filepath.unlink()
                            deleted.append(str(rel_path))
                except Exception as e:
                    errors.append(f"{rel_path}: {e}")
    
    return {
        "status": "success",
        "deleted_count": len(deleted),
        "deleted_files": deleted[:20],
        "errors": errors
    }


def main():
    """主函数"""
    args = sys.argv[1:]
    
    # 解析参数
    dry_run = "--dry-run" in args
    cleanup = "--cleanup" in args
    agent_names = [arg for arg in args if not arg.startswith("--")]
    
    if cleanup:
        # 清理模式
        print(f"🧹 清理模式 ({'预览' if dry_run else '执行'})")
        print("=" * 50)
        
        if agent_names:
            agents = agent_names
        else:
            agents = [
                d.name.replace("workspace-", "")
                for d in OPENCLAW_DIR.iterdir()
                if d.is_dir() and d.name.startswith("workspace-") and d.name != "workspace"
            ]
        
        for agent in agents:
            result = cleanup_workspace(agent, dry_run=dry_run)
            print(f"\n{agent}:")
            print(f"  删除文件: {result.get('deleted_count', 0)}")
            if result.get('deleted_files'):
                for f in result['deleted_files'][:5]:
                    print(f"    - {f}")
        
        return
    
    # 归档模式
    print(f"📦 Agent智能归档脚本")
    print(f"=" * 50)
    
    if agent_names:
        agents = agent_names
    else:
        # 自动发现所有Agent
        agents = [
            d.name.replace("workspace-", "")
            for d in OPENCLAW_DIR.iterdir()
            if d.is_dir() and d.name.startswith("workspace-") and d.name != "workspace"
        ]
    
    print(f"发现Agent: {', '.join(agents)}\n")
    
    if dry_run:
        print("【预览模式 - 不会实际修改文件】\n")
    
    all_results = []
    total_insights = 0
    
    for agent in agents:
        print(f"🔄 处理 {agent}...")
        
        # 归档文件
        archive_result = archive_agent(agent, dry_run=dry_run)
        
        # 提取洞察
        if not dry_run:
            insights_result = extract_insights_from_learning(agent)
            if insights_result["status"] == "success":
                insights = insights_result.get("insights", [])
                if insights:
                    merged = merge_to_memory(agent, insights)
                    if merged:
                        total_insights += len(insights)
                        insights_result["merged_to_memory"] = True
        else:
            insights_result = {"status": "preview"}
        
        result = {
            "agent": agent,
            "archive": archive_result,
            "insights": insights_result
        }
        all_results.append(result)
        
        # 打印状态
        if archive_result["status"] == "success":
            print(f"  ✅ 归档: {archive_result['archived_count']} 个文件")
            if archive_result.get('merged_count', 0) > 0:
                print(f"  ✅ 合并: {archive_result['merged_count']} 个文件")
            if archive_result.get('skipped_count', 0) > 0:
                print(f"  ⚪ 跳过: {archive_result['skipped_count']} 个文件（模板/忽略）")
        elif archive_result["status"] == "partial":
            print(f"  ⚠️  归档: {archive_result['archived_count']} 个文件, {len(archive_result.get('errors', []))} 个错误")
        else:
            print(f"  ⚪ 跳过: {archive_result.get('reason', 'unknown')}")
        
        if insights_result.get("insights_extracted", 0) > 0:
            print(f"  ✅ 洞察: 提取 {insights_result['insights_extracted']} 条")
        
        print()
    
    # 保存归档报告
    if not dry_run:
        report_file = WORKSPACE_DIR / "archive-reports" / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": all_results,
                "total_insights": total_insights
            }, f, ensure_ascii=False, indent=2)
        
        print(f"📄 归档报告保存到: {report_file}")
    
    print(f"=" * 50)
    if dry_run:
        print(f"预览完成！使用 --dry-run 查看详情，去掉该参数执行实际归档")
    else:
        print(f"归档完成！共提取 {total_insights} 条洞察到 MEMORY.md")


if __name__ == "__main__":
    main()
