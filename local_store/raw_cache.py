from __future__ import annotations

import pandas as pd

from config.local_store import RAW_DATE_COLUMNS, RAW_FILES, RAW_KEYS
from local_store.csv_store import read_csv_cache, replace_by_date_range


def get_raw_path(source: str):
    if source not in RAW_FILES:
        raise KeyError(f"Unsupported raw source: {source}")
    return RAW_FILES[source]


def save_raw_range(source: str, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    path = get_raw_path(source)
    date_col = RAW_DATE_COLUMNS[source]
    key_cols = RAW_KEYS.get(source)
    return replace_by_date_range(
        path=path,
        new_df=df,
        start_date=start_date,
        end_date=end_date,
        date_col=date_col,
        key_cols=key_cols,
    )


def load_raw(source: str) -> pd.DataFrame:
    path = get_raw_path(source)
    date_col = RAW_DATE_COLUMNS[source]
    return read_csv_cache(path, [date_col])


def load_raw_range(source: str, start_date: str, end_date: str) -> pd.DataFrame:
    df = load_raw(source)
    if df.empty:
        return df
    date_col = RAW_DATE_COLUMNS[source]
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    return df.loc[df[date_col].between(start, end)].reset_index(drop=True)
