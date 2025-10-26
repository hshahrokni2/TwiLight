# 🚀 TwiLight - Autonomous Crypto Trading System

An advanced, AI-powered cryptocurrency trading system with 7 intelligent agents, real-time dashboard, and multi-exchange support.

## 🌟 Features

- **7 Trading Agents**: Scalping, Swing Trading, Research, Market Data, Portfolio Management, Risk Management, and Execution
- **Multi-Exchange Support**: Binance and Kraken integration
- **AI-Powered Analysis**: Integration with OpenAI GPT-4, Anthropic Claude, Grok, and Perplexity
- **Real-Time Dashboard**: Beautiful web interface with live portfolio tracking, P&L analytics, and agent status
- **Risk Management**: Automated stop-loss, take-profit, and position sizing
- **Telegram Bot**: Real-time notifications and trading updates
- **Multi-Agent Orchestration**: Intelligent decision pipeline with confidence-based execution

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Stunning Dashboard                       │
│              (Real-time UI + AI Assistant)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Pipeline                       │
│  1. Agent Analysis → 2. Decision Ranking →                  │
│  3. Risk Validation → 4. Execution                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Scalping    │   │    Swing     │   │   Research   │
│   Agent      │   │    Agent     │   │    Agent     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            Market Data → Portfolio → Risk Manager            │
│                  → Execution Agent                           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Binance    │   │    Kraken    │   │  PostgreSQL  │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Python 3.10+
- **Dashboard**: Dash (Plotly), Flask
- **Database**: PostgreSQL
- **Cache**: Redis
- **Exchanges**: CCXT library (Binance, Kraken)
- **AI**: OpenAI, Anthropic, xAI (Grok), Perplexity
- **Notifications**: python-telegram-bot

## 📁 Project Structure

```
TwiLight/
├── agents/                      # Trading agent modules
│   ├── scalping_agent.py       # High-frequency trading
│   ├── swing_agent.py          # Medium-term positions
│   ├── research_agent.py       # Market intelligence
│   ├── market_data_agent.py    # Real-time data aggregation
│   ├── portfolio_agent.py      # Portfolio tracking
│   ├── risk_manager_agent.py   # Risk controls
│   └── execution_agent.py      # Order execution
├── stunning_dashboard.py        # Main dashboard application
├── telegram_bot.py             # Telegram notifications
├── init_db.py                  # Database initialization
├── config_loader.py            # Environment config loader
├── start_trading_system.sh     # Agent startup script
├── requirements.txt            # Python dependencies
├── railway.json                # Railway deployment config
└── README.md                   # This file
```

## 🚀 Deployment Guide

### Railway Deployment (Recommended)

Railway provides easy deployment with PostgreSQL and Redis out of the box.

#### Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app)
- API keys for exchanges and LLM providers

#### Step 1: Push Code to GitHub
```bash
# This repository is already set up at:
# https://github.com/hshahrokni2/TwiLight
```

#### Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `hshahrokni2/TwiLight`
4. Railway will automatically detect the configuration

#### Step 3: Add PostgreSQL and Redis

1. In your Railway project, click "New" → "Database" → "PostgreSQL"
2. Click "New" → "Database" → "Redis"
3. Railway will automatically set `DATABASE_URL` and `REDIS_URL` environment variables

#### Step 4: Configure Environment Variables

Go to your Railway project → Variables tab and add:

**Exchange API Keys:**
```
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_API_SECRET=your_kraken_secret
```

**LLM API Keys:**
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...
PERPLEXITY_API_KEY=pplx-...
```

**Telegram:**
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
TELEGRAM_GROUP_CHAT_ID=your_group_chat_id
```

**Trading Configuration:**
```
INITIAL_CAPITAL=100
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.05
USE_ENV_CONFIG=true
```

#### Step 5: Deploy

1. Railway will automatically deploy when you push to GitHub
2. Access your dashboard at: `https://your-project.railway.app`
3. Monitor logs in Railway dashboard

### Local Development

#### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis

#### Setup

1. Clone the repository:
```bash
git clone https://github.com/hshahrokni2/TwiLight.git
cd TwiLight
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
```bash
# Create database
createdb crypto_trading

