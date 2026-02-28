# 实施计划：集成上下文压缩到MuskOrchestrator

## 概述
将实验验证的上下文压缩模块集成到Agent会话管理中，实现自动检测和压缩长上下文，
提升多Agent会话性能，减少40-60%的token消耗。

## 需求
- [R1] 自动检测超过阈值的上下文（默认8000 tokens）
- [R2] 实现选择性保留压缩策略
- [R3] 100%保留工具调用结果和关键决策点
- [R4] 提供压缩统计监控和日志
- [R5] 支持配置化（阈值、压缩比例可调）
- [R6] 对现有功能零影响（渐进式推出）

## 架构变更
- [C1] 新建: `utils/context_manager.py` - 上下文管理器（从experiments迁移）
- [C2] 新建: `utils/context_compression.py` - 压缩策略实现
- [C3] 新建: `config/context.yaml` - 压缩配置
- [C4] 修改: `sessions_spawn` 调用逻辑 - 集成压缩
- [C5] 新建: `tests/test_context_compression.py` - 单元测试
- [C6] 新建: `tests/integration/test_session_compression.py` - 集成测试

## 实施步骤

### Phase 1: 基础设施搭建（估计30分钟）

1. **创建上下文压缩模块** (文件: `utils/context_compression.py`)
   - 行动: 从 `experiments/context_compression_module.py` 迁移核心逻辑
   - 原因: 提供独立可测试的压缩功能
   - 依赖: 无
   - 风险: 低
   - 验收: 模块可独立导入，测试通过

2. **创建上下文管理器** (文件: `utils/context_manager.py`)
   - 行动: 封装压缩逻辑，提供简洁API
   - 代码:
     ```python
     class ContextManager:
         def __init__(self, threshold=8000, ratio=0.5):
             self.threshold = threshold
             self.ratio = ratio
             self.compressor = SelectiveRetentionCompressor(ratio)
         
         def compress_if_needed(self, messages):
             if self.estimate_tokens(messages) > self.threshold:
                 return self.compressor.compress(messages)
             return messages
     ```
   - 依赖: 步骤1
   - 风险: 低
   - 验收: 管理器可检测阈值并触发压缩

3. **添加配置文件** (文件: `config/context.yaml`)
   - 行动: 创建压缩配置
   - 内容:
     ```yaml
     context_compression:
       enabled: true
       threshold: 8000  # tokens
       target_ratio: 0.5  # 保留50%
       recent_keep_ratio: 0.2  # 始终保留最近20%
       log_stats: true
     ```
   - 依赖: 步骤2
   - 风险: 低
   - 验收: 配置可被正确读取

### Phase 2: 集成到会话管理（估计45分钟）

4. **创建会话包装器** (文件: `utils/session_wrapper.py`)
   - 行动: 包装sessions_spawn，在消息传递前压缩
   - 原因: 对现有代码最小侵入
   - 代码:
     ```python
     def spawn_with_compression(agent_id, task, **kwargs):
         # 在task中注入压缩逻辑
         # 或者包装返回的session
         pass
     ```
   - 依赖: 步骤3
   - 风险: 中 - 需要测试与现有系统的兼容性
   - 验收: 长任务自动触发压缩

5. **添加压缩统计日志** (文件: `utils/context_manager.py` 扩展)
   - 行动: 添加压缩统计追踪
   - 内容:
     ```python
     def get_stats(self):
         return {
             'total_compresses': self.compress_count,
             'total_tokens_saved': self.tokens_saved,
             'avg_compression_ratio': self.avg_ratio
         }
     ```
   - 依赖: 步骤4
   - 风险: 低
   - 验收: 可查看压缩统计

### Phase 3: 测试与验证（估计45分钟）

