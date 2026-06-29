from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility


class RODSExtractor:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @utility.timer()
    @conn.deco.postgres(dbname="RODS_DATA")
    def extract(self, cur=None) -> pd.DataFrame:
        sql = f"""
            SELECT
                admit_date::date AS date,
                CASE
                    WHEN (age >= 0) AND (age <= 6) THEN '00-06歲'
                    WHEN (age >= 7) AND (age <= 12) THEN '07-12歲'
                    WHEN (age >= 13) AND (age <= 18) THEN '13-18歲'
                    WHEN (age >= 19) AND (age <= 64) THEN '19-64歲'
                    WHEN (age >= 65) THEN '65歲以上'
                    ELSE '未知'
                END AS age_group,
                CASE branch
                    WHEN 'Kaoping' THEN '高屏區'
                    WHEN 'East' THEN '東區'
                    WHEN 'Central' THEN '中區'
                    WHEN 'North' THEN '北區'
                    WHEN 'South' THEN '南區'
                    WHEN 'Taipei' THEN '台北區'
                    ELSE branch
                END AS branch,
                county,
                SUM(e_i) AS EV,
                SUM(rods_rs) AS ILI,
                SUM(acutediarrhea) AS DI,
                SUM(total) AS total
            FROM rods_visit
            WHERE admit_date >= '{self.start_date}'::date
              AND admit_date <= '{self.end_date}'::date
              AND (
                    COALESCE(e_i, 0) > 0
                 OR COALESCE(rods_rs, 0) > 0
                 OR COALESCE(acutediarrhea, 0) > 0
              )
            GROUP BY
                admit_date,
                age_group,
                branch,
                county
            ORDER BY
                admit_date,
                age_group,
                branch,
                county
        """
        cur.execute(sql)
        df = pd.DataFrame.from_records(cur.fetchall(), columns=[c[0].lower() for c in cur.description])
        df["source"] = "RODS"
        return df
