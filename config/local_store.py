from __future__ import annotations

from config.settings import LOCAL_DATA_DIR

RAW_FILES = {
    "nhi_er": LOCAL_DATA_DIR / "raw_nhi_er_target_disease.csv",
    "nhi_opd": LOCAL_DATA_DIR / "raw_nhi_opd_target_disease.csv",
    "rods": LOCAL_DATA_DIR / "raw_rods_target_disease.csv",
    "weather": LOCAL_DATA_DIR / "raw_weather_data.csv",
}

RAW_DATE_COLUMNS = {
    "nhi_er": "date",
    "nhi_opd": "date",
    "rods": "date",
    "weather": "date",
}

RAW_KEYS = {
    "nhi_er": ["date", "source", "branch", "county", "age_group"],
    "nhi_opd": ["date", "source", "branch", "county", "age_group"],
    "rods": ["date", "source", "branch", "county", "age_group"],
    "weather": ["date", "county"],
}