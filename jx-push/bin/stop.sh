#!/bin/bash
# Push Service 停止脚本

# 获取脚本所在目录
BIN_DIR=$(cd "$(dirname "$0")"; pwd)
BASE_DIR=$(cd "$BIN_DIR/.."; pwd)
PID_FILE="$BASE_DIR/app.pid"

# 显示调试信息
echo "=== Stop Script Debug Info ==="
echo "脚本目录: $BIN_DIR"
echo "基础目录: $BASE_DIR"
echo "PID文件路径: $PID_FILE"
echo "当前工作目录: $(pwd)"
echo "=============================="

echo "Stopping Push Service..."

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "PID文件不存在: $PID_FILE"
    echo "应用可能未运行或PID文件已被删除"
    
    # 尝试查找可能的进程
    PROCESSES=$(ps aux | grep "jx-push" | grep -v grep | awk '{print $2}')
    if [ -n "$PROCESSES" ]; then
        echo "发现相关进程: $PROCESSES"
        echo "是否要强制停止这些进程? (y/N): "
        read -r REPLY
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$PROCESSES" | xargs kill -TERM
            sleep 3
            # 检查是否还有残留进程
            REMAINING=$(ps -p $PROCESSES > /dev/null 2>&1 && echo "running" || echo "stopped")
            if [ "$REMAINING" = "running" ]; then
                echo "强制终止残留进程..."
                echo "$PROCESSES" | xargs kill -KILL
            fi
            echo "进程已停止"
        fi
    else
        echo "未发现相关运行进程"
    fi
    exit 1
fi

PID=$(cat "$PID_FILE")

# 验证PID是否为数字
if ! [[ "$PID" =~ ^[0-9]+$ ]]; then
    echo "PID文件内容无效: $PID"
    rm -f "$PID_FILE"
    exit 1
fi

echo "读取到PID: $PID"

# 首先检查PID文件中的PID是否有效
if ps -p "$PID" > /dev/null; then
    echo "PID $PID 有效，正在停止..."
    echo "正在向进程 $PID 发送SIGTERM信号..."
    kill -TERM "$PID"
    
    # 等待优雅关闭
    TIMEOUT=30
    COUNT=0
    while ps -p "$PID" > /dev/null && [ $COUNT -lt $TIMEOUT ]; do
        echo -n "."
        sleep 1
        COUNT=$((COUNT + 1))
    done
    echo ""
    
    # 如果还在运行，强制杀死
    if ps -p "$PID" > /dev/null; then
        echo "进程未响应SIGTERM，正在强制终止进程 $PID..."
        kill -KILL "$PID"
        # 等待强制终止完成
        sleep 2
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    echo "应用已成功停止"
else
    echo "进程 $PID 未在运行，尝试查找实际的Java进程..."
    
    # 查找实际的Java进程
    ACTUAL_PIDS=$(ps -ef | grep "jx-push.jar" | grep -v grep | awk '{print $2}')
    if [ -n "$ACTUAL_PIDS" ]; then
        echo "发现实际Java进程: $ACTUAL_PIDS"
        echo "正在停止这些进程..."
        echo "$ACTUAL_PIDS" | xargs kill -TERM
        sleep 3
        
        # 检查是否还有残留进程
        REMAINING=$(ps -ef | grep "jx-push.jar" | grep -v grep | awk '{print $2}' | wc -l)
        if [ "$REMAINING" -gt 0 ]; then
            echo "进程未响应SIGTERM，正在强制终止..."
            echo "$ACTUAL_PIDS" | xargs kill -KILL
            sleep 2
        fi
        
        # 清理PID文件
        rm -f "$PID_FILE"
        echo "应用已成功停止"
    else
        echo "未发现任何Java进程，清理PID文件"
        rm -f "$PID_FILE"
    fi
fi