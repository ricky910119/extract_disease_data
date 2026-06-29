from __future__ import annotations

import pandas as pd

from utils.dates import list_iso_yearweeks


def missing_yearweeks_from_df(df: pd.DataFrame, yearweek_col: str = "yearweek") -> list[int]:
    if df.empty or yearweek_col not in df.columns:
        return []
    actual = sorted(pd.Series(df[yearweek_col]).dropna().astype(int).unique())
    if not actual:
        return []

    min_yw = str(actual[0])
    max_yw = str(actual[-1])
    start = f"{min_yw[:4]}-01-04"
    end = f"{max_yw[:4]}-12-28"
    expected = [yw for yw in list_iso_yearweeks(start, end) if actual[0] <= yw <= actual[-1]]
    return sorted(set(expected) - set(actual))
