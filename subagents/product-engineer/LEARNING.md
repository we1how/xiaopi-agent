# ProductEngineer - 学习日志

> 技术探索，永无止境

---

## 学习记录索引（近30天）

| 日期 | 优先级 | 来源 | 标题/主题 | 关键词 |
|------|--------|------|-----------|--------|
| 2026-03-07 | P0 | GitHub/HN | claude-replay - 会话可视化工具 | AI开发, 会话分享, HTML播放器 |
| 2026-03-07 | P0 | GitHub Trending | webnovel-writer - 长篇网文AI创作 | Claude Code插件, RAG, 761⭐ |
| 2026-03-07 | P0 | Vercel Blog | Stripe GA + Slack Agent Skill | Skill as Code, AI-native平台 |
| 2026-03-06 | P0 | GitHub / HN Show HN | PageAgent - 阿里页内GUI Agent | 纯前端, Copilot, DOM文本化 |
| 2026-03-05 | P0 | Vercel Blog | Security boundaries in agentic architectures | Agent安全, 四层边界, Prompt Injection |
| 2026-03-05 | P0 | GitHub Trending | Alibaba OpenSandbox | AI沙盒, 多语言SDK, 安全隔离 |
| 2026-03-04 | P0 | GitHub Trending | UltraRAG - 首个MCP架构RAG框架 | 低代码, MCP协议, RAG编排 |
| 2026-03-03 | P0 | GitHub Trending | Microsoft MarkItDown - 文档转Markdown工具 | LLM文档处理, MCP, PDF/Office |
| 2026-03-02 | P0 | GitHub Trending | ByteDance DeerFlow 2.0 - Agent基础设施 | LangGraph, Skill加载, Sandbox |
| 2026-03-01 | P0 | GitHub Trending | Alibaba OpenSandbox - AI应用沙盒 | 安全隔离, 多语言SDK |
| 2026-02-28 | P1 | GitHub Trending | Scrapling自适应网页抓取 + PageIndex | 反爬, Vectorless RAG |
| 2026-02-28 | P1 | GitHub Trending | OpenSandbox + PageIndex + 其他 | 沙盒, 无向量RAG |
| 2026-02-25 | P1 | 实战项目 | Stock Platform MVP开发 | backtesting.py, Streamlit |

---

## 2026年3月

### 2026-03-07 [P0] 周末深度分析 - AI开发工具与平台演进

**主题**：claude-replay + webnovel-writer + Vercel平台能力演进
**来源**：GitHub/Hacker News + Vercel Blog
**周末特别任务**：深度技术分析与信息差评估

#### 内容1：claude-replay - Claude Code会话可视化
**链接**：<https://github.com/es617/claude-replay>

**核心洞察**：
- 将`~/.claude/projects/` JSONL日志转换为**自包含HTML播放器**
- 单文件输出、无外部依赖，支持邮件分享/iframe嵌入
- 功能完整：播放控制、速度调节、书签章节、敏感信息脱敏
- 解决痛点：AI辅助开发过程难分享（录屏太大、文本日志难读）

**信息差价值（国内落地）**：
- 国内Cursor/Windsurf用户增长快，但缺乏类似开源会话分享工具
- 可复用模式：AI IDE本地日志→可分享交互式回放
- 潜在产品：面向国内开发者社区的"AI编程过程可视化"工具

#### 内容2：webnovel-writer - 长篇网文AI创作系统
**链接**：<https://github.com/lingfengQAQ/webnovel-writer> (761⭐)

**核心洞察**：
- **首个**专门针对长篇网文场景优化的Claude Code插件
- 解决AI写作两大痛点：**遗忘**（上下文丢失）和**幻觉**（设定不一致）
- 支持**200万字量级**连载创作
- 核心创新：RAG记忆系统（ModelScope Embeddings + Jina Reranker）+ 追读力系统

**信息差价值（国外→国内）**：
- 典型"国外工具+国内场景"创新：Claude Code + 中国网文产业（300亿+市场）
- 可复用模式：Coding Agent→Writing Agent，适用于公众号/小红书/短视频脚本
- 技术架构参考：双阶段检索（Embedding召回+Reranker精排）+ 显式记忆管理

