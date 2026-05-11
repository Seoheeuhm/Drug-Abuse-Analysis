"""
1_처방현황.py - 마약류 의약품 처방 현황 분석 페이지
담당: 지선
"""

# TODO: 식약처 Open API 연동 - 의약품 성분/효능/부작용 데이터

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# utils 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_prescription_data

# 페이지 설정
st.set_page_config(page_title="처방 현황", page_icon="📊", layout="wide")

st.title("📊 마약류 의약품 처방 현황")
st.markdown("---")

# 데이터 로드
df = load_prescription_data()

# 상단 요약 지표
st.subheader("📈 처방 현황 요약")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("총 처방 건수", f"{df['처방량'].sum():,}건", help="샘플 데이터 기준")
with col2:
    st.metric("분석 성분 수", f"{len(df)}종", help="샘플 데이터 기준")
with col3:
    st.metric("최다 처방 성분", df.loc[df['처방량'].idxmax(), '성분명'], help="샘플 데이터 기준")

st.markdown("---")

# 차트 영역: 2열 레이아웃
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("💊 성분별 처방량 (막대 그래프)")
    # TODO: 실제 식약처 API 데이터로 교체
    fig_bar = px.bar(
        df,
        x="성분명",
        y="처방량",
        color="성분명",
        title="성분별 처방량 비교",
        labels={"처방량": "처방 건수", "성분명": "의약품 성분"},
        text="처방량",
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("🥧 성분 비율 (파이 차트)")
    # TODO: 실제 식약처 API 데이터로 교체
    fig_pie = px.pie(
        df,
        names="성분명",
        values="처방량",
        title="성분별 처방 비율",
        hole=0.3,  # 도넛 차트 형태
    )
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# 효능군별 분석
st.subheader("⚕️ 효능군별 분포")

# TODO: 실제 API 데이터에서 효능 분류 추가
fig_efficacy = px.bar(
    df,
    x="효능",
    y="처방량",
    color="효능",
    title="효능군별 처방량",
    labels={"처방량": "처방 건수", "효능": "효능 분류"},
)
fig_efficacy.update_layout(showlegend=False)
st.plotly_chart(fig_efficacy, use_container_width=True)

st.markdown("---")

# 부작용 현황 테이블
st.subheader("⚠️ 주요 부작용 현황")

# TODO: 실제 부작용 신고 데이터 연동
st.dataframe(
    df[["성분명", "효능", "부작용", "처방량"]].rename(
        columns={"성분명": "성분", "처방량": "처방 건수"}
    ),
    use_container_width=True,
    hide_index=True,
)

st.caption("※ 현재 샘플 데이터 기준 | 실제 데이터는 식약처 Open API 연동 후 갱신 예정")
