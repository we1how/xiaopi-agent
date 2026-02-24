#!/bin/bash
# 小皮 iMessage 实时对话系统
# 通过轮询 chat.db 检测新消息

CHAT_ID=3
LAST_ID_FILE="/tmp/imessage_last_id"
DB_PATH="$HOME/Library/Messages/chat.db"

# 获取最后一条消息ID
get_last_id() {
  sqlite3 "$DB_PATH" "SELECT MAX(ROWID) FROM message WHERE cache_roomnames IS NULL OR cache_roomnames = '';" 2>/dev/null || echo "0"
}

# 获取新消息
get_new_messages() {
  local last_id=$1
  sqlite3 "$DB_PATH" <<EOF
SELECT m.ROWID, m.text, h.id as sender, m.is_from_me, datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE m.ROWID > $last_id AND m.cache_roomnames IS NULL
ORDER BY m.ROWID DESC
LIMIT 5;
EOF
}

# 初始化
echo "🦀 小皮 iMessage 对话系统启动..."
echo "监听 Chat ID: $CHAT_ID"
echo "发送 'stop' 停止监听"
echo ""

LAST_ID=$(get_last_id)
echo "当前最新消息ID: $LAST_ID"

# 主循环
while true; do
  sleep 2
  
  NEW_MESSAGES=$(get_new_messages $LAST_ID)
  
  if [ -n "$NEW_MESSAGES" ]; then
    echo "$NEW_MESSAGES" | while IFS='|' read -r rowid text sender is_from_me time; do
      if [ "$is_from_me" = "0" ]; then
        echo ""
        echo "📩 [$time] 收到来自 $sender:"
        echo "   $text"
        echo ""
        
        # 自动回复
        if [[ "$text" == *"小皮"* ]] || [[ "$text" == *"测试"* ]] || [[ "$text" == *"stop"* ]]; then
          if [[ "$text" == *"stop"* ]]; then
            echo "🛑 收到停止指令，退出监听"
            exit 0
          fi
          
          echo "🤖 正在回复..."
          imsg send --to "$sender" --text "🦀 收到: $text" 2>/dev/null
        fi
      fi
      
      # 更新最后ID
      if [ "$rowid" -gt "$LAST_ID" ]; then
        LAST_ID=$rowid
      fi
    done
  fi
done
