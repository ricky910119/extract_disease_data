from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import PROJECT_NAME, STATE_PATH


def default_state() -> dict[str, Any]:
    return {
        "project": PROJECT_NAME,
        "last_run_id": None,
        "local_store": {},
        "postgres_tables": {},
    }


def load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    if not path.exists():
        return default_state()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def update_local_source_state(
    state: dict[str, Any],
    source: str,
    start_date: str,
    end_date: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    state.setdefault("local_store", {})[source] = {
        "last_success_start_date": start_date,
        "last_success_end_date": end_date,
        **profile,
    }
    return state


def update_pg_table_state(
    state: dict[str, Any],
    table_key: str,
    start_yearweek: int,
    end_yearweek: int,
    profile: dict[str, Any],
) -> dict[str, Any]:
    state.setdefault("postgres_tables", {})[table_key] = {
        "last_success_start_yearweek": start_yearweek,
        "last_success_end_yearweek": end_yearweek,
        **profile,
    }
    return state
