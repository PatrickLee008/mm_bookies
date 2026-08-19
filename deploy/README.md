# MM Bookies · 单机三套 Docker 部署方案

> 目标：一台 CentOS 7 服务器上部署 **3 套**互相隔离的完整应用，端口隔离 + 数据隔离，
> 配置与数据落物理存储目录。
>
> **数据存储**：MySQL 用**物理机**上的一个 MySQL8 实例，三套连**不同库** `onex2_db_1/2/3`；
> Redis 每套一个独立容器。**只跑一个爬虫**（主套 set1），公共赛事数据由 **db-sync 服务**
> 增量同步到另外两个库，副本套再各自重建 Redis 缓存。

---

## 1. 应用清单与角色

| # | 应用 | 类型 | 运行形态 | 容器端口 | 依赖 |
|---|------|------|----------|---------|------|
| 1 | **app_server** | Flask + uWSGI | 常驻(3 worker) | 8282 | 物理机 MySQL, 本套 Redis(db0) |
| 2 | **scraper** | Python | 循环(见 §2 角色) | – | 物理机 MySQL, 本套 Redis, 外部代理 |
| 3 | **jxboot-services-onex2** | JFinal + Undertow | 常驻 | 9101 | 物理机 MySQL, 本套 Redis(db7) |
| 4 | **jeeplus-web** | Spring Boot 3.3.3 | 常驻 | 8082 | 物理机 MySQL, 本套 Redis(db3) |
| 5 | **jx-push** | Spring Boot 3.3.3 | 常驻(WS/SSE) | 8090 | 物理机 MySQL, 本套 Redis（prod 用 Redis 作队列，**不需 RabbitMQ**）|
| 6 | **mm_bookies_uniapp** | 静态 H5 | nginx :80 | – | 反代 app_server / jx-push |
| 7 | **web_manager** | 静态前端 | nginx :80 | – | 反代 jeeplus-web |
| 8 | **db-sync**（新增，全局 1 个）| Python | 循环 | – | 物理机 MySQL（对 3 库有权限）|
| + | **Redis 7** | 缓存 | 每套 1 个容器 | 6379 | 数据落物理盘 |
| + | **MySQL 8**（物理机，非容器）| 数据库 | 3 个库 | 3306 | 物理机本地磁盘 |

**代码扫描确认的关键结论：**
- `app_server` 的 `requirements.txt` 带了 paddleocr/opencv/scipy/matplotlib 等 2~3GB 的 OCR/CV 库，但**运行时未 import**，镜像用精简依赖 `requirements.runtime.txt`。
- `app_server` 的赛事列表 API `get_match_list` **从 Redis 读缓存**（不是直接查 MySQL）→ 所以副本套光同步 MySQL 不够，还必须重建本套 Redis 缓存（见 §2）。
- `scraper` 的 `main()` 跑一轮即退出，属定时批处理；`cache_to_redis()` 从“本进程配置指向的库”读、写“本进程配置指向的 Redis”，可独立复用。
- `jx-push` 生产 `push.queue.type=redis`，**不需要 RabbitMQ**。

---

## 2. 数据流与“单爬虫 + 增量同步”架构

```
                    (网页赔率源)
                         │ 爬取
                         ▼
 ┌──────────────── set1 (主套) ────────────────┐
 │  scraper(ibet_runner2.py)                    │
 │    ├─ 写 → 物理机 MySQL: onex2_db_1           │
 │    └─ 刷 → set1 Redis (赛事缓存 live_matches) │
 └──────────────────────────────────────────────┘
                         │
        db-sync 服务（全局1个，跨库全量覆盖增量同步）
        onex2_db_1 ──► onex2_db_2 , onex2_db_3
        （5张公共表：m_app_match / m_app_match_attr /
          result / m_app_league_team_scraper / m_app_league）
                         │
   ┌─────────────────────┴──────────────────────┐
   ▼                                             ▼
 ┌──── set2 (副本) ────┐                 ┌──── set3 (副本) ────┐
 │ scraper(cache_only) │                 │ scraper(cache_only) │
 │  读 onex2_db_2       │                 │  读 onex2_db_3       │
 │  → 刷 set2 Redis     │                 │  → 刷 set3 Redis     │
 └──────────────────────┘                 └──────────────────────┘
```

