# main3.py
import os
import threading
import requests
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime
from flask import Flask

# ======================== CONFIG ==========================
BOT_TOKEN = "7264977373:AAEZcqW5XL2LqLoQKbLUOKW1N0pdiGE2kFs"
CHAT_ID = "510189896"  # Đúng chat ID số
COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "TRX",
    "DOT", "MATIC", "SHIB", "LTC", "TON", "APT", "BCH", "NEAR", "ARB", "OP",
    "UNI", "XLM", "INJ", "SUI", "AAVE", "ETC", "RUNE", "SEI", "RNDR", "GRT"
]
TIMEFRAMES = ["h1", "h4", "d"]
INTERVAL_SECONDS = 900  # 15 phút
# ==========================================================

# Flask App để Render nhận diện port
app = Flask(__name__)

@app.route("/")
def home():
    return "Crypto bot is running!"

def fetch_ohlcv(coin, timeframe):
    url = f"https://min-api.cryptocompare.com/data/v2/histo{timeframe}?fsym={coin}&tsym=USDT&limit=100"
    r = requests.get(url)
    data = r.json()["Data"]["Data"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volumeto": "Volume"}, inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def calculate_indicators(df):
    # RSI
    delta = df["Close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df


def detect_wedge(df):
    highs = df["High"][-5:]
    lows = df["Low"][-5:]
    slope_high = np.polyfit(range(5), highs, 1)[0]
    slope_low = np.polyfit(range(5), lows, 1)[0]

    if slope_high < 0 and slope_low > 0:
        if df["Close"].iloc[-1] > highs.max():
            return "Breakout tăng"
        elif df["Close"].iloc[-1] < lows.min():
            return "Breakout giảm"
    return None


def draw_chart(df, coin, timeframe, note):
    filename = f"chart_{coin}_{timeframe}.png"
    mpf.plot(df[-50:], type='candle', style='charles', title=f"{coin} {timeframe.upper()} - {note}",
             ylabel='Price', savefig=filename)
    return filename


def send_alert(coin, timeframe, signal, image_path):
    text = f"🚨 {coin}/{timeframe.upper()} phát hiện tín hiệu: {signal}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": text}, files={"photo": photo})


def run_bot():
    while True:
        print(f"[~] Đang kiểm tra tín hiệu lúc {datetime.now()}")
        for coin in COINS:
            for tf in TIMEFRAMES:
                try:
                    df = fetch_ohlcv(coin, tf)
                    df = calculate_indicators(df)
                    wedge_signal = detect_wedge(df)

                    rsi = df["RSI"].iloc[-1]
                    macd = df["MACD"].iloc[-1]
                    signal = df["Signal"].iloc[-1]

                    rsi_note = "RSI quá bán" if rsi < 20 else "RSI quá mua" if rsi > 80 else ""
                    macd_note = "MACD vàng (tăng)" if macd > signal else "MACD chết (giảm)" if macd < signal else ""

                    notes = [note for note in [wedge_signal, rsi_note, macd_note] if note]

                    if notes:
                        chart = draw_chart(df, coin, tf, ", ".join(notes))
                        send_alert(coin, tf, ", ".join(notes), chart)
                        print(f"[+] Alert sent for {coin} {tf}: {notes}")
                    else:
                        print(f"[-] No signal for {coin} {tf}")
                except Exception as e:
                    print(f"[!] Error with {coin} {tf}: {e}")
        time.sleep(INTERVAL_SEC_


