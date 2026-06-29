from __future__ import annotations

from datetime import datetime

import pandas as pd

from config.settings import DISEASE_VALUE_COLUMNS
from utils.dates import add_calendar_columns


AGE_GROUP_VALUE_CANDIDATES = [
    "age_group",
    "agegroup",
    "age_group_name",
    "agegroup_name",
    "age_name",
    "name",
]

AGE_GROUP_ORDER_CANDIDATES = [
    "sort_order",
    "age_group_order",
    "agegroup_order",
    "order_no",
    "seq",
    "id",
]

AGE_GROUP_SUFFIX_CANDIDATES = [
    "age_group_code",
    "agegroup_code",
    "column_suffix",
    "suffix",
    "code",
]


def _normalize_age_group_text(value) -> str:
    if pd.isna(value):
        return "未知"

    text = str(value).strip()
    text = text.replace("[", "").replace("]", "")
    text = text.replace(" ", "")

    aliases = {
        "0-6歲": "00-06歲",
        "00-6歲": "00-06歲",
        "00-06歲": "00-06歲",
        "7-12歲": "07-12歲",
        "07-12歲": "07-12歲",
        "13-18歲": "13-18歲",
        "19-64歲": "19-64歲",
        "65+": "65歲以上",
        "65歲以上": "65歲以上",
        "未知": "未知",
    }

    return aliases.get(text, text)


def _age_group_to_suffix(value: str) -> str:
    text = _normalize_age_group_text(value)

    mapping = {
        "00-06歲": "00_06",
        "07-12歲": "07_12",
        "13-18歲": "13_18",
        "19-64歲": "19_64",
        "65歲以上": "65_plus",
        "未知": "unknown",
    }

    if text in mapping:
        return mapping[text]

    suffix = (
        text.lower()
        .replace("歲以上", "_plus")
        .replace("歲", "")
        .replace("-", "_")
        .replace("+", "_plus")
        .replace(" ", "_")
    )

    return suffix


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None


