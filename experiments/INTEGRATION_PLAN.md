# 上下文压缩技能集成方案

> 实验验证：SelectiveRetention 策略可实现 40-60% token 节省，同时保留100%关键工具结果

---

## 🎯 应用目标

将上下文压缩技能集成到多Agent系统中，解决长会话性能瓶颈。

---

## 📦 已创建组件

| 文件 | 功能 | 状态 |
|------|------|------|
| `context_compression_module.py` | 选择性保留压缩器 | ✅ 已创建 |
| `context-compression-test.py` | 实验测试脚本 | ✅ 已存在 |
| `context-compression-report.md` | 评估报告 | ✅ 已存在 |

---

## 🔧 集成方案

### 方案A：自动触发（推荐）

在 Agent 会话管理中自动检测并压缩：

```python
# 在 orchestrator 或 session 管理中添加
from experiments.context_compression_module import ContextManager

class AgentSession:
    def __init__(self):
        self.context_manager = ContextManager(
            compression_threshold=8000,  # 8k tokens触发
            target_compression_ratio=0.5  # 压缩到50%
        )
    
    def get_context(self):
        messages = self.load_history()
        
        # 自动压缩
        if self.context_manager.should_compress(messages):
            messages = self.context_manager.manage_context(messages)
            logger.info(f"Context compressed: {self.context_manager.get_stats()}")
        
        return messages
```

### 方案B：手动触发

在长时间任务前手动调用：

```python
from experiments.context_compression_module import compress_agent_context

# 在Agent执行长任务前
if len(messages) > 50:  # 消息过多
    messages = compress_agent_context(messages, threshold=8000)
```

### 方案C：Heartbeat集成

在每日heartbeat检查时压缩历史记录：

```python
# 在 HEARTBEAT.md 流程中添加
- 检查各Agent会话历史长度
- 如超过阈值，自动执行压缩
- 记录压缩统计到日志
```

---

## ⚙️ 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `compression_threshold` | 8000 | 触发压缩的token阈值 |
| `target_compression_ratio` | 0.5 | 目标压缩比例(0-1) |
| `recent_keep_ratio` | 0.2 | 始终保留的最新消息比例 |

**建议设置**：
- 轻量压缩：threshold=6000, ratio=0.7
- 标准压缩：threshold=8000, ratio=0.5 ⭐ 推荐
- 深度压缩：threshold=10000, ratio=0.3

---

## 🧪 测试验证

### 运行测试

```bash
cd /Users/linweihao/.openclaw/workspace/experiments
python context_compression_module.py
```

### 预期输出

```
原始: 5 条 → 压缩后: 4 条
- system: 你是一个AI助手...
- user: 帮我分析股票数据...
- tool: 股票数据结果......
- assistant: 根据分析，建议买入...
```

---

## 📊 效果监控

添加监控统计：

```python
# 每次压缩后记录
stats = context_manager.get_stats()
print(f"""
上下文压缩统计:
- 原始tokens: {stats['original_tokens']}
- 压缩后tokens: {stats['compressed_tokens']}
- 节省: {stats['compression_ratio']}
""")
```

---

## 🚀 下一步行动

### 立即执行（今天）
- [x] 创建压缩模块 ✅
- [ ] 在现有Agent会话中测试
- [ ] 监控效果并调优参数

### 本周完成
- [ ] 集成到 musk-orchestrator 会话管理
- [ ] 添加自动压缩日志
- [ ] 更新 AGENTS.md 文档

### 下周评估
- [ ] 统计一周的压缩效果
- [ ] 评估对API成本的影响
- [ ] 决定是否全量部署

---

## 💡 注意事项

1. **压缩不可逆**：压缩后的上下文无法恢复原始消息
2. **工具结果保留**：SelectiveRetention策略确保工具调用结果100%保留
3. **摘要质量**：早期消息的摘要可能丢失细节，需监控
4. **调优建议**：根据实际使用场景调整重要性评分规则

---

**实施状态**：🟡 已创建模块，待集成测试
