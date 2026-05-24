"""
2_의료기관현황.py - 의료기관 및 수입/수출 현황 분석 페이지
담당: 시은
"""

import numpy as np
import streamlit as st

from modules.hospital.data_fetch import EP_MANU, EP_PRESC, fetch, preprocess, yoy_metric
from modules.hospital.charts import (
    build_bubble_chart, build_dependency_chart, build_divs_bar,
    build_gap_chart, build_rank_table, build_yoy_heatmap,
)

st.set_page_config(
    page_title="의료용 마약류 취급 기관 현황",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def spacer(n: int = 1):
    st.markdown("<br>" * n, unsafe_allow_html=True)

_HELP_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" '
    'viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:block;transform:translateY(3px);">'
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
    '<circle cx="12" cy="17" r="0.8" fill="#555" stroke="none"/>'
    '</svg>'
)

def tip(label: str, tooltip: str) -> str:
    safe = tooltip.replace('"', '&quot;').replace('\n', '&#10;')
    return (
        f'<strong style="font-size:1rem;">{label}</strong>&nbsp;'
        f'<span class="tip-icon" data-tip="{safe}">{_HELP_ICON}</span>'
    )

@st.cache_data(ttl=1800, show_spinner=False)
def load_data():
    return fetch(EP_PRESC), fetch(EP_MANU)

with st.spinner("데이터 불러오는 중..."):
    raw_presc, raw_manu = load_data()
    df_presc, df_manu = preprocess(raw_presc, raw_manu)

ALL_YEARS = (
    sorted(df_presc["YEAR"].unique().tolist())
    if not df_presc.empty
    else [2019, 2020, 2021, 2022, 2023, 2024]
)

# ── 헤더 + CSS ───────────────────────────────────────────
st.title("의료용 마약류 취급 기관 현황")
spacer(1)