#### 内容3：Vercel平台能力演进
| 功能 | 核心洞察 | 信息差价值 |
|------|----------|-----------|
| Stripe GA | `vercel integration add stripe`一键生产支付，自动密钥交换 | 支付集成"零配置"体验 |
| Slack Agent Skill | `npx skills add vercel-labs/slack-agent-skill`，单会话完成全链路 | "Skill as Code"模式 |
| Bulk Redirects | 百万级redirect低成本低延迟实现 | 边缘配置规模化架构 |

**核心洞察**：AI-native平台定义——让整个开发工作流都可被Agent理解和操作

#### 主动提案
| 提案 | 理由 | 建议行动 |
|------|------|----------|
| 引入claude-replay工具链 | 团队使用Claude Code频繁，缺乏会话分享机制 | 1. 全局安装`npm install -g claude-replay`<br>2. 建立会话分享规范 |
| 评估"Skill as Code"架构 | Vercel Skills展示可复用Agent工作流最佳实践 | 1. 调研Vercel Skills规范复用性<br>2. 设计Agent Skill封装标准 |
| 研究webnovel-writer的RAG架构 | 长文本记忆方案对通用Agent上下文管理有参考价值 | 1. 读取docs/architecture.md<br>2. 评估Embedding+Reranker双阶段检索 |
| 关注中国开发者Agent创新 | webnovel-writer证明国内开发者能深度结合国外工具与本土场景 | 1. 监控GitHub Trending中文项目<br>2. 建立"国内Agent应用"追踪清单 |

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

### 2026-03-06 [P0] PageAgent - 阿里页内GUI Agent

| 项目 | 内容 |
|------|------|
| **来源** | GitHub / HN Show HN |
| **链接** | https://github.com/alibaba/page-agent |
| **热度** | 66 points, 35 comments |

**核心洞察**：
1. **纯前端架构**：JavaScript SDK，无需服务器端headless浏览器
2. **文本优先**：基于DOM文本化而非截图OCR，大幅降低token消耗
3. **BYOLL设计**：自带LLM，支持OpenAI/Claude/Qwen等任意兼容API
4. **产品化场景**：SaaS Copilot、智能表单填写、无障碍访问
5. **技术栈**：TypeScript，基于browser-use，MIT许可证

**可应用性**：
- 适合内部工具/后台系统的AI化改造
- 几行代码即可添加Copilot功能，无需后端重构
- 无服务器成本，数据不离开浏览器，安全合规

**提案建议**：
选择1个内部高频后台系统进行PageAgent POC验证（2天完成），验证复杂表单的自然语言操作效果和成本优势。

---

### 2026-03-05 [P0] Security boundaries in agentic architectures

**来源**：Vercel Blog (Malte Ubl, Harpreet Arora)  
**主题**：Agentic系统安全边界设计

**核心洞察**：
1. **四层安全边界**：Agent本身、Agent Secrets、生成代码执行、文件系统/环境
2. **零边界架构风险**：当前默认架构使生成代码能直接访问所有凭据，存在严重Prompt Injection风险
3. **三层演进路径**：
   - 零边界（当前默认）→ Secret Injection Proxy → 独立计算分离

**可应用性**：
- 评估OpenSandbox作为Agent执行环境
- 设计Agent Secrets管理机制
- 研究Secret Injection Proxy模式

---

### 2026-03-05 [P0] Alibaba OpenSandbox

**来源**：GitHub Trending Python  
**主题**：AI应用通用沙盒平台

**核心洞察**：
1. **多语言SDK**：Python/Java/JS/C#/Go
2. **统一沙盒API**：Docker/K8s运行时
3. **安全隔离**：命令执行、文件系统、代码解释器隔离
4. **网络策略**：Ingress Gateway + Egress Controls

**适用场景**：
- Coding Agents
- GUI Agents
- Agent Evaluation
- RL Training

---

_Building, learning, iterating_ ⚡
