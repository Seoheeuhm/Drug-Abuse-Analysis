"""
3_Interactive_Analysis.py - RAG + Claude API 하이브리드 대화형 분석
"""

import streamlit as st
from anthropic import Anthropic
import httpx
import os
from utils.rag_setup import search_docs

st.title("💬 대화형 데이터 분석")
st.markdown("청소년 약물 오남용에 대해 질문하세요")

# API 키
api_key = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("API 키 없음")
    st.stop()

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 히스토리 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("source") == "rag":
                st.caption("📄 RAG 문서 기반 답변 — 크롤링된 공공기관 데이터를 참고했습니다.")
            elif msg.get("source") == "claude":
                st.caption("🤖 Claude AI 지식 기반 답변 — DB에서 관련 문서를 찾지 못해 AI가 직접 답변했습니다.")

# 사용자 입력
if user_input := st.chat_input("질문 입력"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🔍 검색 및 분석 중..."):
            try:
                # 1단계: RAG 검색
                search_result = search_docs(user_input, k=3)

                client = Anthropic(api_key=api_key, timeout=30.0)

                if search_result:
                    # 2-A: 검색 결과 있음 → 문서 활용 여부를 Claude가 직접 판단 후 출처 표기
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
                    # 2-B: 검색 결과 없음 → 약물 관련이면 Claude 지식으로 답변, 무관하면 거절
                    prompt = f"""당신은 청소년 약물 오남용 예방 전문 챗봇입니다.

질문: {user_input}

아래 기준으로 응답하세요:
- 약물·마약·의약품·중독·오남용·예방·치료·부작용 등 약물과 조금이라도 관련된 질문 → 전문 지식으로 상세하고 정확하게 답변
- 날씨·요리·스포츠 등 약물과 전혀 무관한 질문 → "죄송하지만, 약물 오남용 관련 질문만 답변드립니다." 한 문장만 출력

약물 관련 질문이라면 데이터베이스에 없는 내용이라도 반드시 답변하세요."""

                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )

                raw_answer = response.content[0].text

                # 출처 마커 파싱 후 본문에서 제거
                if "##SOURCE:RAG##" in raw_answer:
                    source = "rag"
                    answer = raw_answer.replace("##SOURCE:RAG##", "").rstrip()
                elif "##SOURCE:AI##" in raw_answer:
                    source = "claude"
                    answer = raw_answer.replace("##SOURCE:AI##", "").rstrip()
                else:
                    source = "rag" if search_result else "claude"
                    answer = raw_answer

                st.write(answer)
                if source == "rag":
                    st.caption("📄 RAG 문서 기반 답변 — 크롤링된 공공기관 데이터를 참고했습니다.")
                else:
                    st.caption("🤖 Claude AI 지식 기반 답변")

                st.session_state.messages.append({"role": "assistant", "content": answer, "source": source})

            except Exception as e:
                st.error(f"에러: {e}")

# 사이드바
with st.sidebar:
    st.header("📊 상태")
    st.write(f"대화 수: {len(st.session_state.messages)}")

    if st.button("🔄 초기화"):
        st.session_state.messages = []
        st.rerun()
