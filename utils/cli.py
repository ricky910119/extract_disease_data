from __future__ import annotations

import argparse

from config.sources import ALL_SOURCES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="extract_disease_data ETL")
    parser.add_argument(
        "--mode",
        choices=["initial", "incremental", "check-only"],
        required=True,
        help="執行模式",
    )
    parser.add_argument(
        "--source",
        choices=["all", *ALL_SOURCES],
        default="all",
        help="指定來源；預設 all",
    )
    parser.add_argument("--start-date", default=None, help="資料起始日 YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="資料結束日 YYYY-MM-DD")
    parser.add_argument("--lookback-days", type=int, default=None, help="incremental 回補天數")
    parser.add_argument("--skip-extract", action="store_true", help="直接使用既有 local raw cache 重算模型表")
    parser.add_argument("--skip-upload", action="store_true", help="只更新 local raw cache，不上傳 PG")
    return parser.parse_args()
