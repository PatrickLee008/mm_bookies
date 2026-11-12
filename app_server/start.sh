#!/usr/bin/env bash
# 通用 Python 服务管理脚本（Soccer2_App_Server / MMBookies app_server 共用）
# 用法: ./start.sh {start|stop|restart|status|logs [error|all]|help}
# 环境由配置文件决定（04: .env / 02: env_config.py），脚本不接受环境参数。
# 不用 set -e：is_running/stop 等函数有意的非零返回会被误杀。
set -u

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
SERVICE_NAME="$(basename "$SCRIPT_DIR")"

PID_FILE="$SCRIPT_DIR/app_server.pid"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/app_server.log"
ERROR_LOG="$LOG_DIR/error.log"

# 虚拟环境候选目录：生产 / 测试；可用 VENV_ACTIVATE 指向 bin/activate 覆盖
VENV_CANDIDATES=(
    "/www/server/pyporject_evn/envFS"
    "/root/envApp"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# 解析虚拟环境, 设置 PYTHON_CMD
resolve_python() {
    local venv_dir="" c
    if [ -n "${VENV_ACTIVATE:-}" ]; then
        venv_dir="$(dirname "$(dirname "$VENV_ACTIVATE")")"
    else
        for c in "${VENV_CANDIDATES[@]}"; do
            if [ -x "$c/bin/python" ]; then
                venv_dir="$c"
                break
            fi
        done
    fi
    if [ -z "$venv_dir" ] || [ ! -x "$venv_dir/bin/python" ]; then
        print_error "找不到可用的 Python 虚拟环境"
        print_error "已检查: ${VENV_ACTIVATE:-${VENV_CANDIDATES[*]}}"
        print_error "可设置 VENV_ACTIVATE 指向 venv 的 bin/activate"
        exit 1
    fi
    PYTHON_CMD="$venv_dir/bin/python"
    print_info "使用虚拟环境: $venv_dir"
}

# 检查 Redis（仅告警, 不致命）
check_redis() {
    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "找不到 Redis 客户端"
        return 1
    fi
    if ! redis-cli ping >/dev/null 2>&1; then
        print_warning "Redis 未运行，服务可能无法正常工作"
        return 1
    fi
    print_info "Redis 状态正常"
    return 0
}

# 找出本服务全部 app.py 进程：按 /proc/<pid>/cwd 匹配脚本目录, 不依赖 PID 文件。
# 这样能停掉旧前台部署遗留、无 PID 文件的进程, 也覆盖 debug reloader 的子进程。
app_pids() {
    local pid cwd
    for pid in $(pgrep -f 'app\.py' 2>/dev/null); do
        [ "$pid" = "$$" ] && continue
        cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null)"
        [ "$cwd" = "$SCRIPT_DIR" ] && echo "$pid"
    done
}

is_running() {
    [ -n "$(app_pids | xargs)" ]
}

start() {
    print_info "正在启动 $SERVICE_NAME 服务..."

    if is_running; then
        print_warning "服务已经在运行中 (PID: $(app_pids | xargs))"
        return 1
    fi

    rm -f "$PID_FILE"
    resolve_python
    check_redis
    mkdir -p "$LOG_DIR"

    print_info "使用 $PYTHON_CMD 启动服务..."
    nohup "$PYTHON_CMD" "$SCRIPT_DIR/app.py" >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    echo $! > "$PID_FILE"

    sleep 2

    if is_running; then
        print_info "服务启动成功 (PID: $(app_pids | xargs))"
        print_info "日志文件: $LOG_FILE"
        print_info "错误日志: $ERROR_LOG"
        print_info "使用 'tail -f $LOG_FILE' 查看实时日志"
        return 0
    else
        print_error "服务启动失败，请查看日志: $ERROR_LOG"
        return 1
    fi
}

stop() {
    print_info "正在停止 $SERVICE_NAME 服务..."

    local pids i
    pids="$(app_pids | xargs)"
    if [ -z "$pids" ]; then
        print_warning "服务未运行"
        rm -f "$PID_FILE"
        return 1
    fi

    print_info "停止进程 (PID: $pids)..."
    kill $pids 2>/dev/null

    for i in $(seq 1 10); do
        [ -z "$(app_pids | xargs)" ] && break
        sleep 1
    done

    pids="$(app_pids | xargs)"
    if [ -n "$pids" ]; then
        print_warning "正常停止超时，尝试强制停止..."
        kill -9 $pids 2>/dev/null
        sleep 1
    fi

    if [ -z "$(app_pids | xargs)" ]; then
        print_info "服务已停止"
        rm -f "$PID_FILE"
        return 0
    else
        print_error "无法停止服务 (PID: $(app_pids | xargs))"
        return 1
    fi
}

restart() {
    print_info "正在重启 $SERVICE_NAME 服务..."
    stop
    sleep 1
    start
}

status() {
    local pids
    pids="$(app_pids | xargs)"
    if [ -n "$pids" ]; then
        print_info "服务正在运行 (PID: $pids)"
        echo ""
        ps -p "$(echo $pids | tr ' ' ',')" -o pid,ppid,cmd,%mem,%cpu,etime 2>/dev/null
        echo ""
        print_info "日志文件信息:"
        [ -f "$LOG_FILE" ] && echo "  主日志: $LOG_FILE ($(du -h "$LOG_FILE" | cut -f1))"
        [ -f "$ERROR_LOG" ] && echo "  错误日志: $ERROR_LOG ($(du -h "$ERROR_LOG" | cut -f1))"
        return 0
    else
        print_warning "服务未运行"
        return 1
    fi
}

logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_error "日志文件不存在: $LOG_FILE"
        return 1
    fi
    case "${1:-}" in
        error)
            print_info "显示错误日志 (Ctrl+C 退出):"
            tail -f "$ERROR_LOG"
            ;;
        all)
            print_info "显示所有日志 (Ctrl+C 退出):"
            tail -f "$LOG_FILE" "$ERROR_LOG"
            ;;
        *)
            print_info "显示主日志 (Ctrl+C 退出):"
            tail -f "$LOG_FILE"
            ;;
    esac
}

help() {
    echo "$SERVICE_NAME 服务管理脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "命令说明:"
    echo "  start       - 启动服务(后台运行)"
    echo "  stop        - 停止服务"
    echo "  restart     - 重启服务"
    echo "  status      - 查看服务状态"
    echo "  logs        - 查看实时主日志"
    echo "    logs error  - 查看错误日志"
    echo "    logs all    - 查看所有日志"
    echo "  help        - 显示帮助信息"
    echo ""
    echo "环境由配置文件决定（.env / env_config.py），无需在脚本后传环境参数。"
    echo "虚拟环境自动探测: ${VENV_CANDIDATES[*]}（可用 VENV_ACTIVATE 覆盖）"
    echo ""
    echo "日志文件位置:"
    echo "  主日志: $LOG_FILE"
    echo "  错误日志: $ERROR_LOG"
    echo "  PID文件: $PID_FILE"
}

case "${1:-}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs "${2:-}" ;;
    help|--help|-h) help ;;
    "")      help ;;
    *)
        print_error "无效的命令: $1"
        echo ""
        help
        exit 1
        ;;
esac

exit $?