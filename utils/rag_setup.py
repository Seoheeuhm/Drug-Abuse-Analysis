"""
청소년 약물 오남용 RAG 시스템
URL 크롤링 + 로컬 문서(PDF, TXT) 통합 로드 + Chroma 벡터 DB
"""

import os
import bs4
import streamlit as st
from langchain_community.document_loaders import WebBaseLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ==========================================
# 0. 경로 및 환경 설정 (상황에 맞게 수정)
# ==========================================
DATA_DIR = "./data/raw"
DB_DIR = "./vector_db"      

# 청소년 약물 오남용 관련 정부/공공기관 URL 목록
DOCUMENT_URLS = [
    "https://www.mfds.go.kr/brd/m_99/view.do?seq=48089",
    "https://www.mohw.go.kr/board.es?mid=a10411010200&bid=0019",
    "https://ko.wikipedia.org/wiki/약물_남용",
    "https://ko.wikipedia.org/wiki/덱스트로메토르판"
]


def load_local_documents(directory):
    """로컬 폴더에서 TXT 및 PDF 문서를 로드"""
    documents = []
    if not os.path.exists(directory):
        print(f"⚠️ 경고: {directory} 경로를 찾을 수 없습니다. 로컬 문서 로드를 건너뜁니다.")
        return documents

    print(f"로컬 폴더 데이터 로드 시작: {directory}")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if filename.endswith('.txt'):
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
                print(f"  ✅ Loaded Text: {filename}")
            except Exception as e:
                print(f"  ❌ Error loading {filename}: {e}")
                
        elif filename.endswith('.pdf'):
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"  ✅ Loaded PDF: {filename}")
            except Exception as e:
                print(f"  ❌ Error loading {filename}: {e}")
                
    return documents


def create_vectordb():
    """
    URL 크롤링 데이터와 로컬 문서를 통합하여 Chroma 벡터 DB 생성
    """
    print("\n" + "="*60)
    print("청소년 약물 오남용 RAG 시스템 구축 시작")
    print("="*60 + "\n")

    all_docs = []

    # 1. URL 크롤링 진행
    print(f"총 {len(DOCUMENT_URLS)}개 URL 크롤링 시작...\n")
    success_count = 0
    fail_count = 0

    for i, url in enumerate(DOCUMENT_URLS, 1):
        try:
            print(f"[{i}/{len(DOCUMENT_URLS)}] 크롤링 중: {url}")
            loader = WebBaseLoader(
                url,
                bs_kwargs={"parse_only": bs4.SoupStrainer(["article", "p", "div", "main"])}
            )
            docs = loader.load()

            if docs and len(docs[0].page_content) > 100:
                all_docs.extend(docs)
                success_count += 1
                print(f"    ✅ 성공: {len(docs[0].page_content)}자 추출\n")
            else:
                fail_count += 1
                print(f"    ⚠️ 내용 부족, 스킵\n")
        except Exception as e:
            fail_count += 1
            print(f"    ❌ 실패: {str(e)[:50]}\n")

    print(f"🌐 URL 크롤링 완료: 성공 {success_count}개, 실패 {fail_count}개\n")

    # 2. 로컬 문서(PDF, TXT) 로드 진행
    local_docs = load_local_documents(DATA_DIR)
    all_docs.extend(local_docs)
    print(f"📁 로컬 문서 로드 완료: {len(local_docs)}개 페이지/파일 추가됨")
    print(f"📊 총 수집된 원본 문서 개수: {len(all_docs)}\n")

    if len(all_docs) == 0:
        print("⚠️ 경고: 수집된 문서가 하나도 없습니다! 프로그램을 종료합니다.")
        return None

    # 3. 텍스트 청크 분할 (Text Splitting)
    print("문서 청크 분할 중...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=650,        # 첫 번째 코드(800)와 두 번째 코드(500)의 절충안
        chunk_overlap=100,      # 중첩 영역 지정
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(all_docs)
    print(f"✅ {len(chunks)}개 청크 생성 완료\n")

    # 4. 고성능 한국어 임베딩 모델 초기화 (bge-m3)
    print("한국어 임베딩 모델 로딩 중 (BAAI/bge-m3)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'},  # GPU 환경이라면 'cuda'로 변경 가능
        encode_kwargs={'normalize_embeddings': True}
    )
    print("✅ 임베딩 모델 로드 완료\n")

    # 5. Chroma 벡터 DB 생성 및 로컬 저장
    print(f"벡터 DB 생성 및 로컬 저장 중... 경로: {DB_DIR}")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    print("\n" + "="*60)
    print("🎉 RAG 시스템 벡터 DB 구축 완료!")
    print("="*60)

    return vectordb


@st.cache_resource
def load_vectordb():
    """
    저장된 Chroma 벡터 DB 로드 (Streamlit 캐싱 적용)
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )


def search_docs(query, k=3):
    """
    질문과 유사한 문서 검색 후 컨텍스트 반환
    """
    try:
        vectordb = load_vectordb()
        docs = vectordb.similarity_search(query, k=k)

        if docs:
            context = "\n\n".join([
                f"[문서 {i+1}]\n{doc.page_content[:500]}..."
                for i, doc in enumerate(docs)
            ])
            return context
        else:
            return None

    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return None


# 스크립트 직접 실행 시에만 DB 구축 작동
if __name__ == "__main__":
    create_vectordb()