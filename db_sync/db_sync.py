# -*- coding: utf-8 -*-
"""
db_sync —— 跨库增量同步服务（单机同一 MySQL 实例、多库之间）

场景：
  - 物理机上一个 MySQL8 实例，三套各用一个库：onex2_db_1(主) / onex2_db_2 / onex2_db_3
  - 只有主库有爬虫写入公共赛事数据；本服务把主库的公共表【全量覆盖】增量同步到其余库
  - 因三库同实例，采用服务端跨库 INSERT...SELECT...ON DUPLICATE KEY UPDATE，不把数据搬到 Python

策略：全量覆盖（以主库为准）。按“水位列”(watermark) 增量：只处理自上次以来有变化的行，
      再用 ON DUPLICATE KEY UPDATE 覆盖目标库同主键的所有列。幂等、可重复执行。

限制：只做 INSERT/UPDATE 覆盖，不传播主库的“物理删除”（业务用 hide/status 软标记，会随列覆盖同步）。
      如需传播硬删除，另加对账任务。

配置（环境变量，见 .env.example）：
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD      —— 连接物理机 MySQL（账号需对相关库有权限）
  SYNC_SOURCE_DB                              —— 主库名，如 onex2_db_1
  SYNC_TARGET_DBS                             —— 目标库，逗号分隔，如 onex2_db_2,onex2_db_3
  SYNC_TABLES                                 —— 表清单；每项 "表名[:水位表达式]"，分号分隔
  SYNC_INTERVAL                               —— 循环间隔秒，默认 15
  SYNC_STATE_FILE                             —— 水位持久化文件，默认 /app/state/sync_state.json
  SYNC_OVERLAP_SECONDS                        —— 水位回退重叠秒，默认 5（防止边界漏行）
  SYNC_RUN_ONCE                               —— =1 只跑一轮退出（调试用）
"""
import os
import sys
import json
import time
import signal
import logging
from datetime import datetime, timedelta

import pymysql

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("db_sync")

# ---------------- 配置解析 ----------------
DB_HOST = os.getenv("DB_HOST", "host.docker.internal")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
SOURCE_DB = os.getenv("SYNC_SOURCE_DB", "onex2_db_1")
TARGET_DBS = [x.strip() for x in os.getenv("SYNC_TARGET_DBS", "").split(",") if x.strip()]
INTERVAL = int(os.getenv("SYNC_INTERVAL", "15"))
STATE_FILE = os.getenv("SYNC_STATE_FILE", "/app/state/sync_state.json")
OVERLAP = int(os.getenv("SYNC_OVERLAP_SECONDS", "5"))
RUN_ONCE = os.getenv("SYNC_RUN_ONCE", "0") == "1"

# 默认同步 5 张公共表及其水位列（无水位列的表将每轮全表覆盖）
DEFAULT_TABLES = (
    "m_app_match:COALESCE(UPDATE_TIME,CREATE_TIME);"
    "m_app_match_attr:COALESCE(UPDATE_TIME,CREATE_TIME);"
    "result:CREATE_TIME;"
    "m_app_league_team_scraper:COALESCE(update_time,create_time);"
    "m_app_league:COALESCE(update_time,create_time)"
)


def parse_tables(spec):
    """解析 "表名[:水位表达式];..." -> [(table, wm_expr_or_None), ...]"""
    out = []
    for item in spec.split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            name, wm = item.split(":", 1)
            out.append((name.strip(), wm.strip() or None))
        else:
            out.append((item, None))
    return out


TABLES = parse_tables(os.getenv("SYNC_TABLES", DEFAULT_TABLES))

_running = True


def _stop(signum, frame):
    global _running
    log.info("收到退出信号 %s，准备结束", signum)
    _running = False


signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT, _stop)


# ---------------- 状态持久化 ----------------
def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)


# ---------------- 元数据反射 ----------------
_meta_cache = {}


def get_columns(cur, schema, table):
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
        (schema, table),
    )
    return [r[0] for r in cur.fetchall()]


def get_pk(cur, schema, table):
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY' "
        "ORDER BY ORDINAL_POSITION",
        (schema, table),
    )
    return [r[0] for r in cur.fetchall()]


