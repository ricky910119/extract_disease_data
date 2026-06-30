from __future__ import annotations

import argparse

from config.settings import INITIAL_START_DATE, END_DATE_LAG_DAYS
from extractors.model_source_total_weekly_county import (
    run_model_source_total_weekly_county,
)
from utils.dates import auto_end_date


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill model_source_total_weekly_county full history."
    )

    parser.add_argument(
        "--start-date",
        default=INITIAL_START_DATE,
        help=f"Start date, default={INITIAL_START_DATE}",
    )

    parser.add_argument(
        "--end-date",
        default=None,
        help="End date, default=auto_end_date(END_DATE_LAG_DAYS)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    start_date = args.start_date
    end_date = args.end_date or str(auto_end_date(END_DATE_LAG_DAYS))

    print(
        "[BACKFILL] model_source_total_weekly_county "
        f"start_date={start_date}, end_date={end_date}"
    )

    df = run_model_source_total_weekly_county(
        start_date=start_date,
        end_date=end_date,
    )

    print("[BACKFILL] finished")
    print(f"[BACKFILL] rows={len(df)}")

    if not df.empty:
        print(
            df.groupby("data_source", as_index=False)
            .agg(
                rows=("yearweek", "size"),
                min_yearweek=("yearweek", "min"),
                max_yearweek=("yearweek", "max"),
                total_count_sum=("total_count", "sum"),
            )
        )


if __name__ == "__main__":
    main()