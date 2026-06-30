from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility

from transforms.model_source_total_weekly_county import (
    build_model_source_total_weekly_county,
)


TARGET_SCHEMA = "disease_forecast_data"
TARGET_TABLE = "model_source_total_weekly_county"


def validate_date_string(value: str, name: str) -> str:
    try:
        pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD, got {value}") from exc

    return value


@utility.timer()
@conn.deco.postgres(dbname="DIM_DATA")
def query_dim_weekdate(
    start_date: str,
    end_date: str,
    cur=None,
) -> pd.DataFrame:
    """
    查 DIM_DATA.public.dim_weekdate，提供每日日期與 yearweek 對照。
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    sql = f"""
        SELECT
            CAST("date" AS date) AS admit_date,
            yearweek AS yearweek
        FROM public.dim_weekdate
        WHERE CAST("date" AS date)
              BETWEEN '{start_date}'::date AND '{end_date}'::date
        ORDER BY CAST("date" AS date)
    """

    cur.execute(sql)

    df = pd.DataFrame.from_records(
        cur.fetchall(),
        columns=[c[0] for c in cur.description],
    )

    df.columns = [c.upper() for c in df.columns]

    df["ADMIT_DATE"] = pd.to_datetime(df["ADMIT_DATE"]).dt.date
    df["YEARWEEK"] = df["YEARWEEK"].astype(str)

    print(
        f"[TOTAL][EXTRACT] dim_weekdate rows={len(df)}, "
        f"min_date={df['ADMIT_DATE'].min()}, "
        f"max_date={df['ADMIT_DATE'].max()}"
    )

    return df


@utility.timer()
@conn.deco.oracle()
def query_nhi_total_by_recode(
    start_date: str,
    end_date: str,
    recode_oipd: str,
    total_column_name: str,
    cur=None,
) -> pd.DataFrame:
    """
    查 Oracle CDCDW.V_FACT_NHI_DT 的 NHI OPD / ER 每日縣市總人次。
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    recode_oipd = recode_oipd.upper().strip()
    total_column_name = total_column_name.upper().strip()

    sql = f"""
        SELECT
            TRUNC(ADMIT_DATE) AS ADMIT_DATE,
            COUNTY,
            SUM(TOTAL) AS {total_column_name}
        FROM CDCDW.V_FACT_NHI_DT
        WHERE TRUNC(ADMIT_DATE)
              BETWEEN DATE '{start_date}' AND DATE '{end_date}'
          AND RECODE_OIPD = '{recode_oipd}'
        GROUP BY
            TRUNC(ADMIT_DATE),
            COUNTY
        ORDER BY
            TRUNC(ADMIT_DATE),
            COUNTY
    """

    cur.execute(sql)

    df = pd.DataFrame.from_records(
        cur.fetchall(),
        columns=[c[0] for c in cur.description],
    )

    df.columns = [c.upper() for c in df.columns]

    if df.empty:
        print(f"[TOTAL][EXTRACT][WARN] NHI {recode_oipd} is empty")
        return df

    df["ADMIT_DATE"] = pd.to_datetime(df["ADMIT_DATE"]).dt.date
    df[total_column_name] = df[total_column_name].fillna(0).astype(int)

    print(
        f"[TOTAL][EXTRACT] NHI {recode_oipd} rows={len(df)}, "
        f"min_date={df['ADMIT_DATE'].min()}, "
        f"max_date={df['ADMIT_DATE'].max()}"
    )

    return df


