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

# 激活虚拟环境: 按顺序检查候选目录, 使用第一个存在的
#   /www/server/pyporject_evn/envFS  生产服务器
#   /root/envApp                     测试服务器 (192.168.3.208)
# 也可通过环境变量 VENV_ACTIVATE 直接指定 activate 文件
VENV_CANDIDATES=(
    "/www/server/pyporject_evn/envFS"
    "/root/envApp"
)
if [ -z "${VENV_ACTIVATE:-}" ]; then
    for venv_dir in "${VENV_CANDIDATES[@]}"; do
        if [ -f "$venv_dir/bin/activate" ]; then
            VENV_ACTIVATE="$venv_dir/bin/activate"
            break
        fi
    done
fi
if [ -z "${VENV_ACTIVATE:-}" ] || [ ! -f "$VENV_ACTIVATE" ]; then
    echo "[start.sh] 错误: 虚拟环境不存在, 已检查: ${VENV_ACTIVATE:-${VENV_CANDIDATES[*]}}" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

echo "[start.sh] 目录: $SCRIPT_DIR"
echo "[start.sh] APP_ENV=${APP_ENV:-<从 .env 读取>}"
echo "[start.sh] 虚拟环境: ${VIRTUAL_ENV:-未激活}"
echo "[start.sh] 解释器: $(python --version 2>&1)"

exec python app.py
