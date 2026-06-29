from __future__ import annotations

import pandas as pd

from config.settings import AGE_GROUP_COLUMN_MAP, MODEL_AGE_COLUMNS


def pivot_age_counts(df_weekly: pd.DataFrame) -> pd.DataFrame:
    if df_weekly.empty:
        return pd.DataFrame()

    df = df_weekly.copy()
    df["age_col"] = df["age_group"].map(AGE_GROUP_COLUMN_MAP).fillna("count_age_unknown")

    index_cols = [
        "source",
        "yearweek",
        "year",
        "week",
        "week_start_date",
        "week_end_date",
        "branch",
        "county",
        "disease",
    ]

    pivot = (
        df.pivot_table(
            index=index_cols,
            columns="age_col",
            values="count",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    pivot.columns.name = None

    for col in MODEL_AGE_COLUMNS:
        if col not in pivot.columns:
            pivot[col] = 0
        pivot[col] = pd.to_numeric(pivot[col], errors="coerce").fillna(0).astype(int)

    total_visit = (
        df.groupby(index_cols, dropna=False, as_index=False)
        .agg(total_visit=("total", "sum"))
    )

    out = pivot.merge(total_visit, on=index_cols, how="left")
    out["count_total"] = out[MODEL_AGE_COLUMNS].sum(axis=1).astype(int)
    out["total_visit"] = pd.to_numeric(out["total_visit"], errors="coerce").fillna(0).astype(int)

    ordered = index_cols + ["count_total", "total_visit"] + MODEL_AGE_COLUMNS
    return out[ordered].sort_values(["yearweek", "county", "disease"]).reset_index(drop=True)
