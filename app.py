import os

import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from korean_stocks import CODE_TO_EXCHANGE, KOREAN_STOCKS, STOCK_NAMES

st.set_page_config(page_title="주식 티커 분석기", layout="wide")

st.title("📈 주식 티커 분석기")
st.caption(
    "티커를 입력하거나 한국 종목명을 선택하면 가격 흐름, 이동평균선, 수익률, "
    "거래량, 기업 정보를 확인하고 Gemini AI 분석 리포트를 생성할 수 있습니다."
)
st.warning(
    "이 앱의 분석 결과는 투자 자문이 아닌 참고용 정보입니다. "
    "투자 판단과 책임은 본인에게 있습니다."
)


# ─────────────────────────── 티커 정규화 ────────────────────────────


def resolve_6digit(code: str) -> str:
    """6자리 종목코드를 올바른 거래소 접미사로 변환.

    매핑 테이블에 있으면 해당 접미사를 사용하고,
    없으면 .KS(KOSPI)를 먼저 시도한 뒤 데이터가 없으면 .KQ(KOSDAQ)를 반환.
    """
    if code in CODE_TO_EXCHANGE:
        return f"{code}.{CODE_TO_EXCHANGE[code]}"
    # 매핑에 없는 경우 KOSPI 먼저 시도
    for suffix in ("KS", "KQ"):
        candidate = f"{code}.{suffix}"
        try:
            test = yf.Ticker(candidate).history(period="5d")
            if not test.empty:
                return candidate
        except Exception:
            pass
    return f"{code}.KS"  # 기본값


def normalize_ticker(user_input: str) -> str:
    """사용자 입력 → 유효한 Yahoo Finance 티커 반환."""
    text = user_input.strip()
    lower_text = text.lower()

    # 1) 한글·영문 종목명 매핑
    if lower_text in KOREAN_STOCKS:
        return KOREAN_STOCKS[lower_text]
    if text in KOREAN_STOCKS:
        return KOREAN_STOCKS[text]

    # 2) 이미 접미사가 포함된 경우 (.KS / .KQ / .T 등)
    if "." in text:
        return text.upper()

    # 3) 6자리 숫자코드
    if text.isdigit() and len(text) == 6:
        return resolve_6digit(text)

    # 4) 미국/기타 티커
    return text.upper()


# ─────────────────────────── 데이터 로드 ────────────────────────────


