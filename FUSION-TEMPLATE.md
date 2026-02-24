# 🤖 VS Code + Claude Code + OpenClaw 融合指令模板

> **使用方式**: 在 Claude Code 聊天中直接复制并填充 `{}` 部分，或保存为代码片段快速插入

---

## 🎯 融合触发指令

### 1. 快速交接 - 一句话触发

```
让 OpenClaw 接管
```

**效果**: Claude Code 自动生成 handoff.md，OpenClaw 立即开始执行

---

### 2. 标准交接格式

```
🔄 交给 OpenClaw:

**已完成**: {刚才完成的工作}
**需要执行**: {具体任务}
**优先级**: {P0/P1/P2}
**特殊要求**: {额外注意事项}
```

**示例**:
```
🔄 交给 OpenClaw:

**已完成**: 实现了用户登录的 JWT 认证逻辑
**需要执行**: 
  1. 为 auth.ts 生成完整的单元测试
  2. 运行测试并修复失败项
  3. 格式化代码并提交
  4. 创建 PR 到 main 分支
**优先级**: P0
**特殊要求**: 测试要覆盖边界情况（过期 token、无效签名）
```

---

### 3. 完整项目交接

```markdown
# OpenClaw Handoff Document

## 📋 任务概览
- **来源**: Claude Code (VS Code)
- **时间**: {当前时间}
- **项目**: ${workspaceFolder}

## ✅ 已完成工作
{详细描述刚才完成的代码/设计}

## 📁 修改的文件
```
{文件列表，每行一个}
```

## 🎯 需要 OpenClaw 执行
1. {具体步骤1}
2. {具体步骤2}
3. {具体步骤3}

## 🔗 相关上下文
- 业务背景: {为什么做这个}
- 技术决策: {为什么选择这个方案}
- 已知问题: {待解决的边界情况}

## 📤 期望输出
{完成后的具体成果}
```

---

## 🧠 Claude Code 提示词模板

### 让 Claude Code 主动建议交接

```
在完成这个功能后，请：
1. 检查是否有需要 OpenClaw 接手的任务
2. 如果有，使用标准交接格式输出
3. 告诉我可以在 VS Code Command Palette 运行哪个任务
```

### 代码注释标记（供 OpenClaw 扫描）

```typescript
// TODO(OpenClaw): 生成这个函数的单元测试
function calculateDiscount(price: number, code: string): number {
  // ...
}

// FIXME(OpenClaw): 添加输入验证，防止 XSS
export function renderUserInput(input: string): string {
  // ...
}

// NOTE(OpenClaw): 这部分逻辑需要性能优化
// 建议：缓存结果、使用 Web Worker、或分批处理
```

---

## 🔄 常用工作流快捷指令

### 开发 → 测试 → PR 完整流程

```
Claude Code: 实现 {功能描述}
  ↓
Claude Code: "让 OpenClaw 接管"
  ↓
OpenClaw: 
  - 读取 .openclaw/handoff.md
  - 生成测试
  - 运行测试
  - git commit
  - 创建 PR
  - 在 VS Code 通知结果
```

### 重构批量应用

```
Claude Code: 演示如何重构 {旧模式} → {新模式}
  ↓
Claude Code: "把这个模式应用到全项目，让 OpenClaw 执行"
  ↓
OpenClaw:
  - 全局搜索旧模式
  - 批量替换
  - 运行测试验证
  - 生成重构报告
```

### 紧急热修复

```
Claude Code: 快速修复 {bug描述}
  ↓
Claude Code: "让 OpenClaw 立即部署"
  ↓
OpenClaw:
  - 创建 hotfix 分支
  - 提交修复
  - 合并到 main
  - 打 tag
  - 触发部署
  - 发送通知
```

---

## 📊 任务状态标记

在代码或文档中使用以下标记，OpenClaw 会自动识别并更新状态：

| 标记 | 含义 | OpenClaw 动作 |
|------|------|---------------|
| `// TODO(OpenClaw)` | 待办事项 | 加入任务队列 |
| `// FIXME(OpenClaw)` | 需要修复 | 高优先级处理 |
| `// REVIEW(OpenClaw)` | 需要审查 | 代码审查流程 |
| `// TEST(OpenClaw)` | 缺少测试 | 生成测试用例 |
| `// DOC(OpenClaw)` | 缺少文档 | 生成/更新文档 |
| `// OPTIMIZE(OpenClaw)` | 需要优化 | 性能分析+优化 |

---

## 🔧 VS Code 快捷操作

### 快捷键绑定（推荐添加到 keybindings.json）

```json
[
  {
    "key": "ctrl+shift+o",
    "command": "workbench.action.tasks.runTask",
    "args": "🚀 OpenClaw: 接管当前任务"
  },
  {
    "key": "ctrl+shift+t",
    "command": "workbench.action.tasks.runTask",
    "args": "🧪 OpenClaw: 运行测试"
  },
  {
    "key": "ctrl+shift+p",
    "command": "workbench.action.tasks.runTask",
    "args": "📦 OpenClaw: 提交并创建 PR"
  }
]
```

### Command Palette 快捷入口

```
Cmd/Ctrl+Shift+P → "Tasks: Run Task" → 选择 OpenClaw 任务
```

---

## 💡 最佳实践

1. **保持上下文完整**: Claude Code 交给 OpenClaw 时，务必传递完整的业务背景
2. **使用标准化标记**: `// TODO(OpenClaw)` 让 OpenClaw 能自动扫描任务
3. **渐进式交接**: 复杂任务分步交接，不要一次性丢给 OpenClaw 太多
4. **反馈循环**: OpenClaw 完成后，在 Claude Code 中查看结果并继续
5. **任务追踪**: 使用 `.openclaw/tasks/` 目录管理长期任务

---

**记住**: Claude Code 是你的左手（思考+创造），OpenClaw 是你的右手（执行+自动化）。两只手配合，干活不累。
