"""
2_의료기관현황.py - 의료기관 및 수입/수출 현황 분석 페이지
담당: 시은
"""

# TODO: 공공데이터포털 API 3개 연동
# - 약국현황/종별 취급현황: https://www.data.go.kr/data/15139163/openapi.do
# - 수입실적: https://www.data.go.kr/data/15136552/openapi.do
# - 수출실적: https://www.data.go.kr/data/15136564/openapi.do

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# utils 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_hospital_data

# 페이지 설정
st.set_page_config(page_title="의료기관 현황", page_icon="🏥", layout="wide")

st.title("🏥 의료기관 및 수입/수출 현황")
st.markdown("---")

# 데이터 로드
df = load_hospital_data()

# 3개 탭 구성
tab_pharmacy, tab_import, tab_export = st.tabs(["🏪 약국 현황", "📥 수입 실적", "📤 수출 실적"])

# ── 탭 1: 약국 현황 ──────────────────────────────────────────────
with tab_pharmacy:
    st.subheader("🏪 전국 약국 현황")

    # TODO: 공공데이터포털 약국현황 API 연동 후 지역별 실제 데이터로 교체
    # 지역별 샘플 데이터
    region_data = pd.DataFrame({
        "지역": ["서울", "경기", "부산", "인천", "대구", "광주", "대전", "울산", "세종", "강원"],
        "약국수": [5200, 4800, 2100, 1500, 1300, 900, 850, 600, 200, 700],
        "종별": ["도시", "도시", "도시", "도시", "도시", "도시", "도시", "도시", "도시", "농촌"],
    })

    col1, col2 = st.columns(2)

    with col1:
        # 지역별 약국 수 막대 그래프
        fig_region = px.bar(
            region_data,
            x="지역",
            y="약국수",
            color="종별",
            title="지역별 약국 분포",
            labels={"약국수": "약국 수 (개)", "지역": "지역"},
            text="약국수",
        )
        fig_region.update_traces(textposition="outside")
        st.plotly_chart(fig_region, use_container_width=True)

    with col2:
        # 연도별 약국 수 증가 추세
        fig_trend = px.line(
            df,
            x="연도",
            y="약국수",
            title="연도별 약국 수 증가 추세",
            labels={"약국수": "약국 수 (개)", "연도": "연도"},
            markers=True,
        )
        fig_trend.update_traces(line_color="#2196F3", line_width=3)
        st.plotly_chart(fig_trend, use_container_width=True)

    # 종별 취급현황 테이블
    st.subheader("🏷 종별 약국 취급 현황")
    # TODO: API 연동 후 실제 종별 데이터로 교체
    category_data = pd.DataFrame({
        "약국 종별": ["일반약국", "병원내약국", "한방약국", "기타"],
        "수량 (개)": [20000, 2500, 1200, 300],
        "비율 (%)": [83.3, 10.4, 5.0, 1.3],
    })
    st.dataframe(category_data, use_container_width=True, hide_index=True)

    st.caption("※ 샘플 데이터 기준 | 공공데이터포털 약국현황 API 연동 후 갱신 예정")

# ── 탭 2: 수입 실적 ──────────────────────────────────────────────
with tab_import:
    st.subheader("📥 마약류 의약품 수입 실적")

    # TODO: 공공데이터포털 수입실적 API 연동 후 실제 데이터로 교체
    import_data = pd.DataFrame({
        "연도": [2019, 2020, 2021, 2022, 2023],
        "수입량(톤)": [420, 450, 500, 600, 700],
        "수입액(억원)": [1200, 1350, 1500, 1800, 2100],
        "주요품목": ["해열진통제", "해열진통제", "수면유도제", "수면유도제", "수면유도제"],
    })

    col1, col2 = st.columns(2)

    with col1:
        # 수입량 추세 그래프
        fig_import_qty = px.area(
            import_data,
            x="연도",
            y="수입량(톤)",
            title="연도별 수입량 추세 (톤)",
            labels={"수입량(톤)": "수입량 (톤)", "연도": "연도"},
        )
        fig_import_qty.update_traces(fill="tozeroy", line_color="#FF5722")
        st.plotly_chart(fig_import_qty, use_container_width=True)

    with col2:
        # 수입액 추세 그래프
        fig_import_val = px.bar(
            import_data,
            x="연도",
            y="수입액(억원)",
            title="연도별 수입액 추세 (억원)",
            labels={"수입액(억원)": "수입액 (억원)", "연도": "연도"},
            color="수입액(억원)",
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig_import_val, use_container_width=True)

    st.dataframe(import_data, use_container_width=True, hide_index=True)
    st.caption("※ 샘플 데이터 기준 | 공공데이터포털 수입실적 API 연동 후 갱신 예정")

# ── 탭 3: 수출 실적 ──────────────────────────────────────────────
with tab_export:
    st.subheader("📤 마약류 의약품 수출 실적")

    # TODO: 공공데이터포털 수출실적 API 연동 후 실제 데이터로 교체
    export_data = pd.DataFrame({
        "연도": [2019, 2020, 2021, 2022, 2023],
        "수출량(톤)": [180, 200, 230, 260, 300],
        "수출액(억원)": [500, 580, 670, 780, 920],
        "주요수출국": ["미국", "일본", "미국", "중국", "중국"],
    })

    col1, col2 = st.columns(2)

    with col1:
        # 수출량 추세
        fig_export_qty = px.area(
            export_data,
            x="연도",
            y="수출량(톤)",
            title="연도별 수출량 추세 (톤)",
            labels={"수출량(톤)": "수출량 (톤)", "연도": "연도"},
        )
        fig_export_qty.update_traces(fill="tozeroy", line_color="#4CAF50")
        st.plotly_chart(fig_export_qty, use_container_width=True)

    with col2:
        # 수출액 추세
        fig_export_val = px.bar(
            export_data,
            x="연도",
            y="수출액(억원)",
            title="연도별 수출액 추세 (억원)",
            labels={"수출액(억원)": "수출액 (억원)", "연도": "연도"},
            color="수출액(억원)",
            color_continuous_scale="Greens",
        )
        st.plotly_chart(fig_export_val, use_container_width=True)

    st.dataframe(export_data, use_container_width=True, hide_index=True)
    st.caption("※ 샘플 데이터 기준 | 공공데이터포털 수출실적 API 연동 후 갱신 예정")
