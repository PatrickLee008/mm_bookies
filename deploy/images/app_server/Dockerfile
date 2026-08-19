# app_server —— 移动端后台接口服务 (Flask + uWSGI)
# 构建上下文 = 仓库根目录:  docker build -f deploy/images/app_server/Dockerfile -t mmbookies/app_server:latest .
FROM python:3.8-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Yangon \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 系统依赖：lxml/premailer 需 libxml2/libxslt；Pillow 需 libjpeg/zlib；gevent/uwsgi 需 gcc
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g; s/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
 && apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ make libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev libffi-dev \
      tzdata curl \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

# 精简版依赖（已剔除运行时未使用的 OCR/CV 重型库 paddleocr/opencv/scipy/matplotlib 等）
COPY deploy/images/app_server/requirements.runtime.txt /app/requirements.txt
RUN pip install --no-cache-dir uwsgi==2.0.21 -r requirements.txt

# 拷贝应用源码（.env / .env.<APP_ENV> 运行时由宿主机 config 目录挂载覆盖）
COPY app_server/ /app/
COPY deploy/images/app_server/uwsgi.docker.ini /app/uwsgi.ini

EXPOSE 8282
# 健康检查命中 app.py 里的 /hello
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fs http://127.0.0.1:8282/hello || exit 1

CMD ["uwsgi", "--ini", "uwsgi.ini"]
