from __future__ import annotations

from typing import Any

from eic_utils import conn, utility

from config.settings import POSTGRES_DBNAME
from config.tables import POSTGRES_TABLES


def _split_table_name(table_name: str) -> tuple[str, str]:
    parts = table_name.split(".")
    if len(parts) != 2:
        raise ValueError(f"table_name must include schema: {table_name}")
    return parts[0], parts[1]


@utility.timer()
@conn.deco.postgres(dbname=POSTGRES_DBNAME)
def profile_pg_table(table_key: str, cur=None) -> dict[str, Any]:
    table_cfg = POSTGRES_TABLES[table_key]
    table_name = table_cfg["table_name"]
    schema, table = _split_table_name(table_name)
    pk = table_cfg["primary_key"]

    result: dict[str, Any] = {
        "table_name": table_name,
        "table_exists": False,
        "row_count": 0,
        "min_yearweek": None,
        "max_yearweek": None,
        "duplicated_key_count": None,
        "null_key_count": None,
    }

    cur.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = ?
          AND table_name = ?
        """,
        (schema, table),
    )
    exists = cur.fetchone()[0] > 0
    result["table_exists"] = bool(exists)
    if not exists:
        return result

    cur.execute(f"SELECT COUNT(*), MIN(yearweek), MAX(yearweek) FROM {table_name}")
    row_count, min_yw, max_yw = cur.fetchone()
    result["row_count"] = int(row_count or 0)
    result["min_yearweek"] = int(min_yw) if min_yw is not None else None
    result["max_yearweek"] = int(max_yw) if max_yw is not None else None

    pk_cols = [f'"{c}"' for c in pk]
    if pk_cols:
        pk_expr = ", ".join(pk_cols)
        cur.execute(f"""
            SELECT COALESCE(SUM(cnt - 1), 0)
            FROM (
                SELECT {pk_expr}, COUNT(*) AS cnt
                FROM {table_name}
                GROUP BY {pk_expr}
                HAVING COUNT(*) > 1
            ) t
        """)
        result["duplicated_key_count"] = int(cur.fetchone()[0] or 0)

        null_condition = " OR ".join([f'"{c}" IS NULL' for c in pk])
        cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {null_condition}")
        result["null_key_count"] = int(cur.fetchone()[0] or 0)

    return result


def profile_all_pg_tables() -> dict[str, dict[str, Any]]:
    return {key: profile_pg_table(key) for key in POSTGRES_TABLES}
