# ProductEngineer - 学习日志

> 技术探索，永无止境

---

## 学习记录索引（近30天）

| 日期 | 优先级 | 来源 | 标题/主题 | 关键词 |
|------|--------|------|-----------|--------|
| 2026-03-05 | P0 | Vercel Blog/GitHub | Agent Security Boundaries + OpenSandbox | 安全架构, 沙盒隔离, Level 3 |
| 2026-03-04 | P0 | GitHub Trending | UltraRAG - 首个MCP架构RAG框架 | 低代码, MCP协议, RAG编排 |
| 2026-03-03 | P0 | GitHub Trending | Microsoft MarkItDown - 文档转Markdown工具 | LLM文档处理, MCP, PDF/Office |
| 2026-03-02 | P0 | GitHub Trending | ByteDance DeerFlow 2.0 - Agent基础设施 | LangGraph, Skill加载, Sandbox |
| 2026-03-01 | P0 | GitHub Trending | Alibaba OpenSandbox - AI应用沙盒 | 安全隔离, 多语言SDK |
| 2026-02-28 | P1 | GitHub Trending | Scrapling自适应网页抓取 + PageIndex | 反爬, Vectorless RAG |
| 2026-02-28 | P1 | GitHub Trending | OpenSandbox + PageIndex + 其他 | 沙盒, 无向量RAG |
| 2026-02-25 | P1 | 实战项目 | Stock Platform MVP开发 | backtesting.py, Streamlit |

---

## 2026年3月

### 2026-03-05 [P0] Security Boundaries in Agentic Architectures

**主题**：Security boundaries in agentic architectures + Alibaba OpenSandbox  
**来源**：Vercel Blog + GitHub (Alibaba/OpenSandbox)  
**链接**：<https://vercel.com/blog/security-boundaries-in-agentic-architectures>

**核心洞察**：
1. **Agent安全架构四层边界**：Agent Harness / Secrets / 生成代码 / 文件系统。当前主流工具（Claude Code/Cursor）默认"零边界"，生成代码可直接访问所有凭据，存在严重Prompt Injection风险
2. **安全架构演进路径**：
   - Level 1: 零边界（现状）
   - Level 2: Secret Injection Proxy（代理注入凭据，防泄露但无法阻止运行时滥用）
   - Level 3: 独立计算分离（Agent与生成代码运行在不同VM/沙盒）← 推荐
3. **Alibaba OpenSandbox**：恰好实现Level 3架构的开源方案，支持多语言SDK、Docker/K8s运行时，专门面向Coding Agents、GUI Agents、AI代码执行场景

**信息差分析**：
- **国内讨论度**：极低 - Agent沙盒安全在国内尚未成为主流话题
- **技术组合价值**：Vercel架构理论 + Alibaba开源实现 = 完整可落地的技术栈
- **紧迫性**：中 - 安全加固，非阻塞但重要

**主动提案**：
1. **评估OpenSandbox集成** — 是否作为我们Agent的代码执行沙盒环境？
2. **建立技术壁垒** — 国内Agent安全关注度低，抢先布局形成能力优势
3. **输出技术内容** — 可输出技术文章/内部分享

**下一步**：
- 本周内完成OpenSandbox技术调研
- 评估与当前OpenClaw执行层的集成可行性
- 决策是否引入作为安全加固措施

---

### 2026-03-04 [P0] UltraRAG - 首个MCP架构RAG开发框架

**来源**：GitHub Trending - OpenBMB/UltraRAG  
**链接**：<https://github.com/OpenBMB/UltraRAG>  
**主题**：基于Model Context Protocol的低代码RAG管道编排框架

**核心洞察**：
1. **MCP架构落地RAG**：UltraRAG是第一个将Retriever、Generator等核心组件标准化为独立MCP Server的框架，通过MCP Client实现条件分支、循环等复杂控制流编排
2. **YAML驱动低代码**：几十行YAML即可实现迭代式RAG、多路召回等复杂逻辑，大幅降低实验门槛
3. **可视化RAG IDE**：提供Pipeline Builder支持"画布搭建"与"代码编辑"双向实时同步，真正实现RAG开发的可视化调试
4. **开箱即用的评估体系**：内置标准化评测流程和主流研究benchmark，解决RAG领域"效果难复现"痛点
5. **DeepResearch Pipeline内置**：一键部署多步检索整合生成万字调研报告的能力

**信息差分析**：
- **国内讨论度**: 极低（刚 trending 1天）
- **应用场景**: OpenClaw技能编排、RAG工作流设计、MCP生态扩展
- **行动建议**: **本周调研** - 评估YAML编排语法和MCP Server注册机制，考虑迁移到OpenClaw技能层

---

### 2026-03-03 [P0] Microsoft MarkItDown - LLM文档处理利器

**来源**：GitHub Trending - microsoft/markitdown  
**链接**：<https://github.com/microsoft/markitdown>  
**主题**：将PDF/Word/Excel/PPT等任意文档转换为LLM友好的Markdown格式

**核心洞察**：
1. **精准定位**：填补"文档→LLM可消费文本"的空白，保留文档结构（标题、列表、表格、链接）
2. **MCP协议支持**：提供Model Context Protocol服务器，可直接集成Claude Desktop等工具
3. **插件化架构**：按需安装依赖（`pip install 'markitdown[pdf,docx]'`），避免臃肿
4. **多模态覆盖**：支持PDF、Office、图片OCR、音频转录、YouTube字幕、ZIP解压等
5. **微软背书**：与AutoGen同团队，有望成为文档处理领域的事实标准

