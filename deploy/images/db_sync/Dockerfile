# db_sync —— 跨库增量同步服务（单容器，全局仅 1 个）
# 构建上下文 = 仓库根目录
FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Yangon \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g; s/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
 && apt-get update && apt-get install -y --no-install-recommends tzdata \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

COPY db_sync/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY db_sync/db_sync.py /app/db_sync.py

# 水位持久化目录（compose 挂载卷）
VOLUME ["/app/state"]
CMD ["python", "/app/db_sync.py"]
