#!/bin/bash
# Push Service 状态检查脚本

# 获取脚本所在目录
BIN_DIR=$(cd "$(dirname "$0")"; pwd)
BASE_DIR=$(cd "$BIN_DIR/.."; pwd)
PID_FILE="$BASE_DIR/app.pid"
LOG_FILE="$BASE_DIR/logs/application.log"

# 显示基本信息
echo "=== Push Service 状态检查 ==="
echo "脚本目录: $BIN_DIR"
echo "基础目录: $BASE_DIR"
echo "PID文件: $PID_FILE"
echo "日志文件: $LOG_FILE"
echo "============================"

echo ""
# 检查PID文件和进程状态
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "PID文件内容: $PID"
    
    # 验证PID是否为有效数字
    if [[ "$PID" =~ ^[0-9]+$ ]] && ps -p "$PID" > /dev/null; then
        echo "状态: 运行中 (RUNNING)"
        echo "进程ID: $PID"
        echo "启动时间: $(ps -o lstart= -p "$PID")"
        echo "内存使用: $(ps -o rss= -p "$PID" | awk '{print int($1/1024) " MB"}')"
        echo "CPU使用率: $(ps -o %cpu= -p "$PID")%"
        
        # 检查端口占用
        PORT_PROCESS=$(netstat -tlnp 2>/dev/null | grep :8090 | awk '{print $7}' | cut -d'/' -f1)
        if [ "$PORT_PROCESS" = "$PID" ]; then
            echo "端口8090: 正常监听"
        elif [ -n "$PORT_PROCESS" ]; then
            echo "端口8090: 被其他进程占用 (PID: $PORT_PROCESS)"
        else
            echo "端口8090: 未监听"
        fi
    else
        echo "状态: 已停止 (STOPPED)"
        echo "PID文件存在但进程未运行"
        echo "正在清理陈旧的PID文件..."
        rm -f "$PID_FILE"
    fi
else
    echo "状态: 已停止 (STOPPED)"
    echo "未找到PID文件"
    
    # 查找可能的相关进程
    PROCESSES=$(ps aux | grep "jx-push" | grep -v grep | awk '{print $2}')
    if [ -n "$PROCESSES" ]; then
        echo "发现相关进程: $PROCESSES"
        echo "注意: 这些进程可能不是通过标准脚本启动的"
    fi
fi

echo ""
# 检查日志文件
echo "=== 日志信息 ==="
if [ -f "$LOG_FILE" ]; then
    echo "日志文件大小: $(du -h "$LOG_FILE" | cut -f1)"
    echo "最后10行日志:"
    tail -n 10 "$LOG_FILE"
    
    # 检查最近的错误
    ERROR_COUNT=$(grep -c "ERROR\|Exception\|error" "$LOG_FILE" 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "最近错误数量: $ERROR_COUNT"
        echo "最近5个错误:"
        grep -A 2 -B 2 "ERROR\|Exception\|error" "$LOG_FILE" | tail -n 15
    fi
else
    echo "日志文件不存在: $LOG_FILE"
fi

echo ""
echo "=== 系统资源 ==="
echo "系统负载: $(uptime | awk -F'load average:' '{print $2}')"
echo "可用内存: $(free -h | awk '/^Mem:/ {print $7}')"
echo "磁盘使用: $(df -h . | awk 'NR==2 {print $5}')"