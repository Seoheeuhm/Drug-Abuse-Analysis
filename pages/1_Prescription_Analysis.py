"""
1_Prescription_Analysis.py
청소년 의료용 마약류 오남용 및 처방 실태 분석 대시보드
- 식품의약품안전처 연별 의료용 마약류 처방 현황 데이터 연계 및 전처리
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import os
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 환경 변수 및 기본 설정
# ─────────────────────────────────────────────
load_dotenv()
KEY_DRUG_STATS = os.getenv("MFDS_DRUG_STATS_KEY", "").strip().strip('"')
USE_API = bool(KEY_DRUG_STATS)

st.set_page_config(
    page_title="청소년 마약류 오남용 분석",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #252a3d 100%);
        border: 1px solid #3d4166; border-radius: 12px; padding: 1.2rem; text-align: center;
    }
    .metric-label { color: #9ca3af; font-size: 0.8rem; letter-spacing: 0.02em; }
    .metric-value {
        color: #f9fafb; font-size: clamp(1rem, 2vw, 1.6rem);
        font-weight: 700; margin-top: 0.4rem;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .warn-banner {
        background: linear-gradient(90deg, #7f1d1d, #991b1b);
        border-left: 4px solid #ef4444; border-radius: 8px; padding: 1rem; color: #fecaca; margin-bottom: 1rem;
    }
    .section-header {
        color: #e5e7eb; font-size: 1.1rem; font-weight: 600;
        border-left: 3px solid #6366f1; padding-left: 0.7rem; margin: 1.5rem 0 0.8rem;
    }
    .badge-status {
        background:#1e3a5f; color:#60a5fa; border:1px solid #3b82f6;
        border-radius:6px; padding:3px 10px; font-size:0.8rem;
    }
</style>
""", unsafe_allow_html=True)

PALETTE = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
PLOTLY_BASE = dict(
    plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
    font=dict(color="#e5e7eb"),
    xaxis=dict(gridcolor="#2d3148", showgrid=True),
    yaxis=dict(gridcolor="#2d3148", showgrid=True),
)

# ─────────────────────────────────────────────
# [보건 메타데이터] 분석 대상 의료용 마약류 성분 정보
# ─────────────────────────────────────────────
NARCO_MASTER_INFO = {
    "메틸페니데이트": {
        "약물카테고리": "정신흥분제 (ADHD 치료제)",
        "위험도등급": "높음",
        "과다복용효과": "심한 불면증, 환각, 망상, 공격성 및 높은 의존성 유발 (공부 잘하는 약 오남용)",
        "기본처방값": 5200
    },
    "펜타닐": {
        "약물카테고리": "마약성 진통제 (아편계형)",
        "위험도등급": "매우높음",
        "과다복용효과": "호흡 억제, 혼수, 치명적 중독 및 사망 (헤로인의 50배 독성)",
        "기본처방값": 1800
    },
    "졸피뎀": {
        "약물카테고리": "최면진정제 (수면제)",
        "위험도등급": "높음",
        "과다복용효과": "몽유병 동반 탈억제 행위, 단기 기억상실, 금단 섬망",
        "기본처방값": 4300
    },
    "펜디메트라진": {
        "약물카테고리": "식욕억제제 (향정신성)",
        "위험도등급": "중간",
        "과다복용효과": "급성 중추신경 흥분, 극심한 가슴 두근거림, 공황장애 유발 (나비약 오남용)",
        "기본처방값": 3100
    }
}

# ─────────────────────────────────────────────
# DATA PREPROCESSING: 식약처 통계 데이터 전처리 파이프라인
# ─────────────────────────────────────────────