6. **创建单元测试** (文件: `tests/test_context_compression.py`)
   - 行动: 测试压缩算法各种场景
   - 测试用例:
     - 正常压缩场景
     - 边界情况（空消息、单条消息）
     - 工具结果保留验证
     - 阈值触发验证
   - 依赖: 步骤1-5
   - 风险: 低
   - 验收: 测试覆盖率>80%，全部通过

7. **创建集成测试** (文件: `tests/integration/test_session_compression.py`)
   - 行动: 测试完整会话流程
   - 测试场景:
     - 长会话自动压缩
     - 压缩后消息完整性
     - 多Agent并行压缩
   - 依赖: 步骤6
   - 风险: 中
   - 验收: 集成测试通过，无回归

8. **性能基准测试** (文件: `tests/benchmark_compression.py`)
   - 行动: 测量压缩性能和效果
   - 指标:
     - 压缩耗时
     - token节省比例
     - 内存占用
   - 依赖: 步骤7
   - 风险: 低
   - 验收: 压缩耗时<100ms，节省40-60% tokens

### Phase 4: 文档与发布（估计30分钟）

9. **更新文档** (文件: `AGENTS.md`)
   - 行动: 添加上下文压缩说明
   - 内容:
     - 功能说明
     - 配置方法
     - 监控统计
   - 依赖: 步骤8
   - 风险: 低
   - 验收: 文档清晰完整

10. **创建监控面板** (文件: `logs/compression_stats.jsonl`)
    - 行动: 记录每次压缩的统计
    - 格式: JSON Lines，每行一次压缩记录
    - 依赖: 步骤9
    - 风险: 低
    - 验收: 可追踪历史压缩效果

## 测试策略

### 单元测试
- `tests/test_context_compression.py`
  - 测试压缩算法正确性
  - 测试重要性评分
  - 测试摘要生成

### 集成测试  
- `tests/integration/test_session_compression.py`
  - 测试会话全流程
  - 测试多Agent并行
  - 测试阈值触发

### E2E测试
- 手动测试长会话场景
- 验证压缩后Agent行为正常
- 验证统计日志正确

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 压缩丢失关键信息 | 中 | 高 | 工具结果白名单；决策点关键词保护；保留最近20% |
| 性能开销过大 | 低 | 中 | 仅超阈值触发；异步压缩；缓存机制 |
| 与现有功能冲突 | 中 | 高 | 渐进式推出；可配置开关；A/B测试 |
| 压缩后Agent理解下降 | 低 | 高 | 摘要质量保证；保留高重要性消息；监控反馈 |
| 配置复杂 | 低 | 低 | 合理默认值；配置文档；示例配置 |

## 成功标准

- [ ] SC1: 上下文超过8000 tokens自动触发压缩
- [ ] SC2: 压缩后节省40-60% tokens
- [ ] SC3: 100%保留工具调用结果
- [ ] SC4: 单元测试覆盖率>80%
- [ ] SC5: 集成测试全部通过
- [ ] SC6: 现有功能无回归
- [ ] SC7: 压缩耗时<100ms
- [ ] SC8: 可配置开关（启用/禁用）
- [ ] SC9: 统计日志可追踪
- [ ] SC10: 文档完整

## 实施时间表

| Phase | 预计时间 | 实际时间 | 状态 |
|-------|----------|----------|------|
| Phase 1: 基础设施 | 30分钟 | - | ⏳ 待开始 |
| Phase 2: 集成 | 45分钟 | - | ⏳ 待开始 |
| Phase 3: 测试 | 45分钟 | - | ⏳ 待开始 |
| Phase 4: 文档 | 30分钟 | - | ⏳ 待开始 |
| **总计** | **2.5小时** | - | ⏳ 待开始 |

## 下一步行动

1. @product-engineer 按Phase 1开始实施
2. 每完成一个Phase提交给 @rigorous-qa 审查
3. 全部完成后 @musk-orchestrator 验收

---
**计划创建时间**: 2026-02-27  
**计划创建者**: @planner (via @musk-orchestrator)  
**版本**: v1.0
