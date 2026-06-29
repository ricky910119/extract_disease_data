from __future__ import annotations

import pandas as pd

from config.settings import DISEASE_VALUE_COLUMNS


def normalize_age_group(value) -> str:
    """統一年齡組文字格式。"""
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


def normalize_disease_raw(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    將疾病來源資料整理成 wide raw cache 格式。

    輸出粒度：
    date + source + branch + county + age_group
    """
    output_cols = [
        "date",
        "source",
        "branch",
        "county",
        "age_group",
        *DISEASE_VALUE_COLUMNS,
        "total",
    ]

    if df.empty:
        return pd.DataFrame(columns=output_cols)

    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]

    required_cols = ["date", "branch", "county", "age_group"]
    for col in required_cols:
        if col not in out.columns:
            raise KeyError(f"raw disease column not found: {col}")

    out["date"] = pd.to_datetime(out["date"]).dt.date
    out["source"] = source
    out["branch"] = out["branch"].fillna("未知")
    out["county"] = out["county"].fillna("未知")
    out["age_group"] = out["age_group"].apply(normalize_age_group)

    for disease_col in DISEASE_VALUE_COLUMNS:
        lower_col = disease_col.lower()

        if lower_col in out.columns and disease_col not in out.columns:
            out[disease_col] = out[lower_col]

        if disease_col not in out.columns:
            out[disease_col] = 0

        out[disease_col] = (
            pd.to_numeric(out[disease_col], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    if "total" not in out.columns:
        out["total"] = 0

    out["total"] = (
        pd.to_numeric(out["total"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    out = (
        out[output_cols]
        .groupby(["date", "source", "branch", "county", "age_group"], dropna=False, as_index=False)
        .agg({
            **{c: "sum" for c in DISEASE_VALUE_COLUMNS},
            "total": "sum",
        })
        .sort_values(["date", "source", "branch", "county", "age_group"])
        .reset_index(drop=True)
    )

    return out