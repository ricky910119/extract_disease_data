from __future__ import annotations

import pandas as pd

from transforms.disease_model import (
    build_disease_age_pivot_model,
    merge_disease_model_with_weather,
)


def build_model_dataset(
    df_raw_disease: pd.DataFrame,
    df_weather_weekly: pd.DataFrame | None = None,
    df_dim_agegroup: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    建立最終模型資料。

    疾病資料會先依 yearweek + branch + county 彙總，
    再將 disease x age_group 轉為欄位，
    最後合併 weather_weekly_city。
    """
    if df_raw_disease.empty:
        return pd.DataFrame()

    disease_model = build_disease_age_pivot_model(
        df_raw=df_raw_disease,
        df_dim_agegroup=df_dim_agegroup,
    )

    return merge_disease_model_with_weather(
        df_disease_model=disease_model,
        df_weather_weekly=df_weather_weekly,
    )