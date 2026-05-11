# Drug-Abuse-Analysis

## 📌 프로젝트 소개
청소년 마약류 의약품 과다복용(OD) 문제 분석 대시보드

### 문제 정의
감기약, 해열진통제, 수면유도제 등을 과다복용해 환각을 경험하려는 OD(OverDose) 행위가 청소년 사이에서 확산되고 있습니다.

### 해결 방안
의약품 처방 현황, 의료기관 분포, 수입/수출 데이터를 통합 분석하여 문제의 실태를 파악하고 정책적 시사점을 도출합니다.

## 🛠 기술 스택
- **Frontend**: Streamlit
- **Data Analysis**: Pandas, Plotly
- **AI**: Anthropic Claude API
- **Data Source**: 공공데이터포털 Open API

## 👥 역할 분담
- **처방 현황 분석** (지선): 성분 비율, 효능, 부작용 분석
- **의료기관 현황** (시은): 약국 분포, 수입/수출 실적 추세
- **대화형 분석** (주현, 서희): Claude API 기반 자연어 질의응답

## 🚀 실행 방법

### 1. 클론
```bash
git clone https://github.com/Seoheeuhm/Drug-Abuse-Analysis.git
cd Drug-Abuse-Analysis
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

### 4. Streamlit secrets 설정 (대화형 분석 사용 시)
```bash
mkdir -p .streamlit
# .streamlit/secrets.toml 파일 생성 후 아래 내용 입력
# ANTHROPIC_API_KEY = "your_api_key_here"
```

### 5. 실행
```bash
streamlit run Home.py
```

## 📊 데이터 출처
- [식품의약품안전처 오픈API](https://data.mfds.go.kr/)
- [공공데이터포털 - 약국현황](https://www.data.go.kr/data/15139163/openapi.do)
- [공공데이터포털 - 수입실적](https://www.data.go.kr/data/15136552/openapi.do)
- [공공데이터포털 - 수출실적](https://www.data.go.kr/data/15136564/openapi.do)

## 📝 License
MIT License
