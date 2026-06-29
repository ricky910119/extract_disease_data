from __future__ import annotations

POSTGRES_DBNAME_BY_SOURCE_DB = {
    "postgres": "postgres",
    "postgres_rods_data": "RODS_DATA",
    "postgres_cwb_data": "CWB_DATA",
    "postgres_dim_data": "DIM_DATA",
}

SOURCES = {
    "nhi_er": {
        "source_name": "NHI_ER",
        "source_db": "oracle",
        "source_table": "CDCDW.V_FACT_NHI_DT",
        "date_column": "admit_date",
        "age_column": "age_group",
        "branch_column": "branch",
        "county_column": "county",
        "recode_oipd": "ER",
        "disease_columns": {
            "EV": "EV",
            "ILI": "ICD_48X",
            "DI": "DIARRHOEA",
        },
        "total_column": "total",
        "target": "nhi_er",
    },

    "nhi_opd": {
        "source_name": "NHI_OPD",
        "source_db": "oracle",
        "source_table": "CDCDW.V_FACT_NHI_DT",
        "date_column": "admit_date",
        "age_column": "age_group",
        "branch_column": "branch",
        "county_column": "county",
        "recode_oipd": "OPD",
        "disease_columns": {
            "EV": "EV",
            "ILI": "ICD_48X",
            "DI": "DIARRHOEA",
        },
        "total_column": "total",
        "target": "nhi_opd",
    },

    "rods": {
        "source_name": "RODS",
        "source_db": "postgres_rods_data",
        "source_table": "public.mv_rods_visit",
        "date_column": "admit_date",
        "age_column": "age",
        "branch_column": "branch",
        "county_column": "county",
        "disease_columns": {
            "EV": "e_i",
            "ILI": "rods_rs",
            "DI": "acutediarrhea",
        },
        "total_column": "total",
        "target": "rods",
    },

    "weather": {
        "source_name": "WEATHER",
        "source_db": "cwb_data",
        "source_table": "public.weather_daily_city",
        "date_column": "weather_date",
        "county_column": "city_std",
        "target": "weather",
    },
    "dim_agegroup": {
        "source_name": "DIM_AGEGROUP",
        "source_db": "postgres_dim_data",
        "source_table": "public.dim_agegroup",
        "target": "dim_agegroup",
    },
}

DISEASE_SOURCES = ["nhi_er", "nhi_opd", "rods"]
ALL_SOURCES = ["nhi_er", "nhi_opd", "rods", "weather"]