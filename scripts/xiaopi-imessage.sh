#!/bin/bash
# 小皮 iMessage 自动监听回复系统
# 每 5 秒检查一次新消息

DB="$HOME/Library/Messages/chat.db"
LAST_ID=$(sqlite3 "$DB" "SELECT MAX(ROWID) FROM message WHERE is_from_me = 0;" 2>/dev/null || echo "0")

echo "🐱 小皮 iMessage 监听已启动"
echo "等待新消息..."
echo "发送 '帮助' 查看可用指令"
echo ""

while true; do
  sleep 5
  
  # 检查新消息
  NEW_MSG=$(sqlite3 "$DB" <<EOF 2>/dev/null
SELECT m.ROWID, m.text, h.id, datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE m.is_from_me = 0 
  AND m.ROWID > $LAST_ID
ORDER BY m.ROWID DESC
LIMIT 1;
EOF
)
  
  if [ -n "$NEW_MSG" ]; then
    ROWID=$(echo "$NEW_MSG" | cut -d'|' -f1)
    TEXT=$(echo "$NEW_MSG" | cut -d'|' -f2)
    SENDER=$(echo "$NEW_MSG" | cut -d'|' -f3)
    TIME=$(echo "$NEW_MSG" | cut -d'|' -f4)
    
    echo "[$TIME] 收到: $TEXT"
    
    # 更新最后ID
    LAST_ID=$ROWID
    
    # 自动回复逻辑
    if [[ "$TEXT" == *"帮助"* ]] || [[ "$TEXT" == *"help"* ]]; then
      REPLY="🐱 小皮指令列表：
1. 股票 [代码] - 分析股票
2. 天气 [城市] - 查天气
3. 总结 [链接/文件] - 阅读总结
4. 电影 [类型] - 推荐电影
5. 直接说需求 - 我会尽力帮忙"
      
    elif [[ "$TEXT" == "股票"* ]] || [[ "$TEXT" == "分析"* ]]; then
      CODE=$(echo "$TEXT" | grep -oE '[0-9]{6}' | head -1)
      if [ -n "$CODE" ]; then
        REPLY="🐱 收到股票分析请求：$CODE，正在分析...（完整功能稍后接入）"
      else
        REPLY="🐱 请提供股票代码，例如：股票 600519"
      fi
      
    elif [[ "$TEXT" == "天气"* ]]; then
      CITY=$(echo "$TEXT" | sed 's/天气//g' | xargs)
      if [ -n "$CITY" ]; then
        REPLY="🐱 查询 $CITY 天气...（完整功能稍后接入）"
      else
        REPLY="🐱 请提供城市，例如：天气 上海"
      fi
      
    elif [[ "$TEXT" == "电影"* ]]; then
      REPLY="🐱 电影推荐功能稍后接入，先看部诺兰的吧：《星际穿越》"
      
    elif [[ "$TEXT" == "在吗"* ]] || [[ "$TEXT" == "你好"* ]]; then
      REPLY="🐱 在的！有什么可以帮你？"
      
    else
      # 默认回复
      REPLY="🐱 收到：\"$TEXT\"

我已记录，稍后处理。需要具体帮助请发送\"帮助\"查看指令。"
    fi
    
    # 发送回复
    imsg send --to "$SENDER" --text "$REPLY" 2>/dev/null
    echo "↳ 回复已发送"
  fi
done
