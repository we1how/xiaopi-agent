#!/usr/bin/env python3
"""
A股本地数据库测试报告生成脚本
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import subprocess

# 清除代理环境变量
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    if key in os.environ:
        del os.environ[key]

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StockDBTestReport:
    """A股数据库测试报告生成器"""
    
    def __init__(self):
        self.report = {
            "test_time": datetime.now().isoformat(),
            "environment": {},
            "installation": {},
            "data_fetching": {},
            "query_tests": {},
            "errors": [],
            "storage": {}
        }
        self.base_path = Path("~/StockData").expanduser()
        
    def check_environment(self):
        """检查环境"""
        logger.info("🔍 检查环境...")
        self.report["environment"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "base_path": str(self.base_path)
        }
        
    def test_installation(self):
        """测试依赖安装"""
        logger.info("📦 测试依赖安装...")
        results = {}
        
        packages = [
            ("akshare", "akshare"),
            ("duckdb", "duckdb"),
            ("pandas", "pandas"),
            ("numpy", "numpy"),
            ("tushare", "tushare"),
            ("pyarrow", "pyarrow"),
            ("openpyxl", "openpyxl"),
            ("requests", "requests"),
        ]
        
        all_success = True
        for name, import_name in packages:
            try:
                __import__(import_name)
                results[name] = "✅ 已安装"
            except ImportError as e:
                results[name] = f"❌ 未安装: {e}"
                all_success = False
        
        self.report["installation"] = {
            "status": "✅ 全部安装成功" if all_success else "❌ 部分包缺失",
            "details": results
        }
        return all_success
    
    def test_data_fetching(self):
        """测试数据拉取"""
        logger.info("📊 测试数据拉取...")
        results = {}
        
        try:
            import akshare as ak
            
            # 测试1: 股票基本信息
            logger.info("  测试 stock_info_a_code_name...")
            try:
                df = ak.stock_info_a_code_name()
                results["stock_basic"] = {
                    "status": "✅ 成功",
                    "count": len(df),
                    "columns": list(df.columns),
                    "sample": df.head(3).to_dict(orient='records')
                }
            except Exception as e:
                results["stock_basic"] = {"status": f"❌ 失败: {e}"}
                self.report["errors"].append(f"stock_basic: {e}")
            
            # 测试2: 实时行情
            logger.info("  测试 stock_zh_a_spot_em...")
            try:
                df = ak.stock_zh_a_spot_em()
                results["spot_data"] = {
                    "status": "✅ 成功",
                    "count": len(df),
                    "columns": list(df.columns)[:10]  # 只显示前10个列
                }
            except Exception as e:
                results["spot_data"] = {
                    "status": f"❌ 失败: {str(e)[:100]}",
                    "note": "可能是网络代理问题"
                }
                self.report["errors"].append(f"spot_data: {e}")
            
            # 测试3: 历史数据
            logger.info("  测试 stock_zh_a_hist...")
            try:
                df = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                                        start_date="20240101", end_date="20241231")
                results["historical"] = {
                    "status": "✅ 成功",
                    "count": len(df),
                    "columns": list(df.columns)
                }
            except Exception as e:
                results["historical"] = {"status": f"❌ 失败: {e}"}
                self.report["errors"].append(f"historical: {e}")
                
        except Exception as e:
            results["error"] = f"导入 akshare 失败: {e}"
            self.report["errors"].append(f"akshare_import: {e}")
        
        self.report["data_fetching"] = results
        return results
    
    def test_duckdb(self):
        """测试 DuckDB 数据库"""
        logger.info("🗄️ 测试 DuckDB 数据库...")
        results = {}
        
        try:
            import duckdb
            
            # 创建测试数据库
            test_db_path = self.base_path / "test.duckdb"
            conn = duckdb.connect(str(test_db_path))
            
            # 创建测试表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_stocks (
                    code VARCHAR,
                    name VARCHAR,
                    price DOUBLE
                )
            """)
            
            # 插入测试数据
            conn.execute("""
                INSERT INTO test_stocks VALUES 
                ('000001', '平安银行', 10.5),
                ('000002', '万科A', 15.2)
            """)
            
            # 查询测试
            result = conn.execute("SELECT * FROM test_stocks").fetchall()
            
            conn.close()
            
            # 删除测试文件
            test_db_path.unlink()
            
            results["status"] = "✅ 成功"
            results["query_result"] = result
            
        except Exception as e:
            results["status"] = f"❌ 失败: {e}"
            self.report["errors"].append(f"duckdb: {e}")
        
        self.report["query_tests"] = results
        return results
    
    def check_storage(self):
        """检查存储占用"""
        logger.info("💾 检查存储占用...")
        results = {}
        
        try:
            # 检查 StockData 目录
            if self.base_path.exists():
                total_size = 0
                file_count = 0
                
                for path in self.base_path.rglob("*"):
                    if path.is_file():
                        total_size += path.stat().st_size
                        file_count += 1
                
                results["stock_data_dir"] = {
                    "path": str(self.base_path),
                    "exists": True,
                    "file_count": file_count,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
            else:
                results["stock_data_dir"] = {
                    "path": str(self.base_path),
                    "exists": False
                }
            
            # 检查日志文件
            log_path = self.base_path / "logs"
            if log_path.exists():
                log_size = sum(f.stat().st_size for f in log_path.glob("*") if f.is_file())
                results["logs"] = {
                    "size_kb": round(log_size / 1024, 2)
                }
                
        except Exception as e:
            results["error"] = str(e)
        
        self.report["storage"] = results
        return results
    
    def check_logs(self):
        """检查日志文件"""
        logger.info("📋 检查日志文件...")
        log_entries = []
        
        log_path = self.base_path / "logs" / "init.log"
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # 获取最近20行
                    log_entries = lines[-20:] if len(lines) > 20 else lines
            except Exception as e:
                log_entries = [f"读取日志失败: {e}"]
        else:
            log_entries = ["日志文件不存在"]
        
        self.report["log_snippets"] = log_entries
        return log_entries
    
    def generate_report(self):
        """生成完整报告"""
        logger.info("📝 生成测试报告...")
        
        # 运行所有测试
        self.check_environment()
        self.test_installation()
        self.test_data_fetching()
        self.test_duckdb()
        self.check_storage()
        self.check_logs()
        
        # 保存报告
        report_path = self.base_path / "logs" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成文本报告
        text_report = self._format_text_report()
        text_path = self.base_path / "logs" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        logger.info(f"✅ 报告已保存: {report_path}")
        return text_report
    
    def _format_text_report(self):
        """格式化文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("A股本地数据库测试报告")
        lines.append("=" * 60)
        lines.append(f"测试时间: {self.report['test_time']}")
        lines.append("")
        
        # 环境信息
        lines.append("📋 环境信息")
        lines.append("-" * 40)
        env = self.report['environment']
        lines.append(f"Python: {env.get('python_version', 'N/A')[:50]}...")
        lines.append(f"平台: {env.get('platform', 'N/A')}")
        lines.append("")
        
        # 安装结果
        lines.append("📦 依赖安装")
        lines.append("-" * 40)
        install = self.report['installation']
        lines.append(f"状态: {install.get('status', 'N/A')}")
        for pkg, status in install.get('details', {}).items():
            lines.append(f"  {pkg}: {status}")
        lines.append("")
        
        # 数据拉取
        lines.append("📊 数据拉取测试")
        lines.append("-" * 40)
        for test_name, result in self.report['data_fetching'].items():
            if isinstance(result, dict):
                status = result.get('status', 'N/A')
                lines.append(f"{test_name}: {status}")
                if 'count' in result:
                    lines.append(f"  数据量: {result['count']}")
            else:
                lines.append(f"{test_name}: {result}")
        lines.append("")
        
        # 查询测试
        lines.append("🗄️ 数据库查询测试")
        lines.append("-" * 40)
        query = self.report.get('query_tests', {})
        lines.append(f"状态: {query.get('status', 'N/A')}")
        if 'query_result' in query:
            lines.append(f"查询结果: {query['query_result']}")
        lines.append("")
        
        # 存储占用
        lines.append("💾 存储占用")
        lines.append("-" * 40)
        storage = self.report.get('storage', {})
        if 'stock_data_dir' in storage:
            sd = storage['stock_data_dir']
            lines.append(f"StockData目录: {sd.get('path', 'N/A')}")
            lines.append(f"  存在: {sd.get('exists', False)}")
            if sd.get('exists'):
                lines.append(f"  文件数: {sd.get('file_count', 0)}")
                lines.append(f"  总大小: {sd.get('total_size_mb', 0)} MB")
        lines.append("")
        
        # 错误日志
        lines.append("⚠️ 错误日志")
        lines.append("-" * 40)
        if self.report['errors']:
            for error in self.report['errors']:
                lines.append(f"- {str(error)[:100]}")
        else:
            lines.append("无错误")
        lines.append("")
        
        # 日志片段
        lines.append("📄 最近日志片段")
        lines.append("-" * 40)
        for line in self.report.get('log_snippets', [])[-10:]:
            lines.append(line.strip())
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("测试完成")
        lines.append("=" * 60)
        
        return "\n".join(lines)


if __name__ == "__main__":
    tester = StockDBTestReport()
    report = tester.generate_report()
    print("\n" + report)
