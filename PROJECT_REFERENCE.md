# PROJECT REFERENCE — OptiTrade AI → Alpaca Trading Bot
*Share this file with Claude in future sessions to resume where we left off.*

---

## What This Project Does
Receives BUY/SELL signals from TradingView (OptiTrade AI indicator) via webhooks,
and automatically places trades on an Alpaca paper/live account.
Hosted on Railway for 24/7 uptime. Coded on Replit.

---

## GitHub Repo
https://github.com/ambrose2107/trading-bot

---

## Tech Stack
- **Language**: Python 3.11
- **Framework**: Flask 3.0
- **Database**: SQLite (trades.db)
- **Broker API**: Alpaca Markets (paper trading)
- **Hosting**: Railway
- **Dev Environment**: Replit
- **Signal Source**: TradingView + OptiTrade AI indicator

---

## Environment Variables (set in Railway + Replit Secrets)
```
ALPACA_API_KEY      = <your key>
ALPACA_SECRET_KEY   = <your secret>
ALPACA_MODE         = paper
APP_SECRET_KEY      = <random string>
DASHBOARD_PASSWORD  = <your password>
WEBHOOK_SECRET      = my_secret_123
MAX_POSITION_SIZE   = 10
DAILY_LOSS_LIMIT    = 500
MAX_OPEN_POSITIONS  = 5
KILL_SWITCH         = false
```

---

## Key URLs (once deployed on Railway)
- Dashboard:   https://YOUR-RAILWAY-URL/
- Webhook:     https://YOUR-RAILWAY-URL/webhook   ← paste in TradingView
- Health check:https://YOUR-RAILWAY-URL/health

---

## TradingView Alert Setup
1. OptiTrade 2.0 indicator → Inputs tab
2. Long Entry box:  JSON with "action":"buy"
3. Short Entry box: JSON with "action":"sell"
4. Create Alert → Webhook URL → paste Railway /webhook URL
5. Message = {{strategy.order.alert_message}}

**Webhook JSON format:**
```json
{
  "secret": "my_secret_123",
  "symbol": "AAPL",
  "action": "buy",
  "quantity": 1,
  "order_type": "market"
}
```

---

## Indicators Analysed

### 1. OptiTrade 2.0 Buy-Sell Strategy ✅ (RECOMMENDED)
- **Type**: Flip strategy — BUY closes any short, opens long. SELL closes any long, opens short.
- **Alert boxes**: Long Entry / Short Entry
- **File**: OptiTrade_2_0_Buy-Sell_Strategy.txt
- **Best for**: Full automation

### 2. OptiTrade 2.0 HWR Strategy
- **Type**: Trend-following — separate entry and exit signals
- **Signals**: startLongTrade / endLongTrade / startShortTrade / endShortTrade
- **Alert boxes**: (Long) Custom Alert / (Short) Custom Alert
- **File**: OptiTrade_2_0_HWR_Strategy.txt
- **Best for**: Automation with 4 separate alerts (entry + exit)

### 3. OptiTrade 2.0 TP-SL Strategy
- **Type**: Entry + up to 4 Take Profits + Stop Loss
- **Alert boxes**: Multiple (entry + TP1-4 + SL per direction)
- **File**: OptiTrade_2_0_TP-SL_Strategy.txt
- **Best for**: Manual TP/SL on broker side; only automate entry

---

## Files Built
```
main.py                     Entry point; gunicorn imports app object
app.py                      Flask factory — registers blueprints
core/config.py              All settings from env vars
core/database.py            SQLite — trades + webhook_log tables
core/logger.py              Centralised logging
brokers/alpaca_adapter.py   Alpaca REST API wrapper
webhook/handler.py          Signal processor — validates, risk-checks, executes
webhook/routes.py           POST /webhook  +  GET /health
dashboard/routes.py         Web UI API routes + login/logout
dashboard/templates/login.html     Password login page
dashboard/templates/dashboard.html Live monitoring dashboard
test_bot.py                 23 unit tests — all passing ✅
requirements.txt            flask, requests, python-dotenv, gunicorn
Procfile                    gunicorn start command
railway.json                Railway deploy config
.env.example                Template for local .env file
README.md                   Full setup guide
PROJECT_REFERENCE.md        This file
```

---

## Tests (23 — all passing)
- Config: 4 tests (mode, base URL, secret, kill switch)
- Database: 4 tests (log trade, log webhook, multiple trades, failed trade)
- Webhook Handler: 9 tests (buy, sell, flip close, wrong secret, bad action, zero qty, max size, missing symbol, kill switch)
- Flask Routes: 6 tests (health, bad JSON, wrong secret, valid buy, dashboard redirect, login page)

---

## Railway Hosting Steps
1. railway.app → New Project → Deploy from GitHub
2. Connect GitHub → select this repo
3. Settings → Variables → add all env vars
4. Settings → Domains → copy URL → use as webhook URL in TradingView

---

## What Was Done Before This Bot (original repo)
The original trading-bot repo used internal strategies (MA crossover, RSI) to generate signals.
This new version replaces that — signals now come ONLY from TradingView webhooks (OptiTrade AI).
The broker adapter pattern (brokers/alpaca_adapter.py) was preserved from the original design.

---

## Planned Next Features (Phase 2)
- [ ] Daily loss limit auto-stop (partially in config, needs runtime enforcement)
- [ ] Telegram / email notification on each trade
- [ ] Support for multiple symbols via symbol config list
- [ ] TP/SL automation for TP-SL strategy
- [ ] Position sizing based on account equity %
- [ ] Trade history export (CSV download)
- [ ] Scheduled market-hours check (only trade 9:30–16:00 ET)
