from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from eic_utils import conn, utility

from config.settings import ALLOW_CREATE_TABLE, BATCH_SIZE, POSTGRES_DBNAME


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    return out.replace({np.nan: None, pd.NaT: None})


def _pg_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "TEXT"
    if pd.api.types.is_bool_dtype(series):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE PRECISION"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMP"
    if series.name in {"date", "week_start_date", "week_end_date"}:
        return "DATE"
    return "TEXT"


def _split_table_name(table_name: str) -> tuple[str, str]:
    parts = table_name.split(".")
    if len(parts) != 2:
        raise ValueError(f"table_name must include schema: {table_name}")
    return parts[0], parts[1]


def _build_create_table_sql(df: pd.DataFrame, table_name: str, primary_key: list[str]) -> str:
    schema, table = _split_table_name(table_name)
    columns_sql = []
    for col in df.columns:
        columns_sql.append(f'"{col}" {_pg_type(df[col])}')

    pk_cols = [c for c in primary_key if c in df.columns]
    if pk_cols:
        quoted_pk_cols = ", ".join([f'"{c}"' for c in pk_cols])
        pk_sql = f", PRIMARY KEY ({quoted_pk_cols})"
    else:
        pk_sql = ""

    columns_block = ", ".join(columns_sql)
    return f'''
        CREATE SCHEMA IF NOT EXISTS "{schema}";
        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            {columns_block}
            {pk_sql}
        );
    '''


@utility.timer()
@conn.deco.postgres(dbname=POSTGRES_DBNAME)
def ensure_table_exists(df: pd.DataFrame, table_name: str, primary_key: list[str], cur=None) -> None:
    if df.empty:
        return
    sql = _build_create_table_sql(df, table_name, primary_key)
    cur.execute(sql)


@utility.timer()
@conn.deco.postgres(dbname=POSTGRES_DBNAME)
def replace_yearweek_range(
    df: pd.DataFrame,
    table_name: str,
    start_yearweek: int,
    end_yearweek: int,
    primary_key: list[str],
    cur=None,
) -> int:
    if df.empty:
        return 0

    df = _clean_df(df)
    if ALLOW_CREATE_TABLE:
        create_sql = _build_create_table_sql(df, table_name, primary_key)
        cur.execute(create_sql)

    cur.execute(
        f"DELETE FROM {table_name} WHERE yearweek >= ? AND yearweek <= ?",
        (int(start_yearweek), int(end_yearweek)),
    )

    insert_columns = '", "'.join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    insert_sql = f'INSERT INTO {table_name} ("{insert_columns}") VALUES ({placeholders})'

    rows = list(df.itertuples(index=False, name=None))
    for i in range(0, len(rows), BATCH_SIZE):
        cur.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    return len(df)


@utility.timer()
@conn.deco.postgres(dbname=POSTGRES_DBNAME)
def upsert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    primary_key: list[str],
    cur=None,
) -> int:
    if df.empty:
        return 0

    df = _clean_df(df)
    if ALLOW_CREATE_TABLE:
        create_sql = _build_create_table_sql(df, table_name, primary_key)
        cur.execute(create_sql)

    insert_columns = '", "'.join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    conflict_columns = '", "'.join(primary_key)
    update_columns = ", ".join([
        f'"{c}" = excluded."{c}"'
        for c in df.columns
        if c not in primary_key
    ])

    sql = f'''
        INSERT INTO {table_name} ("{insert_columns}")
        VALUES ({placeholders})
        ON CONFLICT ("{conflict_columns}")
        DO UPDATE SET {update_columns}
    '''

    rows = list(df.itertuples(index=False, name=None))
    for i in range(0, len(rows), BATCH_SIZE):
        cur.executemany(sql, rows[i:i + BATCH_SIZE])
    return len(df)
