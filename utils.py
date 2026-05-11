"""
utils.py - 공통 데이터 로드 및 API 유틸리티 함수 모음
"""

import pandas as pd
import streamlit as st
import requests


@st.cache_data
def load_prescription_data() -> pd.DataFrame:
    """처방 현황 데이터 로드 (지선)"""
    # TODO: 식약처 Open API 연동 후 실제 데이터로 교체
    # 샘플 데이터 생성
    return pd.DataFrame({
        "성분명": ["성분A", "성분B", "성분C"],
        "처방량": [100, 200, 150],
        "효능": ["진통", "해열", "수면유도"],
        "부작용": ["졸음", "어지러움", "구토"],
    })


@st.cache_data
def load_hospital_data() -> pd.DataFrame:
    """의료기관/수입수출 데이터 로드 (시은)"""
    # TODO: 공공데이터포털 API 연동 후 실제 데이터로 교체
    # 샘플 데이터
    return pd.DataFrame({
        "연도": [2021, 2022, 2023],
        "약국수": [1000, 1100, 1200],
        "수입량": [500, 600, 700],
    })


@st.cache_data
def load_all_data() -> pd.DataFrame:
    """대화형 분석용 전체 데이터 (주현, 서희)"""
    # TODO: 각 API 연동 완료 후 실제 데이터 통합 방식 재검토
    df1 = load_prescription_data()
    df2 = load_hospital_data()
    return pd.concat([df1, df2], ignore_index=True)


def fetch_openapi(url: str, params: dict) -> dict:
    """공공데이터 Open API 호출 공통 함수"""
    # TODO: 타임아웃, 재시도 로직, 에러 핸들링 강화 검토
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
