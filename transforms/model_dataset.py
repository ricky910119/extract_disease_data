from __future__ import annotations

from datetime import datetime

import pandas as pd

from transforms.disease_age_pivot import pivot_age_counts
from transforms.disease_weekly import build_disease_weekly


def build_model_dataset(df_raw_disease: pd.DataFrame, df_weather_weekly: pd.DataFrame | None = None) -> pd.DataFrame:
    if df_raw_disease.empty:
        return pd.DataFrame()

    disease_weekly = build_disease_weekly(df_raw_disease)
    disease_pivot = pivot_age_counts(disease_weekly)

    if df_weather_weekly is not None and not df_weather_weekly.empty:
        weather = df_weather_weekly.copy()
        merge_cols = ["yearweek", "county"]
        drop_cols = [c for c in ["year", "week", "week_start_date", "week_end_date"] if c in weather.columns]
        weather = weather.drop(columns=drop_cols, errors="ignore")
        out = disease_pivot.merge(weather, on=merge_cols, how="left")
    else:
        out = disease_pivot

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out["updated_at"] = now
    return out.sort_values(["yearweek", "county", "disease"]).reset_index(drop=True)
