from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from checks.local_profile import profile_all_raw_sources, profile_raw_source
from checks.pg_profile import profile_all_pg_tables, profile_pg_table
from config.settings import INITIAL_START_DATE, INCREMENTAL_LOOKBACK_DAYS, END_DATE_LAG_DAYS
from config.sources import ALL_SOURCES, DISEASE_SOURCES
from config.tables import POSTGRES_TABLES
from extractors.nhi import NHIExtractor
from extractors.rods import RODSExtractor
from extractors.weather import WeatherExtractor
from local_store.raw_cache import load_raw, load_raw_range, save_raw_range
from loaders.replace_strategy import upload_yearweek_range
from transforms.disease_raw import normalize_disease_raw
from transforms.model_dataset import build_model_dataset
from transforms.weather_weekly import build_weather_weekly
from utils.cli import parse_args
from utils.dates import auto_end_date, date_range_to_yearweek_range, resolve_incremental_start
from utils.logger import build_run_id, setup_logger
from utils.state import load_state, save_state, update_local_source_state, update_pg_table_state
from extractors.dim_agegroup import load_dim_agegroup

def selected_sources(source_arg: str) -> list[str]:
    if source_arg == "all":
        return list(ALL_SOURCES)
    return [source_arg]


def extract_source(source: str, start_date: str, end_date: str) -> pd.DataFrame:
    if source == "nhi_er":
        df = NHIExtractor(start_date, end_date).extract_er()
        return normalize_disease_raw(df, "NHI_ER")
    if source == "nhi_opd":
        df = NHIExtractor(start_date, end_date).extract_opd()
        return normalize_disease_raw(df, "NHI_OPD")
    if source == "rods":
        df = RODSExtractor(start_date, end_date).extract()
        return normalize_disease_raw(df, "RODS")
    if source == "weather":
        return WeatherExtractor(start_date, end_date).extract()
    raise KeyError(f"Unsupported source: {source}")


def refresh_local_cache(source: str, start_date: str, end_date: str, logger) -> dict:
    logger.info(f"extract source={source} start_date={start_date} end_date={end_date}")
    df = extract_source(source, start_date, end_date)
    logger.info(f"extract source={source} rows={len(df)}")
    saved = save_raw_range(source, df, start_date, end_date)
    logger.info(f"local cache source={source} total_rows={len(saved)}")
    return profile_raw_source(source)


def build_weather_for_range(start_date: str, end_date: str) -> pd.DataFrame:
    raw_weather = load_raw_range("weather", start_date, end_date)
    if raw_weather.empty:
        return pd.DataFrame()
    return build_weather_weekly(raw_weather)


def upload_weather(start_date: str, end_date: str, logger) -> tuple[int, dict]:
    start_yw, end_yw = date_range_to_yearweek_range(start_date, end_date)
    weather_weekly = build_weather_for_range(start_date, end_date)
    if weather_weekly.empty:
        logger.warning("weather_weekly_city skipped: local raw weather is empty")
        return 0, {}

    rows = upload_yearweek_range("weather", weather_weekly, start_yw, end_yw)
    logger.info(f"upload weather_weekly_city rows={rows} yearweek={start_yw}-{end_yw}")
    profile = profile_pg_table("weather")
    return rows, profile


def upload_model_source(source: str, start_date: str, end_date: str, logger) -> tuple[int, dict]:
    start_yw, end_yw = date_range_to_yearweek_range(start_date, end_date)
    raw_disease = load_raw_range(source, start_date, end_date)
    if raw_disease.empty:
        logger.warning(f"model source={source} skipped: local raw disease is empty")
        return 0, {}

    weather_weekly = build_weather_for_range(start_date, end_date)
    dim_agegroup = load_dim_agegroup()

    model_df = build_model_dataset(
        df_raw_disease=raw_disease,
        df_weather_weekly=weather_weekly,
        df_dim_agegroup=dim_agegroup,
    )
    if model_df.empty:
        logger.warning(f"model source={source} skipped: model dataset is empty")
        return 0, {}

    rows = upload_yearweek_range(source, model_df, start_yw, end_yw)
    logger.info(f"upload model source={source} rows={rows} yearweek={start_yw}-{end_yw}")
    profile = profile_pg_table(source)
    return rows, profile


