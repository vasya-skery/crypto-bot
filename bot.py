import os
import time
import requests
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import ccxt

load_dotenv('config.env')

SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
TIMEFRAME = os.getenv('TIMEFRAME', '1h')
RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', 30))
RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', 70))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

exchange = ccxt.binance()
last_signal = None

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

def calculate_rsi(prices, period=14):
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0)
    losses = (-deltas).where(deltas < 0, 0)
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal():
    global last_signal
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = calculate_rsi(df['close'])
        
        current_price = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        
        signal = None
        if last_signal != 'BUY' and current_rsi < RSI_OVERSOLD:
            signal = 'BUY'
        elif last_signal != 'SELL' and current_rsi > RSI_OVERBOUGHT:
            signal = 'SELL'
        
        if signal:
            last_signal = signal
            return signal, current_price, current_rsi
        return None, current_price, current_rsi
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def main():
    print(f"Trading bot started: {SYMBOL} | {TIMEFRAME}")
    print(f"RSI params: Oversold={RSI_OVERSOLD}, Overbought={RSI_OVERBOUGHT}")
    
    while True:
        signal, price, rsi = get_signal()
        if signal:
            msg = f"📢 Сигнал: {signal}\nПара: {SYMBOL}\nЦіна: ${price:,.2f}\nRSI: {rsi:.2f}"
            print(msg)
            send_telegram(msg)
        else:
            print(f"Ціна: ${price:,.2f} | RSI: {rsi:.2f}")
        time.sleep(3600)

if __name__ == "__main__":
    main()