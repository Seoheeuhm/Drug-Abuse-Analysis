"""
modules/hospital/data_fetch.py
"""
import os
import warnings

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore")

SERVICE_KEY = os.getenv("SERVICE_KEY", "")
BASE     = "https://apis.data.go.kr/1471000"
EP_PRESC = f"{BASE}/NarkMedcInstYrInfoService01/getNarkMedcInstYrInfo01?serviceKey={SERVICE_KEY}"
EP_MANU  = f"{BASE}/NarkManuImpexpInfoService/getNarkManuImpexpInfo?serviceKey={SERVICE_KEY}"

NUM_COLS = {
    "PRSC_INST_NUM", "PRSC_DOCT_NUM", "PRSC_PATNT_NUM", "PRSC_CNT",
    "ENTP_NUM", "PRDLST_NUM",
}


def fetch(url: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{url}&pageNo=1&numOfRows=500&type=json", timeout=15)
        r.raise_for_status()
        items = r.json().get("body", {}).get("items", [])
        if isinstance(items, dict):
            items = items.get("item", [])
        if not items:
            return pd.DataFrame()
        df = pd.DataFrame(items)
        for col in df.columns:
            if col in NUM_COLS:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


def preprocess(raw_presc: pd.DataFrame, raw_manu: pd.DataFrame):
    df_presc = raw_presc.copy()
    if not df_presc.empty:
        df_presc["YEAR"] = df_presc["TRMT_YM"].astype(str).str[:4].astype(int)

    df_manu = raw_manu.copy()
    if not df_manu.empty:
        df_manu["YEAR"] = df_manu["TRMT_YM"].astype(str).str[:4].astype(int)
        df_manu = df_manu[df_manu["TRMT_YM"].astype(str).str.endswith("12")].copy()

    return df_presc, df_manu


def yoy_metric(series: pd.Series):
    if series.empty:
        return None, None, None
    latest_yr  = series.index.max()
    latest_val = series[latest_yr]
    prev_yr    = latest_yr - 1
    delta_pct  = None
    if prev_yr in series.index and series[prev_yr] > 0:
        delta_pct = (latest_val - series[prev_yr]) / series[prev_yr] * 100
    return latest_val, delta_pct, latest_yr
