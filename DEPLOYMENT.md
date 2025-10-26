# 🚂 Railway Deployment Guide

Quick guide to deploy TwiLight to Railway.

## 🎯 Quick Start

### 1. Create Railway Project

1. Go to **https://railway.app/new**
2. Click **"Deploy from GitHub repo"**
3. Select **`hshahrokni2/TwiLight`**

### 2. Add Databases

1. Click **"New"** → **"Database"** → **"PostgreSQL"**
2. Click **"New"** → **"Database"** → **"Redis"**
3. Railway automatically sets `DATABASE_URL` and `REDIS_URL`

### 3. Configure Environment Variables

Click on your service → **Variables** tab → **RAW Editor**

Copy the template below and replace with your actual values:

```bash
# Exchange APIs
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
KRAKEN_API_KEY=your_kraken_key
KRAKEN_API_SECRET=your_kraken_secret

# LLM APIs
OPENAI_API_KEY=sk-proj-your_key
ANTHROPIC_API_KEY=sk-ant-your_key
GROK_API_KEY=xai-your_key
PERPLEXITY_API_KEY=pplx-your_key

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=7171577450
TELEGRAM_GROUP_CHAT_ID=-4800163944

# Trading Config
INITIAL_CAPITAL=100
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.05
USE_ENV_CONFIG=true
PORT=8050
```

**💡 Your actual production credentials are saved locally in `CREDENTIALS.env`**

### 4. Deploy

1. Click **"Save"** - Railway auto-deploys
2. Go to **Settings** → **Generate Domain**
3. Access your dashboard at the generated URL!

## ✅ Verification

- Dashboard loads and shows portfolio
- Exchange connections: ✅ Connected
- Trading agents operational
- Telegram bot responding

## 📊 Monitor

- View logs in **Deployments** tab
- Check for: `✅ Dash is running on...`
- Watch agent decisions in real-time

## 🔄 Updates

Push to GitHub → Railway auto-deploys:
```bash
git add .
git commit -m "Update"
git push origin main
```

## 💰 Cost

- Hobby Plan: $5/month (500 hours)
- Pro Plan: $20/month (unlimited)
- Databases: Included

## 🆘 Troubleshooting

**Dashboard not loading?**
- Check logs for errors
- Verify DATABASE_URL exists
- Check domain is generated

**Exchange errors?**
- Verify API keys (no spaces)
- Check IP whitelist disabled
- Verify trading permissions enabled

**Agents not starting?**
- Check LLM API keys valid
- Verify Redis connected
- Check logs for errors

## 🔗 Links

- **GitHub**: https://github.com/hshahrokni2/TwiLight
- **Railway**: https://railway.app/dashboard
- **Docs**: See README.md for full documentation

## 🎉 Success!

After deployment:
- ✅ Code on GitHub
- ✅ Railway project running
- ✅ Dashboard accessible
- ✅ Trading agents operational
- ✅ Ready to trade!

---

*See `CREDENTIALS.env` locally for your actual production API keys*
