# 🎬 融合工作流实战演示

> **场景**: 你在 VS Code 中开发 newsAI 项目的新功能——"新闻情绪指数计算"
> **目标**: 感受"一个超级 AI 助手用两只手干活"的无缝体验

---

## 工作流全景图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🧠 一个超级 AI 助手                           │
│                                                                       │
│    ┌─────────────────────┐        ┌─────────────────────┐            │
│    │   🤖 Claude Code    │ ←——→   │    ⚡ OpenClaw      │            │
│    │    (左手 - 思考)     │  融合   │   (右手 - 执行)      │            │
│    └─────────────────────┘        └─────────────────────┘            │
│            ↑                              ↑                          │
│            │       VS Code                │      Shell/Terminal      │
│            │       (对话界面)              │      (执行界面)          │
│            │                              │                          │
│    ╔══════════════════════════════════════════════════════════╗       │
│    ║     👤 你 (MuskOrchestrator) - 只需要说人话即可           ║       │
│    ╚══════════════════════════════════════════════════════════╝       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎥 场景演示：开发新闻情绪指数功能

### 【第1幕】需求分析与设计

**📍 位置**: VS Code - Claude Code 聊天窗口

**你**:
```
我要给 newsAI 加一个"情绪指数"功能：
- 分析单条新闻的情绪（正面/负面/中性）
- 计算当天所有新闻的整体情绪指数
- 可视化展示

先帮我设计架构。
```

**Claude Code (左手)**:
```
好的，我来设计这个情绪指数模块的架构：

📁 建议的文件结构:
src/
  sentiment/
    ├── analyzer.ts          # 核心分析器
    ├── types.ts             # 类型定义
    ├── index-calculator.ts  # 指数计算
    └── visualizer.ts        # 可视化

🎯 关键技术决策:
1. 使用 Moonshot API 进行情感分析
2. 指数计算采用加权平均 (阅读量权重)
3. 可视化使用简单的 ASCII 图表 + 可选的 Web 图表

💡 接下来我可以：
A) 完整实现所有代码
B) 先实现核心 analyzer，然后让 OpenClaw 接手测试和文档

建议选 B——你确认架构后，我快速写核心代码，剩下的交给 OpenClaw 标准化处理。
```

**你**:
```
选 B，开始吧
```

---

### 【第2幕】核心代码开发

**📍 位置**: VS Code - Claude Code Inline 编辑

**Claude Code (左手)** 快速编写核心代码：

```typescript
// src/sentiment/analyzer.ts
import { OpenAI } from 'openai';

export type Sentiment = 'positive' | 'negative' | 'neutral';

export interface SentimentResult {
  sentiment: Sentiment;
  score: number;  // -1 to 1
  confidence: number;
}

export class SentimentAnalyzer {
  private client: OpenAI;
  
  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey, baseURL: 'https://api.moonshot.cn/v1' });
  }

  async analyze(text: string): Promise<SentimentResult> {
    // TODO(OpenClaw): 添加缓存机制，避免重复调用 API
    const response = await this.client.chat.completions.create({
      model: 'moonshot-v1-8k',
      messages: [
        {
          role: 'system',
          content: '分析文本情绪，返回 JSON: {sentiment: "positive|negative|neutral", score: -1到1, confidence: 0到1}'
        },
        { role: 'user', content: text }
      ],
      response_format: { type: 'json_object' }
    });
    
    return JSON.parse(response.choices[0].message.content!);
  }
}

// FIXME(OpenClaw): 需要添加错误处理和重试逻辑
// TEST(OpenClaw): 为 analyze 方法生成单元测试
```

**Claude Code (左手)**:
```
核心代码已完成。我注意到几个需要 OpenClaw 处理的事项：

🔄 **建议交给 OpenClaw 执行**:

**任务**: 完成情绪指数模块的测试、文档和集成
**原因**: 涉及批量测试生成、API 文档、CI 配置
**交接内容**:
```
- 新增文件: src/sentiment/analyzer.ts
- 功能: 新闻情绪分析核心模块
- 依赖: openai 包
- 待办: 缓存机制、错误处理、单元测试
```

**执行命令**: `openclaw run "完成情绪指数模块：生成测试、添加缓存、错误处理、更新文档"`

你可以在 VS Code 中：
1. Cmd+Shift+P → "Tasks: Run Task" → 选择 "🚀 OpenClaw: 接管当前任务"
2. 或者直接说 "让 OpenClaw 接管"
```

**你**:
```
让 OpenClaw 接管
```

---

### 【第3幕】OpenClaw 无缝接管

**📍 位置**: OpenClaw 自动激活（终端/后台）

**Claude Code 自动生成交接文件** `.openclaw/handoff.md`:

```markdown
# OpenClaw Handoff Document

## 📋 任务概览
- **来源**: Claude Code (VS Code)
- **时间**: 2026-02-21 12:30
- **项目**: /Users/linweihao/projects/newsAI

## ✅ 已完成工作
实现了新闻情绪分析的核心模块：
- SentimentAnalyzer 类，使用 Moonshot API
- 支持正面/负面/中性分类 + 置信度分数
- 返回结构化数据便于后续计算

## 📁 修改的文件
- src/sentiment/analyzer.ts (新建)

## 🎯 需要 OpenClaw 执行
1. 为 SentimentAnalyzer 生成完整单元测试（含 mock）
2. 添加 API 错误处理和指数退避重试
3. 实现 Redis 缓存机制（避免重复分析）
4. 生成 src/sentiment/index-calculator.ts
5. 更新项目 README，添加情绪指数使用说明
6. 运行全部测试确保不破坏现有功能
7. git commit 并创建 PR

## 🔗 相关上下文
- 使用 Moonshot API，baseURL: https://api.moonshot.cn/v1
- 模型: moonshot-v1-8k
- 返回格式: JSON with sentiment, score, confidence

## 📤 期望输出
- 完整的测试套件（覆盖率 >80%）
- 健壮的的错误处理
- 更新后的文档
- 可以合并的 PR
```

---

### 【第4幕】OpenClaw 全自动执行

**OpenClaw (右手)** 开始执行：

```
⚡ OpenClaw 已接管任务

📖 读取交接文档... 完成
📁 扫描项目结构... 完成

⚡ 执行步骤:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Step 1: 生成单元测试
   创建 tests/sentiment/analyzer.test.ts
   - 测试正常情感分析
   - 测试 API 错误处理
   - 测试无效输入
   覆盖率: 85%

✅ Step 2: 添加错误处理和重试
   更新 src/sentiment/analyzer.ts
   - 添加 try-catch
   - 实现指数退避重试 (3次)
   - 添加日志记录

✅ Step 3: 实现缓存机制
   创建 src/sentiment/cache.ts
   - Redis 客户端封装
   - 缓存 key: hash(text)
   - TTL: 24小时

✅ Step 4: 生成指数计算器
   创建 src/sentiment/index-calculator.ts
   - 加权平均算法
   - 时间衰减因子
   - 输出: 0-100 的情绪指数

✅ Step 5: 更新文档
   更新 README.md
   - 添加情绪指数章节
   - 使用示例代码
   - API 参考

✅ Step 6: 运行测试
   全部通过 (42/42)
   覆盖率: 87%

✅ Step 7: Git 操作
   git add .
   git commit -m "feat(sentiment): add news sentiment analysis module
   
   - Implement SentimentAnalyzer with Moonshot API
   - Add Redis caching for analysis results
   - Add retry logic with exponential backoff
   - Implement sentiment index calculator
   - Full test coverage (87%)
   - Update documentation"
   
   git push origin feature/sentiment-analysis

✅ Step 8: 创建 PR
   PR #127: feat(sentiment): add news sentiment analysis
   描述已自动生成，包含变更摘要

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 全部完成！PR 链接: https://github.com/we1how/newsAI/pull/127

📊 交付物:
- 8 个新文件
- 847 行代码
- 87% 测试覆盖率
- 1 个可合并的 PR
```

---

### 【第5幕】回到 VS Code 继续

**📍 位置**: VS Code - 通知栏显示 "OpenClaw 任务完成"

**Claude Code (左手)**:
```
🎉 OpenClaw 已完成全部任务！

📋 摘要:
- ✅ 测试已生成并通过
- ✅ 缓存和错误处理已添加
- ✅ 文档已更新
- ✅ PR #127 已创建

你可以：
1. 在 VS Code 侧边栏查看 Git 变更
2. 在浏览器中打开 PR 查看详情
3. 继续下一步开发

🤔 接下来做什么？
- A) 在 VS Code 里 review PR 内容
- B) 让 OpenClaw 部署到测试环境
- C) 开始开发下一个功能（情绪可视化图表）
```

**你**:
```
选 C，开始做可视化图表
```

**Claude Code (左手)**:
```
好的，我们来实现情绪可视化...

（继续循环：设计 → 编码 → 交接 → OpenClaw执行）
```

---

## 🔄 融合工作流的核心体验

### 你的感受

```
Before (分工模式):
❌ "Claude Code 写完代码，我还要手动打开终端"
❌ "OpenClaw 做了什么我得切窗口去看"
❌ "两个工具的上下文要重复说两遍"

After (融合模式):
✅ "在 VS Code 说一句话，OpenClaw 自动接手"
✅ "Claude Code 知道 OpenClaw 的存在，主动建议交接"
✅ "一个大脑两只手，我只管下指令"
```

### 关键融合点

| 融合点 | 实现方式 | 效果 |
|--------|----------|------|
| **上下文共享** | `.openclaw/handoff.md` 自动传递 | 不用重复说明 |
| **意图识别** | "让 OpenClaw 接管" 触发关键词 | 一句话激活 |
| **任务接力** | Claude Code 生成交接文档 | OpenClaw 无缝继续 |
| **代码标记** | `// TODO(OpenClaw)` 注释 | 待办自动入队 |
| **快捷入口** | VS Code Tasks + 快捷键 | 鼠标/键盘一键触发 |
| **进度同步** | OpenClaw 完成后通知 VS Code | 实时状态更新 |

---

## 🎯 其他典型场景

### 场景2: 紧急 Bug 修复

```
你: 生产环境有个 bug，用户登录后页面白屏

Claude Code: 
  "正在分析... 发现是 localStorage 解析错误。
  已修复 src/utils/storage.ts，添加了 try-catch。
  
  🔄 交给 OpenClaw 热修复部署？"

你: 立即部署

OpenClaw:
  - 创建 hotfix 分支
  - 提交修复
  - 合并到 main
  - 打 tag v1.2.1
  - 触发 GitHub Actions 部署
  - 发送 Slack 通知: "热修复已部署 v1.2.1"
```

### 场景3: 大规模重构

```
你: 把所有 var 改成 const/let

Claude Code:
  "这是一个批量重构任务，直接交给 OpenClaw 更合适。
  我帮你生成重构规则文件。"
  
  [生成 .openclaw/refactor-plan.md]

你: 让 OpenClaw 执行

OpenClaw:
  - 全局搜索所有 var
  - 根据上下文判断 const/let
  - 批量替换
  - 运行测试验证
  - 提交 PR
```

### 场景4: 代码审查

```
你: review 一下我刚写的代码

Claude Code:
  "代码逻辑没问题，但我注意到几个可以优化的地方...
  
  🔄 建议交给 OpenClaw:
  - 运行 lint 检查
  - 生成代码复杂度报告
  - 检查测试覆盖率
  - 给出优化建议"

你: 执行

OpenClaw:
  - 生成详细审查报告
  - 自动修复简单问题（格式化、unused imports）
  - 标记需要人工确认的问题
  - 在 VS Code 的 Problems 面板显示
```

---

## 🚀 快速开始

### 1. 配置环境

```bash
# 已自动生成以下文件
~/.claude/settings.json          # Claude Code 融合配置
.vscode/tasks.json               # 快捷任务
.vscode/settings.json            # VS Code 设置
.vscode/extensions.json          # 推荐扩展
FUSION-TEMPLATE.md               # 融合指令模板
```

### 2. VS Code 安装扩展

```
Cmd+Shift+P → "Extensions: Show Recommended Extensions"
安装 anthropic.claude-code 等推荐扩展
```

### 3. 第一次试用

```
1. 在 VS Code 打开任意项目
2. Cmd+Shift+P → "Tasks: Run Task" 
3. 选择 "🚀 OpenClaw: 接管当前任务"
4. 或者直接在 Claude Code 里说 "让 OpenClaw 接管"
```

---

**融合工作流已就绪。你现在拥有一个超级 AI 助手——左手 Claude Code 思考创造，右手 OpenClaw 执行自动化，你只需要说人话。**
