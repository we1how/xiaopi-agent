# Context Compression Module
# 上下文压缩模块 - 生产级实现

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from datetime import datetime

class MessageType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

@dataclass
class Message:
    role: str
    content: str
    message_type: MessageType = MessageType.ASSISTANT
    importance_score: float = 0.0
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class SelectiveRetentionCompressor:
    """
    选择性保留压缩器
    策略：基于重要性评分保留关键消息，对旧消息生成摘要
    """
    
    # 关键词权重配置
    HIGH_IMPORTANCE_KEYWORDS = [
        '结论', '决定', '建议', '提案', 'action', 'decision',
        '完成', '成功', '结果', 'result', 'done', 'error'
    ]
    
    def __init__(self, target_ratio: float = 0.5, recent_keep_ratio: float = 0.2):
        """
        Args:
            target_ratio: 目标压缩比例 (0.0-1.0)
            recent_keep_ratio: 始终保留的最新消息比例
        """
        self.target_ratio = max(0.1, min(0.9, target_ratio))
        self.recent_keep_ratio = max(0.1, min(0.5, recent_keep_ratio))
        
    def calculate_importance(self, message: Message) -> float:
        """
        计算消息重要性评分
        
        评分规则：
        - 工具调用结果: +3.0 (必须保留)
        - 用户指令: +2.0
        - 系统消息: +1.5
        - 工具调用: +1.0
        - 关键词匹配: +1.0 ~ +2.0
        """
        score = 0.0
        
        # 基于消息类型评分
        type_scores = {
            MessageType.TOOL_RESULT: 3.0,
            MessageType.USER: 2.0,
            MessageType.SYSTEM: 1.5,
            MessageType.TOOL_CALL: 1.0,
            MessageType.ASSISTANT: 0.5
        }
        score += type_scores.get(message.message_type, 0.5)
        
        # 基于内容关键词评分
        content_lower = message.content.lower()
        if any(kw in content_lower for kw in ['结论', '决定', '建议', '提案', 'action', 'decision']):
            score += 2.0
        if any(kw in content_lower for kw in ['完成', '成功', '失败', 'error', 'done', '结果']):
            score += 1.0
            
        return score
    
    def compress(self, messages: List[Message]) -> tuple[List[Message], Dict[str, Any]]:
        """
        执行压缩
        
        Returns:
            (压缩后的消息列表, 统计信息)
        """
        if not messages or len(messages) <= 3:
            return messages, {"compressed": False, "reason": "too_few_messages"}
            
        original_count = len(messages)
        
        # 计算重要性
        for msg in messages:
            msg.importance_score = self.calculate_importance(msg)
        
        # 保留最新消息
        recent_count = max(1, int(len(messages) * self.recent_keep_ratio))
        recent_messages = messages[-recent_count:]
        older_messages = messages[:-recent_count]
        
        # 对旧消息按重要性排序
        older_sorted = sorted(older_messages, key=lambda x: x.importance_score, reverse=True)
        
        # 计算需要保留的旧消息数量
        target_total = max(recent_count + 1, int(len(messages) * self.target_ratio))
        keep_older_count = max(0, target_total - recent_count)
        
        # 选择高重要性旧消息
        kept_older = older_sorted[:keep_older_count]
        discarded_older = older_sorted[keep_older_count:]
        
        # 对丢弃的消息生成摘要
        summary = self._generate_summary(discarded_older)
        
        # 合并结果
        result = []
        if summary:
            result.append(Message(
                role="system",
                content=summary,
                message_type=MessageType.SYSTEM,
                importance_score=1.0,
                timestamp=datetime.now().isoformat(),
                metadata={"type": "compression_summary"}
            ))
        
        # 按原始顺序排序保留的旧消息
        kept_older_sorted = sorted(kept_older, key=lambda x: x.timestamp or "")
        result.extend(kept_older_sorted)
        result.extend(recent_messages)
        
        # 生成统计
        stats = {
            "compressed": True,
            "original_count": original_count,
            "compressed_count": len(result),
            "reduction_ratio": 1 - (len(result) / original_count) if original_count > 0 else 0,
            "summary_generated": bool(summary),
            "tool_results_preserved": sum(1 for m in result if m.message_type == MessageType.TOOL_RESULT)
        }
        
        return result, stats
    
    def _generate_summary(self, messages: List[Message]) -> str:
        """为丢弃的消息生成摘要"""
        if not messages:
            return ""
            
        tool_calls = [m for m in messages if m.message_type == MessageType.TOOL_CALL]
        decisions = [m for m in messages if any(kw in m.content.lower() 
                     for kw in ['决定', '结论', '建议', '完成'])]
        
        parts = [f"[上下文摘要: 已压缩 {len(messages)} 条历史消息]"]
        
        if tool_calls:
            parts.append(f"执行了 {len(tool_calls)} 次工具调用")
        if decisions:
            parts.append(f"包含 {len(decisions)} 个决策点")
            
        return " | ".join(parts)


