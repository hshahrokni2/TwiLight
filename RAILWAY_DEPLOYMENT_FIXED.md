# 🚂 Railway Deployment Guide - FIXED

This guide explains how to properly deploy the Crypto Trading System on Railway after fixing the deployment issues.

## 🔍 What Was Fixed

### Previous Issues:
1. ❌ **Multiple Services Configuration** - Procfile defined 3 process types (web, agents, telegram) but Railway doesn't support this like Heroku does
2. ❌ **Hardcoded Paths** - Code referenced `/opt/crypto-trading/config.json` which doesn't exist on Railway
3. ❌ **Database Initialization During Build** - Database wasn't available during build phase
4. ❌ **Separate Railway Services** - 3 separate services were created but weren't properly configured

### Solutions Applied:
1. ✅ **Unified Startup Script** - `railway_start.sh` runs all components (dashboard, agents, telegram bot) in a single service
2. ✅ **Flexible Configuration** - Updated all files to use `config_loader.py` and `agent_config_loader.py` for environment variable support
3. ✅ **Runtime Database Init** - Database initialization moved to runtime instead of build time
4. ✅ **Single Service Architecture** - Everything runs in one Railway service (more cost-effective)

---

## 📋 Prerequisites

Before deploying, you need:

1. **Railway Account** - Sign up at [railway.app](https://railway.app)
2. **GitHub Account** - Your code is already on GitHub at https://github.com/hshahrokni2/TwiLight
3. **Exchange API Keys** - At least one exchange (Binance or Kraken)
4. **OpenAI API Key** - For GPT-powered trading intelligence

---

## 🚀 Deployment Steps

### Step 1: Clean Up Existing Services

**IMPORTANT:** Delete the 3 failed services first to start fresh.

1. Go to your Railway dashboard
2. For each service (agents, telegram, web):
   - Click on the service
   - Go to Settings
   - Scroll down and click "Delete Service"

### Step 2: Create New Single Service

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **hshahrokni2/TwiLight**
4. Railway will automatically detect the configuration

### Step 3: Add PostgreSQL Database

1. In your new project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically:
   - Provision a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Link it to your service

### Step 4: Configure Environment Variables

1. Click on your service → **"Variables"** tab
2. Click **"+ New Variable"** and add the following:

#### Required Variables:

```bash
# Exchange API Keys (at least one exchange required)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

KRAKEN_API_KEY=your_kraken_api_key_here
KRAKEN_API_SECRET=your_kraken_api_secret_here

# OpenAI API Key (required for GPT-powered agents)
OPENAI_API_KEY=your_openai_api_key_here

# System Configuration
USE_ENV_CONFIG=true
PYTHONUNBUFFERED=1
```

#### Optional Variables:

```bash
# Telegram Bot (for mobile notifications)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_user_id
TELEGRAM_GROUP_CHAT_ID=your_group_id

# Additional LLM Providers
ANTHROPIC_API_KEY=your_anthropic_key
GROK_API_KEY=your_grok_key
PERPLEXITY_API_KEY=your_perplexity_key

# Trading Configuration
INITIAL_CAPITAL=100
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.05
```

### Step 5: Deploy

1. Railway will automatically deploy after you add environment variables
2. Monitor the deployment logs:
   - Click "Deployments" tab
   - Click on the latest deployment
   - Watch the build and deploy logs

### Step 6: Get Your Dashboard URL

1. Go to your service → **"Settings"** tab
2. Under **"Domains"**, click **"Generate Domain"**
3. Railway will provide a URL like: `https://your-app.up.railway.app`
4. Visit this URL to access your dashboard

### Step 7: Login to Dashboard

- Username: `admin`
- Password: `CryptoTrader2024!`

---

## 📊 What Gets Deployed

The unified deployment includes:

1. **Web Dashboard** (`stunning_dashboard.py`)
   - Real-time portfolio monitoring
   - Trading agent visualization
   - GPT-5 AI assistant integration
   - Live market data from exchanges

2. **Trading Agents** (7 agents running in background):
   - Market Data Agent - Fetches real-time prices
   - Research Agent - Analyzes market trends
   - Scalping Agent - High-frequency trading
   - Swing Agent - Medium-term trading
   - Portfolio Agent - Portfolio management
   - Risk Manager Agent - Risk assessment
   - Execution Agent - Order execution

3. **Telegram Bot** (if token provided):
   - `/status` - Portfolio status
   - `/positions` - Open positions
   - `/trades` - Recent trades
   - `/pnl` - Profit/loss summary

4. **Database Initialization**:
   - Creates all required tables
   - Sets up indexes for performance

---

## 🔍 Verifying Deployment

### Check Deployment Logs

Look for these success messages in your Railway deployment logs:

```
🚀 Starting Crypto Trading System on Railway...
📁 Working directory: /app
🗄️  Initializing database...
🌐 Running on Railway - using provided database
✅ Connected to Railway database
All tables created successfully
🤖 Starting trading agents...
   ✅ Market Data Agent started
   ✅ Research Agent started
   ✅ Scalping Agent started
   ✅ Swing Agent started
   ✅ Portfolio Agent started
   ✅ Risk Manager Agent started
   ✅ Execution Agent started
📱 Starting Telegram bot...
   ✅ Telegram Bot started
🎨 Starting dashboard...
   Dashboard will be available on port 8050
Dash is running on http://0.0.0.0:8050/
```

### Common Success Indicators:

- ✅ Build completes without errors
- ✅ All agents start successfully
- ✅ Dashboard is accessible via Railway URL
- ✅ You can login to the dashboard
- ✅ Exchange balances are displayed (if API keys are valid)

---

## 🐛 Troubleshooting

### Deployment Failed

**Check:**
1. All required environment variables are set
2. API keys are valid and have correct permissions
3. PostgreSQL database is linked to your service

**Solution:**
- Click "Redeploy" after fixing environment variables
- Check deployment logs for specific error messages

### Dashboard Shows "API Error"

**Possible Causes:**
- Invalid exchange API keys
- API keys don't have trading permissions
- Exchange is blocking requests (try Kraken if Binance fails)

**Solution:**
1. Verify API keys are correct
2. Check API key permissions on exchange website
3. Generate new API keys if needed

### Database Connection Error

**Symptoms:**
```
Error connecting to Railway database
```

**Solution:**
1. Make sure PostgreSQL is added to your project
2. Check that DATABASE_URL is set (Railway sets this automatically)
3. Restart the deployment

### Agents Not Starting

**Check Logs For:**
```
Error in agent initialization
```

**Solution:**
- Ensure config.json exists in repo OR environment variables are set
- Verify database connection is working
- Check that all dependencies are installed

### Port Already in Use

**Symptoms:**
```
Address already in use
```

**Solution:**
- This shouldn't happen on Railway (each deployment gets fresh environment)
- If it occurs, redeploy the service

---

## 📝 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Service                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         railway_start.sh (Entry Point)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ├─────────────────┬───────────────┤
│                          ▼                 ▼               ▼
│  ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   Dashboard      │  │   Agents    │  │ Telegram Bot │  │
│  │  (Foreground)    │  │ (Background)│  │ (Background) │  │
│  └──────────────────┘  └─────────────┘  └──────────────┘  │
│           │                    │                  │         │
│           └────────────────────┴──────────────────┘         │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         PostgreSQL Database (Railway)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Estimation

Railway pricing (as of 2024):

- **Hobby Plan**: $5/month
  - $5 included usage credit
  - Additional usage: $0.000463/GB-hour for memory
  - PostgreSQL included in usage

- **Pro Plan**: $20/month
  - $20 included usage credit
  - Better for production use

**Estimated Monthly Cost:**
- Small deployment: ~$5-10/month (Hobby)
- Production: ~$20-30/month (Pro)

---

## 🔒 Security Best Practices

1. **API Keys:**
   - Never commit API keys to GitHub
   - Use Railway environment variables
   - Limit API key permissions (no withdrawals)

2. **Dashboard Password:**
   - Change default password in `stunning_dashboard.py`:
     ```python
     VALID_USERNAME_PASSWORD_PAIRS = {
         'admin': 'YOUR_SECURE_PASSWORD_HERE'
     }
     ```

3. **Database:**
   - Railway automatically secures PostgreSQL
   - Don't expose database credentials

4. **Trading Risk:**
   - Start with small capital
   - Test with paper trading first
   - Set conservative risk limits

---

## 📚 Additional Resources

- **Railway Documentation**: https://docs.railway.app/
- **GitHub Repository**: https://github.com/hshahrokni2/TwiLight
- **Exchange API Docs**:
  - Binance: https://binance-docs.github.io/apidocs/
  - Kraken: https://docs.kraken.com/rest/

---

## 🎯 Next Steps After Deployment

1. **Monitor Performance:**
   - Check dashboard regularly
   - Watch trading agent decisions
   - Monitor profit/loss

2. **Adjust Parameters:**
   - Update risk management settings via environment variables
   - Modify trading pairs in config
   - Adjust position sizes

3. **Scale Up:**
   - Once comfortable, increase initial capital
   - Add more trading pairs
   - Enable additional agents

4. **Backup Data:**
   - Regularly backup database
   - Export trading history
   - Keep logs of important decisions

---

## ✅ Success Checklist

Before considering deployment complete:

- [ ] All 3 old services deleted from Railway
- [ ] New single service created and deployed successfully
- [ ] PostgreSQL database added and linked
- [ ] All required environment variables set
- [ ] Dashboard accessible via Railway URL
- [ ] Can login to dashboard with credentials
- [ ] Exchange balances showing (if API keys valid)
- [ ] Agents showing activity in Agent Intelligence panel
- [ ] Database tables created (check logs)
- [ ] Telegram bot responding (if configured)

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**: Railway deployment logs show detailed error messages
2. **Verify Config**: Double-check all environment variables
3. **Test Locally**: Try running `bash railway_start.sh` locally first
4. **GitHub Issues**: Report bugs at https://github.com/hshahrokni2/TwiLight/issues

---

**Happy Trading! 🚀📈**
