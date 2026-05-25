import os
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드


# ── API 키 & 엔드포인트 설정 ──────────────────────────────────
DRUG_INFO_API_KEY = os.getenv("MFDS_DRUG_INFO_KEY")   # 의약품 개요정보 키
DRUG_PRMN_API_KEY = os.getenv("MFDS_NARCOTIC_KEY")    # 마약류 허가정보 키

DRUG_INFO_URL = (
    "https://apis.data.go.kr/1471000"
    "/DrbEasyDrugInfoService/getDrbEasyDrugList"
)
DRUG_PRMN_URL = (
    "https://apis.data.go.kr/1471000"
    "/DrugPrdtPrmsnInfoService/getDrugPrdtPrmsnDtlInq05"
)


@st.cache_data(ttl=3600)
def fetch_drug_data(page_no: int = 1, num_of_rows: int = 100, **kwargs) -> dict:
    """마약류 의약품 데이터 API 호출"""
    params = {
        "serviceKey": MFDS_DRUG_INFO_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "type": "json",
        **kwargs
    }

    try:
        response = requests.get(
            BASE_URL + "/getDrugPrdtPrmsnDtlInq04", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return {}
    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return {}


def parse_drug_dataframe(raw: dict) -> pd.DataFrame:
    """API 응답 → DataFrame 변환"""
    try:
        items = raw.get("body", {}).get("items", [])
        if not items:
            return pd.DataFrame()
        return pd.DataFrame(items)
    except Exception as e:
        st.error(f"데이터 파싱 오류: {e}")
        return pd.DataFrame()


@st.cache_data
def load_hospital_data() -> pd.DataFrame:
    """의료기관/수입수출 데이터 로드 (시은)"""
    return pd.DataFrame({
        "연도":   [2021, 2022, 2023],
        "약국수": [1000, 1100, 1200],
        "수입량": [500,  600,  700],
    })


@st.cache_data
def load_all_data() -> pd.DataFrame:
    """대화형 분석용 전체 데이터 (주현, 서희)"""
    df1 = load_prescription_data()
    df2 = load_hospital_data()
    return pd.concat([df1, df2], ignore_index=True)


def fetch_openapi(url: str, params: dict) -> dict:
    """공공데이터 Open API 호출 공통 함수"""
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