st.markdown("""
<style>
.tip-icon {
    position: relative;
    display: inline-block;
    cursor: help;
    margin-left: 6px;
}
.tip-icon::after {
    content: attr(data-tip);
    position: absolute;
    bottom: 135%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(40,40,40,0.93);
    color: #fff;
    padding: 8px 14px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 400;
    white-space: pre-line;
    line-height: 1.7;
    min-width: 320px;
    visibility: hidden;
    opacity: 0;
    transition: opacity .15s;
    z-index: 9999;
    pointer-events: none;
    text-align: left;
}
.tip-icon:hover::after {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# ── 필터 ─────────────────────────────────────────────────
fc1, fc2, _ = st.columns([1, 1, 4])
with fc1:
    sy = st.selectbox("시작 연도", ALL_YEARS, index=0, key="sy")
with fc2:
    ey = st.selectbox("종료 연도", ALL_YEARS, index=len(ALL_YEARS) - 1, key="ey")

if sy > ey:
    st.error("시작 연도가 종료 연도보다 큽니다.")
    st.stop()

df_psc = df_presc[df_presc["YEAR"].isin(range(sy, ey + 1))].copy() if not df_presc.empty else df_presc
df_mnu = df_manu[df_manu["YEAR"].isin(range(sy, ey + 1))].copy() if not df_manu.empty else df_manu

st.markdown("---")

# ── KPI ──────────────────────────────────────────────────
if not df_presc.empty:
    df_sum = df_presc[df_presc["MEDC_INST_CLSFY_NM"] == "합계"]
    k1, k2, k3, k4 = st.columns(4)
    for k_col, col_nm, label, icon, unit in [
        (k1, "PRSC_INST_NUM", "처방 기관 수",  "🏥",      "개"),
        (k2, "PRSC_DOCT_NUM", "처방 의사 수",  "👨‍⚕️",   "명"),
        (k3, "PRSC_CNT",      "처방 건수",     "📋",      "건"),
        (k4, "PRSC_PATNT_NUM","처방 환자 수",  "🧑‍🤝‍🧑", "명"),
    ]:
        val, pct, yr = yoy_metric(df_sum.groupby("YEAR")[col_nm].sum())
        if val is not None:
            k_col.metric(
                f"{icon} {label} ({yr})",
                f"{int(val):,}{unit}",
                delta=f"{pct:+.1f}% 전년 대비" if pct is not None else None,
            )

spacer(3)

# ── SECTION 1 — 종별 처방 현황 ───────────────────────────
st.subheader("종별 의료용 마약류 처방 현황")
spacer(1)

if not df_psc.empty:
    df_detail     = df_psc[df_psc["MEDC_INST_CLSFY_NM"] != "합계"].copy()
    latest_yr_sel = df_psc["YEAR"].max()
    col_rank, col_yoy = st.columns([2, 3])

    with col_rank:
        st.markdown(f"**기관별 처방 순위 ({latest_yr_sel}년)**")
        st.dataframe(
            build_rank_table(df_detail, latest_yr_sel),
            use_container_width=True,
            height=560,
            column_config={
                "처방 건수 (%)": st.column_config.ProgressColumn("처방 건수 (%)", min_value=0, max_value=100, format="%.1f%%"),
                "기관 수 (%)":   st.column_config.ProgressColumn("기관 수 (%)",   min_value=0, max_value=100, format="%.1f%%"),
                "의사 수 (%)":   st.column_config.ProgressColumn("의사 수 (%)",   min_value=0, max_value=100, format="%.1f%%"),
            },
        )

    with col_yoy:
        st.markdown(
            tip("연도별 YoY (%)", "YoY(Year Over Year): 전년도 대비 증감율\n초록=전년 대비 증가 / 빨강=감소"),
            unsafe_allow_html=True,
        )
        fig_yoy = build_yoy_heatmap(df_detail)
        if fig_yoy:
            st.plotly_chart(fig_yoy, width="stretch")
        else:
            st.info("연도가 2개 이상이어야 YoY 계산이 가능합니다.")

spacer(3)

# ── SECTION 2 — 버블 + 갭 ────────────────────────────────
if not df_psc.empty:
    bubble_yr = df_psc["YEAR"].max()
    df_lat = (
        df_psc[(df_psc["YEAR"] == bubble_yr) & (df_psc["MEDC_INST_CLSFY_NM"] != "합계")]
        .groupby("MEDC_INST_CLSFY_NM")[["PRSC_CNT", "PRSC_INST_NUM"]]
        .sum().reset_index()
    )
    df_lat["처방량 비중(%)"] = (df_lat["PRSC_CNT"]      / df_lat["PRSC_CNT"].sum()      * 100).round(2)
    df_lat["기관 수 비중(%)"] = (df_lat["PRSC_INST_NUM"] / df_lat["PRSC_INST_NUM"].sum() * 100).round(2)
    df_lat["집중도 갭(%p)"]  = (df_lat["처방량 비중(%)"] - df_lat["기관 수 비중(%)"]).round(1)
    qty_log = np.log1p(df_lat["PRSC_CNT"])
    df_lat["size_norm"] = 8 + 47 * (qty_log - qty_log.min()) / (qty_log.max() - qty_log.min() + 1e-9)
    df_lat["x_plot"] = df_lat["기관 수 비중(%)"].clip(lower=0.05)
    df_lat["y_plot"] = df_lat["처방량 비중(%)"].clip(lower=0.05)

    col_bubble, col_gap = st.columns([3, 2.5])
    with col_bubble:
        st.markdown(f"**처방량 비중 vs 처방 기관 수 비중 ({bubble_yr}년)**")
        st.plotly_chart(build_bubble_chart(df_lat), width="stretch")
    with col_gap:
        st.markdown(tip("집중도 갭 순위", "집중도 = 처방량 비중 − 기관 수 비중"), unsafe_allow_html=True)
        st.plotly_chart(build_gap_chart(df_lat), width="stretch")

spacer(3)

# ── SECTION 3 — 제조·수입·수출 ──────────────────────────
st.markdown("---")
st.subheader("마약류 의약품 제조·수입·수출 품목 현황")
spacer(1)

if not df_manu.empty:
    mk1, mk2, mk3, mk4 = st.columns(4)
    for mk_col, rpt_type, val_col, label, icon, unit in [
        (mk1, "수입", "PRDLST_NUM", "수입 품목 수", "📥", "개"),
        (mk2, "수출", "PRDLST_NUM", "수출 품목 수", "📤", "개"),
        (mk3, "수입", "ENTP_NUM",   "수입 업체 수", "🏭", "개사"),
        (mk4, "수출", "ENTP_NUM",   "수출 업체 수", "🏭", "개사"),
    ]:
        ser = (
            df_manu[(df_manu["RPT_TYPE_NM"] == rpt_type) & (df_manu["NARK_DIVS_NM"] == "합계")]
            .groupby("YEAR")[val_col].sum()
        )
        val, pct, yr = yoy_metric(ser)
        if val is not None:
            mk_col.metric(
                f"{icon} {label} ({yr})",
                f"{int(val):,}{unit}",
                delta=f"{pct:+.1f}% 전년 대비" if pct is not None else None,
            )
    spacer(2)

if not df_mnu.empty:
    col_rank, col_dep = st.columns([1, 2])

    with col_rank:
        latest_manu_yr = df_mnu["YEAR"].max()
        st.markdown(f"**품목 수 순위 ({latest_manu_yr}년)**")

        df_rank_manu = (
            df_mnu[(df_mnu["YEAR"] == latest_manu_yr) & (df_mnu["NARK_DIVS_NM"] == "합계")]
            .groupby("RPT_TYPE_NM")["PRDLST_NUM"].sum().reset_index()
        )
        df_rank_manu = (
            df_rank_manu[df_rank_manu["RPT_TYPE_NM"].isin(["제조", "수입", "수출"])]
            .sort_values("PRDLST_NUM", ascending=False).reset_index(drop=True)
        )
        df_prev_manu = (
            df_mnu[(df_mnu["YEAR"] == latest_manu_yr - 1) & (df_mnu["NARK_DIVS_NM"] == "합계")]
            .groupby("RPT_TYPE_NM")["PRDLST_NUM"].sum()
        )

        cards_html = '<div style="border-radius:8px;overflow:hidden;border:1px solid #e0e0e0;">'
        for i, row in df_rank_manu.iterrows():
            name, value = row["RPT_TYPE_NM"], int(row["PRDLST_NUM"])
            divider  = "border-top:1px solid #e0e0e0;" if i > 0 else ""
            yoy_html = ""
            if name in df_prev_manu.index and df_prev_manu[name] > 0:
                chg = (value - df_prev_manu[name]) / df_prev_manu[name] * 100
                color, arrow = ("#4CAF50", "▲") if chg >= 0 else ("#F44336", "▼")
                yoy_html = (
                    f'<div style="font-size:13px;color:{color};margin-top:4px;">'
                    f'{arrow} {abs(chg):.1f}% 전년 대비</div>'
                )
            cards_html += (
                f'<div style="{divider}background:#f8f9fa;padding:14px 18px;">'
                f'<div style="color:#888;font-size:12px;font-weight:600;">{i+1}위</div>'
                f'<div style="font-size:17px;font-weight:bold;margin:3px 0;">{name}</div>'
                f'<div style="font-size:22px;font-weight:bold;color:#333;">{value:,}개</div>'
                + yoy_html + '</div>'
            )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

    with col_dep:
        st.markdown(
            tip("해외 의존도", "수출 품목 수 ÷ 수입 품목 수 × 100\n높을수록 수입된 품목 중 수출로 이어지는 비중이 크며,\n낮을수록 수입 의존도가 높음을 의미합니다."),
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_dependency_chart(df_mnu), width="stretch")

    spacer(2)
    st.markdown("**마약류 구분별 품목 수**")
    st.markdown(
        '<p style="color:#aaa;font-size:13px;margin-top:-8px;">'
        '마약 = 마약류관리에관한법률상 마약 &nbsp;/&nbsp; 향정 = 향정신성의약품</p>',
        unsafe_allow_html=True,
    )
    col_imp_bar, col_exp_bar = st.columns(2)
    for col_w, rpt_type, title in [
        (col_imp_bar, "수입", "수입 기준"),
        (col_exp_bar, "수출", "수출 기준"),
    ]:
        with col_w:
            st.markdown(f"**{title}**")
            st.plotly_chart(build_divs_bar(df_mnu, rpt_type), width="stretch")

spacer(2)

# ── 원본 데이터 ──────────────────────────────────────────
with st.expander("원본 데이터 보기"):
    t1, t2 = st.tabs(["처방현황", "제조·수출입"])
    with t1:
        st.dataframe(df_presc, use_container_width=True, height=300)
    with t2:
        st.dataframe(df_manu, use_container_width=True, height=300)
