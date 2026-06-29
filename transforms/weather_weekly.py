from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.dates import add_calendar_columns


SUM_COLUMNS = {
    "raw_station_rows",
    "precipitation_accumulation_mean",
    "precipitation_duration_total_mean",
    "sunshine_duration_total_mean",
    "global_solar_radiation_accumulation_mean",
    "evaporation_class_a_pan_accumulation_mean",
}

MAX_COLUMNS = {
    "station_count",
    "station_pressure_max",
    "sea_level_pressure_max",
    "air_temperature_max",
    "dew_point_temperature_max",
    "relative_humidity_max",
    "wind_speed_ten_minutely_max",
    "peak_gust_max",
    "precipitation_accumulation_max",
    "precipitation_hourly_maximum_max",
    "precipitation_sixty_minutely_maximum_max",
    "precipitation_ten_minutely_maximum_max",
    "precipitation_duration_total_max",
    "global_solar_radiation_hourly_maximum_max",
    "uv_index_maximum_max",
    "air_temperature_non_null_station_count",
    "relative_humidity_non_null_station_count",
    "precipitation_non_null_station_count",
    "station_pressure_non_null_station_count",
    "wind_speed_non_null_station_count",
    "sunshine_duration_non_null_station_count",
    "uv_index_non_null_station_count",
}

MIN_COLUMNS = {
    "station_pressure_min",
    "sea_level_pressure_min",
    "air_temperature_min",
    "dew_point_temperature_min",
    "relative_humidity_min",
}

MODE_COLUMNS = {
    "wind_direction_prevailing_mode",
    "wind_direction_ten_minutely_max_mode",
    "peak_gust_direction_mode",
}

KEEP_TEXT_COLUMNS = {"city"}


def _mode_or_none(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return None
    mode_values = values.mode()
    if mode_values.empty:
        return values.iloc[0]
    return mode_values.iloc[0]


def _build_agg_dict(df: pd.DataFrame) -> dict[str, str | callable]:
    agg_dict: dict[str, str | callable] = {}
    reserved = {"date", "county", "year", "week", "yearweek", "week_start_date", "week_end_date"}

    for col in df.columns:
        if col in reserved:
            continue
        if col in KEEP_TEXT_COLUMNS:
            agg_dict[col] = _mode_or_none
            continue
        if col in MODE_COLUMNS:
            agg_dict[col] = _mode_or_none
            continue

        converted = pd.to_numeric(df[col], errors="coerce")
        if not converted.notna().any():
            continue

        df[col] = converted
        if col in SUM_COLUMNS:
            agg_dict[col] = "sum"
        elif col in MAX_COLUMNS or col.endswith("_max"):
            agg_dict[col] = "max"
        elif col in MIN_COLUMNS or col.endswith("_min"):
            agg_dict[col] = "min"
        else:
            agg_dict[col] = "mean"

    return agg_dict


def build_weather_weekly(df_raw: pd.DataFrame, date_col: str = "date", county_col: str = "county") -> pd.DataFrame:
    """將每日縣市天氣資料整理為週別縣市天氣資料。"""
    if df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    date_col = date_col.lower()
    county_col = county_col.lower()

    if date_col not in df.columns:
        raise KeyError(f"weather date column not found: {date_col}")
    if county_col not in df.columns:
        raise KeyError(f"weather county column not found: {county_col}")

    df = df.rename(columns={date_col: "date", county_col: "county"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["county"] = df["county"].fillna("未知")
    df = add_calendar_columns(df, "date")

    group_cols = ["yearweek", "year", "week", "week_start_date", "week_end_date", "county"]
    agg_dict = _build_agg_dict(df)

    if agg_dict:
        weekly = df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()
    else:
        weekly = df[group_cols].drop_duplicates().reset_index(drop=True)

    observed_days = (
        df.groupby(group_cols, dropna=False)["date"]
        .nunique()
        .reset_index(name="weather_observed_days")
    )
    weekly = weekly.merge(observed_days, on=group_cols, how="left")
    weekly["weather_observed_days"] = weekly["weather_observed_days"].fillna(0).astype(int)
    weekly["weather_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return weekly.sort_values(["yearweek", "county"]).reset_index(drop=True)
