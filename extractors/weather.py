from __future__ import annotations

import pandas as pd
from eic_utils import conn, utility

from config.settings import WEATHER_DBNAME


WEATHER_DAILY_CITY_COLUMNS = [
    "weather_date",
    "city",
    "city_std",
    "raw_station_rows",
    "station_count",
    "lat_mean",
    "lon_mean",
    "station_pressure_mean",
    "station_pressure_min",
    "station_pressure_max",
    "sea_level_pressure_mean",
    "sea_level_pressure_min",
    "sea_level_pressure_max",
    "air_temperature_mean",
    "air_temperature_min",
    "air_temperature_max",
    "air_temperature_daily_range_mean",
    "dew_point_temperature_mean",
    "dew_point_temperature_min",
    "dew_point_temperature_max",
    "relative_humidity_mean",
    "relative_humidity_min",
    "relative_humidity_max",
    "wind_speed_mean",
    "wind_speed_ten_minutely_max",
    "wind_direction_prevailing_mode",
    "wind_direction_ten_minutely_max_mode",
    "peak_gust_max",
    "peak_gust_direction_mode",
    "precipitation_accumulation_mean",
    "precipitation_accumulation_max",
    "precipitation_hourly_maximum_mean",
    "precipitation_hourly_maximum_max",
    "precipitation_sixty_minutely_maximum_mean",
    "precipitation_sixty_minutely_maximum_max",
    "precipitation_ten_minutely_maximum_mean",
    "precipitation_ten_minutely_maximum_max",
    "precipitation_duration_total_mean",
    "precipitation_duration_total_max",
    "sunshine_duration_total_mean",
    "sunshine_duration_rate_mean",
    "global_solar_radiation_accumulation_mean",
    "global_solar_radiation_hourly_maximum_max",
    "visibility_mean",
    "evaporation_class_a_pan_accumulation_mean",
    "uv_index_maximum_mean",
    "uv_index_maximum_max",
    "total_cloud_amount_mean",
    "air_temperature_non_null_station_count",
    "relative_humidity_non_null_station_count",
    "precipitation_non_null_station_count",
    "station_pressure_non_null_station_count",
    "wind_speed_non_null_station_count",
    "sunshine_duration_non_null_station_count",
    "uv_index_non_null_station_count",
]


class WeatherExtractor:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    @utility.timer()
    @conn.deco.postgres(dbname=WEATHER_DBNAME)
    def extract(self, cur=None) -> pd.DataFrame:
        """抽取每日縣市層級天氣資料。"""
        select_columns = []
        for col in WEATHER_DAILY_CITY_COLUMNS:
            if col == "weather_date":
                select_columns.append("weather_date::date AS date")
            elif col == "city_std":
                select_columns.append("city_std AS county")
            else:
                select_columns.append(col)

        select_sql = ",\n                ".join(select_columns)
        sql = f"""
            SELECT
                {select_sql}
            FROM public.weather_daily_city
            WHERE weather_date >= '{self.start_date}'::date
              AND weather_date <= '{self.end_date}'::date
            ORDER BY weather_date, city_std
        """

        cur.execute(sql)
        df = pd.DataFrame.from_records(
            cur.fetchall(),
            columns=[c[0].lower() for c in cur.description],
        )

        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["county"] = df["county"].fillna(df.get("city", "未知"))
        return df