def load_data(ticker: str, period: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    info = stock.info
    return hist, info


# ─────────────────────────── RSI 계산 ───────────────────────────────


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ─────────────────────────── Gemini 프롬프트 ─────────────────────────


def build_prompt(
    ticker: str,
    company_name: str,
    current_price: float,
    returns: float,
    ma20: float,
    ma60: float,
    ma200: float,
    rsi: float,
    high_52,
    low_52,
    avg_volume: float,
    sector: str,
    industry: str,
    summary: str,
) -> str:
    return f"""
## Role & Identity

당신은 월가 헤지펀드에서 30년간 연평균 40% 이상의 수익률을 기록한 AI 수석 퀀트·테크니컬 전략가입니다.
윌리엄 오닐(CANSLIM)의 성장주 철학과 마크 미너비니(Mark Minervini)의 변동성 축소(VCP) 이론을 결합하여 분석하십시오.

## Important Rules

- 아래에 제공된 데이터만 우선적으로 활용하십시오.
- 데이터가 부족한 항목은 "확인 필요"라고 명시하십시오.
- 투자 자문이 아닌 참고용 분석으로 작성하십시오.
- 과도한 확신 표현은 피하십시오.

## 제공 데이터

- 티커: {ticker}
- 회사명: {company_name}
- 현재가: {current_price:.2f}
- 기간 수익률: {returns:.2f}%
- 20일 이동평균선: {ma20:.2f}
- 60일 이동평균선: {ma60:.2f}
- 200일 이동평균선: {ma200:.2f}
- RSI(14): {rsi:.2f}
- 52주 최고가: {high_52}
- 52주 최저가: {low_52}
- 평균 거래량: {avg_volume:,.0f}
- 섹터: {sector}
- 산업: {industry}
- 기업 소개: {summary}

## 분석 프레임워크

### 0단계: Fundamental Check
- 제공된 기업 소개와 산업 정보를 바탕으로 성장 스토리/재료 가능성 간단 요약

### 1단계: Trend Filter
- 현재 주가가 200일 이동평균선 위/아래인지 판단
- 아래라면 장기 추세 리스크를 강조

### 2단계: Sector Strength
- 섹터와 산업을 바탕으로 상대적 강도 가능성을 보수적으로 평가

### 3단계: Technical Indicators
- 20일/60일/200일 이동평균선 위치 관계 해석
- RSI 기반 모멘텀 해석
- 수급 상태를 보수적으로 설명

### 4단계: Risk Management
- 현재가와 이동평균선을 참고해 합리적 손절/목표 구간 제시

---

## Output Format

### 📊 [{ticker}: {company_name}] 딥 다이브 리포트

1. 최종 판결 (Signal):
[🚨강력 매수 (Top Pick)] / [✅매수 (Buy)] / [⚠️관망 (Wait)] / [⛔매도 (Sell)]
- 판결 이유를 한 줄로 요약

2. 퀀트 스코어보드 (10점 만점)
- 펀더멘털: (점수) / 요약
- 기술적 추세: (점수) / 요약
- 수급/모멘텀: (점수) / 요약
- 종합 점수: X점

3. 차트 정밀 분석 (Technical Deep Dive)
- 추세 (Trend):
- 패턴 (Pattern):
- 수급 (Volume):
- 위험 요소:

4. 0.1% 스나이퍼 트레이딩 전략
- 🎯 진입 추천가 (Buy Zone):
- ✂️ 칼손절가 (Stop-loss):
- 🚀 1차 목표가 (Target 1):
- 💰 2차 목표가 (Target 2):

5. Analyst's Insight:
- 윌리엄 오닐 관점과 추세 추종 관점에서 코멘트

6. 주의사항 및 면책조항 (Disclaimer)
- 반드시 참고용 분석이며 투자 책임은 본인에게 있다고 명시
"""


# ─────────────────────────── Gemini 호출 ─────────────────────────────


def get_gemini_api_key() -> str | None:
    """환경변수 또는 Streamlit secrets에서 API 키를 안전하게 로드."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    return key or None


def run_gemini_analysis(prompt: str) -> tuple[str | None, str | None]:
    api_key = get_gemini_api_key()
    if not api_key:
        return None, (
            "GEMINI_API_KEY가 설정되지 않았습니다. "
            "로컬 실행 시 환경변수로, Streamlit Cloud 배포 시 Secrets에 키를 추가해주세요. "
            "(README의 'Gemini API 키 설정' 참고)"
        )
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as exc:
        return None, f"Gemini 호출 중 오류가 발생했습니다: {exc}"


# ═══════════════════════════ 사이드바 UI ═══════════════════════════


st.sidebar.header("분석 설정")

search_mode = st.sidebar.radio(
    "검색 방식",
    ["한국 종목 선택", "티커 직접 입력"],
    index=0,
    help="한국 종목은 목록에서 선택하고, 미국 주식 등은 티커를 직접 입력하세요.",
)

if search_mode == "한국 종목 선택":
    selected_name = st.sidebar.selectbox(
        "종목명 검색",
        options=STOCK_NAMES,
        index=STOCK_NAMES.index("삼성전자") if "삼성전자" in STOCK_NAMES else 0,
        help="목록에서 종목을 선택하세요. 검색창에 타이핑하면 필터링됩니다.",
    )
    user_input = selected_name
else:
    user_input = st.sidebar.text_input(
        "주식 티커",
        value="AAPL",
        help="예: AAPL, TSLA, MSFT, 005930.KS, 000660.KQ",
    ).strip()

period = st.sidebar.selectbox(
    "조회 기간",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
)
show_ma20 = st.sidebar.checkbox("20일 이동평균선", value=True)
show_ma60 = st.sidebar.checkbox("60일 이동평균선", value=True)
show_ma200 = st.sidebar.checkbox("200일 이동평균선", value=True)

# ═══════════════════════════ 메인 콘텐츠 ═══════════════════════════

ticker = normalize_ticker(user_input)

if user_input:
    try:
        hist, info = load_data(ticker, period)

        if hist.empty:
            st.error(
                f"**{user_input}** ({ticker}) 데이터를 불러올 수 없습니다. "
                "티커 또는 종목명을 다시 확인해주세요."
            )
        else:
            hist = hist.copy()
            hist["MA20"] = hist["Close"].rolling(20).mean()
            hist["MA60"] = hist["Close"].rolling(60).mean()
            hist["MA200"] = hist["Close"].rolling(200).mean()
            hist["RSI14"] = calculate_rsi(hist["Close"], 14)

            current_price = hist["Close"].iloc[-1]
            start_price = hist["Close"].iloc[0]
            returns = ((current_price - start_price) / start_price) * 100
            high_price = hist["High"].max()
            low_price = hist["Low"].min()
            avg_volume = hist["Volume"].mean()

            ma20_series = hist["MA20"].dropna()
            ma60_series = hist["MA60"].dropna()
            ma200_series = hist["MA200"].dropna()
            rsi_series = hist["RSI14"].dropna()
            ma20 = ma20_series.iloc[-1] if not ma20_series.empty else current_price
            ma60 = ma60_series.iloc[-1] if not ma60_series.empty else current_price
            ma200 = ma200_series.iloc[-1] if not ma200_series.empty else current_price
            rsi14 = rsi_series.iloc[-1] if not rsi_series.empty else 50.0

            company_name = info.get("longName", ticker)
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            market_cap = info.get("marketCap", "N/A")
            high_52 = info.get("fiftyTwoWeekHigh", "N/A")
            low_52 = info.get("fiftyTwoWeekLow", "N/A")
            summary = info.get("longBusinessSummary", "N/A")

            st.info(f"입력값: **{user_input}** → 조회 티커: **{ticker}**")

            # ── 주요 지표 ──
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("현재가", f"{current_price:,.2f}")
            col2.metric("기간 수익률", f"{returns:,.2f}%")
            col3.metric("기간 최고가", f"{high_price:,.2f}")
            col4.metric("평균 거래량", f"{avg_volume:,.0f}")
            col5.metric("RSI(14)", f"{rsi14:.2f}")

            # ── 주가 차트 ──
            st.subheader("주가 차트")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="종가")
            )
            if show_ma20:
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist["MA20"], mode="lines", name="MA20")
                )
            if show_ma60:
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist["MA60"], mode="lines", name="MA60")
                )
            if show_ma200:
                fig.add_trace(
                    go.Scatter(
                        x=hist.index, y=hist["MA200"], mode="lines", name="MA200"
                    )
                )
            fig.update_layout(
                height=500,
                xaxis_title="날짜",
                yaxis_title="가격",
                legend_title="범례",
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── 거래량 ──
            st.subheader("거래량")
            st.bar_chart(hist["Volume"])

            # ── 기업 정보 ──
            st.subheader("기업 정보")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**회사명:** {company_name}")
                st.write(f"**섹터:** {sector}")
                st.write(f"**산업:** {industry}")
            with info_col2:
                st.write(f"**시가총액:** {market_cap}")
                st.write(f"**52주 최고가:** {high_52}")
                st.write(f"**52주 최저가:** {low_52}")

            if summary and summary != "N/A":
                st.subheader("기업 소개")
                st.write(summary)

            # ── 최근 데이터 ──
            st.subheader("최근 데이터")
            st.dataframe(hist.tail(10))

            # ── Gemini AI 분석 ──
            st.subheader("🤖 Gemini AI 분석")
            st.caption(
                "버튼을 누르면 현재 데이터를 바탕으로 AI 딥 다이브 리포트를 생성합니다. "
                "GEMINI_API_KEY가 필요합니다."
            )
            if st.button("AI 딥 다이브 리포트 생성"):
                prompt = build_prompt(
                    ticker=ticker,
                    company_name=company_name,
                    current_price=current_price,
                    returns=returns,
                    ma20=ma20,
                    ma60=ma60,
                    ma200=ma200,
                    rsi=rsi14,
                    high_52=high_52,
                    low_52=low_52,
                    avg_volume=avg_volume,
                    sector=sector,
                    industry=industry,
                    summary=summary,
                )
                with st.spinner("Gemini가 분석 리포트를 생성 중입니다..."):
                    analysis, error = run_gemini_analysis(prompt)

                if error:
                    st.error(error)
                else:
                    st.markdown(analysis)

    except Exception as exc:
        st.error(f"오류가 발생했습니다: {exc}")
else:
    st.info("왼쪽 사이드바에서 종목을 선택하거나 티커를 입력해주세요.")