- **爬虫只跑一个**：主套 set1 的 scraper 容器 `SCRAPER_ENTRY=ibet_runner2.py`，完整爬取写主库并刷 set1 缓存。
- **db-sync**：一个全局容器，连物理机 MySQL，用服务端跨库 `INSERT ... SELECT ... ON DUPLICATE KEY UPDATE` 把主库 5 张公共表**全量覆盖**同步到另外两个库（按水位列增量、只处理变化行、幂等）。数据不经过 Python，最快最省。
- **副本套刷缓存**：set2/set3 的 scraper 容器 `SCRAPER_ENTRY=cache_only.py`，**不爬网页**，只调用 `cache_to_redis()` 从本套已同步的库重建本套 Redis 赛事缓存。

> **同步策略 = 全量覆盖**（按你的选择）：以主库为准，目标库同主键行的所有列被覆盖，包含 `hide/MANUAL_ON/status` 等——即副本套不做本地人工改盘/隐藏（如需本地人工操作，改用“保留本地字段”策略，联系我调整 db_sync 的更新列即可）。
> **同步表**：`m_app_match`、`m_app_match_attr`、`result`、`m_app_league_team_scraper`、`m_app_league`（可在 `SYNC_TABLES` 增删）。
> **限制**：只覆盖不传播“物理删除”（业务用 hide/status 软标记，会随列覆盖同步）。

---

## 3. 隔离策略

- **网络隔离**：每套一个独立 bridge 网络，套内用容器名互访（`redis`、`app_server`、`jx-push`…）；访问物理机 MySQL 走 `host.docker.internal`（compose 已配 `extra_hosts: host-gateway`）。
- **数据隔离**：MySQL 三库分离（`onex2_db_1/2/3`）；Redis 每套独立容器（否则三套同 db 索引会撞库）。
- **端口隔离**：对外端口 `1xxxx / 2xxxx / 3xxxx` 三段（§5）。
- **配置/数据外置**：全部落 `/data/mmbookies/setN/`。

---

## 4. 目录结构

### 4.1 仓库内
```
deploy/
├── README.md
├── docker-compose.yml            # 单套编排模板（无 mysql，连物理机 MySQL）
├── docker-compose.sync.yml       # 全局 db-sync 编排
├── env/{set1,set2,set3,sync}.env
├── images/
│   ├── app_server/{Dockerfile, uwsgi.docker.ini, requirements.runtime.txt}
│   ├── scraper/{Dockerfile, run-loop.sh}
│   ├── db_sync/Dockerfile
│   ├── jxboot/Dockerfile
│   ├── jeeplus-web/Dockerfile
│   ├── jx-push/Dockerfile
│   └── nginx/{uniapp.conf, web_manager.conf}
└── scripts/{build-all.sh, init-host-dirs.sh}

db_sync/{db_sync.py, requirements.txt, .env.example}   # 同步服务源码
scraper/cache_only.py                                  # 副本套“只刷缓存”入口(新增)
```

### 4.2 服务器物理存储
```
/data/mmbookies/
├── set1/  (set2/ set3/ 同构)
│   ├── redis/data
│   ├── config/{app_server, scraper, jxboot, jeeplus-web, jx-push, nginx}
│   ├── logs/{...}
│   ├── static/app_server        # 后端上传图片
│   ├── uploads/jeeplus          # 管理端上传
│   └── web/{uniapp, manager}    # 两个前端静态产物
└── sync/{state, logs}           # db-sync 水位状态与日志

# MySQL 数据在物理机本机（如 /var/lib/mysql 或独立数据盘），不在上面目录内
```

---

## 5. 端口分配表（宿主机对外）

| 服务 | set1 | set2 | set3 |
|------|------|------|------|
| uniapp 前端 | **18080** | 28080 | 38080 |
| 管理端前端 | **18081** | 28081 | 38081 |
| app_server API | 18282 | 28282 | 38282 |
| jeeplus-web API | 18082 | 28082 | 38082 |
| jx-push WS/SSE | 18090 | 28090 | 38090 |
| jxboot 结算 | 19101 | 29101 | 39101 |
| Redis（仅管理，可关）| 16379 | 26379 | 36379 |
| MySQL（物理机）| 3306（三套共用实例、不同库）| | |

---

## 6. 部署步骤

