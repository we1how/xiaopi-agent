#!/usr/bin/env python3
"""
Agent归档触发器 - 供MuskOrchestrator调用
在子Agent任务完成后自动触发归档

Usage:
    from scripts.trigger_archive import archive_after_session
    
    # 子Agent完成后
    archive_after_session("quant-munger", "/path/to/session/workspace")
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional

def archive_after_session(agent_name: str, session_workspace: Optional[str] = None) -> Dict:
    """
    子Agent会话完成后触发归档
    
    Args:
        agent_name: Agent名称 (quant-munger, product-engineer, etc.)
        session_workspace: 会话工作区路径（可选，如果不提供则使用默认workspace-{agent}）
        
    Returns:
        归档结果摘要
    """
    script_path = Path("/Users/linweihao/.openclaw/workspace/scripts/archive_agent_outputs.py")
    
    try:
        result = subprocess.run(
            ["python3", str(script_path), agent_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "agent": agent_name,
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            "agent": agent_name,
            "status": "timeout",
            "error": "Archive script timed out after 60s"
        }
    except Exception as e:
        return {
            "agent": agent_name,
            "status": "error",
            "error": str(e)
        }


def archive_all_agents() -> Dict:
    """
    归档所有Agent
    
    Returns:
        归档结果摘要
    """
    script_path = Path("/Users/linweihao/.openclaw/workspace/scripts/archive_agent_outputs.py")
    
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试归档单个Agent
    import sys
    
    if len(sys.argv) > 1:
        agent = sys.argv[1]
        result = archive_after_session(agent)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 归档所有
        result = archive_all_agents()
        print(json.dumps(result, indent=2, ensure_ascii=False))