class ContextManager:
    """
    上下文管理器 - 集成到Agent会话中
    """
    
    def __init__(self, 
                 enabled: bool = True,
                 compression_threshold: int = 20,
                 target_compression_ratio: float = 0.5,
                 recent_keep_ratio: float = 0.2,
                 log_stats: bool = True):
        """
        Args:
            enabled: 是否启用压缩
            compression_threshold: 触发压缩的消息数阈值（简化估算）
            target_compression_ratio: 目标压缩比例
            recent_keep_ratio: 保留的最新消息比例
            log_stats: 是否记录统计
        """
        self.enabled = enabled
        self.compression_threshold = compression_threshold
        self.compressor = SelectiveRetentionCompressor(
            target_ratio=target_compression_ratio,
            recent_keep_ratio=recent_keep_ratio
        )
        self.log_stats = log_stats
        
        # 统计追踪
        self.stats = {
            "total_compresses": 0,
            "total_messages_processed": 0,
            "total_messages_saved": 0,
            "compression_history": []
        }
        
    def should_compress(self, messages: List[Message]) -> bool:
        """判断是否需要压缩"""
        if not self.enabled:
            return False
        if len(messages) < self.compression_threshold:
            return False
        return True
    
    def compress_messages(self, messages: List[Dict]) -> tuple[List[Dict], Dict[str, Any]]:
        """
        压缩消息列表 - 主入口
        
        Args:
            messages: 消息字典列表 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            (压缩后的消息列表, 统计信息)
        """
        # 转换为Message对象
        msg_objects = []
        for i, m in enumerate(messages):
            msg_type = MessageType.ASSISTANT
            role = m.get("role", "assistant")
            
            if role == "user":
                msg_type = MessageType.USER
            elif role == "system":
                msg_type = MessageType.SYSTEM
            elif "tool_calls" in m:
                msg_type = MessageType.TOOL_CALL
            elif "tool_call_id" in m:
                msg_type = MessageType.TOOL_RESULT
            
            msg_objects.append(Message(
                role=role,
                content=m.get("content", ""),
                message_type=msg_type,
                timestamp=m.get("timestamp", datetime.now().isoformat()),
                metadata=m.get("metadata", {})
            ))
        
        # 检查是否需要压缩
        if not self.should_compress(msg_objects):
            return messages, {"compressed": False, "reason": "below_threshold"}
        
        # 执行压缩
        compressed_objects, stats = self.compressor.compress(msg_objects)
        
        # 更新统计
        if stats.get("compressed"):
            self.stats["total_compresses"] += 1
            self.stats["total_messages_processed"] += len(msg_objects)
            self.stats["total_messages_saved"] += len(msg_objects) - len(compressed_objects)
            
            if self.log_stats:
                self.stats["compression_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    **stats
                })
        
        # 转换回字典格式
        result = []
        for m in compressed_objects:
            msg_dict = {"role": m.role, "content": m.content}
            if m.metadata:
                msg_dict["metadata"] = m.metadata
            result.append(msg_dict)
        
        return result, stats
    
    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        stats = self.stats.copy()
        if stats["total_messages_processed"] > 0:
            stats["avg_reduction_ratio"] = (
                stats["total_messages_saved"] / stats["total_messages_processed"]
            )
        else:
            stats["avg_reduction_ratio"] = 0
        return stats
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total_compresses": 0,
            "total_messages_processed": 0,
            "total_messages_saved": 0,
            "compression_history": []
        }


# 便捷函数
def compress_context(messages: List[Dict], 
                    threshold: int = 20,
                    ratio: float = 0.5) -> tuple[List[Dict], Dict[str, Any]]:
    """
    压缩上下文的便捷函数
    
    Args:
        messages: 消息列表
        threshold: 触发压缩的消息数阈值
        ratio: 目标压缩比例
        
    Returns:
        (压缩后的消息列表, 统计信息)
    """
    manager = ContextManager(
        enabled=True,
        compression_threshold=threshold,
        target_compression_ratio=ratio
    )
    return manager.compress_messages(messages)


if __name__ == "__main__":
    # 测试
    test_messages = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "帮我分析股票数据"},
        {"role": "assistant", "content": "我来帮您分析", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "content": "股票数据结果: AAPL涨5%...", "tool_call_id": "1"},
        {"role": "assistant", "content": "根据分析，建议买入AAPL"},
        {"role": "user", "content": "为什么？"},
        {"role": "assistant", "content": "因为PE ratio低于行业平均..."},
        {"role": "user", "content": "还有其他推荐吗？"},
        {"role": "assistant", "content": "我还看好MSFT和GOOGL..."},
    ]
    
    print(f"原始消息数: {len(test_messages)}")
    compressed, stats = compress_context(test_messages, threshold=5, ratio=0.6)
    print(f"压缩后消息数: {len(compressed)}")
    print(f"压缩统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    print("\n压缩后的消息:")
    for i, m in enumerate(compressed):
        print(f"{i+1}. [{m['role']}] {m['content'][:60]}...")
