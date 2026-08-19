# jeeplus-web —— 管理端后端 (Spring Boot 3.3.3, 构建于 JDK17)
# 构建上下文 = 仓库根目录
FROM eclipse-temurin:21-jre

ENV TZ=Asia/Yangon \
    JAVA_OPTS="-server -Xms512m -Xmx1536m -XX:+UseG1GC -Djava.awt.headless=true -Dfile.encoding=UTF-8" \
    SPRING_PROFILES_ACTIVE=prod

WORKDIR /app
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# jeeplus-vue.jar 通过 MANIFEST Class-Path 引用 lib/*.jar，需保持目录结构
# config/ 由宿主机挂载覆盖（application-prod.yml 内数据库/Redis 指向容器名 mysql/redis）
COPY jeeplus-web/ /app/

EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=5 \
  CMD curl -fs http://127.0.0.1:8082/actuator/health || exit 1

# classes/ 内含模板/mybatis 资源，一并加入 classpath，配置从外部 config 目录加载
ENTRYPOINT ["sh","-c","exec java $JAVA_OPTS -cp \"jeeplus-vue.jar:classes:lib/*\" com.jeeplus.JeeplusWebApplication --spring.profiles.active=$SPRING_PROFILES_ACTIVE --spring.config.additional-location=file:/app/config/"]
