import os
import time
import asyncio
import requests
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import ccxt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv('config.env')

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
TIMEFRAME = os.getenv('TIMEFRAME', '1h')
RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', 30))
RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', 70))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

exchange = ccxt.binance()
last_signals = {s: None for s in SYMBOLS}

def calculate_rsi(prices, period=14):
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0)
    losses = (-deltas).where(deltas < 0, 0)
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_prices():
    result = []
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = calculate_rsi(df['close'])
            price = df['close'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            result.append((symbol, price, rsi))
        except Exception as e:
            result.append((symbol, None, None))
    return result

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Crypto RSI Bot\n\n"
        "Commands:\n"
        "/start - Start\n"
        "/prices - Current prices & RSI\n"
        "/status - Bot status\n"
        "/help - Help"
    )

async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_prices()
    msg = "Prices & RSI:\n\n"
    for symbol, price, rsi in data:
        if price:
            msg += f"{symbol}: ${price:,.2f} | RSI: {rsi:.2f}\n"
        else:
            msg += f"{symbol}: Error\n"
    await update.message.reply_text(msg)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_prices()
    msg = "Status:\n\n"
    for symbol, price, rsi in data:
        if rsi:
            zone = "OVERSOLD" if rsi < RSI_OVERSOLD else "OVERBOUGHT" if rsi > RSI_OVERBOUGHT else "NEUTRAL"
            msg += f"{symbol}: {zone} (RSI: {rsi:.2f})\n"
        else:
            msg += f"{symbol}: Error\n"
    msg += f"\nParams: Oversold={RSI_OVERSOLD}, Overbought={RSI_OVERBOUGHT}"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Crypto RSI Bot\n\n"
        "Strategy: RSI\n"
        "BUY: RSI < 30 (oversold)\n"
        "SELL: RSI > 70 (overbought)\n\n"
        "/prices - Check prices\n"
        "/status - Check signals\n"
        "/help - This help"
    )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help")

def main():
    print(f"Starting bot for: {', '.join(SYMBOLS)}")
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("prices", prices_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    print("Bot ready!")
    app.run_polling()

if __name__ == "__main__":
    main()