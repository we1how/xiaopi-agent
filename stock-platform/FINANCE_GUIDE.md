# Finance 功能使用指南

## 快速开始

### 1. 一键启动（推荐）

```bash
./start.sh
```

这个脚本会：
1. 检查 Docker 是否安装并运行
2. 自动启动 RSSHub 服务
3. 等待 RSSHub 就绪
4. 启动 Streamlit 应用

### 2. 手动启动

如果你更喜欢手动控制：

```bash
# 启动 RSSHub
docker-compose up -d

# 等待几秒后启动应用
streamlit run app.py
```

### 3. 停止服务

```bash
./stop.sh
```

或手动：

```bash
docker-compose down
```

---

## Finance 页面功能

### 三栏布局

1. **左侧 - RSS路由管理**
   - 查看已配置的 RSS 源
   - 启用/禁用路由
   - 添加新路由（支持预设和自定义）

2. **中间 - 新闻列表**
   - 显示选中路由的新闻
   - 勾选感兴趣的新闻
   - 点击查看详情
   - 导入选中到 AI 助手

3. **右侧 - AI分析助手**
   - 配置 API Key（支持 Moonshot/Claude）
   - 选择分析模板
   - 与 AI 对话分析新闻
   - 复制分析结果

---

## 内置 RSS 路由

| 名称 | 路径 | 说明 |
|------|------|------|
| 财联社深度 | `/cls/depth/1000` | 财联社深度报道 |
| 财联社电报 | `/cls/telegraph` | 7x24小时电报 |
| 新浪财经 | `/sina/column/roll` | 新浪财经滚动新闻 |
| 华尔街见闻 | `/wallstreetcn/hot` | 热门文章 |
| 东方财富 | `/eastmoney/search/web` | 资讯搜索 |

---

## 添加自定义 RSS 路由

1. 点击左侧「➕ 添加路由」
2. 选择预设或自定义
3. 填写信息：
   - 名称：显示名称
   - URL：完整的 RSSHub URL
   - 解析器：generic（通用）或 cls（财联社特定格式）
4. 点击「测试连接」验证
5. 点击「保存路由」

### RSSHub URL 格式

```
http://localhost:1200/{路由}/{参数}
```

示例：
- `http://localhost:1200/cls/depth/1000`
- `http://localhost:1200/sina/column/roll`

---

## AI 分析模板

### 内置模板

1. **股票影响分析** - 分析新闻对 A 股的影响程度
2. **新闻摘要** - 生成一句话摘要
3. **市场情绪分析** - 分析新闻反映的市场情绪
4. **行业影响分析** - 分析对相关行业的影响
5. **自定义分析** - 自由输入 prompt

### 自定义模板

1. 选择「自定义分析」模板
2. 在文本框中输入你的 prompt
3. 使用 `{news_content}` 作为新闻内容占位符

---

## API 配置

### Moonshot（推荐）

```
Base URL: https://api.moonshot.cn/v1
Model: kimi-k2.5
```

### Claude

```
Base URL: https://api.anthropic.com/v1
Model: claude-3-sonnet-20240229
```

---

## 故障排除

### RSSHub 连接失败

```bash
# 检查 RSSHub 是否运行
curl http://localhost:1200

# 查看日志
docker-compose logs rsshub

# 重启 RSSHub
docker-compose restart rsshub
```

### Docker 未安装

```bash
# macOS
brew install --cask docker

# 启动 Docker Desktop
open /Applications/Docker.app
```

### 新闻获取失败

1. 检查 RSSHub 是否正常运行
2. 测试具体路由：
   ```bash
   curl http://localhost:1200/cls/depth/1000
   ```
3. 检查网络连接
4. 查看 finance 模块日志

---

## 文件结构

```
stock-platform/
├── docker-compose.yml    # RSSHub 部署配置
├── start.sh              # 一键启动脚本
├── stop.sh               # 停止脚本
├── FINANCE_GUIDE.md      # 本指南
├── finance/              # Finance 模块
│   ├── finance_page.py   # 主页面
│   ├── rss_manager.py    # RSS 路由管理
│   ├── news_fetcher.py   # 新闻获取
│   ├── prompt_templates.py # Prompt 管理
│   └── ai_chat.py        # AI 聊天组件
├── utils/                # 工具模块
│   └── rsshub_manager.py # RSSHub 管理
└── config/               # 配置文件
    ├── rss_routes.json   # RSS 路由配置
    └── prompts.json      # Prompt 模板
```
