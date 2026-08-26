#!/usr/bin/env bash
# 启动 app.py 的脚本
# 用法:
#   ./start.sh                启动 (使用 .env 中的 APP_ENV)
#   ./start.sh develop        指定环境启动 (会写入 .env 的 APP_ENV)
#   APP_ENV=production ./start.sh
set -euo pipefail

# 切换到脚本所在目录 (app_server)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 若传入环境参数, 覆盖 APP_ENV
if [ "${1:-}" != "" ]; then
    export APP_ENV="$1"
fi

# 激活虚拟环境
VENV_ACTIVATE="/root/envApp/bin/activate"
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "[start.sh] 错误: 虚拟环境不存在: $VENV_ACTIVATE" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

echo "[start.sh] 目录: $SCRIPT_DIR"
echo "[start.sh] APP_ENV=${APP_ENV:-<从 .env 读取>}"
echo "[start.sh] 虚拟环境: ${VIRTUAL_ENV:-未激活}"
echo "[start.sh] 解释器: $(python --version 2>&1)"

exec python app.py
