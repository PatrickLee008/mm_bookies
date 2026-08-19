#!/usr/bin/env bash
# 爬虫循环调度：ibet_runner2.main() 每轮跑完退出，这里按 SCRAPE_INTERVAL 秒间隔反复执行。
# 如需改成固定入口脚本，修改下面的 RUNNER 即可。
set -o pipefail

RUNNER="${SCRAPER_ENTRY:-ibet_runner2.py}"
INTERVAL="${SCRAPE_INTERVAL:-30}"

echo "[scraper] entry=${RUNNER}  interval=${INTERVAL}s  APP_ENV=${APP_ENV}"

# 优雅退出
trap 'echo "[scraper] received TERM, exiting"; exit 0' TERM INT

while true; do
  START=$(date +%s)
  echo "[scraper] ===== run start $(date '+%F %T') ====="
  python "/app/${RUNNER}" || echo "[scraper] run failed (exit=$?), will retry"
  END=$(date +%s)
  echo "[scraper] ===== run done in $((END-START))s ====="
  sleep "${INTERVAL}"
done
