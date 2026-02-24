#!/usr/bin/env node
/**
 * 小皮 iMessage 消息监听守护进程
 * 监听新消息并自动回复
 */

const { spawn } = require('child_process');

console.log('🦀 小皮 iMessage 监听器启动...');
console.log('正在监听 chat.db 变化...\n');

// 启动 imsg watch
const watcher = spawn('imsg', ['watch', '--json'], {
  stdio: ['ignore', 'pipe', 'pipe']
});

let buffer = '';

watcher.stdout.on('data', (data) => {
  buffer += data.toString();
  
  // 处理行
  let lines = buffer.split('\n');
  buffer = lines.pop(); // 保留未完成行
  
  for (const line of lines) {
    if (!line.trim()) continue;
    
    try {
      const msg = JSON.parse(line);
      
      // 只处理收到的消息（不是自己发的）
      if (msg.is_from_me === false && msg.text && msg.sender) {
        const time = new Date().toLocaleTimeString('zh-CN');
        console.log(`\n📩 [${time}] 收到来自 ${msg.sender}:`);
        console.log(`   ${msg.text}`);
        
        // 自动回复触发词
        const triggerWords = ['小皮', '测试', 'help', '帮助', '你好', '在吗'];
        const shouldReply = triggerWords.some(w => msg.text.includes(w));
        
        if (shouldReply) {
          console.log('🤖 触发自动回复...');
          const reply = spawn('imsg', ['send', '--to', msg.sender, '--text', `🦀 小皮收到: "${msg.text}"`], {
            stdio: 'inherit'
          });
        }
      }
    } catch (e) {
      // 忽略解析错误
    }
  }
});

watcher.stderr.on('data', (data) => {
  // 忽略错误输出
});

watcher.on('close', (code) => {
  console.log(`监听器退出 (code ${code})，5秒后重启...`);
  setTimeout(() => {
    process.exit(1); // 让外部进程管理器重启
  }, 5000);
});

// 优雅退出
process.on('SIGINT', () => {
  console.log('\n🛑 停止监听...');
  watcher.kill();
  process.exit(0);
});