def resolve_dates_for_source(mode: str, args, state: dict, source: str) -> tuple[str, str]:
    """
    依照 mode 與 source 自動決定執行日期區間。

    initial:
        start_date = INITIAL_START_DATE
        end_date   = auto_end_date()

    incremental:
        start_date = 該 source 上次成功 end_date - lookback_days
        end_date   = auto_end_date()
    """
    end = args.end_date or str(auto_end_date(END_DATE_LAG_DAYS))

    if args.start_date:
        return args.start_date, end

    if mode == "initial":
        return INITIAL_START_DATE, end

    lookback_days = (
        args.lookback_days
        if args.lookback_days is not None
        else INCREMENTAL_LOOKBACK_DAYS
    )

    source_state = state.get("local_store", {}).get(source, {})
    last_end = (
        source_state.get("last_success_end_date")
        or source_state.get("max_date")
    )

    start = resolve_incremental_start(
        last_success_end_date=last_end,
        lookback_days=lookback_days,
        default_start_date=INITIAL_START_DATE,
    )

    return str(start), end


def run_check_only(logger) -> None:
    logger.info("check-only local raw profile")
    local_profiles = profile_all_raw_sources()
    for source, profile in local_profiles.items():
        logger.info(f"local_profile source={source} profile={profile}")

    logger.info("check-only postgres profile")
    pg_profiles = profile_all_pg_tables()
    for table_key, profile in pg_profiles.items():
        logger.info(f"pg_profile table_key={table_key} profile={profile}")


def main() -> None:
    args = parse_args()
    run_id = build_run_id()
    logger = setup_logger(run_id)
    state = load_state()
    state["last_run_id"] = run_id

    logger.info(f"run_id={run_id} mode={args.mode} source={args.source}")

    if args.mode == "check-only":
        run_check_only(logger)
        save_state(state)
        return

    sources = selected_sources(args.source)

    source_ranges = {
        source: resolve_dates_for_source(args.mode, args, state, source)
        for source in sources
    }

    for source, (start_date, end_date) in source_ranges.items():
        start_yw, end_yw = date_range_to_yearweek_range(start_date, end_date)
        logger.info(
            f"resolved_range source={source} "
            f"start_date={start_date} end_date={end_date} "
            f"yearweek={start_yw}-{end_yw}"
        )

    if not args.skip_extract:
        for source in sources:
            start_date, end_date = source_ranges[source]

            try:
                profile = refresh_local_cache(source, start_date, end_date, logger)
                state = update_local_source_state(state, source, start_date, end_date, profile)
            except NotImplementedError as e:
                logger.warning(f"source={source} skipped: {e}")
            except Exception:
                logger.exception(f"source={source} failed during extract/cache")
                save_state(state)
                raise

    if not args.skip_upload:
        try:
            if "weather" in sources:
                start_date, end_date = source_ranges["weather"]
                start_yw, end_yw = date_range_to_yearweek_range(start_date, end_date)

                rows, profile = upload_weather(start_date, end_date, logger)
                if profile:
                    state = update_pg_table_state(state, "weather", start_yw, end_yw, profile)

            model_sources = [s for s in sources if s in DISEASE_SOURCES]

            for source in model_sources:
                start_date, end_date = source_ranges[source]
                start_yw, end_yw = date_range_to_yearweek_range(start_date, end_date)

                rows, profile = upload_model_source(source, start_date, end_date, logger)
                if profile:
                    state = update_pg_table_state(state, source, start_yw, end_yw, profile)
        except Exception:
            logger.exception("upload failed")
            save_state(state)
            raise

    save_state(state)
    logger.info("run finished")


if __name__ == "__main__":
    main()