def table_meta(cur, source_db, target_db, table):
    """返回 (共有列, 主键列, 非主键列)；结果缓存。"""
    key = (source_db, target_db, table)
    if key in _meta_cache:
        return _meta_cache[key]
    src_cols = get_columns(cur, source_db, table)
    tgt_cols = set(get_columns(cur, target_db, table))
    if not src_cols:
        raise RuntimeError(f"源库缺表 {source_db}.{table}")
    if not tgt_cols:
        raise RuntimeError(f"目标库缺表 {target_db}.{table}")
    cols = [c for c in src_cols if c in tgt_cols]  # 取交集，容忍轻微 schema 差异
    pk = [c for c in get_pk(cur, source_db, table) if c in cols]
    if not pk:
        raise RuntimeError(f"表 {table} 无主键，无法 upsert")
    non_pk = [c for c in cols if c not in pk]
    _meta_cache[key] = (cols, pk, non_pk)
    return _meta_cache[key]


# ---------------- 单表同步 ----------------
def sync_one(cur, source_db, target_db, table, wm_expr, last_wm):
    cols, pk, non_pk = table_meta(cur, source_db, target_db, table)
    col_list = ", ".join(f"`{c}`" for c in cols)
    if non_pk:
        upd = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in non_pk)
    else:
        # 全为主键列的表：主键相同即无需更新，用主键自身占位
        upd = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in pk)

    where = ""
    params = []
    if wm_expr and last_wm:
        where = f"WHERE {wm_expr} >= %s"
        params.append(last_wm)

    sql = (
        f"INSERT INTO `{target_db}`.`{table}` ({col_list}) "
        f"SELECT {col_list} FROM `{source_db}`.`{table}` {where} "
        f"ON DUPLICATE KEY UPDATE {upd}"
    )
    cur.execute(sql, params)
    affected = cur.rowcount

    # 计算新水位
    new_wm = last_wm
    if wm_expr:
        cur.execute(f"SELECT MAX({wm_expr}) FROM `{source_db}`.`{table}`")
        row = cur.fetchone()
        if row and row[0]:
            mx = row[0]
            if isinstance(mx, datetime):
                mx = mx - timedelta(seconds=OVERLAP)  # 回退重叠，防边界漏行
                new_wm = mx.strftime("%Y-%m-%d %H:%M:%S")
            else:
                new_wm = str(mx)
    return affected, new_wm


def run_cycle(conn, state):
    with conn.cursor() as cur:
        for target_db in TARGET_DBS:
            tstate = state.setdefault(target_db, {})
            for table, wm_expr in TABLES:
                last_wm = tstate.get(table) if wm_expr else None
                try:
                    affected, new_wm = sync_one(cur, SOURCE_DB, target_db, table, wm_expr, last_wm)
                    conn.commit()
                    if wm_expr and new_wm:
                        tstate[table] = new_wm
                    if affected:
                        log.info("[%s.%s] upsert 影响 %s 行 (水位=%s)", target_db, table, affected, tstate.get(table))
                except Exception:
                    conn.rollback()
                    log.exception("[%s.%s] 同步失败", target_db, table)
    save_state(state)


def main():
    if not TARGET_DBS:
        log.error("未配置 SYNC_TARGET_DBS，退出")
        sys.exit(1)
    log.info("db_sync 启动: 源=%s 目标=%s 表=%s 间隔=%ss",
             SOURCE_DB, TARGET_DBS, [t[0] for t in TABLES], INTERVAL)
    state = load_state()

    while _running:
        start = time.time()
        try:
            conn = pymysql.connect(
                host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
                charset="utf8mb4", autocommit=False, connect_timeout=10,
            )
            try:
                run_cycle(conn, state)
            finally:
                conn.close()
        except Exception:
            log.exception("本轮同步异常")
        if RUN_ONCE:
            log.info("RUN_ONCE=1，单轮结束退出")
            break
        elapsed = time.time() - start
        time.sleep(max(1, INTERVAL - elapsed))


if __name__ == "__main__":
    main()
