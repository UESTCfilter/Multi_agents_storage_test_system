#!/bin/bash
# 启动脚本 - 带 Kimi API Key

cd "$(dirname "$0")"
source venv/bin/activate

# 设置 API Key（修改这里）
export MOONSHOT_API_KEY="${MOONSHOT_API_KEY:-你的_API_KEY_HERE}"

# 杀掉旧进程
pkill -f "python -m backend.main" 2>/dev/null
sleep 1

# 启动后端
echo "Starting backend with Kimi K2.5..."
python -m backend.main