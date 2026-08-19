# scraper —— 数据爬虫服务（批处理：main() 跑一轮即退出，需循环调度）
# 构建上下文 = 仓库根目录
FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Yangon \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    APP_ENV=production \
    SCRAPE_INTERVAL=30

WORKDIR /app

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g; s/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
 && apt-get update && apt-get install -y --no-install-recommends \
      gcc libxml2-dev libxslt1-dev tzdata \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

COPY scraper/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper/ /app/
COPY deploy/images/scraper/run-loop.sh /app/run-loop.sh
RUN chmod +x /app/run-loop.sh

# 以循环方式反复执行爬虫（.env 由 config 目录挂载覆盖，APP_ENV 控制加载 .env.<env>）
CMD ["/app/run-loop.sh"]