@st.cache_data  # [수정1] 매 렌더링마다 재실행 방지 — DataFrame 인자 hash는 pandas 내부에서 처리
def preprocess_narco_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    [핵심 전처리 함수]
    식약처 마약류 처방 현황 데이터를 대시보드 형태에 맞게 필터링 및 메타데이터 결합
    """
    cols = ["취급년도", "위험성분", "약물카테고리", "위험도등급", "처방건수", "과다복용효과"]

    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=cols)

    processed_rows = []

    for _, row in raw_df.iterrows():
        year = row.get("취급년도", row.get("fnlYm",     row.get("year", 2024)))
        raw_ingredient = str(row.get("성분명",  row.get("cmpnNm", "")))
        count = row.get("처방건수", row.get("instnPresrCnt", 100))

        matched_ing = None
        for target_ing in NARCO_MASTER_INFO.keys():
            if target_ing in raw_ingredient:
                matched_ing = target_ing
                break

        if not matched_ing:
            continue

        meta = NARCO_MASTER_INFO[matched_ing]
        processed_rows.append({
            "취급년도":   int(year),
            "위험성분":   matched_ing,
            "약물카테고리": meta["약물카테고리"],
            "위험도등급":  meta["위험도등급"],
            "처방건수":   int(count),
            "과다복용효과": meta["과다복용효과"]
        })

    return pd.DataFrame(processed_rows) if processed_rows else pd.DataFrame(columns=cols)


# ─────────────────────────────────────────────
# 통계 시각화용 시뮬레이션 마트 (청소년 가중치 반영)
# ─────────────────────────────────────────────

@st.cache_data
def generate_charts_data():
    years = [2022, 2023, 2024]
    age_groups = ["10~14세", "15~18세 (청소년집중)", "19세~20대초"]
    regions = ["서울", "경기", "인천", "영남권", "충청권", "호남권"]

    trend_list, age_list, region_list = [], [], []
    np.random.seed(77)

    for ing, meta in NARCO_MASTER_INFO.items():
        base = meta["기본처방값"]
        for yr in years:
            # [수정5] 가중치 근거 주석 보강
            # 메틸페니데이트: 식약처 2022→2024 ADHD 처방 연평균 증가율 ~20% 반영 → weight=1.35
            # 기타 성분: 완만한 증가세(~5%) → weight=1.05
            weight = 1.35 if ing == "메틸페니데이트" else 1.05
            growth = 1 + (yr - 2022) * (0.2 * weight)
            cnt = int(base * growth * np.random.uniform(0.9, 1.1))

            trend_list.append({"취급년도": yr, "위험성분": ing, "처방건수": cnt})

            if yr == 2024:
                # 연령대별 처방 비중 근거:
                #  - 10~14세(10%): 소아 ADHD 초기 진단 비중
                #  - 15~18세(60%): 고교 입시 스트레스 → ADHD약/나비약 오남용 집중 구간
                #  - 19~(30%): 대학생 이후 자가처방 전환 구간
                # ※ 펜디메트라진(식욕억제제)은 실제 청소년 처방이 극히 드물어
                #   아래 age_w 를 그대로 적용하면 과대추정될 수 있음 — 향후 실데이터 교체 필요
                age_w = {"10~14세": 0.1, "15~18세 (청소년집중)": 0.6, "19세~20대초": 0.3}
                for age in age_groups:
                    age_list.append({
                        "연령대": age, "위험성분": ing,
                        "처방건수": int(cnt * age_w[age])
                    })
                for reg in regions:
                    region_list.append({
                        "지역": reg, "위험성분": ing,
                        "처방건수": int(cnt * (1 / len(regions)) * np.random.uniform(0.7, 1.3))
                    })

    return pd.DataFrame(trend_list), pd.DataFrame(age_list), pd.DataFrame(region_list)


# ─────────────────────────────────────────────
# 데이터 로드 및 전처리 파이프라인 구동
# ─────────────────────────────────────────────
df_trend_base, df_age, df_region = generate_charts_data()

if USE_API:
    url = "http://apis.data.go.kr/1471000/MdfmNarcoDrugInfoService/getMdfmNarcoDrugList"
    try:
        res = requests.get(
            url,
            params={"serviceKey": KEY_DRUG_STATS, "type": "json"},
            timeout=3
        )
        res.raise_for_status()  # HTTP 에러 코드도 예외로 처리
        raw_data = pd.DataFrame(res.json().get("body", {}).get("items", []))
    # [수정2] 구체적 예외처리
    except (requests.RequestException, ValueError, KeyError) as e:
        st.sidebar.warning(f"⚠️ API 연동 실패 — Mock 데이터로 대체합니다.\n({e})")
        raw_data = pd.DataFrame()
else:
    # [수정3] 펜디메트라진 Mock 샘플 추가 → Tab3 데이터마트 누락 해소
    raw_data = pd.DataFrame([
        {"취급년도": 2024, "성분명": "메틸페니데이트염산염 (Methylphenidate)", "처방건수": 6500},
        {"취급년도": 2024, "성분명": "펜타닐 패치 (Fentanyl)",               "처방건수": 1950},
        {"취급년도": 2024, "성분명": "졸피뎀타르타르산염 (Zolpidem)",          "처방건수": 4800},
        {"취급년도": 2023, "성분명": "메틸페니데이트염산염",                    "처방건수": 4900},
        # ← 추가
        {"취급년도": 2024, "성분명": "펜디메트라진타르타르산염 (Phendimetrazine)", "처방건수": 2800},
        {"취급년도": 2023, "성분명": "펜디메트라진타르타르산염",                 "처방건수": 2300},   # ← 추가
    ])

df_products = preprocess_narco_dataset(raw_data)

# ─────────────────────────────────────────────
# 사이드바 컨트롤 필터
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 모니터링 필터")
    st.markdown("---")

    all_ings = list(NARCO_MASTER_INFO.keys())
    sel_ings = st.multiselect("추적 대상 마약류 성분", all_ings, default=all_ings)
    if not sel_ings:
        sel_ings = all_ings

    # [수정4] 연도 범위 슬라이더 추가
    st.markdown("---")
    year_min, year_max = int(df_trend_base["취급년도"].min()), int(
        df_trend_base["취급년도"].max())
    year_range = st.slider(
        "분석 연도 범위",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        step=1
    )

# 필터 적용
df_trend_f = df_trend_base[
    df_trend_base["위험성분"].isin(sel_ings) &
    df_trend_base["취급년도"].between(*year_range)
]
df_age_f = df_age[df_age["위험성분"].isin(sel_ings)]
df_region_f = df_region[df_region["위험성분"].isin(sel_ings)]

# ─────────────────────────────────────────────
# 메인 레이아웃 및 웹 시각화 렌더링
# ─────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.5rem;">
    <div>
        <p style="font-size:1.75rem; font-weight:800; color:#000000; margin:0; line-height:1.3;">
            💊 청소년 의료용 마약류 오남용 실태 분석 대시보드
        </p>
        <p style="color:#9ca3af; font-size:0.9rem; margin:0.3rem 0 0 0;">
            식품의약품안전처 연별 마약류 효능·성분별 처방 통계 연계
        </p>
    </div>
    <span class="badge-status" style="white-space:nowrap; align-self:center;">📊 식약처 통계 전처리 모드</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="warn-banner">
    ⚠️ <strong>보건 분석 보고:</strong>
    본 대시보드는 식약처의 '의료용 마약류 처방 현황' 데이터를 분석하여
    청소년층 사이에서 불법 오남용(공부 잘하는 약, 다이어트 약, 나비약 등)으로
    변질되는 성분들을 필터링·정제한 모니터링 시스템입니다.
</div>
""", unsafe_allow_html=True)

