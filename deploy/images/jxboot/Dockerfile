# jxboot-services-onex2 —— Java 结算服务 (JFinal/Jboot + Undertow, 原用 JDK18)
# 构建上下文 = 仓库根目录
FROM eclipse-temurin:21-jre

ENV TZ=Asia/Yangon \
    JAVA_OPTS="-server -Xms512m -Xmx2048m -Djava.awt.headless=true -Dfile.encoding=UTF-8" \
    MAIN_CLASS=com.jxboot.services.JxBootServicesOneX2Application

WORKDIR /app
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 通过 classpath 启动：config 目录 + lib/*.jar（应用主 jar 在 lib/jxboot-services-onex2-1.0.0.jar）
# config/ 由宿主机挂载覆盖（jboot.properties 内数据源/Redis 指向容器名 mysql/redis）
COPY jxboot-services-onex2/ /app/

EXPOSE 9101
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fs http://127.0.0.1:9101/ >/dev/null 2>&1 || exit 0

# JDK21 兼容旧反射：放开常见 add-opens，避免 JFinal/Druid 反射告警
ENTRYPOINT ["sh","-c","exec java $JAVA_OPTS --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -cp \"/app/config:/app/lib/*\" $MAIN_CLASS"]
