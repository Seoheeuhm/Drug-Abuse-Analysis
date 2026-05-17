"""
modules/hospital/charts.py
"""
import math

import numpy as np
import pandas as pd
import plotly.express as px


def build_rank_table(df_detail: pd.DataFrame, latest_yr: int) -> pd.DataFrame:
    rank_raw = (
        df_detail[df_detail["YEAR"] == latest_yr]
        .groupby("MEDC_INST_CLSFY_NM")[["PRSC_CNT", "PRSC_INST_NUM", "PRSC_DOCT_NUM"]]
        .sum()
        .reset_index()
        .sort_values("PRSC_CNT", ascending=False)
        .reset_index(drop=True)
    )
    rank_raw.index += 1
    return pd.DataFrame({
        "기관 종별":     rank_raw["MEDC_INST_CLSFY_NM"],
        "처방 건수 (%)": (rank_raw["PRSC_CNT"]      / rank_raw["PRSC_CNT"].sum()      * 100).round(1),
        "기관 수 (%)":   (rank_raw["PRSC_INST_NUM"] / rank_raw["PRSC_INST_NUM"].sum() * 100).round(1),
        "의사 수 (%)":   (rank_raw["PRSC_DOCT_NUM"] / rank_raw["PRSC_DOCT_NUM"].sum() * 100).round(1),
    })


def build_yoy_heatmap(df_detail: pd.DataFrame):
    pivot = (
        df_detail.groupby(["YEAR", "MEDC_INST_CLSFY_NM"])["PRSC_CNT"]
        .sum()
        .unstack("MEDC_INST_CLSFY_NM")
        .sort_index()
    )
    yoy = (pivot.pct_change() * 100).dropna(how="all").round(1)
    if yoy.empty:
        return None
    fig = px.imshow(
        yoy.T,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".1f",
        aspect="auto",
        labels={"x": "연도", "y": "기관 종별", "color": "YoY(%)"},
    )
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title="YoY(%)", ticksuffix="%"),
    )
    return fig


def build_bubble_chart(df_lat: pd.DataFrame, bubble_yr: int):
    fig = px.scatter(
        df_lat,
        x="x_plot",
        y="y_plot",
        size="size_norm",
        color="MEDC_INST_CLSFY_NM",
        text="MEDC_INST_CLSFY_NM",
        size_max=55,
        color_discrete_sequence=px.colors.qualitative.Set2,
        hover_data={
            "처방량 비중(%)": ":.1f",
            "기관 수 비중(%)": ":.1f",
            "x_plot": False,
            "y_plot": False,
            "size_norm": False,
            "PRSC_CNT": ":,",
            "MEDC_INST_CLSFY_NM": False,
        },
        labels={
            "x_plot": "기관 수 비중 (%)",
            "y_plot": "처방량 비중 (%)",
            "MEDC_INST_CLSFY_NM": "기관 종별",
            "PRSC_CNT": "처방 건수",
        },
    )

    ax_min   = float(df_lat[["x_plot", "y_plot"]].min().min()) * 0.7
    ax_max   = float(df_lat[["x_plot", "y_plot"]].max().max()) * 1.5
    log_min  = math.log10(max(ax_min, 1e-3))
    log_max  = math.log10(ax_max)
    ann_pos  = 10 ** ((log_min + log_max) / 2)

    # add_shape 대신 scatter trace로 대각선 추가 (log축 auto-range 왜곡 방지)
    fig.add_scatter(
        x=[ax_min, ax_max], y=[ax_min, ax_max],
        mode="lines",
        line=dict(color="#9E9E9E", width=1.2, dash="dot"),
        showlegend=False, hoverinfo="skip",
    )
    fig.add_annotation(
        x=ann_pos, y=ann_pos * 1.4,
        text="처방량 = 기관 수 비중",
        showarrow=False,
        font=dict(size=10, color="#9E9E9E"),
        xref="x", yref="y",
    )
    fig.update_traces(
        textposition="top center",
        marker=dict(opacity=0.8, line=dict(width=1.5, color="white")),
        cliponaxis=False,
    )
    fig.update_xaxes(type="log", title="기관 수 비중 (%)", range=[log_min, log_max + 0.5])
    fig.update_yaxes(type="log", title="처방량 비중 (%)", range=[log_min, log_max + 0.5])
    fig.update_layout(
        height=520,
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        margin=dict(l=0, r=30, t=40, b=100),
    )
    return fig


