"""
Home.py - 청소년 마약류 의약품 과다복용 분석 대시보드 메인 페이지
"""

import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="청소년 약물 오남용 분석",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 메인 타이틀
st.title("💊 청소년 마약류 의약품 과다복용 분석 대시보드")
st.markdown("---")

# 프로젝트 개요 섹션
st.header("📌 프로젝트 개요")

col_problem, col_goal = st.columns(2)

with col_problem:
    st.subheader("🚨 문제 정의")
    st.warning(
        """
        감기약, 해열진통제, 수면유도제 등을 과다복용해
        환각을 경험하려는 **OD(OverDose)** 행위가 청소년 사이에서 확산되고 있습니다.
        """
    )

with col_goal:
    st.subheader("🎯 분석 목적")
    st.info(
        """
        의약품 처방 및 유통 현황 데이터를 통합 분석하여
        청소년 약물 오남용 문제의 실태를 파악하고
        정책적 시사점을 도출합니다.
        """
    )

st.markdown("---")

# 주요 지표 메트릭 섹션 (예시값)
st.header("📊 주요 지표")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🏥 전국 약국 수",
        value="24,000개",
        delta="+1,200개 (전년 대비)",
        help="전국 등록 약국 현황 (2023년 기준 예시값)",
    )

with col2:
    st.metric(
        label="💊 마약류 처방 건수",
        value="1,250만 건",
        delta="+8.3% (전년 대비)",
        help="마약류 의약품 연간 처방 건수 (2023년 기준 예시값)",
    )

with col3:
    st.metric(
        label="📦 수입 실적",
        value="700톤",
        delta="+16.7% (전년 대비)",
        help="마약류 의약품 연간 수입량 (2023년 기준 예시값)",
    )

st.markdown("---")

# 페이지 안내 섹션
st.header("🗂 페이지 구성")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(
        """
        ### 📊 처방 현황
        - 의약품 성분별 처방 비율
        - 효능군별 분포 분석
        - 주요 부작용 현황

        **담당: 지선**
        """
    )

with col_b:
    st.markdown(
        """
        ### 🏥 의료기관 현황
        - 전국 약국 분포 현황
        - 마약류 수입 실적 추세
        - 마약류 수출 실적 추세

        **담당: 시은**
        """
    )

with col_c:
    st.markdown(
        """
        ### 💬 대화형 분석
        - Claude AI 기반 자연어 질의
        - 데이터 기반 인사이트 도출
        - 맞춤형 분석 결과 제공

        **담당: 주현, 서희**
        """
    )

st.markdown("---")

# 데이터 출처 안내
st.caption(
    "📂 데이터 출처: 식품의약품안전처 오픈API · 공공데이터포털(약국현황, 수입/수출 실적)"
)
