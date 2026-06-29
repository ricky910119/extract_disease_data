from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility

from config.sources import SOURCES


class NHIExtractor:
    """從 Oracle NHI 來源資料表抽取 ER / OPD 目標疾病資料。"""

    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @utility.timer()
    @conn.deco.oracle()
    def extract_er(self, cur=None) -> pd.DataFrame:
        """抽取 NHI ER 目標疾病資料。"""
        return self._extract_by_source("nhi_er", cur=cur)

    @utility.timer()
    @conn.deco.oracle()
    def extract_opd(self, cur=None) -> pd.DataFrame:
        """抽取 NHI OPD 目標疾病資料。"""
        return self._extract_by_source("nhi_opd", cur=cur)

    def _extract_by_source(self, source_key: str, cur=None) -> pd.DataFrame:
        source = SOURCES[source_key]

        source_table = source["source_table"]
        source_name = source["source_name"]

        date_col = source["date_column"]
        age_col = source["age_column"]
        branch_col = source["branch_column"]
        county_col = source["county_column"]
        total_col = source["total_column"]
        recode_oipd = source["recode_oipd"]

        disease_columns = source["disease_columns"]
        ev_col = disease_columns["EV"]
        ili_col = disease_columns["ILI"]
        di_col = disease_columns["DI"]

        disease_condition = self._build_oracle_disease_condition(
            disease_columns=disease_columns
        )

        sql = f"""
            SELECT
                TRUNC({date_col}) AS admit_date,

                '[' || {age_col} || ']' AS age_group,

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

                SUM(NVL({ev_col}, 0)) AS EV,
                SUM(NVL({ili_col}, 0)) AS ILI,
                SUM(NVL({di_col}, 0)) AS DI,
                SUM(NVL({total_col}, 0)) AS total

            FROM {source_table}

            WHERE {date_col} >= TO_DATE('{self.start_date}', 'YYYY-MM-DD')
              AND {date_col} <= TO_DATE('{self.end_date}', 'YYYY-MM-DD')
              AND recode_oipd = '{recode_oipd}'
              AND ({disease_condition})

            GROUP BY
                TRUNC({date_col}),
                {age_col},
                {branch_col},
                {county_col}

            ORDER BY
                TRUNC({date_col}),
                {age_col},
                {branch_col},
                {county_col}
        """

        cur.execute(sql)

        df = pd.DataFrame.from_records(
            cur.fetchall(),
            columns=[c[0].lower() for c in cur.description],
        )

        if df.empty:
            return df

        df = df.rename(columns={"admit_date": "date"})
        df["source"] = source_name
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df

    @staticmethod
    def _build_oracle_disease_condition(
        disease_columns: dict[str, str]
    ) -> str:
        conditions = [
            f"NVL({col}, 0) > 0"
            for col in disease_columns.values()
        ]
        return "\n                 OR ".join(conditions)