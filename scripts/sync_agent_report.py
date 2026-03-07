#!/usr/bin/env python3
"""
Agent报告实时归档工具
在子Agent完成任务时立即同步到 workspace/subagents/{agent}/reports/

Usage:
    from scripts.sync_agent_report import sync_report
    
    # 子Agent生成报告后调用
    sync_report("quant-munger", "/path/to/report.md")
"""

import shutil
from pathlib import Path
from datetime import datetime

def sync_report(agent_name: str, report_path: str, report_name: str = None) -> dict:
    """
    将子Agent报告实时同步到 workspace/subagents/{agent}/reports/
    
    Args:
        agent_name: Agent名称 (quant-munger, product-engineer等)
        report_path: 报告源文件路径
        report_name: 目标文件名（可选，默认使用原文件名）
        
    Returns:
        dict: {status, source, target, message}
    """
    source = Path(report_path)
    
    if not source.exists():
        return {
            "status": "error",
            "message": f"Source file not found: {report_path}"
        }
    
    # 目标目录：workspace/subagents/{agent}/reports/
    target_dir = Path.home() / ".openclaw" / "workspace" / "subagents" / agent_name / "reports"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 目标文件名
    if report_name is None:
        report_name = source.name
    
    target = target_dir / report_name
    
    try:
        shutil.copy2(source, target)
        return {
            "status": "success",
            "source": str(source),
            "target": str(target),
            "message": f"Report synced to {target}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Sync failed: {str(e)}"
        }


def sync_learning_md(agent_name: str) -> dict:
    """
    同步Agent的LEARNING.md到正确位置
    
    ⚠️ 重要：此函数现在默认跳过LEARNING.md同步，避免覆盖历史记录
    如需更新，请手动编辑或使用专门的合并工具
    
    源：workspace-{agent}/LEARNING.md
    目标：workspace/subagents/{agent}/LEARNING.md
    """
    home = Path.home()
    source = home / f".openclaw/workspace-{agent_name}/LEARNING.md"
    target_dir = home / f".openclaw/workspace/subagents/{agent_name}"
    target = target_dir / "LEARNING.md"
    
    if not source.exists():
        return {
            "status": "skipped",
            "message": f"LEARNING.md not found for {agent_name}"
        }
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 如果目标已存在，跳过同步（避免覆盖历史记录）
        if target.exists():
            return {
                "status": "skipped",
                "message": f"LEARNING.md exists, skipped to avoid overwriting history"
            }
        else:
            # 只有目标不存在时才复制
            shutil.copy2(source, target)
            return {
                "status": "copied",
                "message": f"LEARNING.md synced to {target}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Sync failed: {str(e)}"
        }


def auto_sync_all():
    """
    自动同步所有Agent的报告和学习记录
    由子Agent在任务完成后调用
    """
    import os
    
    home = Path.home()
    agents = []
    
    # 发现所有Agent
    for item in home.glob(".openclaw/workspace-*"):
        if item.is_dir() and item.name != "workspace":
            agent_name = item.name.replace("workspace-", "")
            agents.append(agent_name)
    
    results = []
    
    for agent in agents:
        agent_dir = home / f".openclaw/workspace-{agent}"
        
        # 1. 同步reports目录下的文件
        reports_dir = agent_dir / "reports"
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.md"):
                result = sync_report(agent, report_file)
                results.append({"agent": agent, "file": report_file.name, **result})
        
        # 2. 同步LEARNING.md
        learning_result = sync_learning_md(agent)
        results.append({"agent": agent, "file": "LEARNING.md", **learning_result})
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 手动同步特定Agent
        agent = sys.argv[1]
        results = auto_sync_all()
        for r in results:
            if r["agent"] == agent:
                print(f"{r['file']}: {r['status']} - {r['message']}")
    else:
        # 同步所有Agent
        results = auto_sync_all()
        print("Agent报告同步完成")
        for r in results:
            print(f"  {r['agent']}/{r['file']}: {r['status']}")