def build_gap_chart(df_lat: pd.DataFrame):
    df_gap = (
        df_lat[["MEDC_INST_CLSFY_NM", "집중도 갭(%p)"]]
        .sort_values("집중도 갭(%p)", ascending=False)
    )
    fig = px.bar(
        df_gap,
        x="집중도 갭(%p)",
        y="MEDC_INST_CLSFY_NM",
        orientation="h",
        color="집중도 갭(%p)",
        color_continuous_scale=["#EF5350", "#EEEEEE", "#42A5F5"],
        color_continuous_midpoint=0,
        text=df_gap["집중도 갭(%p)"].apply(lambda x: f"{x:+.1f}%p"),
        labels={"집중도 갭(%p)": "갭(%p)", "MEDC_INST_CLSFY_NM": ""},
    )
    fig.update_traces(textposition="auto", cliponaxis=False, insidetextanchor="end")
    fig.update_layout(
        height=520,
        coloraxis_showscale=False,
        margin=dict(l=100, r=120, t=10, b=0),
    )
    return fig


def build_dependency_chart(df_mnu: pd.DataFrame):
    imp_s = (
        df_mnu[(df_mnu["RPT_TYPE_NM"] == "수입") & (df_mnu["NARK_DIVS_NM"] == "합계")]
        .groupby("YEAR")["PRDLST_NUM"].sum()
    )
    exp_s = (
        df_mnu[(df_mnu["RPT_TYPE_NM"] == "수출") & (df_mnu["NARK_DIVS_NM"] == "합계")]
        .groupby("YEAR")["PRDLST_NUM"].sum()
    )
    ratio = (exp_s / imp_s * 100).dropna().reset_index()
    ratio.columns = ["YEAR", "RATIO"]
    ratio["text"] = ratio["RATIO"].apply(lambda x: f"{x:.1f}%")

    fig = px.line(ratio, x="YEAR", y="RATIO", text="text", markers=True)
    fig.update_traces(
        line=dict(color="#7E57C2", width=2.5),
        marker=dict(size=9),
        textposition="top center",
        textfont=dict(size=12),
    )
    fig.update_layout(
        height=400,
        xaxis=dict(type="category", title="연도"),
        yaxis=dict(title="수출/수입 비율 (%)", ticksuffix="%"),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def build_divs_bar(df_mnu: pd.DataFrame, rpt_type: str):
    divs_color = {"마약": "#EF5350", "향정": "#7E57C2"}
    df_bar = (
        df_mnu[
            (df_mnu["RPT_TYPE_NM"] == rpt_type) &
            (df_mnu["NARK_DIVS_NM"] != "합계")
        ]
        .groupby(["YEAR", "NARK_DIVS_NM"])["PRDLST_NUM"]
        .sum()
        .reset_index()
    )
    fig = px.bar(
        df_bar,
        x="YEAR", y="PRDLST_NUM", color="NARK_DIVS_NM",
        barmode="stack",
        color_discrete_map=divs_color,
        text_auto=True,
        labels={"YEAR": "연도", "PRDLST_NUM": "품목 수", "NARK_DIVS_NM": "마약류 구분"},
    )
    fig.update_layout(
        height=360,
        xaxis=dict(tickmode="linear", dtick=1, title="연도"),
        yaxis=dict(title="품목 수"),
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right"),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig
