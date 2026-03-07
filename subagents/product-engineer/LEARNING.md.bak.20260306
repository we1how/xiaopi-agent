# LEARNING.md - Product Engineer 学习记录

## 学习记录索引

### 已学习项目（近7天）
| 日期 | 项目名称 | 来源 | 核心洞察 |
|------|----------|------|----------|
| 2026-03-05 | Security boundaries in agentic architectures | Vercel Blog | Agent安全的四层架构与隔离策略 |
| 2026-03-05 | Alibaba OpenSandbox | GitHub Trending | AI应用通用沙盒平台，支持多语言SDK |

---

### 今日学习（2026-03-05）

#### 内容1：Security boundaries in agentic architectures
- **来源**：Vercel Blog (Malte Ubl, Harpreet Arora)
- **核心洞察**：Agentic系统需要四层安全边界——Agent本身、Agent Secrets、生成代码执行、文件系统/环境。当前默认的"零边界"架构使生成的代码能直接访问所有凭据，存在严重的Prompt Injection风险。
- **信息差价值**：高
- **可应用性**：架构

#### 内容2：Alibaba OpenSandbox
- **来源**：GitHub Trending Python
- **核心洞察**：阿里巴巴开源的AI应用通用沙盒平台，提供多语言SDK（Python/Java/JS/C#/Go）、统一沙盒API、Docker/K8s运行时，专门支持Coding Agents、GUI Agents、AI代码执行等场景。
- **信息差价值**：高
- **可应用性**：工具/架构

---

## 关键学习要点

### Agent安全架构最佳实践

**四 Actor 模型**：
1. **Agent Harness**: 可信任的标准SDLC组件
2. **Agent Secrets**: API Token、数据库凭据等，需严格保护
3. **Generated Code Execution**: 不可信的wildcard，需要隔离
4. **Filesystem/Environment**: 运行环境

**三层安全架构演进**：
1. **零边界（当前默认）**：所有组件共享安全上下文，风险最高
2. **Secret Injection Proxy**: 代理层注入凭据，防止泄露但无法阻止运行时滥用
3. **独立计算分离**: Agent Harness与生成代码在独立VM/沙盒中运行，最优安全

### Alibaba OpenSandbox 特性
- 多语言SDK支持
- Docker + Kubernetes高性能运行时
- 内置命令执行、文件系统、代码解释器
- Ingress Gateway + Egress Controls网络策略
- 适用场景：Coding Agents、GUI Agents、Agent Evaluation、RL Training

---

## 可应用技术

### 立即可以应用：
- [ ] 评估OpenSandbox作为我们的Agent执行环境
- [ ] 设计Agent Secrets管理机制，避免直接暴露给Agent
- [ ] 研究Secret Injection Proxy模式

### 需要进一步研究：
- [ ] OpenSandbox与现有K8s基础设施集成方案
- [ ] 与Claude Code/Cursor沙盒模式的对比