**信息差分析**：
- **国内讨论度**: 少量（刚 trending 2天）
- **应用场景**: OpenClaw文档解析、知识库构建、RAG预处理
- **行动建议**: **本周调研** - 评估替换当前文档解析方案，特别是PDF表格提取场景

---

### 2026-03-02 [P0] DeerFlow 2.0 - 全栈智能体基础设施

**来源**：GitHub Trending - ByteDance DeerFlow 2.0  
**主题**：SuperAgent Harness - 从Deep Research框架到全栈智能体基础设施

**洞察**：
DeerFlow 2.0通过LangGraph+LangChain构建，定义了新一代Agent架构范式：
- **渐进式Skill加载**（按需而非全量）
- **All-in-One沙盒**（Browser+Shell+File+MCP+VSCode Server）
- **长短时记忆分层**
- **子代理并行编排**

字节跳动在GitHub Trending登顶说明市场对「Agent基础设施」需求强烈。

**可应用**：
- 借鉴DeerFlow的Context Engineering和Skill渐进加载机制，优化OpenClaw的token使用效率
- 评估All-in-One Sandbox方案替代当前多容器架构

---

### 2026-03-01 [P0] Alibaba OpenSandbox - AI应用沙盒平台

**来源**：GitHub Trending - Alibaba OpenSandbox  
**主题**：AI应用沙盒平台 - Agent安全执行基础设施

**洞察**：
OpenSandbox提供了统一的沙盒协议和多语言SDK，解决了Coding Agents/GUI Agents的安全隔离和可扩展部署问题。阿里巴巴和Anthropic都在布局Agent基础设施，说明这是下一代Agent系统的关键能力。

**可应用**：
- 评估是否将OpenSandbox集成到OpenClaw的Agent执行层
- 提供更安全的代码执行和工具调用环境

---

## 2026年2月

### 2026-02-28 [P1] 周末技术发现

#### 1. Scrapling - 自适应网页抓取框架

**来源**：GitHub Trending Python

**核心特性**：
- 自适应解析器：自动学习网站变化并重新定位元素
- 内置绕过反爬系统（Cloudflare Turnstile等）
- StealthyFetcher/DynamicFetcher 支持无头浏览器抓取
- 可扩展的爬虫框架，支持暂停/恢复和代理轮换

**主动提案**：
- 🎯 发现机会：Scrapling可用于Stock Platform的数据抓取模块

#### 2. PageIndex - Vectorless RAG

**来源**：GitHub Trending

**核心创新**：
- 无需向量数据库和chunking的RAG新方法
- 基于树结构的文档索引 + LLM推理检索
- 模拟人类专家阅读长文档的方式
- 提供MCP Server和API集成

**主动提案**：
- 🤝 需要协作：评估PageIndex是否可以集成到现有知识库系统

#### 3. OpenSandbox（阿里巴巴开源AI沙箱平台）

**核心价值**：通用AI应用沙箱平台，支持Docker/Kubernetes运行时
**技术亮点**：多语言SDK（Python/Java/JS）、统一沙箱协议API、内置网络策略
**应用场景**：AI代码执行、浏览器自动化、桌面环境、RL训练

#### 4. 其他发现

- **wifi-densepose**：WiFi信号实现穿墙人体姿态估计，使用普通mesh路由器
- **Trae Agent**：字节跳动开源的LLM软件工程Agent

---

### 2026-02-25

**今日学习**：
- 主题：Stock Platform MVP开发
- 来源：实战项目
- 收获：
  - 深入使用backtesting.py框架
  - Streamlit高级组件（session_state, caching）
  - DuckDB与Pandas的高效集成
  - 动态策略加载的实现方法

**代码片段**：
```python
# 动态策略加载
def load_strategy_from_file(file_path):
    spec = importlib.util.spec_from_file_location("strategy", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

**下一步**：
- AI策略优化模块设计
- 考虑集成Optuna进行超参优化

---

## 学习记录模板

```markdown
## {日期}

### 今日学习
- 主题：{技术/工具}
- 来源：{文档/项目/教程}
- 收获：{要点}
- 代码片段：{关键代码}

### 实验记录
- 尝试：{尝试内容}
- 结果：{成功/失败}
- 踩坑：{遇到的问题}
- 解决：{解决方案}

### 主动提案
- 发现：{发现}
- 建议：{建议}

### 下一步
- {行动计划}
```

---

## 国外情报源（信息差优势）

**每日自动获取**：
```bash
python scripts/western_intelligence.py
```

**数据源**：
- Hacker News（技术圈风向标）
- GitHub Trending（开源趋势）
- Product Hunt（新产品发现）
- Vercel/Stripe Blog（工程文化）

**信息差分析框架**：
1. **发现**：国外新技术/工具/框架
2. **验证**：技术成熟度和社区活跃度
3. **应用**：在项目中试用的场景
4. **分享**：整理成技术文章/教程

**数据位置**：`~/.openclaw/workspace/data/agent-intelligence/product-engineer/`

---

_Building, learning, iterating_ ⚡
