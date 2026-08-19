#!/usr/bin/env bash
# 在仓库根目录执行：构建全部应用镜像（构建上下文 = 仓库根目录）
# 用法： bash deploy/scripts/build-all.sh [TAG]
set -e
cd "$(dirname "$0")/../.."       # 切到仓库根目录
ROOT=$(pwd)
TAG=${1:-latest}
echo ">>> 构建上下文: $ROOT   TAG: $TAG"

docker build -f deploy/images/app_server/Dockerfile   -t mmbookies/app_server:$TAG  .
docker build -f deploy/images/scraper/Dockerfile      -t mmbookies/scraper:$TAG     .
docker build -f deploy/images/db_sync/Dockerfile      -t mmbookies/db_sync:$TAG     .
docker build -f deploy/images/jxboot/Dockerfile       -t mmbookies/jxboot:$TAG      .
docker build -f deploy/images/jeeplus-web/Dockerfile  -t mmbookies/jeeplus-web:$TAG .
docker build -f deploy/images/jx-push/Dockerfile      -t mmbookies/jx-push:$TAG     .

echo ">>> 完成。镜像列表："
docker images | grep mmbookies

# 可选：导出为 tar 便于离线拷贝到 CentOS7 服务器（MySQL 用物理机，无需 mysql 镜像）
# docker save mmbookies/app_server:$TAG mmbookies/scraper:$TAG mmbookies/db_sync:$TAG \
#   mmbookies/jxboot:$TAG mmbookies/jeeplus-web:$TAG mmbookies/jx-push:$TAG \
#   redis:7-alpine nginx:1.25-alpine -o mmbookies-images-$TAG.tar
