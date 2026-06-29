from __future__ import annotations

from config.settings import POSTGRES_SCHEMA

POSTGRES_TABLES = {
    "weather": {
        "table_name": f"{POSTGRES_SCHEMA}.weather_weekly_city",
        "time_column": "yearweek",
        "primary_key": ["yearweek", "county"],
        "replace_strategy": "yearweek_range",
    },
    "nhi_er": {
        "table_name": f"{POSTGRES_SCHEMA}.model_nhi_er_weekly_county",
        "time_column": "yearweek",
        "primary_key": ["source", "yearweek", "branch", "county"],
        "replace_strategy": "yearweek_range",
    },
    "nhi_opd": {
        "table_name": f"{POSTGRES_SCHEMA}.model_nhi_opd_weekly_county",
        "time_column": "yearweek",
        "primary_key": ["source", "yearweek", "branch", "county"],
        "replace_strategy": "yearweek_range",
    },
    "rods": {
        "table_name": f"{POSTGRES_SCHEMA}.model_rods_weekly_county",
        "time_column": "yearweek",
        "primary_key": ["source", "yearweek", "branch", "county"],
        "replace_strategy": "yearweek_range",
    },
}
