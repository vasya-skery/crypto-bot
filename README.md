# Crypto Trading Bot

Бот для торгівлі криптовалютою на Binance з надсиланням сигналів у Telegram.

## Встановлення

```bash
cd crypto-bot
pip install -r requirements.txt
```

## Налаштування

1. Створи `config.env` на основі `config.env.example`:
```bash
copy config.env.example config.env
```

2. Заповни налаштування:
- `BINANCE_API_KEY` та `BINANCE_API_SECRET` - отримати на Binance
- `TELEGRAM_BOT_TOKEN` - від @BotFather
- `TELEGRAM_CHAT_ID` - від @userinfobot

## Запуск

```bash
python bot.py
```

## Стратегія

RSI (Relative Strength Index):
- BUY: RSI < 30 (перепродано)
- SELL: RSI > 70 (перекуплено)