# jx-push —— WebSocket/SSE 消息推送服务 (Spring Boot 3.3.3, 构建于 JDK17)
# 生产 profile 使用 Redis 作消息队列(push.queue.type=redis)，无需 RabbitMQ。
# 构建上下文 = 仓库根目录
FROM eclipse-temurin:21-jre

ENV TZ=Asia/Yangon \
    JAVA_OPTS="-server -Xms512m -Xmx1024m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication -Djava.awt.headless=true -Dfile.encoding=UTF-8 -Djava.security.egd=file:/dev/./urandom" \
    PROFILE=prod

WORKDIR /app
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# jx-push.jar 的 MANIFEST Class-Path 引用 config/ 与 lib/*.jar，需保持目录结构
COPY jx-push/ /app/

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fs http://127.0.0.1:8090/actuator/health || exit 1

ENTRYPOINT ["sh","-c","exec java $JAVA_OPTS -jar jx-push.jar --spring.config.location=file:/app/config/ --spring.profiles.active=$PROFILE --logging.file.name=/app/logs/application.log"]
