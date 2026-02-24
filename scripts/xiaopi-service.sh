#!/bin/bash
# 小皮 iMessage 服务管理

SCRIPT_PATH="$HOME/.openclaw/workspace/scripts/xiaopi-imessage.sh"
PID_FILE="/tmp/xiaopi-imessage.pid"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
      echo "🐱 小皮已经在运行中 (PID: $(cat $PID_FILE))"
      exit 0
    fi
    
    echo "🐱 启动小皮 iMessage 监听..."
    nohup "$SCRIPT_PATH" > /tmp/xiaopi-imessage.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ 已启动 (PID: $!)"
    echo "日志: tail -f /tmp/xiaopi-imessage.log"
    ;;
    
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID" 2>/dev/null
        echo "🛑 已停止小皮监听"
      else
        echo "进程已不存在"
      fi
      rm -f "$PID_FILE"
    else
      echo "小皮没有在运行"
    fi
    ;;
    
  status)
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
      echo "🐱 小皮运行中 (PID: $(cat $PID_FILE))"
      echo "最新日志:"
      tail -5 /tmp/xiaopi-imessage.log 2>/dev/null || echo "暂无日志"
    else
      echo "🐱 小皮未运行"
    fi
    ;;
    
  log)
    tail -f /tmp/xiaopi-imessage.log 2>/dev/null || echo "暂无日志"
    ;;
    
  *)
    echo "用法: $0 {start|stop|status|log}"
    echo ""
    echo "  start  - 启动 iMessage 监听"
    echo "  stop   - 停止监听"
    echo "  status - 查看状态"
    echo "  log    - 查看实时日志"
    ;;
esac
