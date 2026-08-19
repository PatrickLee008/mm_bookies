#!/bin/bash
# Push Service 启动脚本 兼容任意目录执行

# 1. 强制获取脚本真实绝对路径，不受执行目录影响
SCRIPT_PATH=$(readlink -f "$0")
BIN_DIR=$(dirname "$SCRIPT_PATH")
# 项目根目录：bin 的上一级
BASE_DIR=$(dirname "$BIN_DIR")

# 固定关键绝对路径，杜绝相对路径出错
CONFIG_DIR="${BASE_DIR}/config"
MAIN_JAR="${BASE_DIR}/jx-push.jar"
LOG_FILE="${BASE_DIR}/logs/application.log"
PID_FILE="${BASE_DIR}/app.pid"

PROFILE=${PROFILE:-prod}

show_help() {
    echo "用法:"
    echo "  sh bin/start.sh        后台启动prod环境"
    echo "  sh bin/start.sh -f     前台调试"
    echo "  sh bin/start.sh -p dev 指定dev环境"
}

FOREGROUND=0
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -f|--foreground)
            FOREGROUND=1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 环境校验
if [[ "$PROFILE" != "dev" && "$PROFILE" != "prod" ]]; then
    echo "错误：环境仅支持 dev / prod"
    exit 1
fi

# 先校验jar是否存在（新增校验，直接报清楚）
if [ ! -f "${MAIN_JAR}" ]; then
    echo "【致命错误】Jar 文件不存在：${MAIN_JAR}"
    echo "当前脚本路径: ${SCRIPT_PATH}"
    echo "项目根目录: ${BASE_DIR}"
    exit 1
fi

# 创建日志目录
mkdir -p "${BASE_DIR}/logs"

echo "==========================================="
echo "启动 Push Service"
echo "环境配置: ${PROFILE}"
echo "脚本路径: ${SCRIPT_PATH}"
echo "项目根目录: ${BASE_DIR}"
echo "Jar包路径: ${MAIN_JAR}"
echo "配置目录: ${CONFIG_DIR}"
echo "日志文件: ${LOG_FILE}"
echo "==========================================="

# JVM 参数
JAVA_OPTS="-server \
-Xms512m -Xmx1024m \
-XX:+UseG1GC \
-XX:MaxGCPauseMillis=200 \
-XX:+UnlockExperimentalVMOptions \
-XX:+UseStringDeduplication \
-XX:+OptimizeStringConcat \
-Dfile.encoding=UTF-8 \
-Djava.awt.headless=true \
-Djava.security.egd=file:/dev/./urandom"

SPRING_OPTS="--spring.config.location=file:${CONFIG_DIR}/ --spring.profiles.active=${PROFILE}"
APP_OPTS="--logging.file.name=${LOG_FILE}"

# 检查旧进程PID
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null; then
        echo "服务已在运行，PID: ${OLD_PID}"
        exit 1
    else
        rm -f "${PID_FILE}"
        echo "清理无效PID文件"
    fi
fi

# 切到项目根目录运行java
cd "${BASE_DIR}" || exit 1
RUN_CMD="java ${JAVA_OPTS} -jar ${MAIN_JAR} ${SPRING_OPTS} ${APP_OPTS}"
echo "执行命令: ${RUN_CMD}"

# 前台调试模式
if [ ${FOREGROUND} -eq 1 ]; then
    exec ${RUN_CMD}
fi

# 后台守护启动
nohup ${RUN_CMD} > "${LOG_FILE}" 2>&1 &
sleep 3

# 查找真实java进程
REAL_JAVA_PID=$(pgrep -f "jx-push.jar")
if [ -n "${REAL_JAVA_PID}" ]; then
    echo "${REAL_JAVA_PID}" > "${PID_FILE}"
    echo "✅ 服务启动成功，Java进程PID: ${REAL_JAVA_PID}"
    echo "查看日志: tail -f ${LOG_FILE}"
    exit 0
else
    echo "❌ 服务启动失败，请查看日志：${LOG_FILE}"
    rm -f "${PID_FILE}"
    exit 1
fi