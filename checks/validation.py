from __future__ import annotations

import pandas as pd


def validate_non_negative(df: pd.DataFrame, columns: list[str]) -> list[str]:
    errors = []
    for col in columns:
        if col in df.columns and (pd.to_numeric(df[col], errors="coerce") < 0).any():
            errors.append(f"{col} contains negative values")
    return errors


def validate_required_columns(df: pd.DataFrame, required_columns: list[str]) -> list[str]:
    return [f"missing required column: {col}" for col in required_columns if col not in df.columns]


def validate_unique_key(df: pd.DataFrame, key_columns: list[str]) -> list[str]:
    existing = [c for c in key_columns if c in df.columns]
    if len(existing) != len(key_columns):
        return ["key columns are incomplete"]
    duplicated = int(df.duplicated(subset=existing).sum())
    if duplicated > 0:
        return [f"duplicated key rows: {duplicated}"]
    return []
