import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="주식 티커 분석기", layout="wide")

st.title("📈 주식 티커 분석기")
st.caption("티커를 입력하면 가격 흐름, 이동평균선, 수익률, 거래량, 기업 정보, 최근 실적 발표 데이터를 확인할 수 있습니다.")

KOREAN_TICKER_MAP = {
    "삼성전자": "005930.KS",
    "sk하이닉스": "000660.KS",
    "하이닉스": "000660.KS",
    "네이버": "035420.KS",
    "naver": "035420.KS",
    "카카오": "035720.KS",
    "lg에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "포스코홀딩스": "005490.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
}


def normalize_ticker(user_input: str) -> str:
    text = user_input.strip()
    lower_text = text.lower()

    if lower_text in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[lower_text]

    if text in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[text]

    if text.isdigit() and len(text) == 6:
        return f"{text}.KS"

    return text.upper()


def load_data(ticker: str, period: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    info = stock.info
    earnings = stock.quarterly_earnings
    return hist, info, earnings


def format_number(value):
    if value in [None, "N/A"]:
        return "N/A"
    try:
        return f"{value:,}"
    except Exception:
        return str(value)


def is_korean_stock(ticker: str) -> bool:
    return ticker.endswith(".KS") or ticker.endswith(".KQ")


def get_currency_symbol(ticker: str) -> str:
    return "₩" if is_korean_stock(ticker) else "$"


def format_price(value, ticker: str) -> str:
    symbol = get_currency_symbol(ticker)
    if value in [None, "N/A"]:
        return "N/A"
    try:
        return f"{symbol}{value:,.2f}"
    except Exception:
        return f"{symbol}{value}"


st.sidebar.header("분석 설정")
user_input = st.sidebar.text_input(
    "주식 티커 또는 종목명",
    value="AAPL",
    help="예: AAPL, TSLA, 005930.KS, 삼성전자, sk하이닉스",
)
period = st.sidebar.selectbox(
    "조회 기간",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
)
show_ma20 = st.sidebar.checkbox("20일 이동평균선", value=True)
show_ma60 = st.sidebar.checkbox("60일 이동평균선", value=True)

ticker = normalize_ticker(user_input)

if user_input:
    try:
        hist, info, earnings = load_data(ticker, period)

        if hist.empty:
            st.error("데이터를 불러올 수 없습니다. 티커 또는 종목명을 다시 확인해주세요.")
        else:
            hist = hist.copy()
            hist["MA20"] = hist["Close"].rolling(20).mean()
            hist["MA60"] = hist["Close"].rolling(60).mean()

            current_price = hist["Close"].iloc[-1]
            start_price = hist["Close"].iloc[0]
            returns = ((current_price - start_price) / start_price) * 100
            high_price = hist["High"].max()
            low_price = hist["Low"].min()
            avg_volume = hist["Volume"].mean()

            st.info(f"입력값: **{user_input}** → 조회 티커: **{ticker}**")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("현재가", format_price(current_price, ticker))
            col2.metric("기간 수익률", f"{returns:,.2f}%")
            col3.metric("기간 최고가", format_price(high_price, ticker))
            col4.metric("평균 거래량", f"{avg_volume:,.0f}")

            st.subheader("주가 차트")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist["Close"],
                    mode="lines",
                    name="종가",
                )
            )

            if show_ma20:
                fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist["MA20"],
                        mode="lines",
                        name="MA20",
                    )
                )

            if show_ma60:
                fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist["MA60"],
                        mode="lines",
                        name="MA60",
                    )
                )

            fig.update_layout(
                height=500,
                xaxis_title="날짜",
                yaxis_title="가격",
                legend_title="범례",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("거래량")
            st.bar_chart(hist["Volume"])

            st.subheader("기업 정보")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**회사명:** {info.get('longName', 'N/A')}")
                st.write(f"**섹터:** {info.get('sector', 'N/A')}")
                st.write(f"**산업:** {info.get('industry', 'N/A')}")
            with info_col2:
                st.write(f"**시가총액:** {format_number(info.get('marketCap', 'N/A'))}")
                st.write(f"**52주 최고가:** {format_price(info.get('fiftyTwoWeekHigh', 'N/A'), ticker)}")
                st.write(f"**52주 최저가:** {format_price(info.get('fiftyTwoWeekLow', 'N/A'), ticker)}")

            summary = info.get("longBusinessSummary")
            if summary:
                st.subheader("기업 소개")
                st.write(summary)

            st.subheader("최근 실적 발표 데이터")
            if isinstance(earnings, pd.DataFrame) and not earnings.empty:
                latest_earnings = earnings.tail(1).copy()
                latest_earnings.index = latest_earnings.index.astype(str)
                st.dataframe(latest_earnings)
            else:
                st.info("최근 실적 발표 데이터를 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 티커 또는 종목명을 입력해주세요.")
