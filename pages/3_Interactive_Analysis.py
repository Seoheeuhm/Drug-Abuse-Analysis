"""
3_대화형분석.py - Claude AI 기반 대화형 데이터 분석 페이지
담당: 주현, 서희
"""

# TODO: Claude API 연동 및 RAG 구현 검토

import streamlit as st
import anthropic
import sys
import os

# utils 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_all_data

# 페이지 설정
st.set_page_config(page_title="대화형 분석", page_icon="💬", layout="wide")

st.title("💬 대화형 데이터 분석")
st.markdown("청소년 마약류 의약품 과다복용 관련 데이터를 AI에게 자유롭게 질문하세요.")
st.markdown("---")

# ── 데이터 로드 ──────────────────────────────────────────────────
# 전체 데이터를 불러와 AI 컨텍스트로 활용
df_all = load_all_data()

# 사이드바: 데이터 미리보기
with st.sidebar:
    st.subheader("📂 로드된 데이터 미리보기")
    st.dataframe(df_all.head(10), use_container_width=True)
    st.caption(f"총 {len(df_all)}행 로드됨")

    st.markdown("---")
    st.subheader("💡 질문 예시")
    examples = [
        "처방량이 가장 많은 성분은 무엇인가요?",
        "약국 수 증가 추세를 분석해주세요.",
        "청소년 OD 위험이 높은 성분은 무엇인가요?",
        "수입량과 처방량의 관계를 설명해주세요.",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            # 예시 질문을 채팅 입력에 반영
            st.session_state["pending_input"] = ex

# ── 대화 히스토리 초기화 ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 이전 대화 메시지 렌더링 ──────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 사용자 입력 처리 ─────────────────────────────────────────────
# 사이드바 예시 버튼으로 입력된 경우 처리
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("데이터에 대해 질문해보세요...") or pending

if user_input:
    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # ── Claude API 호출 ───────────────────────────────────────────
    # TODO: RAG 구현 - 벡터 DB 연동으로 더 정확한 데이터 검색 추가 검토
    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            try:
                # API 키는 Streamlit secrets에서 로드 (.streamlit/secrets.toml)
                api_key = st.secrets["ANTHROPIC_API_KEY"]
                client = anthropic.Anthropic(api_key=api_key)

                # 데이터를 문자열로 변환하여 시스템 컨텍스트에 포함
                data_context = df_all.to_string(index=False)

                # 시스템 프롬프트: AI 역할 및 데이터 컨텍스트 설정
                system_prompt = f"""당신은 청소년 마약류 의약품 과다복용(OD) 문제를 분석하는 전문 데이터 분석가입니다.
아래 데이터를 기반으로 사용자의 질문에 한국어로 답변하세요.
데이터 분석 결과를 명확하고 이해하기 쉽게 설명하고, 정책적 시사점도 함께 제시하세요.

=== 현재 로드된 데이터 ===
{data_context}
========================
"""
                # 대화 히스토리를 포함한 메시지 구성
                # TODO: 토큰 한도 초과 시 히스토리 요약 또는 슬라이딩 윈도우 적용 검토
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                )

                assistant_reply = response.content[0].text
                st.markdown(assistant_reply)

                # 응답 저장
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_reply}
                )

            except KeyError:
                # API 키 미설정 안내
                st.error(
                    "⚠️ API 키가 설정되지 않았습니다.\n\n"
                    "`.streamlit/secrets.toml` 파일에 아래 내용을 추가하세요:\n"
                    "```toml\nANTHROPIC_API_KEY = 'your_api_key_here'\n```"
                )
            except anthropic.APIError as e:
                st.error(f"⚠️ API 호출 오류: {e}")

# ── 대화 초기화 버튼 ─────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑 대화 초기화", type="secondary"):
        st.session_state.messages = []
        st.rerun()
