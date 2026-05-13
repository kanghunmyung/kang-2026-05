# 주식 티커 분석기

Streamlit으로 만든 **주식 티커 분석 앱**입니다.  
한국 종목명 선택 또는 미국 주식 티커 입력으로 가격 추이, 이동평균선(MA20·MA60·MA200), RSI, 수익률, 거래량, 기업 정보를 확인하고 **Gemini AI 딥 다이브 리포트**를 생성할 수 있습니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 한국 종목 검색 | 100개 이상의 KOSPI·KOSDAQ 종목을 이름으로 검색·선택 |
| 미국 주식 지원 | AAPL, TSLA, MSFT 등 미국 티커 직접 입력 |
| 6자리 코드 자동 변환 | 종목코드 입력 시 KOSPI/KOSDAQ 자동 판별 |
| 이동평균선 | MA20 / MA60 / MA200 선택 표시 |
| RSI(14) | 과매수·과매도 모멘텀 지표 |
| 기업 정보 | 섹터, 산업, 시가총액, 52주 고저 |
| Gemini AI 분석 | 실제 지표 데이터를 기반으로 AI 딥 다이브 리포트 생성 |

---

## 설치 방법

```bash
pip install -r requirements.txt
```

---

## 실행 방법

```bash
streamlit run app.py
```

---

## 한국 주식 종목 검색 방법

앱 사이드바에서 **"한국 종목 선택"** 모드를 선택하면 드롭다운 목록에서 종목명으로 검색할 수 있습니다.  
목록에 없는 종목은 **"티커 직접 입력"** 모드에서 아래 형식으로 입력하세요.

| 입력 예시 | 설명 |
|-----------|------|
| `005930.KS` | 삼성전자 (KOSPI) |
| `247540.KQ` | 에코프로비엠 (KOSDAQ) |
| `005930` | 6자리 코드만 입력 시 자동 거래소 판별 |
| `삼성전자` | 한글 종목명 직접 입력도 가능 |

---

## Gemini API 키 설정

AI 분석 기능을 사용하려면 **Google Gemini API 키**가 필요합니다.  
[Google AI Studio](https://aistudio.google.com/app/apikey)에서 무료로 발급받을 수 있습니다.

### 로컬 실행 시

**macOS / Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
streamlit run app.py
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
streamlit run app.py
```

### Streamlit Cloud 배포 시

앱 대시보드 → **Settings → Secrets**에 아래 내용을 추가하세요.

```toml
GEMINI_API_KEY = "your-api-key-here"
```

> **주의:** API 키를 코드에 직접 입력하지 마세요.

---

## 지원 티커 예시

### 미국 주식

- `AAPL`, `TSLA`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `META`

### 한국 KOSPI 주요 종목

삼성전자, SK하이닉스, LG에너지솔루션, 삼성바이오로직스, 현대차, 기아,  
셀트리온, 포스코홀딩스, LG화학, 삼성SDI, KB금융, 신한지주, 카카오, 네이버 등

### 한국 KOSDAQ 주요 종목

에코프로비엠, 에코프로, 포스코DX, 카카오게임즈, 펄어비스, 알테오젠 등

---

## 면책 조항

이 앱의 분석 결과는 **참고용 정보**이며 투자 자문이 아닙니다.  
투자 판단과 그에 따른 책임은 본인에게 있습니다.

---

## 참고

- 주가 데이터는 `yfinance`를 통해 가져옵니다.
- AI 분석은 `google-generativeai` (Gemini 1.5 Flash)를 사용합니다.
- 일부 종목의 데이터는 지연되거나 제한될 수 있습니다.
