from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility


class NHIExtractor:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @utility.timer()
    @conn.deco.oracle()
    def extract_er(self, cur=None) -> pd.DataFrame:
        sql = f"""
            SELECT
                admit_date AS date,
                '[' || age_group || ']' AS age_group,
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
                SUM(EV) AS EV,
                SUM(ICD_48X) AS ILI,
                SUM(DIARRHOEA) AS DI,
                SUM(total) AS total
            FROM CDCDW.V_FACT_NHI_DT
            WHERE admit_date >= TO_DATE('{self.start_date}', 'YYYY-MM-DD')
              AND admit_date <= TO_DATE('{self.end_date}', 'YYYY-MM-DD')
              AND recode_oipd = 'ER'
              AND (
                    NVL(EV, 0) > 0
                 OR NVL(ICD_48X, 0) > 0
                 OR NVL(DIARRHOEA, 0) > 0
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
        df["source"] = "NHI_ER"
        return df

    @utility.timer()
    @conn.deco.oracle()
    def extract_opd(self, cur=None) -> pd.DataFrame:
        sql = f"""
            SELECT
                admit_date AS date,
                '[' || age_group || ']' AS age_group,
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
                SUM(EV) AS EV,
                SUM(ICD_48X) AS ILI,
                SUM(DIARRHOEA) AS DI,
                SUM(total) AS total
            FROM CDCDW.V_FACT_NHI_DT
            WHERE admit_date >= TO_DATE('{self.start_date}', 'YYYY-MM-DD')
              AND admit_date <= TO_DATE('{self.end_date}', 'YYYY-MM-DD')
              AND recode_oipd = 'OPD'
              AND (
                    NVL(EV, 0) > 0
                 OR NVL(ICD_48X, 0) > 0
                 OR NVL(DIARRHOEA, 0) > 0
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
        df["source"] = "NHI_OPD"
        return df
