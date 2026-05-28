"""
3_Interactive_Analysis.py - RAG + Claude API 하이브리드 대화형 분석
"""

import streamlit as st
from anthropic import Anthropic
import os
from utils.rag_setup import search_docs

st.set_page_config(
    page_title="청소년 마약류 오남용 분석",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("청소년 약물 오남용 AI 분석")
st.markdown("궁금한 내용을 자유롭게 질문하세요")

# API 키
api_key = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("API 키 없음")
    st.stop()

WELCOME_MSG = {
    "role": "assistant",
    "content": (
        "안녕하세요! 저는 청소년 약물 오남용 예방을 위한 AI 분석 챗봇입니다.\n\n"
        "공공기관 데이터와 AI를 결합해 약물·마약류·의약품 관련 질문에 답변드립니다. "
        "아래 예시 질문을 눌러보거나, 직접 궁금한 내용을 입력해보세요."
    ),
    "source": "system",
}

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [WELCOME_MSG]
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# 대화 히스토리 표시
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("source") == "rag":
                st.caption("📄 RAG 문서 기반 답변 — 크롤링된 공공기관 데이터를 참고했습니다.")
            elif msg.get("source") == "claude":
                st.caption("🤖 Claude AI 지식 기반 답변 — DB에서 관련 문서를 찾지 못해 AI가 직접 답변했습니다.")

            if msg.get("suggestions"):
                st.markdown("**💡 이런 것도 궁금하세요?**")
                s_cols = st.columns(len(msg["suggestions"]))
                for i, sq in enumerate(msg["suggestions"]):
                    if s_cols[i].button(sq, key=f"hist_{idx}_{i}", use_container_width=True):
                        st.session_state.pending_question = sq
                        st.rerun()

# 실제 대화 여부 (환영 메시지 제외)
real_messages = [m for m in st.session_state.messages if m.get("source") != "system"]

# 예시 질문 버튼 (실제 대화가 없을 때만 표시)
if not real_messages and not st.session_state.pending_question:
    st.markdown("**💡 이런 질문을 해보세요**")
    example_questions = [
        "DXM(덱스트로메토르판)이란?",
        "코데인 부작용은?",
        "청소년 마약 예방 방법",
        "의료용 마약류 종류",
        "약물 중독 치료 방법",
        "향정신성의약품이란?",
    ]
    cols = st.columns(3)
    for i, q in enumerate(example_questions):
        if cols[i % 3].button(q, key=f"ex_{i}", use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()
    st.markdown("---")

# 사용자 입력
chat_input = st.chat_input("질문을 입력하세요")
user_input = chat_input or st.session_state.pending_question
if st.session_state.pending_question:
    st.session_state.pending_question = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            # 1단계: RAG 검색
            with st.spinner("🔍 관련 문서 검색 중..."):
                search_result = search_docs(user_input, k=3)
                client = Anthropic(api_key=api_key, timeout=60.0)

                if search_result:
                    prompt = f"""당신은 청소년 약물 오남용 예방 전문 챗봇입니다.

[참고 문서]
{search_result}

[질문]
{user_input}

[답변 지침]
- 참고 문서에 질문과 관련된 실제 내용(설명, 수치, 사례)이 있으면 → 그 내용을 우선 활용하여 답변
- 참고 문서가 웹사이트 메뉴·네비게이션·각주·법적 분류표 등 실질적 정보가 없으면 → 문서를 무시하고 전문 지식으로 직접 상세하게 답변
- "데이터에 정보가 없습니다"라는 식의 답변은 절대 하지 말 것
- 약물·마약·의약품 관련 질문이면 항상 유용한 답변을 제공할 것
- 청소년이 이해하기 쉽게 설명할 것

답변 맨 마지막 줄에 반드시 다음 중 하나만 출력하세요 (다른 텍스트 없이):
참고 문서를 실제로 활용했으면 → ##SOURCE:RAG##
참고 문서를 무시하고 자체 지식으로 답변했으면 → ##SOURCE:AI##"""
                else:
                    prompt = f"""당신은 청소년 약물 오남용 예방 전문 챗봇입니다.

질문: {user_input}

아래 기준으로 응답하세요:
- 약물·마약·의약품·중독·오남용·예방·치료·부작용 등 약물과 조금이라도 관련된 질문 → 전문 지식으로 상세하고 정확하게 답변
- 날씨·요리·스포츠 등 약물과 전혀 무관한 질문 → "죄송하지만, 약물 오남용 관련 질문만 답변드립니다." 한 문장만 출력

약물 관련 질문이라면 데이터베이스에 없는 내용이라도 반드시 답변하세요."""

            # 2단계: 스트리밍 응답
            placeholder = st.empty()
            full_text = ""
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    display = full_text.replace("##SOURCE:RAG##", "").replace("##SOURCE:AI##", "").rstrip()
                    placeholder.markdown(display)

            # 출처 마커 파싱
            if "##SOURCE:RAG##" in full_text:
                source = "rag"
            elif "##SOURCE:AI##" in full_text:
                source = "claude"
            else:
                source = "rag" if search_result else "claude"
            answer = full_text.replace("##SOURCE:RAG##", "").replace("##SOURCE:AI##", "").rstrip()
            placeholder.markdown(answer)

            if source == "rag":
                st.caption("📄 RAG 문서 기반 답변 — 크롤링된 공공기관 데이터를 참고했습니다.")
            else:
                st.caption("🤖 Claude AI 지식 기반 답변")

            # 3단계: 관련 질문 추천
            suggestions = []
            with st.spinner(""):
                sugg_resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    messages=[{"role": "user", "content": (
                        f'질문 "{user_input}"과 관련된 청소년 약물 오남용 주제의 후속 질문 3개를 생성하세요. '
                        '각 질문을 줄바꿈으로 구분하고, 번호나 기호 없이 질문만 출력하세요.'
                    )}],
                )
                suggestions = [
                    s.strip() for s in sugg_resp.content[0].text.strip().split("\n")
                    if s.strip()
                ][:3]

            if suggestions:
                st.markdown("**💡 이런 것도 궁금하세요?**")
                s_cols = st.columns(len(suggestions))
                for i, sq in enumerate(suggestions):
                    if s_cols[i].button(sq, key=f"sugg_{len(st.session_state.messages)}_{i}", use_container_width=True):
                        st.session_state.pending_question = sq
                        st.rerun()

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "source": source,
                "suggestions": suggestions,
            })

        except Exception as e:
            st.error(f"에러: {e}")

