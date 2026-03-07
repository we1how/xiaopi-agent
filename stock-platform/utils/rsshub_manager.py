"""
RSSHub Docker 容器管理器
负责检测、启动、停止 RSSHub 服务
"""

import subprocess
import requests
import time
import sys
from typing import Tuple, Optional


class RSSHubManager:
    """RSSHub Docker 容器管理器"""

    RSSHUB_URL = "http://localhost:1200"
    CONTAINER_NAME = "rsshub-finance"
    DOCKER_IMAGE = "diygod/rsshub:latest"

    def __init__(self):
        self._skip_check = self._check_skip_flag()

    def _check_skip_flag(self) -> bool:
        """检查是否跳过 RSSHub 检查（通过命令行参数）"""
        return "--skip-rsshub" in sys.argv

    def is_running(self) -> bool:
        """检测 RSSHub 是否已在运行"""
        try:
            response = requests.get(self.RSSHUB_URL, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _container_exists(self) -> bool:
        """检查容器是否已存在"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.CONTAINER_NAME}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return self.CONTAINER_NAME in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def start(self) -> Tuple[bool, str]:
        """
        启动 RSSHub Docker 容器

        Returns:
            (success: bool, message: str)
        """
        try:
            # 检查 Docker 是否可用
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Docker 未安装或未在 PATH 中"
        except subprocess.CalledProcessError:
            return False, "Docker 命令执行失败"

        try:
            # 如果容器已存在，先删除
            if self._container_exists():
                subprocess.run(
                    ["docker", "rm", "-f", self.CONTAINER_NAME],
                    capture_output=True,
                    timeout=10
                )

            # 启动新容器
            result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", self.CONTAINER_NAME,
                    "-p", "1200:1200",
                    "--rm",  # 容器停止后自动删除
                    self.DOCKER_IMAGE
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return False, f"Docker 启动失败: {result.stderr}"

            # 等待服务启动
            max_wait = 30  # 最多等待 30 秒
            wait_interval = 1
            elapsed = 0

            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval

                if self.is_running():
                    return True, "RSSHub 启动成功"

            return False, "RSSHub 启动超时，请检查 Docker 日志"

        except subprocess.TimeoutExpired:
            return False, "Docker 命令执行超时"
        except Exception as e:
            return False, f"启动异常: {str(e)}"

    def stop(self) -> Tuple[bool, str]:
        """
        停止 RSSHub Docker 容器

        Returns:
            (success: bool, message: str)
        """
        try:
            result = subprocess.run(
                ["docker", "stop", self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                return True, "RSSHub 已停止"
            else:
                return False, f"停止失败: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "停止命令超时"
        except Exception as e:
            return False, f"停止异常: {str(e)}"

    def get_logs(self, lines: int = 50) -> str:
        """获取容器日志"""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else f"获取日志失败: {result.stderr}"
        except Exception as e:
            return f"获取日志异常: {str(e)}"

    def ensure_running(self) -> Tuple[bool, str]:
        """
        确保 RSSHub 在运行

        Returns:
            (success: bool, message: str)
            success: True 表示 RSSHub 已就绪，False 表示启动失败
        """
        if self._skip_check:
            return True, "已跳过 RSSHub 检查"

        # 检查是否已在运行
        if self.is_running():
            return True, "RSSHub 已在运行"

        # 尝试启动
        return self.start()


def check_and_start_rsshub() -> Tuple[bool, str, Optional[dict]]:
    """
    检查并启动 RSSHub 的便捷函数

    Returns:
        (success, message, status_info)
        status_info: 包含详细状态信息的字典，用于 Streamlit 显示
    """
    manager = RSSHubManager()

    status_info = {
        "checked": False,
        "running": False,
        "started": False,
        "error": None
    }

    # 检测中
    status_info["checked"] = True

    if manager.is_running():
        status_info["running"] = True
        return True, "RSSHub 服务已就绪", status_info

    # 需要启动
    status_info["started"] = True
    success, message = manager.start()

    if success:
        status_info["running"] = True
        return True, message, status_info
    else:
        status_info["error"] = message
        return False, message, status_info


if __name__ == "__main__":
    # 测试代码
    print("测试 RSSHub 管理器...")

    manager = RSSHubManager()

    print(f"RSSHub 运行状态: {manager.is_running()}")

    if not manager.is_running():
        print("正在启动 RSSHub...")
        success, message = manager.start()
        print(f"启动结果: {success}, {message}")
