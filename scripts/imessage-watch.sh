#!/bin/bash
# iMessage 实时接收脚本
# 通过 imsg watch 监听新消息并处理

echo "🦀 小皮 iMessage 监听器启动..."
echo "监听账号: 8618925630886"
echo "按 Ctrl+C 停止"
echo ""

# 使用 imsg watch 实时监听
imsg watch --json | while read -r line; do
    # 解析 JSON 消息
    sender=$(echo "$line" | jq -r '.sender // empty')
    text=$(echo "$line" | jq -r '.text // empty')
    is_from_me=$(echo "$line" | jq -r '.is_from_me // false')
    
    # 只处理非自己发送的消息
    if [ "$is_from_me" = "false" ] && [ -n "$sender" ] && [ -n "$text" ]; then
        echo ""
        echo "📩 收到消息来自 $sender:"
        echo "   $text"
        echo ""
        
        # 可以在这里添加自动回复逻辑
        if [[ "$text" == *"小皮"* ]] || [[ "$text" == *"测试"* ]]; then
            echo "🤖 触发自动回复..."
            imsg send --to "$sender" --text "🦀 小皮收到: $text"
        fi
    fi
done
