"""
벡터 DB 생성 스크립트
한 번만 실행하면 됨
"""

from utils.rag_setup import create_vectordb

if __name__ == "__main__":
    print("벡터 DB 생성을 시작합니다...\n")
    vectordb = create_vectordb()

    if vectordb:
        print("\n✅ 성공! 이제 Streamlit 앱을 실행할 수 있습니다.")
        print("실행 명령어: streamlit run Home.py")
    else:
        print("\n❌ 실패! URL 연결을 확인하세요.")
