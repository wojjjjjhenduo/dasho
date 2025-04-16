# 美股实时炒股分析网页版（Streamlit版，折叠界面 + 移动端优化 + 中文）

import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io

# NewsAPI 配置
NEWS_API_KEY = "8a06af5467214999ac3adc7decca2092"

# 获取实时数据
def get_realtime_data(tickers):
    data = {}
    for symbol in tickers:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        data[symbol] = {
            "当前价格": info.get("currentPrice"),
            "开盘价": info.get("open"),
            "前收盘": info.get("previousClose"),
            "日高": info.get("dayHigh"),
            "日低": info.get("dayLow"),
            "成交量": info.get("volume"),
            "市值": info.get("marketCap"),
            "市盈率(TTM)": info.get("trailingPE"),
            "每股收益(TTM)": info.get("trailingEps"),
            "股息率": info.get("dividendYield"),
            "Beta值": info.get("beta")
        }
    return pd.DataFrame(data).T

# 技术分析与信号
def calculate_technical_indicators(symbol):
    df = yf.download(symbol, period="3mo", interval="1d")
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["SMA50"] = df["Close"].rolling(window=50).mean()
    df["涨跌幅"] = df["Close"].pct_change() * 100
    df["波动率"] = df["涨跌幅"].rolling(window=10).std()
    df["买入信号"] = np.where((df["SMA20"] > df["SMA50"]) & (df["涨跌幅"] > 1), "买入 📈",
                           np.where((df["SMA20"] < df["SMA50"]) & (df["涨跌幅"] < -1), "卖出 📉", "观望 🕒"))
    return df

# 新闻摘要
def fetch_news_sentiment(symbol):
    url = f"https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])[:5]
        return [article["title"] for article in articles]
    else:
        return ["无法获取新闻"]

# 绘图函数
def plot_with_indicators(df, symbol):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df.index, df["Close"], label="收盘价")
    ax.plot(df.index, df["SMA20"], label="SMA20")
    ax.plot(df.index, df["SMA50"], label="SMA50")
    ax.set_title(f"{symbol} 股价与均线图")
    ax.legend()
    ax.grid()
    st.pyplot(fig)

# 主体界面（手机兼容 + 折叠 + 中文）
st.set_page_config(page_title="美股实时分析", layout="centered")
st.title("📊 美股实时分析工具（适合妈妈使用）")

st.markdown("<h4 style='color:green;'>请选择股票并下载分析结果：</h4>", unsafe_allow_html=True)

all_symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOG", "META", "BABA", "NFLX"]
selected = st.multiselect("📌 选择要分析的股票（可多选）：", all_symbols, default=["AAPL"])

if selected:
    data = get_realtime_data(selected)

    for symbol in selected:
        df = calculate_technical_indicators(symbol)
        latest = df.tail(1)
        signal = latest["买入信号"].values[0]
        data.loc[symbol, "买入信号"] = signal

    st.subheader("📋 实时数据汇总")
    st.dataframe(data[["当前价格", "市盈率(TTM)", "股息率", "Beta值", "买入信号"]])

    st.markdown("<br><b>📥 点击以下按钮导出分析结果为 Excel 文件：</b>", unsafe_allow_html=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, sheet_name="分析结果")
    st.download_button("📥 下载 Excel 文件", data=output.getvalue(), file_name="分析结果.xlsx")

    for symbol in selected:
        with st.expander(f"📈 {symbol} 技术图表与新闻分析"):
            df = calculate_technical_indicators(symbol)
            latest = df.tail(1)
            st.write("📌 当前买卖信号：", latest["买入信号"].values[0])
            plot_with_indicators(df, symbol)

            st.markdown("📰 最新新闻摘要：")
            headlines = fetch_news_sentiment(symbol)
            for i, headline in enumerate(headlines, 1):
                st.markdown(f"{i}. {headline}")
