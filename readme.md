# extract_disease_data

`extract_disease_data` 是疾病與天氣資料的 ETL 專案。流程以本機 raw cache 儲存大量原始資料，PostgreSQL 僅保留整理後可直接供模型使用的正式資料表。

## 1. 資料流

```text
source DB
→ /media/sf_Eic02/Disease_modle_data/*.csv
→ Python transform
→ weekly county disease age pivot
→ merge weekly county weather
→ disease_forecast_data final tables
```

## 2. PostgreSQL 正式資料表

目前規劃上傳 4 張正式表：

1. `disease_forecast_data.weather_weekly_city`
2. `disease_forecast_data.model_nhi_er_weekly_county`
3. `disease_forecast_data.model_nhi_opd_weekly_county`
4. `disease_forecast_data.model_rods_weekly_county`

## 3. Local raw cache

路徑：

```text
/media/sf_Eic02/Disease_modle_data/
```

檔案：

```text
raw_nhi_er_target_disease.csv
raw_nhi_opd_target_disease.csv
raw_rods_target_disease.csv
raw_weather_data.csv
```

## 4. 執行模式

### initial

全量抽取、更新 local raw cache、重算週別模型資料並上傳 PostgreSQL。

```bash
python main.py --mode initial --start-date 2018-01-01 --end-date 2026-06-22
```

### incremental

依 state 與 lookback days 決定回補區間，更新 local raw cache 後重算受影響的 yearweek。

```bash
python main.py --mode incremental
```

指定來源：

```bash
python main.py --mode incremental --source rods
python main.py --mode incremental --source nhi_er
python main.py --mode incremental --source nhi_opd
```

### check-only

檢查 local raw cache 與 PostgreSQL final tables 狀態。

```bash
python main.py --mode check-only
```

## 5. 寫入策略

### local raw cache

CSV 使用 date range replace：

```text
讀取既有 CSV
→ 刪除 start_date ~ end_date
→ 合併新抽取資料
→ 依 key 去重
→ atomic overwrite
```

### PostgreSQL final tables

正式表使用 yearweek range replace：

```text
DELETE target table WHERE yearweek BETWEEN start_yearweek AND end_yearweek
→ INSERT 重算後資料
```

## 6. 目前已完成模組

- NHI ER / OPD extractor
- RODS extractor
- CSV local raw cache
- disease raw normalize
- weekly aggregation
- age group pivot
- weather_daily_city extractor
- weather weekly transform
- model dataset merge
- PostgreSQL yearweek range replace
- local profile
- PG profile
- state
- logs
- CLI main flow

## 7. 天氣來源設定

天氣 extractor 已接上 PostgreSQL 的 `public.weather_daily_city`。

使用欄位：

- 日期欄位：`weather_date`，輸出為 `date`
- 縣市欄位：`city_std`，輸出為 `county`
- 每日縣市天氣欄位會彙整為週別縣市資料

`public.daily` 目前未接入主流程，因為該表沒有縣市欄位，若要使用需另外提供測站或地區對照。

## 8. decorator 規則

NHI Oracle：

```python
@conn.deco.oracle()
```

RODS / PostgreSQL：

```python
@conn.deco.postgres(dbname="RODS_DATA")
```

目標 PostgreSQL：

```python
@conn.deco.postgres(dbname="postgres")
```
