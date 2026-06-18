#!/usr/bin/env python3
"""
每日A股市场 + 财报数据更新脚本（自包含版本）
由 cron 在 9:00 / 15:00 触发，使用 WebSearch 获取数据后更新 market.html

用法: python _daily_update.py
"""

import subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "_daily_update.log")

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")
    print(msg)

if __name__ == "__main__":
    log("=== 每日A股数据更新开始 ===")
    log(f"工作目录: {BASE}")

    # Tell Claude to run the update via git commit hook or just run the searches
    # This script is designed to be called by the cron prompt handler

    log("脚本已就绪，等待 Claude 处理 WebSearch + 数据更新")
    log(f"日志路径: {LOG}")