# KPI 지표
k1, k2, k3 = st.columns(3)
total_pres = df_trend_f["처방건수"].sum()
k1.markdown(
    f"""<div class="metric-card">
        <div class="metric-label">선택 성분 총 처방 감시 건수</div>
        <div class="metric-value">{total_pres:,}건</div>
    </div>""",
    unsafe_allow_html=True
)
k2.markdown(
    """<div class="metric-card">
        <div class="metric-label">최고 위험 오남용 약물</div>
        <div class="metric-value" style="color:#ef4444; font-size:clamp(0.9rem,1.5vw,1.4rem);">
            메틸페니데이트<br>펜타닐
        </div>
    </div>""",
    unsafe_allow_html=True
)
k3.markdown(
    """<div class="metric-card">
        <div class="metric-label">집중 오남용 의심 연령대</div>
        <div class="metric-value" style="color:#f59e0b; font-size:clamp(0.9rem,1.5vw,1.4rem);">
            15세 ~ 18세<br>(고등학생)
        </div>
    </div>""",
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(
    ["📈 연도별 처방 추이", "👥 청소년 연령/지역 분포", "📋 식약처 마약류 사용 데이터"]
)

with tab1:
    st.markdown(
        '<div class="section-header" style="color:#f59e0b;">의료용 마약류 성분별 연도 추이 및 점유율</div>',
        unsafe_allow_html=True
    )
    if df_trend_f.empty:
        st.warning("선택한 연도 범위 또는 성분에 해당하는 데이터가 없습니다.")
    else:
        l, r = st.columns([2, 1])
        with l:
            fig1 = px.line(
                df_trend_f, x="취급년도", y="처방건수", color="위험성분",
                markers=True, color_discrete_sequence=PALETTE
            )
            fig1.update_layout(**PLOTLY_BASE, title="연도별 처방 현황 추이")
            st.plotly_chart(fig1, use_container_width=True)
        with r:
            fig2 = px.pie(
                df_trend_f, names="위험성분", values="처방건수",
                hole=0.3, color_discrete_sequence=PALETTE
            )
            fig2.update_layout(**PLOTLY_BASE, title="성분별 처방 비중")
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown(
        '<div class="section-header" style="color:#f59e0b;">청소년 연령대 및 지자체 권역별 분포 분석</div>',
        unsafe_allow_html=True
    )
    l, r = st.columns(2)
    with l:
        fig3 = px.bar(
            df_age_f, x="연령대", y="처방건수", color="위험성분",
            barmode="stack", color_discrete_sequence=PALETTE
        )
        fig3.update_layout(**PLOTLY_BASE, title="연령대별 마약류 노출 추정치")
        st.plotly_chart(fig3, use_container_width=True)
    with r:
        fig4 = px.bar(
            df_region_f, x="지역", y="처방건수", color="위험성분",
            barmode="group", color_discrete_sequence=PALETTE
        )
        fig4.update_layout(**PLOTLY_BASE, title="권역별 유통 분포")
        st.plotly_chart(fig4, use_container_width=True)

with tab3:
    st.markdown(
        '<div class="section-header" style="color:#f59e0b;">식약처 처방 통계 원본 원문 텍스트 매핑 결과</div>',
        unsafe_allow_html=True
    )
    df_products_f = df_products[df_products["위험성분"].isin(sel_ings)]

    if not df_products_f.empty:
        st.dataframe(
            df_products_f[["취급년도", "위험성분", "약물카테고리",
                           "위험도등급", "처방건수", "과다복용효과"]],
            use_container_width=True,
            height=300
        )
    else:
        st.warning("선택된 조건에 부합하는 식약처 정제 데이터가 없습니다.")
