from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility

from config.sources import SOURCES, POSTGRES_DBNAME_BY_SOURCE_DB


RODS_SOURCE = SOURCES["rods"]
RODS_DBNAME = POSTGRES_DBNAME_BY_SOURCE_DB[RODS_SOURCE["source_db"]]


class RODSExtractor:
    """從 RODS Materialized View 抽取目標疾病資料。"""

    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @utility.timer()
    @conn.deco.postgres(dbname=RODS_DBNAME)
    def extract(self, cur=None) -> pd.DataFrame:
        source_table = RODS_SOURCE["source_table"]
        date_col = RODS_SOURCE["date_column"]
        age_col = RODS_SOURCE["age_column"]
        branch_col = RODS_SOURCE["branch_column"]
        county_col = RODS_SOURCE["county_column"]
        total_col = RODS_SOURCE["total_column"]

        disease_columns = RODS_SOURCE["disease_columns"]
        ev_col = disease_columns["EV"]
        ili_col = disease_columns["ILI"]
        di_col = disease_columns["DI"]

        sql = f"""
            SELECT
                {date_col}::date AS date,

                CASE
                    WHEN ({age_col} >= 0) AND ({age_col} <= 6) THEN '00-06歲'
                    WHEN ({age_col} >= 7) AND ({age_col} <= 12) THEN '07-12歲'
                    WHEN ({age_col} >= 13) AND ({age_col} <= 18) THEN '13-18歲'
                    WHEN ({age_col} >= 19) AND ({age_col} <= 64) THEN '19-64歲'
                    WHEN ({age_col} >= 65) THEN '65歲以上'
                    ELSE '未知'
                END AS age_group,

                CASE {branch_col}
                    WHEN 'Kaoping' THEN '高屏區'
                    WHEN 'East' THEN '東區'
                    WHEN 'Central' THEN '中區'
                    WHEN 'North' THEN '北區'
                    WHEN 'South' THEN '南區'
                    WHEN 'Taipei' THEN '台北區'
                    ELSE {branch_col}
                END AS branch,

                {county_col} AS county,

                SUM(COALESCE({ev_col}, 0)) AS EV,
                SUM(COALESCE({ili_col}, 0)) AS ILI,
                SUM(COALESCE({di_col}, 0)) AS DI,
                SUM(COALESCE({total_col}, 0)) AS total

            FROM {source_table}

            WHERE {date_col} >= '{self.start_date}'::date
              AND {date_col} <= '{self.end_date}'::date
              AND (
                    COALESCE({ev_col}, 0) > 0
                 OR COALESCE({ili_col}, 0) > 0
                 OR COALESCE({di_col}, 0) > 0
              )

            GROUP BY
                {date_col}::date,
                age_group,
                branch,
                {county_col}

            ORDER BY
                {date_col}::date,
                age_group,
                branch,
                {county_col}
        """

        cur.execute(sql)

        df = pd.DataFrame.from_records(
            cur.fetchall(),
            columns=[c[0].lower() for c in cur.description],
        )

        if df.empty:
            return df

        df["source"] = RODS_SOURCE["source_name"]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["county"] = df["county"].fillna("未知")
        df["branch"] = df["branch"].fillna("未知")

        return df