"""
Prompt模板管理模块
管理AI分析的Prompt模板
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
PROMPTS_FILE = os.path.join(CONFIG_DIR, "prompts.json")


class PromptManager:
    """Prompt模板管理器"""

    def __init__(self):
        self.prompts_file = PROMPTS_FILE
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        if not os.path.exists(self.prompts_file):
            # 创建默认配置
            default_config = {
                "templates": [
                    {
                        "id": "stock_impact",
                        "name": "股票影响分析",
                        "category": "analysis",
                        "description": "分析新闻对A股股票的影响程度",
                        "content": "请分析以下新闻内容，完成以下任务：\n1. 将新闻内容总结成一句话；\n2. 判断分析该新闻对国内A股市场哪些具体股票的利好程度判断。从利好到利空依次分为\"强烈利好\"、\"利好\"、\"中性\"、\"利空\"、\"强烈利空\"5个等级。另外，如果不确定或者缺乏足够判断信息，或者新闻和要判断的股票关系不大，则跳过；\n3. 可以有多个股票分析,请用字典格式输出，在字典以外不要输出任何内容：\n{\n    \"summary\": \"新闻的一句话总结(如果没有则用新闻标题代替)\",\n    \"analysis\": [\n        {\n            \"stock\": \"A股股票名称（股票代码.后缀）\",\n            \"impact\": \"强烈利好/利好/中性/利空/强烈利空\",\n            \"reason\": \"影响理由\"\n        }\n    ]\n}；\n\n4. 以下是要分析的新闻内容：\n{news_content}"
                    },
                    {
                        "id": "summary_only",
                        "name": "新闻摘要",
                        "category": "analysis",
                        "description": "仅生成新闻摘要",
                        "content": "请对以下新闻内容进行简要总结，提炼核心信息点：\n\n{news_content}\n\n请用2-3句话概括主要观点。"
                    },
                    {
                        "id": "market_sentiment",
                        "name": "市场情绪分析",
                        "category": "analysis",
                        "description": "分析新闻反映的市场情绪",
                        "content": "请分析以下新闻所反映的市场情绪和投资氛围：\n\n{news_content}\n\n请从以下几个维度分析：\n1. 整体情绪（乐观/中性/谨慎/悲观）\n2. 主要关注点\n3. 对市场的潜在影响"
                    },
                    {
                        "id": "custom",
                        "name": "自定义分析",
                        "category": "custom",
                        "description": "用户自定义prompt",
                        "content": "{news_content}"
                    }
                ],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            self._save_config(default_config)

    def _load_config(self) -> Dict:
        """加载配置"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载Prompt配置失败: {e}")
            return {"templates": [], "last_updated": datetime.now(timezone.utc).isoformat()}

    def _save_config(self, config: Dict):
        """保存配置"""
        config["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get_all_templates(self) -> List[Dict]:
        """获取所有模板"""
        config = self._load_config()
        return config.get("templates", [])

    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """根据ID获取模板"""
        for template in self.get_all_templates():
            if template.get("id") == template_id:
                return template
        return None

    def get_templates_by_category(self, category: str) -> List[Dict]:
        """根据类别获取模板"""
        return [t for t in self.get_all_templates() if t.get("category") == category]

    def add_template(self, template_id: str, name: str, content: str,
                     category: str = "custom", description: str = "") -> bool:
        """添加新模板"""
        config = self._load_config()
        templates = config.get("templates", [])

        # 检查ID是否已存在
        if any(t.get("id") == template_id for t in templates):
            return False

        new_template = {
            "id": template_id,
            "name": name,
            "category": category,
            "description": description or name,
            "content": content
        }

        templates.append(new_template)
        config["templates"] = templates
        self._save_config(config)
        return True

    def update_template(self, template_id: str, **kwargs) -> bool:
        """更新模板"""
        config = self._load_config()
        templates = config.get("templates", [])

        for template in templates:
            if template.get("id") == template_id:
                template.update(kwargs)
                config["templates"] = templates
                self._save_config(config)
                return True

        return False

    def delete_template(self, template_id: str) -> bool:
        """删除模板（不能删除内置模板）"""
        if template_id in ["stock_impact", "summary_only", "market_sentiment"]:
            return False

        config = self._load_config()
        templates = config.get("templates", [])

        original_count = len(templates)
        templates = [t for t in templates if t.get("id") != template_id]

        if len(templates) < original_count:
            config["templates"] = templates
            self._save_config(config)
            return True

        return False

    def render_prompt(self, template_id: str, **kwargs) -> Optional[str]:
        """渲染Prompt模板"""
        template = self.get_template_by_id(template_id)
        if not template:
            return None

        content = template.get("content", "")
        try:
            return content.format(**kwargs)
        except KeyError as e:
            print(f"渲染Prompt失败，缺少参数: {e}")
            return content

    def render_prompt_with_news(self, template_id: str, news_list: List[Dict]) -> Optional[str]:
        """使用新闻列表渲染Prompt"""
        # 组合新闻内容
        news_content = "\n\n".join([
            f"【新闻{i+1}】{news.get('title', '无标题')}\n{news.get('content', '')}"
            for i, news in enumerate(news_list)
        ])

        return self.render_prompt(template_id, news_content=news_content)
