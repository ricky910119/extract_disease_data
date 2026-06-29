from __future__ import annotations

SOURCES = {
    "nhi_er": {
        "source_name": "NHI_ER",
        "source_db": "oracle",
        "target": "nhi_er",
    },
    "nhi_opd": {
        "source_name": "NHI_OPD",
        "source_db": "oracle",
        "target": "nhi_opd",
    },
    "rods": {
        "source_name": "RODS",
        "source_db": "postgres_rods_data",
        "target": "rods",
    },
    "weather": {
        "source_name": "WEATHER",
        "source_db": "postgres",
        "source_table": "public.weather_daily_city",
        "date_column": "weather_date",
        "county_column": "city_std",
        "target": "weather",
    },
}

DISEASE_SOURCES = ["nhi_er", "nhi_opd", "rods"]
ALL_SOURCES = ["nhi_er", "nhi_opd", "rods", "weather"]