# Initialize schema
python init_db.py
```

5. Start Redis:
```bash
redis-server
```

6. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

7. Run the system:
```bash
# Start dashboard
python stunning_dashboard.py

# In another terminal, start trading agents
bash start_trading_system.sh

# In another terminal, start Telegram bot
python telegram_bot.py
```

8. Access dashboard at: http://localhost:8050

## 🔐 Security Notes

- **Never commit `config.json` or `.env` files** to GitHub
- Use environment variables for all secrets in production
- Enable 2FA on all exchange accounts
- Start with small capital for testing
- Use API keys with restricted permissions (no withdrawals)

## 📊 Dashboard Features

### Main Dashboard
- **Portfolio Value**: Real-time total portfolio value with P&L
- **Daily P&L**: Today's profit/loss percentage
- **Total P&L**: All-time profit/loss
- **Open Positions**: Active trades across all exchanges
- **Exchange Balances**: Live balance tracking
- **Recent Trades**: Trade history with timestamps

### Orchestrator Pipeline
- **Agent Analysis**: Real-time agent decision monitoring
- **Decision Ranking**: Confidence-based trade prioritization
- **Risk Validation**: Automated risk checks before execution
- **Execution Status**: Live trade execution tracking

### AI Assistant
- Chat with GPT-5 for portfolio insights
- Ask about agent strategies and market analysis
- Query current positions and performance

## 🤖 Trading Agents

### 1. Scalping Agent
- **Strategy**: High-frequency, small profit targets
- **Timeframe**: 1-5 minutes
- **Risk**: Low per trade, high frequency

### 2. Swing Agent
- **Strategy**: Medium-term trend following
- **Timeframe**: Hours to days
- **Risk**: Medium, position-based

### 3. Research Agent
- **Strategy**: Fundamental and sentiment analysis
- **Data Sources**: News, social media, on-chain data
- **Role**: Provides market intelligence to other agents

### 4. Market Data Agent
- **Role**: Real-time price feeds and technical indicators
- **Exchanges**: Binance, Kraken
- **Indicators**: MA, RSI, MACD, Volume, etc.

### 5. Portfolio Agent
- **Role**: Track all positions and balances
- **Features**: Multi-exchange aggregation, P&L calculation

### 6. Risk Manager Agent
- **Role**: Validate trades against risk rules
- **Features**: Position sizing, stop-loss, max daily loss

### 7. Execution Agent
- **Role**: Execute orders on exchanges
- **Features**: Smart order routing, retry logic, error handling

## 📈 Performance Monitoring

### Telegram Notifications
- Trade executions (buy/sell)
- Daily P&L summaries
- Risk alerts
- Agent status updates

### Dashboard Analytics
- Portfolio value chart
- Trade history table
- Agent confidence scores
- Exchange connection status

## 🔧 Configuration

### Risk Management Parameters

Edit `MAX_POSITION_SIZE`, `MAX_DAILY_LOSS`, etc. in environment variables:

- `MAX_POSITION_SIZE`: Max % of capital per trade (default: 0.1 = 10%)
- `MAX_DAILY_LOSS`: Max % loss per day (default: 0.05 = 5%)
- `STOP_LOSS_PERCENTAGE`: Stop loss % (default: 0.02 = 2%)
- `TAKE_PROFIT_PERCENTAGE`: Take profit % (default: 0.05 = 5%)

### Trading Pairs

To add/remove trading pairs, modify `config_loader.py`:

```python
"trading_pairs": [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT"
]
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check DATABASE_URL is set correctly
echo $DATABASE_URL

# Reinitialize database
python init_db.py
```

### Exchange API Errors
- Verify API keys are correct and have trading permissions
- Check IP whitelist settings on exchange
- Ensure sufficient balance for trading

### Agent Not Starting
```bash
# Check logs
tail -f *.log

# Restart agents
bash start_trading_system.sh
```

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## ⚠️ Disclaimer

**This software is for educational purposes only. Trading cryptocurrencies involves significant risk. You can lose all your capital. Always do your own research and never trade with money you can't afford to lose. The authors are not responsible for any financial losses.**

## 📞 Support

For issues, questions, or suggestions:
- Open a GitHub issue
- Contact via Telegram: @hshahrokni2

---

**Made with ❤️ by the TwiLight Team**