### 6.1 物理机 MySQL8 准备（关键：让容器能连、账号权限、三个库）
```sql
-- 1) 让 MySQL 监听所有网卡（或至少 docker0 网关），/etc/my.cnf:
--    bind-address = 0.0.0.0

-- 2) 建三个库
CREATE DATABASE onex2_db_1 DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE onex2_db_2 DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE onex2_db_3 DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;

-- 3) 导入初始结构/数据到每个库（已有数据先 mysqldump 再导入）
--    mysql onex2_db_1 < onex2_db.sql   （set2/3 同理）

-- 4) 业务账号：允许来自 docker 网段(172.16.0.0/12) 连接
--    每套各自账号，只授权自己的库（与各服务 config 里的账号密码一致）
CREATE USER 'app1'@'172.%' IDENTIFIED BY 'App1_Pass';
GRANT ALL ON onex2_db_1.* TO 'app1'@'172.%';
-- app2/app3 同理授权 onex2_db_2/3 ...

-- 5) db-sync 专用账号：对三库都要有 SELECT/INSERT/UPDATE
CREATE USER 'sync_user'@'172.%' IDENTIFIED BY 'change_me_sync';
GRANT SELECT, INSERT, UPDATE ON onex2_db_1.* TO 'sync_user'@'172.%';
GRANT SELECT, INSERT, UPDATE ON onex2_db_2.* TO 'sync_user'@'172.%';
GRANT SELECT, INSERT, UPDATE ON onex2_db_3.* TO 'sync_user'@'172.%';
FLUSH PRIVILEGES;
```
> 防火墙：放行 docker 网段访问 3306，例如
> `firewall-cmd --permanent --zone=trusted --add-source=172.16.0.0/12 && firewall-cmd --reload`
> 容器内数据库主机统一写 `host.docker.internal`（compose 已把它解析到物理机网关）。

### 6.2 装 Docker（CentOS 7）
```bash
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
sysctl -w vm.max_map_count=262144 && echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
```
> `host.docker.internal:host-gateway` 需 Docker ≥ 20.10（CentOS7 官方源即满足）。

### 6.3 构建镜像
```bash
bash deploy/scripts/build-all.sh latest       # 含 db_sync
```

### 6.4 起每一套
```bash
bash deploy/scripts/init-host-dirs.sh set1     # 建目录（set2/set3 同理）
# 放配置(§7)、前端静态、nginx 配置
cd deploy
docker compose --env-file env/set1.env -p mm_set1 up -d   # 主套(含完整爬虫)
docker compose --env-file env/set2.env -p mm_set2 up -d   # 副本
docker compose --env-file env/set3.env -p mm_set3 up -d   # 副本
```

### 6.5 起全局 db-sync
```bash
cd deploy
# 编辑 env/sync.env 填 DB_USER/DB_PASSWORD（sync_user）
docker compose -f docker-compose.sync.yml --env-file env/sync.env -p mm_sync up -d
docker logs -f mm_sync-db-sync-1     # 看 upsert 影响行数与水位
```

### 6.6 校验
```bash
curl http://127.0.0.1:18282/hello            # set1 app_server
curl http://127.0.0.1:18282/match/list       # 应返回赛事（来自 Redis 缓存）
curl http://127.0.0.1:28282/match/list       # set2 应也有（db-sync + cache_only 生效）
```

---

## 7. 配置适配清单（部署前必改）

各服务 config 放到 `config/<svc>/`，把数据库主机改 `host.docker.internal`、库名改本套、Redis 主机改 `redis`（容器名）。

| 文件 | 改这些 |
|---|---|
| `app_server/.env` | `APP_ENV=production` |
| `app_server/.env.production` | `DB_ADDRESS=host.docker.internal`、`DATABASE=onex2_db_N`、`DB_USER/DB_PASSWORD`=本套账号、`REDIS_HOST=redis` |
| `scraper/.env` | `APP_ENV=production` |
| `scraper/.env.production` | `DB_HOST=host.docker.internal`、`DB_NAME=onex2_db_N`、账号本套、`REDIS_HOST=redis`；`API_URL` 指向本套 app_server |
| `jxboot/jboot.properties` | `...appmain.url=jdbc:mysql://host.docker.internal:3306/onex2_db_N...`、账号本套、`jboot.redis.host=redis`、`devMode=false` |
| `jeeplus-web/application-prod.yml` | `datasource...url=jdbc:mysql://host.docker.internal:3306/onex2_db_N...`、账号本套、`spring.data.redis.host=redis`、`devtools.restart.enabled=false` |
| `jx-push/application-prod.yml` | `datasource.url=...host.docker.internal:3306/onex2_db_N...`、账号本套、`spring.data.redis.host=redis`、确认 `push.queue.type=redis`；FCM 若启用放好 json |
| `nginx/{uniapp,web_manager}.conf` | 已写好反代到容器名，直接用；挂域名/HTTPS 再加 |
| `sync.env` | `DB_USER=sync_user`、`DB_PASSWORD`、`SYNC_SOURCE_DB=onex2_db_1`、`SYNC_TARGET_DBS=onex2_db_2,onex2_db_3` |

---

## 8. 服务器配置评估

### 8.1 单套容器内存（`mem_limit` / 稳态）