def build_age_dimension(df_dim_agegroup: pd.DataFrame | None) -> pd.DataFrame:
    """
    將 dim_agegroup 整理成 transform 使用的年齡組維度。

    輸出欄位：
    age_group
    age_suffix
    age_order
    """
    fallback = pd.DataFrame({
        "age_group": [
            "00-06歲",
            "07-12歲",
            "13-18歲",
            "19-64歲",
            "65歲以上",
            "未知",
        ],
        "age_order": [1, 2, 3, 4, 5, 99],
    })

    if df_dim_agegroup is None or df_dim_agegroup.empty:
        dim = fallback
    else:
        dim_raw = df_dim_agegroup.copy()
        dim_raw.columns = [str(c).strip().lower() for c in dim_raw.columns]

        age_col = _first_existing_column(dim_raw, AGE_GROUP_VALUE_CANDIDATES)
        order_col = _first_existing_column(dim_raw, AGE_GROUP_ORDER_CANDIDATES)
        suffix_col = _first_existing_column(dim_raw, AGE_GROUP_SUFFIX_CANDIDATES)

        if age_col is None:
            dim = fallback
        else:
            dim = pd.DataFrame()
            dim["age_group"] = dim_raw[age_col].apply(_normalize_age_group_text)

            if order_col is not None:
                dim["age_order"] = pd.to_numeric(dim_raw[order_col], errors="coerce")
            else:
                dim["age_order"] = range(1, len(dim_raw) + 1)

            if suffix_col is not None:
                dim["age_suffix"] = (
                    dim_raw[suffix_col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .str.replace("-", "_", regex=False)
                    .str.replace(" ", "_", regex=False)
                )
            else:
                dim["age_suffix"] = dim["age_group"].apply(_age_group_to_suffix)

            dim = dim.drop_duplicates(subset=["age_group"])

    if "age_suffix" not in dim.columns:
        dim["age_suffix"] = dim["age_group"].apply(_age_group_to_suffix)

    dim["age_group"] = dim["age_group"].apply(_normalize_age_group_text)
    dim["age_suffix"] = dim["age_suffix"].astype(str)
    dim["age_order"] = pd.to_numeric(dim["age_order"], errors="coerce").fillna(999).astype(int)

    if "未知" not in set(dim["age_group"]):
        dim = pd.concat([
            dim,
            pd.DataFrame([{
                "age_group": "未知",
                "age_suffix": "unknown",
                "age_order": 999,
            }])
        ], ignore_index=True)

    return (
        dim[["age_group", "age_suffix", "age_order"]]
        .drop_duplicates(subset=["age_group"])
        .sort_values(["age_order", "age_group"])
        .reset_index(drop=True)
    )


def build_disease_age_pivot_model(
    df_raw: pd.DataFrame,
    df_dim_agegroup: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    將 NHI / RODS wide raw disease data 整理成週別縣市模型資料。

    輸出粒度：
    source + yearweek + branch + county

    疾病與年齡層會轉成欄位。
    """
    if df_raw.empty:
        return pd.DataFrame()

    age_dim = build_age_dimension(df_dim_agegroup)

    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    required_cols = ["date", "source", "branch", "county", "age_group"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"disease raw column not found: {col}")

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["source"] = df["source"].fillna("未知")
    df["branch"] = df["branch"].fillna("未知")
    df["county"] = df["county"].fillna("未知")
    df["age_group"] = df["age_group"].apply(_normalize_age_group_text)

    for disease_col in DISEASE_VALUE_COLUMNS:
        lower_col = disease_col.lower()
        if lower_col not in df.columns:
            df[lower_col] = 0
        df[lower_col] = pd.to_numeric(df[lower_col], errors="coerce").fillna(0).astype(int)

    if "total" not in df.columns:
        df["total"] = 0
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
        "age_group",
    ]

    weekly_age = (
        df.groupby(group_cols, dropna=False, as_index=False)
        .agg({
            **{c.lower(): "sum" for c in DISEASE_VALUE_COLUMNS},
            "total": "sum",
        })
    )

    weekly_age = weekly_age.merge(
        age_dim,
        on="age_group",
        how="left",
    )

    weekly_age["age_suffix"] = weekly_age["age_suffix"].fillna(
        weekly_age["age_group"].apply(_age_group_to_suffix)
    )

    index_cols = [
        "source",
        "yearweek",
        "year",
        "week",
        "week_start_date",
        "week_end_date",
        "branch",
        "county",
    ]

    value_cols = [c.lower() for c in DISEASE_VALUE_COLUMNS] + ["total"]

    pivot = (
        weekly_age
        .pivot_table(
            index=index_cols,
            columns="age_suffix",
            values=value_cols,
            aggfunc="sum",
            fill_value=0,
        )
    )

    pivot.columns = [
        f"{disease}_age_{age_suffix}"
        for disease, age_suffix in pivot.columns
    ]

    pivot = pivot.reset_index()

    expected_age_suffixes = age_dim["age_suffix"].tolist()

    expected_cols = []
    for disease_col in [c.lower() for c in DISEASE_VALUE_COLUMNS]:
        for age_suffix in expected_age_suffixes:
            expected_cols.append(f"{disease_col}_age_{age_suffix}")

    for age_suffix in expected_age_suffixes:
        expected_cols.append(f"total_age_{age_suffix}")

    for col in expected_cols:
        if col not in pivot.columns:
            pivot[col] = 0

    for col in expected_cols:
        pivot[col] = pd.to_numeric(pivot[col], errors="coerce").fillna(0).astype(int)

    for disease_col in [c.lower() for c in DISEASE_VALUE_COLUMNS]:
        disease_age_cols = [
            f"{disease_col}_age_{age_suffix}"
            for age_suffix in expected_age_suffixes
            if f"{disease_col}_age_{age_suffix}" in pivot.columns
        ]
        pivot[f"{disease_col}_total"] = pivot[disease_age_cols].sum(axis=1).astype(int)

    total_age_cols = [
        f"total_age_{age_suffix}"
        for age_suffix in expected_age_suffixes
        if f"total_age_{age_suffix}" in pivot.columns
    ]
    pivot["total_visit"] = pivot[total_age_cols].sum(axis=1).astype(int)

    metric_cols = []
    for disease_col in [c.lower() for c in DISEASE_VALUE_COLUMNS]:
        metric_cols.append(f"{disease_col}_total")
    metric_cols.append("total_visit")

    ordered_cols = (
        index_cols
        + metric_cols
        + expected_cols
    )

    return (
        pivot[ordered_cols]
        .sort_values(["yearweek", "branch", "county"])
        .reset_index(drop=True)
    )


def merge_disease_model_with_weather(
    df_disease_model: pd.DataFrame,
    df_weather_weekly: pd.DataFrame | None,
) -> pd.DataFrame:
    """將疾病週別縣市模型資料合併週別縣市天氣資料。"""
    if df_disease_model.empty:
        return pd.DataFrame()

    out = df_disease_model.copy()

    if df_weather_weekly is not None and not df_weather_weekly.empty:
        weather = df_weather_weekly.copy()

        drop_cols = [
            c for c in ["year", "week", "week_start_date", "week_end_date"]
            if c in weather.columns
        ]

        weather = weather.drop(columns=drop_cols, errors="ignore")

        out = out.merge(
            weather,
            on=["yearweek", "county"],
            how="left",
        )

    out["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return out.sort_values(["yearweek", "branch", "county"]).reset_index(drop=True)