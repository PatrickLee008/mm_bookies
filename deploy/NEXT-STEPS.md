# MM Bookies · Docker 部署交接与下一步

> 本文档汇总已完成的 Docker 部署工作、待确认清单，以及可直接复用的“下一步完善提示词”。
> 配套文档见 [README.md](./README.md)（完整方案/架构/端口/建库授权/sizing）。

---

## 一、已完成工作总结

### 1. 目标架构（已定稿）
- 一台 CentOS 7，Docker 部署 **3 套**互相隔离应用；端口隔离 + 数据隔离。
- **MySQL 用物理机** MySQL8，三套连不同库 `onex2_db_1/2/3`（容器经 `host.docker.internal` 访问）。
- **Redis 每套独立容器**。
- **只跑一个爬虫**（set1 主套）→ 写主库 + 刷 set1 缓存；
  **db-sync**（全局 1 容器）把主库 5 张公共表**全量覆盖增量同步**到另两库；
  set2/set3 用 `cache_only.py` **只重建本套 Redis 赛事缓存**（因赛事列表 API 读 Redis）。

### 2. 服务清单与运行方式
| 服务 | 镜像基础 | 启动 | 端口(容器) |
|---|---|---|---|
| app_server | python:3.8-slim + uwsgi | `uwsgi --ini uwsgi.ini` | 8282 |
| scraper / cache_only | python:3.10-slim | `run-loop.sh`（SCRAPER_ENTRY 切角色）| – |
| db_sync | python:3.10-slim | `python db_sync.py` | – |
| jxboot | temurin:21-jre | `java -cp config:lib/*` | 9101 |
| jeeplus-web | temurin:21-jre | `java -cp jar:classes:lib/* ...prod` | 8082 |
| jx-push | temurin:21-jre | `java -jar ...prod` | 8090 |
| uniapp/manager | nginx:1.25-alpine | 挂载静态 + 反代 | 80 |

### 3. 交付物清单
```
deploy/
├── README.md, NEXT-STEPS.md
├── docker-compose.yml            # 单套编排(连物理机MySQL, 爬虫按角色)
├── docker-compose.sync.yml       # 全局 db-sync
├── env/{set1,set2,set3,sync}.env
├── images/{app_server,scraper,db_sync,jxboot,jeeplus-web,jx-push,nginx}/...
└── scripts/{build-all.sh, init-host-dirs.sh}
db_sync/{db_sync.py, requirements.txt, .env.example}   # 新增同步服务源码
scraper/cache_only.py                                  # 新增“只刷缓存”入口
.dockerignore
```
关键结论（代码扫描）：app_server 运行时不用 OCR/CV 重库(已精简)；赛事列表读 Redis；jx-push prod 用 Redis 队列不需 RabbitMQ；scraper 是批处理。

### 4. 尚未做的部分（下一步）
- [ ] 各套 config 实际填值文件（DB host/库名/账号、Redis host）——目前只有改动清单
- [ ] 前端 apiUrl/wsUrl 按套指向（uniapp `siteinfo.js`、web_manager 配置）
- [ ] 镜像实测构建（app_server 依赖、jeeplus classpath、JDK21 兼容需验证）
- [ ] 初始数据库 dump 准备与导入（全新 or 迁移现网）
- [ ] 一键部署脚本、日志轮转、备份 cron、jxboot 健康检查完善
- [ ] 域名/HTTPS（是否加顶层反代）

---

## 二、待确认清单（部署前必须拍板）

| # | 事项 | 选项/影响 |
|---|---|---|
| 1 | **初始数据** | 全新空库建表，还是迁移现网 `onex2_db` dump 到三库？ |
| 2 | **物理机 MySQL** | 版本(8.x?)、bind-address 能否 0.0.0.0、授权网段(172.16/12) |
| 3 | **各套 DB 账号** | 每套独立账号密码？还是统一 root？（影响 config 与授权 SQL）|
| 4 | **配置表同步范围** | `sys_bis_dict` 等爬虫/字典配置是否也纳入 db-sync？（默认只同步 5 张）|
| 5 | **覆盖策略再确认** | 已选“全量覆盖”→ 副本套不能本地改盘/隐藏，OK？否则改“保留本地人工字段” |
| 6 | **JDK21 兼容** | jxboot(原JDK18)/jeeplus/jx-push 实测能否在 temurin:21 跑，异常则回退 18/17 |
| 7 | **app_server 依赖** | 精简依赖首启是否报缺包（需回填） |
| 8 | **jeeplus 启动** | 现网是 `java -jar` 还是 classpath？确认主类/资源加载正常 |
| 9 | **外部对接按套区分** | 支付回调 URL、AWC 回调、短链域名、FCM 凭据、JWT secret 是否每套不同？|
| 10 | **前端入口** | 三套 uniapp/manager 的 apiUrl/wsUrl（走各自 nginx 端口还是各自域名）|
| 11 | **域名/HTTPS** | 是否需要，采用顶层 nginx/Traefik 还是各套 nginx 挂证书 |
| 12 | **时区/端口** | 确认 `Asia/Yangon`；1/2/3xxxx 端口段与现网无冲突 |
| 13 | **资源上限** | 目标服务器实际内存/CPU/磁盘，据此微调 JVM Xmx 与 mem_limit |

---

## 三、下一步完善提示词（可直接复制到新会话）

```
背景：MM Bookies 项目要在一台 CentOS7 上用 Docker 部署 3 套隔离应用，方案已在
deploy/ 目录完成（见 deploy/README.md 与 deploy/NEXT-STEPS.md）。架构要点：
- MySQL 用物理机 MySQL8，三套连 onex2_db_1/2/3；Redis 每套独立容器。
- 只跑一个爬虫(set1)，db_sync 服务把主库5张公共表全量覆盖增量同步到另两库，
  set2/3 用 scraper 的 cache_only.py 只重建本套 Redis 赛事缓存。
- 服务：app_server(Flask/uwsgi)、scraper、db_sync、jxboot、jeeplus-web、jx-push、
  两个 nginx 静态前端。

请帮我推进落地，按下面顺序，每步先问我确认再动手：

1) 生成三套的实际配置文件（填好值，不只是清单）：
   为 set1/2/3 各生成 config/ 下的 app_server(.env/.env.production)、scraper(.env/.env.production)、
   jxboot(jboot.properties)、jeeplus-web(application-prod.yml)、jx-push(application-prod.yml)，
   把 DB 主机改 host.docker.internal、库名 onex2_db_N、Redis 主机 redis、账号密码用我给的值。
   放到 deploy/config-templates/setN/ 供拷贝。

2) 前端按套配置：定位并生成 uniapp 的 siteinfo.js 与 web_manager 的接口地址配置，
   让三套分别指向各自 nginx 端口/域名（apiUrl、wsUrl）。

3) 生成一键部署脚本 deploy/scripts/deploy-set.sh <setN>：建目录→拷配置→拷前端静态→
   docker compose up -d，并加 up 全局 db-sync 的脚本。

4) 加固：compose 加日志 json-file max-size 限制；完善 jxboot 健康检查；
   加 MySQL 备份 cron 脚本；（可选）加顶层 nginx/Traefik 做域名+HTTPS 分流。

5) 出一份“构建与首次上线 checklist”，含验证命令与回滚步骤。

先确认以下事项（我的回答见下，未答的你按推荐默认并标注）：
- 初始数据：全新空库 / 迁移现网 dump？
- 各套 DB 账号密码、sync_user 密码？
- sys_bis_dict 等配置表是否纳入同步？
- 覆盖策略保持“全量覆盖”还是改“保留本地人工字段”？
- 支付回调/AWC/短链/FCM/JWT secret 是否每套不同？各套域名或对外端口是什么？
- 目标服务器实际内存/CPU/磁盘规格？
```

> 使用方法：把上面代码块整段复制，按需在末尾填上你的确认答案，即可让后续会话据此继续完善。
