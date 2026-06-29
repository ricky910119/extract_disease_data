from __future__ import annotations

import pandas as pd

from config.settings import DISEASE_VALUE_COLUMNS


def normalize_age_group(value) -> str:
    if pd.isna(value):
        return "未知"
    text = str(value).strip()
    text = text.replace("[", "").replace("]", "")
    text = text.replace(" ", "")

    aliases = {
        "0-6歲": "00-06歲",
        "00-06歲": "00-06歲",
        "00-6歲": "00-06歲",
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
    if df.empty:
        return pd.DataFrame(columns=["date", "source", "branch", "county", "age_group", "disease", "count", "total"])

    out = df.copy()
    out.columns = [str(c).lower() for c in out.columns]
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out["source"] = source
    out["branch"] = out["branch"].fillna("未知")
    out["county"] = out["county"].fillna("未知")
    out["age_group"] = out["age_group"].apply(normalize_age_group)

    for c in DISEASE_VALUE_COLUMNS:
        lower = c.lower()
        if lower in out.columns and c not in out.columns:
            out[c] = out[lower]
        if c not in out.columns:
            out[c] = 0
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype(int)

    if "total" not in out.columns:
        out["total"] = 0
    out["total"] = pd.to_numeric(out["total"], errors="coerce").fillna(0).astype(int)

    long_df = pd.melt(
        out,
        id_vars=["date", "source", "branch", "county", "age_group", "total"],
        value_vars=DISEASE_VALUE_COLUMNS,
        var_name="disease",
        value_name="count",
    )

    long_df["count"] = pd.to_numeric(long_df["count"], errors="coerce").fillna(0).astype(int)
    long_df["total"] = pd.to_numeric(long_df["total"], errors="coerce").fillna(0).astype(int)

    long_df = long_df[
        ["date", "source", "branch", "county", "age_group", "disease", "count", "total"]
    ].sort_values(
        ["date", "source", "branch", "county", "age_group", "disease"]
    ).reset_index(drop=True)

    return long_df