def query_nhi_opd_total(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    return query_nhi_total_by_recode(
        start_date=start_date,
        end_date=end_date,
        recode_oipd="OPD",
        total_column_name="NHI_OPD_TOTAL",
    )


def query_nhi_er_total(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    return query_nhi_total_by_recode(
        start_date=start_date,
        end_date=end_date,
        recode_oipd="ER",
        total_column_name="NHI_ER_TOTAL",
    )


@utility.timer()
@conn.deco.postgres(dbname="RODS_DATA")
def query_rods_total(
    start_date: str,
    end_date: str,
    cur=None,
) -> pd.DataFrame:
    """
    查 PostgreSQL RODS_DATA.public.mv_rods_visit 的每日縣市總急診人次。
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    sql = f"""
        SELECT
            CAST(admit_date AS date) AS admit_date,
            county AS county,
            SUM(total) AS rods_er_total
        FROM public.mv_rods_visit
        WHERE CAST(admit_date AS date)
              BETWEEN '{start_date}'::date AND '{end_date}'::date
        GROUP BY
            CAST(admit_date AS date),
            county
        ORDER BY
            CAST(admit_date AS date),
            county
    """

    cur.execute(sql)

    df = pd.DataFrame.from_records(
        cur.fetchall(),
        columns=[c[0] for c in cur.description],
    )

    df.columns = [c.upper() for c in df.columns]

    if df.empty:
        print("[TOTAL][EXTRACT][WARN] RODS ER is empty")
        return df

    df["ADMIT_DATE"] = pd.to_datetime(df["ADMIT_DATE"]).dt.date
    df["RODS_ER_TOTAL"] = df["RODS_ER_TOTAL"].fillna(0).astype(int)

    print(
        f"[TOTAL][EXTRACT] RODS ER rows={len(df)}, "
        f"min_date={df['ADMIT_DATE'].min()}, "
        f"max_date={df['ADMIT_DATE'].max()}"
    )

    return df


@conn.deco.postgres(dbname="postgres")
def ensure_target_table(cur=None) -> None:
    """
    建立 disease_forecast_data.model_source_total_weekly_county。
    """
    sql = f"""
        CREATE SCHEMA IF NOT EXISTS {TARGET_SCHEMA};

        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{TARGET_TABLE} (
            data_source TEXT NOT NULL,
            yearweek TEXT NOT NULL,
            year INTEGER NOT NULL,
            week INTEGER NOT NULL,
            county TEXT NOT NULL,
            total_count BIGINT NOT NULL DEFAULT 0,
            extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (data_source, yearweek, county)
        );
    """

    cur.execute(sql)


@utility.timer()
@conn.deco.postgres(dbname="postgres")
def upload_model_source_total_weekly_county(
    df: pd.DataFrame,
    cur=None,
) -> int:
    """
    upsert 每週縣市資料源總就醫人次。
    """
    if df.empty:
        print("[TOTAL][LOAD] no rows to upload")
        return 0

    required_cols = [
        "data_source",
        "yearweek",
        "year",
        "week",
        "county",
        "total_count",
        "extracted_at",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        raise ValueError(f"missing columns: {missing_cols}")

    rows = [
        (
            str(row.data_source),
            str(row.yearweek),
            int(row.year),
            int(row.week),
            str(row.county),
            int(row.total_count),
            row.extracted_at,
        )
        for row in df[required_cols].itertuples(index=False)
    ]

    sql = f"""
        INSERT INTO {TARGET_SCHEMA}.{TARGET_TABLE} (
            data_source,
            yearweek,
            year,
            week,
            county,
            total_count,
            extracted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (data_source, yearweek, county)
        DO UPDATE SET
            year = EXCLUDED.year,
            week = EXCLUDED.week,
            total_count = EXCLUDED.total_count,
            extracted_at = EXCLUDED.extracted_at
    """

    cur.executemany(sql, rows)

    print(f"[TOTAL][LOAD] uploaded rows={len(rows)} -> {TARGET_SCHEMA}.{TARGET_TABLE}")

    return len(rows)


def run_model_source_total_weekly_county(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    完整流程：
        1. extract dim_weekdate
        2. extract NHI OPD total
        3. extract NHI ER total
        4. extract RODS ER total
        5. transform daily total to weekly county total
        6. upload to PostgreSQL
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    ensure_target_table()

    df_weekdate = query_dim_weekdate(
        start_date=start_date,
        end_date=end_date,
    )

    df_nhi_opd_daily = query_nhi_opd_total(
        start_date=start_date,
        end_date=end_date,
    )

    df_nhi_er_daily = query_nhi_er_total(
        start_date=start_date,
        end_date=end_date,
    )

    df_rods_daily = query_rods_total(
        start_date=start_date,
        end_date=end_date,
    )

    df_total = build_model_source_total_weekly_county(
        df_weekdate=df_weekdate,
        df_nhi_opd_daily=df_nhi_opd_daily,
        df_nhi_er_daily=df_nhi_er_daily,
        df_rods_daily=df_rods_daily,
    )

    upload_model_source_total_weekly_county(df_total)

    return df_total