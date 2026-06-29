from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from config.settings import CSV_ENCODING


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv_cache(path: Path, date_columns: Iterable[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    parse_dates = list(date_columns or [])
    return pd.read_csv(path, encoding=CSV_ENCODING, parse_dates=parse_dates)


def write_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding=CSV_ENCODING)
    tmp.replace(path)


def replace_by_date_range(
    path: Path,
    new_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    date_col: str = "date",
    key_cols: list[str] | None = None,
) -> pd.DataFrame:
    new_df = new_df.copy()
    if new_df.empty:
        if path.exists():
            return read_csv_cache(path, [date_col])
        return new_df

    new_df[date_col] = pd.to_datetime(new_df[date_col]).dt.date
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()

    old_df = read_csv_cache(path, [date_col])
    if old_df.empty:
        combined = new_df
    else:
        old_df[date_col] = pd.to_datetime(old_df[date_col]).dt.date
        old_keep = old_df.loc[~old_df[date_col].between(start, end)].copy()
        combined = pd.concat([old_keep, new_df], axis=0, ignore_index=True)

    if key_cols:
        existing_keys = [c for c in key_cols if c in combined.columns]
        if existing_keys:
            combined = combined.drop_duplicates(subset=existing_keys, keep="last")

    sort_cols = [c for c in [date_col, "source", "branch", "county", "age_group", "disease"] if c in combined.columns]
    if sort_cols:
        combined = combined.sort_values(sort_cols).reset_index(drop=True)

    write_csv_atomic(combined, path)
    return combined
