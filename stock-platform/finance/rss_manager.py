"""
RSS路由管理模块
管理RSS源的增删改查
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
ROUTES_FILE = os.path.join(CONFIG_DIR, "rss_routes.json")

# 预设的路由模板
PRESET_ROUTES = {
    "cls": {
        "name": "财联社",
        "category": "finance",
        "parser": "cls",
        "description": "财联社财经新闻"
    },
    "cls_depth": {
        "name": "财联社深度",
        "url": "http://localhost:1200/cls/depth/1000",
        "category": "finance",
        "parser": "cls",
        "description": "财联社深度报道"
    },
    "cls_telegraph": {
        "name": "财联社电报",
        "url": "http://localhost:1200/cls/telegraph",
        "category": "finance",
        "parser": "cls",
        "description": "财联社7x24小时电报"
    },
    "sina_finance": {
        "name": "新浪财经",
        "url": "http://localhost:1200/sina/column/roll",
        "category": "finance",
        "parser": "generic",
        "description": "新浪财经滚动新闻"
    },
    "wallstreetcn_hot": {
        "name": "华尔街见闻",
        "url": "http://localhost:1200/wallstreetcn/hot",
        "category": "finance",
        "parser": "generic",
        "description": "华尔街见闻热门文章"
    },
    "eastmoney_search": {
        "name": "东方财富",
        "url": "http://localhost:1200/eastmoney/search/web",
        "category": "finance",
        "parser": "generic",
        "description": "东方财富网资讯"
    },
    "caixin_latest": {
        "name": "财新网",
        "url": "http://localhost:1200/caixin/latest",
        "category": "finance",
        "parser": "generic",
        "description": "财新网最新文章"
    },
    "jiemian": {
        "name": "界面新闻",
        "url": "http://localhost:1200/jiemian/list/4",
        "category": "finance",
        "parser": "generic",
        "description": "界面新闻财经"
    }
}


class RSSManager:
    """RSS路由管理器"""

    def __init__(self):
        self.routes_file = ROUTES_FILE
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        if not os.path.exists(self.routes_file):
            # 创建默认配置
            default_config = {
                "routes": [
                    {
                        "id": "cls_depth",
                        "name": "财联社深度",
                        "url": "http://localhost:1200/cls/depth/1000",
                        "category": "finance",
                        "enabled": True,
                        "parser": "cls",
                        "description": "财联社深度报道"
                    }
                ],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            self._save_config(default_config)

    def _load_config(self) -> Dict:
        """加载配置"""
        try:
            with open(self.routes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载RSS配置失败: {e}")
            return {"routes": [], "last_updated": datetime.now(timezone.utc).isoformat()}

    def _save_config(self, config: Dict):
        """保存配置"""
        config["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.routes_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get_all_routes(self) -> List[Dict]:
        """获取所有路由"""
        config = self._load_config()
        return config.get("routes", [])

    def get_enabled_routes(self) -> List[Dict]:
        """获取启用的路由"""
        return [r for r in self.get_all_routes() if r.get("enabled", True)]

    def get_route_by_id(self, route_id: str) -> Optional[Dict]:
        """根据ID获取路由"""
        for route in self.get_all_routes():
            if route.get("id") == route_id:
                return route
        return None

    def add_route(self, route_id: str, name: str, url: str, parser: str = "generic",
                  description: str = "", enabled: bool = True) -> bool:
        """添加新路由"""
        config = self._load_config()
        routes = config.get("routes", [])

        # 检查ID是否已存在
        if any(r.get("id") == route_id for r in routes):
            return False

        new_route = {
            "id": route_id,
            "name": name,
            "url": url,
            "category": "finance",
            "enabled": enabled,
            "parser": parser,
            "description": description or name
        }

        routes.append(new_route)
        config["routes"] = routes
        self._save_config(config)
        return True

    def update_route(self, route_id: str, **kwargs) -> bool:
        """更新路由"""
        config = self._load_config()
        routes = config.get("routes", [])

        for route in routes:
            if route.get("id") == route_id:
                route.update(kwargs)
                config["routes"] = routes
                self._save_config(config)
                return True

        return False

    def delete_route(self, route_id: str) -> bool:
        """删除路由"""
        config = self._load_config()
        routes = config.get("routes", [])

        original_count = len(routes)
        routes = [r for r in routes if r.get("id") != route_id]

        if len(routes) < original_count:
            config["routes"] = routes
            self._save_config(config)
            return True

        return False

    def toggle_route(self, route_id: str) -> bool:
        """切换路由启用状态"""
        route = self.get_route_by_id(route_id)
        if route:
            new_state = not route.get("enabled", True)
            return self.update_route(route_id, enabled=new_state)
        return False

    def get_preset_routes(self) -> Dict[str, Dict]:
        """获取预设路由模板"""
        return PRESET_ROUTES.copy()

    def add_preset_route(self, preset_key: str) -> bool:
        """从预设添加路由"""
        if preset_key not in PRESET_ROUTES:
            return False

        preset = PRESET_ROUTES[preset_key]
        return self.add_route(
            route_id=preset_key,
            name=preset["name"],
            url=preset.get("url", ""),
            parser=preset.get("parser", "generic"),
            description=preset.get("description", preset["name"]),
            enabled=True
        )

    def test_route(self, url: str, parser: str = "generic") -> Dict:
        """测试路由是否可用"""
        from finance.news_fetcher import NewsFetcher

        fetcher = NewsFetcher()
        try:
            news = fetcher.fetch_from_url(url, parser=parser, limit=1)
            if news:
                return {"success": True, "message": f"成功获取 {len(news)} 条新闻", "count": len(news)}
            else:
                return {"success": False, "message": "未获取到新闻内容", "count": 0}
        except Exception as e:
            return {"success": False, "message": f"测试失败: {str(e)}", "count": 0}
