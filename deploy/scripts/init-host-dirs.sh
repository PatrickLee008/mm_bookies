#!/usr/bin/env bash
# 在 CentOS7 服务器上初始化某一套的物理目录结构
# 用法： bash init-host-dirs.sh set1
# 注意：MySQL 用【物理机】上的 MySQL8，本脚本不建 mysql 数据目录（数据库在物理机上）。
set -e
SET=${1:?用法: init-host-dirs.sh <set1|set2|set3>}
BASE=/data/mmbookies/$SET
echo ">>> 初始化 $BASE"

mkdir -p $BASE/redis/data \
         $BASE/config/app_server $BASE/config/scraper \
         $BASE/config/jxboot $BASE/config/jeeplus-web $BASE/config/jx-push \
         $BASE/config/nginx \
         $BASE/logs/{app_server,scraper,jxboot,jeeplus-web,jx-push} \
         $BASE/static/app_server \
         $BASE/uploads/jeeplus \
         $BASE/web/uniapp $BASE/web/manager

# 同步服务的全局目录（只需建一次）
mkdir -p /data/mmbookies/sync/{state,logs}

chown -R 999:999 $BASE/redis 2>/dev/null || true
chmod -R 777 $BASE/logs $BASE/static $BASE/uploads 2>/dev/null || true

echo ">>> 目录已就绪。接下来："
echo "  1) 在物理机 MySQL 上创建本套数据库并导入初始结构/数据（见 README §6.2）"
echo "  2) 把各服务配置拷到 $BASE/config/<svc>/ 并把 DB 主机改为 host.docker.internal、库名改为本套(onex2_db_N)"
echo "  3) 把前端静态文件放到 $BASE/web/uniapp 和 $BASE/web/manager"
echo "  4) 把 nginx 配置拷到 $BASE/config/nginx/（uniapp.conf, web_manager.conf）"
