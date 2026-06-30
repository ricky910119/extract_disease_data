from __future__ import annotations

import os
from pathlib import Path

PROJECT_NAME = "extract_disease_data"

POSTGRES_SCHEMA = os.getenv("DISEASE_PG_SCHEMA", "disease_forecast_data")
POSTGRES_DBNAME = os.getenv("DISEASE_PG_DBNAME", "postgres")
RODS_DBNAME = os.getenv("DISEASE_RODS_DBNAME", "RODS_DATA")

LOCAL_DATA_DIR = Path(
    os.getenv(
        "DISEASE_DATA_DIR",
        "/media/sf_Eic02/Disease_modle_data"
    )
)

STATE_PATH = Path(os.getenv("DISEASE_STATE_PATH", "state/state.json"))
LOG_DIR = Path(os.getenv("DISEASE_LOG_DIR", "logs"))

CSV_ENCODING = os.getenv("DISEASE_CSV_ENCODING", "cp950")
CSV_DATE_FORMAT = "%Y-%m-%d"

INITIAL_START_DATE = os.getenv("DISEASE_INITIAL_START_DATE", "2005-01-01")
INCREMENTAL_LOOKBACK_DAYS = int(os.getenv("DISEASE_LOOKBACK_DAYS", "60"))
END_DATE_LAG_DAYS = int(os.getenv("DISEASE_END_DATE_LAG_DAYS", "1"))

ALLOW_CREATE_TABLE = True
BATCH_SIZE = int(os.getenv("DISEASE_BATCH_SIZE", "5000"))

DISEASE_VALUE_COLUMNS = ["EV", "ILI", "DI"]
DISEASE_ALLOWED_VALUES = ["EV", "ILI", "DI"]

AGE_GROUP_COLUMN_MAP = {
    "00-06歲": "count_age_00_06",
    "07-12歲": "count_age_07_12",
    "13-18歲": "count_age_13_18",
    "19-64歲": "count_age_19_64",
    "65歲以上": "count_age_65_plus",
    "未知": "count_age_unknown",
}

MODEL_AGE_COLUMNS = [
    "count_age_00_06",
    "count_age_07_12",
    "count_age_13_18",
    "count_age_19_64",
    "count_age_65_plus",
    "count_age_unknown",
]
WEATHER_DBNAME = "CWB_DATA"
