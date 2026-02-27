# Context Compression Module for OpenClaw Agents
# 上下文压缩模块 - 选择性保留策略

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

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
    message_type: MessageType
    importance_score: float = 0.0
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = None

class SelectiveRetentionCompressor:
    """
    选择性保留压缩器
    策略：基于重要性评分保留关键消息
    """
    
    def __init__(self, target_ratio: float = 0.5):
        """
        Args:
            target_ratio: 目标压缩比例 (0.0-1.0)，默认保留50%
        """
        self.target_ratio = target_ratio
        
    def calculate_importance(self, message: Message) -> float:
        """
        计算消息重要性评分
        
        评分规则：
        - 工具调用结果: +3.0 (必须保留)
        - 用户指令: +2.0
        - 系统消息: +1.5
        - 决策/结论: +2.0
        - 普通对话: +0.5
        """
        score = 0.0
        
        # 基于消息类型评分
        if message.message_type == MessageType.TOOL_RESULT:
            score += 3.0
        elif message.message_type == MessageType.USER:
            score += 2.0
        elif message.message_type == MessageType.SYSTEM:
            score += 1.5
        elif message.message_type == MessageType.TOOL_CALL:
            score += 1.0
            
        # 基于内容关键词评分
        content_lower = message.content.lower()
        if any(kw in content_lower for kw in ['结论', '决定', '建议', '提案', 'action', 'decision']):
            score += 2.0
        if any(kw in content_lower for kw in ['完成', '成功', '失败', 'error', 'done']):
            score += 1.0
            
        return score
    
    def compress(self, messages: List[Message]) -> List[Message]:
        """
        执行压缩
        
        策略：
        1. 计算所有消息重要性
        2. 按重要性排序
        3. 保留top N达到目标比例
        4. 对早期低重要性消息生成摘要
        """
        if not messages:
            return messages
            
        # 计算重要性
        for msg in messages:
            msg.importance_score = self.calculate_importance(msg)
        
        # 保留最新消息的索引（始终保留最近20%）
        recent_count = max(1, int(len(messages) * 0.2))
        recent_messages = messages[-recent_count:]
        older_messages = messages[:-recent_count]
        
        # 对旧消息按重要性排序
        older_sorted = sorted(older_messages, key=lambda x: x.importance_score, reverse=True)
        
        # 计算需要保留的旧消息数量
        target_total = int(len(messages) * self.target_ratio)
        keep_older_count = max(0, target_total - recent_count)
        
        # 选择高重要性旧消息
        kept_older = older_sorted[:keep_older_count]
        
        # 对丢弃的旧消息生成摘要
        discarded_older = older_sorted[keep_older_count:]
        summary = self._generate_summary(discarded_older)
        
        # 合并结果：摘要 + 保留的旧消息 + 最新消息
        result = []
        if summary:
            result.append(Message(
                role="system",
                content=summary,
                message_type=MessageType.SYSTEM,
                importance_score=1.0
            ))
        
        # 按时间顺序重新排序
        kept_older_sorted = sorted(kept_older, key=lambda x: x.timestamp or "")
        result.extend(kept_older_sorted)
        result.extend(recent_messages)
        
        return result
    
    def _generate_summary(self, messages: List[Message]) -> str:
        """为丢弃的消息生成摘要"""
        if not messages:
            return ""
            
        tool_calls = [m for m in messages if m.message_type == MessageType.TOOL_CALL]
        decisions = [m for m in messages if any(kw in m.content.lower() 
                     for kw in ['决定', '结论', '建议'])]
        
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
                 compression_threshold: int = 8000,
                 target_compression_ratio: float = 0.5):
        """
        Args:
            compression_threshold: 触发压缩的token阈值
            target_compression_ratio: 目标压缩比例
        """
        self.compression_threshold = compression_threshold
        self.compressor = SelectiveRetentionCompressor(target_compression_ratio)
        self.original_token_count = 0
        self.compressed_token_count = 0
        
    def should_compress(self, messages: List[Message]) -> bool:
        """判断是否需要压缩"""
        # 简化估算：假设平均每条消息100 tokens
        estimated_tokens = len(messages) * 100
        self.original_token_count = estimated_tokens
        return estimated_tokens > self.compression_threshold
    
    def manage_context(self, messages: List[Message]) -> List[Message]:
        """
        管理上下文 - 主入口
        
        逻辑：
        1. 检查是否需要压缩
        2. 如需要，执行选择性保留压缩
        3. 记录压缩统计
        """
        if not self.should_compress(messages):
            return messages
            
        compressed = self.compressor.compress(messages)
        self.compressed_token_count = len(compressed) * 100
        
        return compressed
    
    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        if self.original_token_count == 0:
            return {"status": "no_compression_yet"}
            
        saved_tokens = self.original_token_count - self.compressed_token_count
        ratio = saved_tokens / self.original_token_count if self.original_token_count > 0 else 0
        
        return {
            "original_tokens": self.original_token_count,
            "compressed_tokens": self.compressed_token_count,
            "saved_tokens": saved_tokens,
            "compression_ratio": f"{ratio:.1%}",
            "threshold": self.compression_threshold
        }


# 便捷函数
def compress_agent_context(messages: List[Dict], 
                          threshold: int = 8000,
                          ratio: float = 0.5) -> List[Dict]:
    """
    压缩Agent上下文的便捷函数
    
    Args:
        messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
        threshold: 触发压缩的token阈值
        ratio: 目标压缩比例
        
    Returns:
        压缩后的消息列表
    """
    # 转换为Message对象
    msg_objects = []
    for m in messages:
        msg_type = MessageType.ASSISTANT
        if m.get("role") == "user":
            msg_type = MessageType.USER
        elif m.get("role") == "system":
            msg_type = MessageType.SYSTEM
        elif "tool_calls" in m:
            msg_type = MessageType.TOOL_CALL
        elif "tool_call_id" in m:
            msg_type = MessageType.TOOL_RESULT
            
        msg_objects.append(Message(
            role=m.get("role", "assistant"),
            content=m.get("content", ""),
            message_type=msg_type
        ))
    
    # 压缩
    manager = ContextManager(threshold, ratio)
    compressed = manager.manage_context(msg_objects)
    
    # 转换回字典格式
    return [{"role": m.role, "content": m.content} for m in compressed]


if __name__ == "__main__":
    # 测试
    test_messages = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "帮我分析股票数据"},
        {"role": "assistant", "content": "我来帮您分析", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "content": "股票数据结果...", "tool_call_id": "1"},
        {"role": "assistant", "content": "根据分析，建议买入"},
    ]
    
    result = compress_agent_context(test_messages, threshold=200, ratio=0.6)
    print(f"原始: {len(test_messages)} 条 → 压缩后: {len(result)} 条")
    for m in result:
        print(f"- {m['role']}: {m['content'][:50]}...")
