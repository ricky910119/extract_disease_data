from __future__ import annotations

from datetime import datetime

import pandas as pd


COUNTY_REPLACE_MAP = {
    "台北縣": "新北市",
    "桃園縣": "桃園市",
    "台中縣": "台中市",
    "台南縣": "台南市",
    "高雄縣": "高雄市",
}


OUTPUT_COLUMNS = [
    "data_source",
    "yearweek",
    "year",
    "week",
    "county",
    "total_count",
    "extracted_at",
]


def normalize_county(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "COUNTY" not in df.columns:
        return df

    df["COUNTY"] = (
        df["COUNTY"]
        .astype(str)
        .str.strip()
        .replace(COUNTY_REPLACE_MAP)
    )

    df = df[
        df["COUNTY"].notna()
        & (df["COUNTY"] != "")
        & (df["COUNTY"] != "None")
        & (df["COUNTY"] != "nan")
    ].copy()

    return df


def attach_yearweek(
    df: pd.DataFrame,
    df_weekdate: pd.DataFrame,
    source_name: str,
) -> pd.DataFrame:
    if df.empty:
        print(f"[TOTAL][WARN] {source_name} daily data is empty")
        return df.copy()

    required_daily_cols = {"ADMIT_DATE", "COUNTY"}
    missing_daily_cols = required_daily_cols - set(df.columns)

    if missing_daily_cols:
        raise ValueError(
            f"{source_name} missing daily columns: {sorted(missing_daily_cols)}"
        )

    required_week_cols = {"ADMIT_DATE", "YEARWEEK"}
    missing_week_cols = required_week_cols - set(df_weekdate.columns)

    if missing_week_cols:
        raise ValueError(
            f"df_weekdate missing columns: {sorted(missing_week_cols)}"
        )

    df = df.copy()
    df_weekdate = df_weekdate.copy()

    df["ADMIT_DATE"] = pd.to_datetime(df["ADMIT_DATE"]).dt.date
    df_weekdate["ADMIT_DATE"] = pd.to_datetime(df_weekdate["ADMIT_DATE"]).dt.date
    df_weekdate["YEARWEEK"] = df_weekdate["YEARWEEK"].astype(str)

    df = pd.merge(
        df,
        df_weekdate[["ADMIT_DATE", "YEARWEEK"]],
        how="left",
        on="ADMIT_DATE",
    )

    missing = int(df["YEARWEEK"].isna().sum())

    if missing > 0:
        print(
            f"[TOTAL][WARN] {source_name} has {missing} rows "
            f"without YEARWEEK mapping"
        )
        print(df[df["YEARWEEK"].isna()].head())

    df = df[df["YEARWEEK"].notna()].copy()
    df["YEARWEEK"] = df["YEARWEEK"].astype(str)

    return df


def daily_to_weekly_source(
    df_daily: pd.DataFrame,
    total_col: str,
    data_source: str,
    force_national: bool = False,
) -> pd.DataFrame:
    total_col = total_col.upper()

    if df_daily.empty:
        return pd.DataFrame(
            columns=[
                "data_source",
                "yearweek",
                "year",
                "week",
                "county",
                "total_count",
            ]
        )

    required_cols = {"YEARWEEK", "COUNTY", total_col}
    missing_cols = required_cols - set(df_daily.columns)

    if missing_cols:
        raise ValueError(
            f"{data_source} missing source columns: {sorted(missing_cols)}"
        )

    df_daily = df_daily.copy()
    df_daily[total_col] = df_daily[total_col].fillna(0).astype(int)

    if force_national:
        group_keys = ["YEARWEEK"]
    else:
        group_keys = ["YEARWEEK", "COUNTY"]

    df_weekly = (
        df_daily
        .groupby(group_keys, as_index=False)
        .agg({total_col: "sum"})
        .rename(
            columns={
                "YEARWEEK": "yearweek",
                "COUNTY": "county",
                total_col: "total_count",
            }
        )
    )

    if force_national:
        df_weekly["county"] = "全國"

    df_weekly["data_source"] = data_source
    df_weekly["yearweek"] = df_weekly["yearweek"].astype(str)
    df_weekly["year"] = df_weekly["yearweek"].str[:4].astype(int)
    df_weekly["week"] = df_weekly["yearweek"].str[4:6].astype(int)
    df_weekly["county"] = df_weekly["county"].astype(str).str.strip()
    df_weekly["total_count"] = df_weekly["total_count"].fillna(0).astype(int)

    df_weekly = df_weekly[
        [
            "data_source",
            "yearweek",
            "year",
            "week",
            "county",
            "total_count",
        ]
    ].copy()

    return df_weekly


def build_model_source_total_weekly_county(
    df_weekdate: pd.DataFrame,
    df_nhi_opd_daily: pd.DataFrame,
    df_nhi_er_daily: pd.DataFrame,
    df_rods_daily: pd.DataFrame,
) -> pd.DataFrame:
    df_weekdate = df_weekdate.copy()
    df_weekdate.columns = [c.upper() for c in df_weekdate.columns]

    df_nhi_opd_daily = df_nhi_opd_daily.copy()
    df_nhi_er_daily = df_nhi_er_daily.copy()
    df_rods_daily = df_rods_daily.copy()

    df_nhi_opd_daily.columns = [c.upper() for c in df_nhi_opd_daily.columns]
    df_nhi_er_daily.columns = [c.upper() for c in df_nhi_er_daily.columns]
    df_rods_daily.columns = [c.upper() for c in df_rods_daily.columns]

    df_nhi_opd_daily = normalize_county(df_nhi_opd_daily)
    df_nhi_er_daily = normalize_county(df_nhi_er_daily)
    df_rods_daily = normalize_county(df_rods_daily)

    df_nhi_opd_daily = attach_yearweek(
        df=df_nhi_opd_daily,
        df_weekdate=df_weekdate,
        source_name="NHI OPD",
    )

    df_nhi_er_daily = attach_yearweek(
        df=df_nhi_er_daily,
        df_weekdate=df_weekdate,
        source_name="NHI ER",
    )

    df_rods_daily = attach_yearweek(
        df=df_rods_daily,
        df_weekdate=df_weekdate,
        source_name="RODS ER",
    )

    df_total = pd.concat(
        [
            daily_to_weekly_source(
                df_daily=df_nhi_opd_daily,
                total_col="NHI_OPD_TOTAL",
                data_source="nhi_opd",
                force_national=False,
            ),
            daily_to_weekly_source(
                df_daily=df_nhi_er_daily,
                total_col="NHI_ER_TOTAL",
                data_source="nhi_er",
                force_national=False,
            ),
            daily_to_weekly_source(
                df_daily=df_rods_daily,
                total_col="RODS_ER_TOTAL",
                data_source="rods",
                force_national=True,
            ),
        ],
        ignore_index=True,
    )

    if df_total.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df_total["extracted_at"] = datetime.now()

    df_total = (
        df_total
        .sort_values(["data_source", "yearweek", "county"])
        .reset_index(drop=True)
    )

    df_total = df_total[OUTPUT_COLUMNS].copy()

    print(
        f"[TOTAL][TRANSFORM] rows={len(df_total)}, "
        f"min_yearweek={df_total['yearweek'].min()}, "
        f"max_yearweek={df_total['yearweek'].max()}"
    )

    print(
        df_total
        .groupby("data_source", as_index=False)
        .agg(
            rows=("yearweek", "size"),
            county_count=("county", "nunique"),
            min_yearweek=("yearweek", "min"),
            max_yearweek=("yearweek", "max"),
            total_count_sum=("total_count", "sum"),
        )
    )

    return df_total