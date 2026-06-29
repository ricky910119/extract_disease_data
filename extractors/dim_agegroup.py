from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility

from config.sources import POSTGRES_DBNAME_BY_SOURCE_DB, SOURCES


DIM_AGEGROUP_SOURCE = SOURCES["dim_agegroup"]
DIM_AGEGROUP_DBNAME = POSTGRES_DBNAME_BY_SOURCE_DB[DIM_AGEGROUP_SOURCE["source_db"]]


@utility.timer()
@conn.deco.postgres(dbname=DIM_AGEGROUP_DBNAME)
def load_dim_agegroup(cur=None) -> pd.DataFrame:
    """讀取年齡組維度表。"""
    source_table = DIM_AGEGROUP_SOURCE["source_table"]

    sql = f"""
        SELECT *
        FROM {source_table}
    """

    cur.execute(sql)

    df = pd.DataFrame.from_records(
        cur.fetchall(),
        columns=[c[0].lower() for c in cur.description],
    )

    return df