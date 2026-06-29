from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config.local_store import RAW_DATE_COLUMNS, RAW_FILES, RAW_KEYS
from config.settings import CSV_ENCODING
from utils.dates import list_months


def profile_raw_source(source: str) -> dict[str, Any]:
    path = RAW_FILES[source]
    date_col = RAW_DATE_COLUMNS[source]
    key_cols = RAW_KEYS.get(source, [])

    result: dict[str, Any] = {
        "file_path": str(path),
        "file_exists": path.exists(),
        "row_count": 0,
        "min_date": None,
        "max_date": None,
        "missing_months": [],
        "duplicated_key_count": None,
        "null_key_count": None,
    }
    if not path.exists():
        return result

    df = pd.read_csv(path, encoding=CSV_ENCODING, parse_dates=[date_col])
    result["row_count"] = int(len(df))
    if df.empty:
        return result

    df[date_col] = pd.to_datetime(df[date_col])
    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()
    result["min_date"] = str(min_date)
    result["max_date"] = str(max_date)

    expected_months = set(list_months(min_date, max_date))
    actual_months = set(df[date_col].dt.to_period("M").astype(str).unique())
    result["missing_months"] = sorted(expected_months - actual_months)

    existing_keys = [c for c in key_cols if c in df.columns]
    if existing_keys:
        result["duplicated_key_count"] = int(df.duplicated(subset=existing_keys).sum())
        result["null_key_count"] = int(df[existing_keys].isna().any(axis=1).sum())

    return result


def profile_all_raw_sources() -> dict[str, dict[str, Any]]:
    return {source: profile_raw_source(source) for source in RAW_FILES}
