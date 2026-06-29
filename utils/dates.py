from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

import pandas as pd


def to_date(value: str | date | datetime | pd.Timestamp) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def today_date() -> date:
    return date.today()


def date_to_iso_yearweek(value: str | date | datetime | pd.Timestamp) -> int:
    d = to_date(value)
    iso = d.isocalendar()
    return int(f"{iso.year}{iso.week:02d}")


def add_calendar_columns(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    iso = out[date_col].dt.isocalendar()
    out["year"] = iso["year"].astype(int)
    out["week"] = iso["week"].astype(int)
    out["yearweek"] = (out["year"].astype(str) + out["week"].astype(str).str.zfill(2)).astype(int)
    out["week_start_date"] = (out[date_col] - pd.to_timedelta(out[date_col].dt.weekday, unit="D")).dt.date
    out["week_end_date"] = (pd.to_datetime(out["week_start_date"]) + pd.to_timedelta(6, unit="D")).dt.date
    out[date_col] = out[date_col].dt.date
    return out


def date_range_to_yearweek_range(start_date: str | date, end_date: str | date) -> tuple[int, int]:
    return date_to_iso_yearweek(start_date), date_to_iso_yearweek(end_date)


def list_months(start_date: str | date, end_date: str | date) -> list[str]:
    start = pd.Period(pd.to_datetime(start_date), freq="M")
    end = pd.Period(pd.to_datetime(end_date), freq="M")
    return [str(p) for p in pd.period_range(start, end, freq="M")]


def list_iso_yearweeks(start_date: str | date, end_date: str | date) -> list[int]:
    start = pd.to_datetime(start_date).normalize()
    end = pd.to_datetime(end_date).normalize()
    dates = pd.date_range(start, end, freq="D")
    weeks = []
    seen = set()
    for d in dates:
        yw = date_to_iso_yearweek(d)
        if yw not in seen:
            seen.add(yw)
            weeks.append(yw)
    return weeks


def resolve_incremental_start(last_success_end_date: str | None, lookback_days: int, default_start_date: str) -> date:
    if not last_success_end_date:
        return to_date(default_start_date)
    return to_date(last_success_end_date) - timedelta(days=lookback_days)