| 服务 | 上限 | 稳态 | 说明 |
|------|------|------|------|
| Redis | 320M | ~80–200M | |
| app_server | 1200M | ~0.8–1.1G | 精简依赖后 |
| scraper/cache_only | 512M | 主套~300–400M / 副本~150–250M | 副本只刷缓存更轻 |
| jxboot | 2200M | ~1.2–1.6G | Xmx1536m |
| jeeplus-web | 1800M | ~1.0–1.4G | Xmx1536m |
| jx-push | 1300M | ~0.9–1.1G | Xmx1024m |
| nginx ×2 | 256M | ~40M | |
| **单套容器合计（稳态）** | | **~4.5–5.9G** | 不含 MySQL |

### 8.2 物理机 MySQL 与 db-sync

| 项 | 稳态 | 说明 |
|----|------|------|
| MySQL8（承载 3 库）| ~2–4G | buffer-pool 建议 1.5–3G；连接数够用 |
| db-sync 容器 | ~80–150M | 服务端 SQL，Python 侧极轻 |

### 8.3 三套总量与推荐规格

| 指标 | 稳态 | 峰值 | **推荐** |
|------|------|------|----------|
| **内存** | 3×~5G + MySQL ~3G ≈ **18G** | ~24G | **32GB**（最低 24GB）|
| **CPU** | – | 每套 2–4 vCPU + MySQL | **16 vCPU**（最低 8）|
| **磁盘** | – | 见 §8.4 | **SSD 300–500GB** |

> 相比“每套独立 MySQL 容器”方案，本方案省掉 2 个 MySQL 容器实例，内存更省、备份更集中。

### 8.4 磁盘/数据评估

| 项 | 估算 |
|----|------|
| 镜像（多套复用同层）| ~2.5–3.5G（app_server~500M、scraper/db_sync~300M、3×JVM 复用 temurin~450M、redis/nginx 小）|
| MySQL 数据（3 库合计）| 初期 3–15G，半年 30–90G（赛事/订单/账变增长）|
| Redis 持久化 ×3 | ~1.5G |
| 日志 ×3 | ~9G（建议接 logrotate / compose json-file max-size）|
| 上传/静态 ×3 | ~30G |
| **合计（建议预留）** | **SSD 300–500GB**，`/data` 与 MySQL 数据盘建议单独 SSD |

---

## 9. 常用运维

```bash
# 某套启停
docker compose --env-file env/set1.env -p mm_set1 up -d
docker compose -p mm_set1 down
docker compose -p mm_set1 restart jeeplus-web

# 同步服务
docker compose -f docker-compose.sync.yml -p mm_sync logs -f
# 手动跑一轮同步（调试）：临时设 SYNC_RUN_ONCE=1

# 物理机 MySQL 备份（三库分别）
mysqldump -uroot -p onex2_db_1 > set1_$(date +%F).sql

# 资源
docker stats
```

---

## 10. 注意事项 / 待确认

1. **JDK**：镜像统一 `temurin:21-jre`（jeeplus/jx-push 为 JDK17 构建、jxboot 原 JDK18，21 向下兼容；jxboot 已加 `--add-opens`）。若 jxboot 在 21 上异常，可把其基础镜像换 `eclipse-temurin:18-jdk`。
2. **app_server 精简依赖**：首启若 `ModuleNotFoundError`，按 `requirements.runtime.txt` 顶部说明加回重建。
3. **jeeplus 启动**：镜像用 `-cp "jeeplus-vue.jar:classes:lib/*"` 启动；若你现网是 `java -jar` 且正常，可改回 ENTRYPOINT。
4. **db-sync 水位列**：默认按 `UPDATE_TIME/CREATE_TIME` 增量；若某表实际无 `UPDATE_TIME` 会退化为每轮全表覆盖（小表无妨）。首次启动会全量拷贝一次。
5. **cache_only 依赖库表**：副本套 `cache_only.py` 复用爬虫，导入时会读若干配置表（如 `sys_bis_dict`、`m_app_league`）——确保这些配置在副本库里也存在（db-sync 已同步 `m_app_league`；`sys_bis_dict` 等业务字典若各套独立维护，需各套自备）。
6. **软删除/隐藏**：全量覆盖策略下副本套的赛事 hide/status 完全跟随主库；副本套运营端对赛事的人工隐藏会被下轮同步覆盖。若需各套独立隐藏，改同步策略。
7. **域名/HTTPS**：如需正式域名，建议在三套 nginx 前再加一层宿主机 nginx/Traefik 做 443 分流，或各套 nginx 挂证书。
