from __future__ import annotations

import pandas as pd

from utils.dates import add_calendar_columns


def build_disease_weekly(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0).astype(int)
    df = add_calendar_columns(df, "date")

    group_cols = [
        "source",
        "yearweek",
        "year",
        "week",
        "week_start_date",
        "week_end_date",
        "branch",
        "county",
        "disease",
        "age_group",
    ]

    weekly = (
        df.groupby(group_cols, dropna=False, as_index=False)
        .agg(count=("count", "sum"), total=("total", "sum"))
    )
    return weekly
