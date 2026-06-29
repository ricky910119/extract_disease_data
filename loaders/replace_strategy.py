from __future__ import annotations

import pandas as pd

from config.tables import POSTGRES_TABLES
from loaders.postgres_loader import replace_yearweek_range


def upload_yearweek_range(table_key: str, df: pd.DataFrame, start_yearweek: int, end_yearweek: int) -> int:
    table_cfg = POSTGRES_TABLES[table_key]
    return replace_yearweek_range(
        df=df,
        table_name=table_cfg["table_name"],
        start_yearweek=start_yearweek,
        end_yearweek=end_yearweek,
        primary_key=table_cfg["primary_key"],
    )