# 사이드바
with st.sidebar:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] [data-testid="stMetric"] {
        text-align: center;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"],
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    st.header("📊 대화 통계")

    user_count = sum(1 for m in st.session_state.messages if m["role"] == "user")
    rag_count = sum(1 for m in st.session_state.messages if m.get("source") == "rag")
    ai_count = sum(1 for m in st.session_state.messages if m.get("source") == "claude")

    col1, col2 = st.columns(2)
    col1.metric("총 질문 수", user_count)
    col2.metric("총 답변 수", user_count)

    if user_count > 0:
        st.markdown("**답변 출처 비율**")
        rag_pct = int(rag_count / user_count * 100)
        ai_pct = int(ai_count / user_count * 100)
        st.progress(rag_pct / 100, text=f"📄 문서 검색 기반: {rag_count}건 ({rag_pct}%)")
        st.progress(ai_pct / 100, text=f"🤖 AI 자체 답변: {ai_count}건 ({ai_pct}%)")

    st.divider()
    st.header("📚 DB 현황")
    st.markdown("""
- **총 청크 수**: 약 425개
- **주요 출처**:
  - 식품의약품안전처
  - 보건복지부
  - 위키백과 (약물 남용)
  - 위키백과 (덱스트로메토르판)
  - 로컬 문서 (PDF/TXT)
""")

    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = [WELCOME_MSG]
        st.rerun()
