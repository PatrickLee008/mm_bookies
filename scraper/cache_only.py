# -*- coding: utf-8 -*-
"""
只刷新 Redis 赛事缓存（供副本套 set2/set3 使用）。

背景：赛事列表 API(get_match_list) 从 Redis 读缓存，而不是直接查 MySQL。
主套 set1 由完整爬虫 ibet_runner2.py 写库并刷缓存；副本套 set2/set3 的 MySQL
由 db_sync 服务从主库全量同步过来，但它们各自的 Redis 还需要用本库数据重建缓存。

本脚本复用爬虫现成的 cache_to_redis()：从"当前进程配置指向的库"读数据、写"当前进程
配置指向的 Redis"，因此在副本套容器里（DB/Redis 都指向本套）运行即可，绝不做网页爬取。
"""
from ibet_runner2 import cache_to_redis, logger


def main():
    logger.info("[cache_only] 开始从本库重建 Redis 赛事缓存 ...")
    try:
        cache_to_redis()
        logger.info("[cache_only] Redis 赛事缓存重建完成")
    except Exception:
        logger.exception("[cache_only] 缓存重建失败")
        raise


if __name__ == "__main__":
    main()
