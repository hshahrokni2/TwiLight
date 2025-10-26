# 🚂 Railway Deployment Guide - Complete & Working

This comprehensive guide will help you deploy the Crypto Trading System on Railway successfully.

## 🎯 Overview

This system runs as a **single unified service** on Railway that includes:
- 📊 **Dashboard** - Beautiful web interface on port 8050
- 🤖 **7 Trading Agents** - Market data, research, scalping, swing, portfolio, risk manager, and execution
- 📱 **Telegram Bot** - Real-time notifications (optional)
- 🗄️ **PostgreSQL Database** - Automatically provided by Railway
- 🔄 **Redis Cache** - Optional, for better performance

---

## ✅ Prerequisites

Before deploying, you need:

1. **Railway Account** - Sign up at [railway.app](https://railway.app)
2. **GitHub Repository** - Your code at https://github.com/hshahrokni2/TwiLight
3. **Exchange API Keys** - At least one exchange:
   - **Kraken** (recommended - works globally)
   - **Binance** (may be geo-restricted in USA)
4. **OpenAI API Key** - Required for GPT-powered trading agents
5. **Optional APIs**:
   - Anthropic (Claude)
   - Grok
   - Perplexity
   - Telegram Bot (for notifications)

---

## 🚀 Deployment Steps

### Step 1: Create New Project in Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select **hshahrokni2/TwiLight** repository
6. Click **"Deploy Now"**

Railway will automatically detect the configuration from `railway.json` and `nixpacks.toml`.

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Link it to your service

**Important:** The database is required - the system will not work without it.

### Step 3: Configure Environment Variables

Click on your service → **"Variables"** tab → Add these required variables:

#### **Required Variables:**

```bash
# Exchange API Keys (at least one exchange required)
KRAKEN_API_KEY=your_kraken_api_key_here
KRAKEN_API_SECRET=your_kraken_secret_here

# Or use Binance (may be geo-restricted)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_secret_here

# OpenAI API Key (required for GPT agents)
OPENAI_API_KEY=sk-your-openai-key-here

# DATABASE_URL is automatically set by Railway when you add PostgreSQL
# You don't need to set this manually
```

#### **Optional Variables:**

```bash
# Additional LLM Providers
ANTHROPIC_API_KEY=your_claude_api_key_here
GROK_API_KEY=your_grok_api_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
TELEGRAM_GROUP_CHAT_ID=your_group_chat_id

# Trading Parameters
INITIAL_CAPITAL=100
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.05

# Redis (optional - for better performance)
# REDIS_URL is automatically set by Railway if you add Redis
```

### Step 4: Deploy and Monitor

1. After setting environment variables, Railway will automatically redeploy
2. Watch the deployment logs in real-time
3. Look for these success messages:
   ```
   ✅ Successfully connected to Railway database!
   ✅ Configuration loaded from environment variables
   ✅ All tables created successfully
   ✅ Market Data Agent started
   ✅ Research Agent started
   ... (and 5 more agents)
   ```

### Step 5: Access Your Dashboard

1. In Railway, click on your service
2. Go to **"Settings"** tab
3. Under **"Networking"**, you'll see your public URL
4. Click the URL to open your dashboard

**Dashboard URL will be:** `https://your-app-name.up.railway.app`

---

## 🔍 Troubleshooting

### Error: "connection to server at localhost failed"

**Cause:** DATABASE_URL is not set
**Solution:** 
1. Make sure you added PostgreSQL to your Railway project
2. The DATABASE_URL should be automatically set
3. Check Variables tab to confirm DATABASE_URL exists

### Error: "Could not find config.json"

**Cause:** Agent is looking for config.json instead of using environment variables
**Solution:**
1. Make sure you're using the latest code with the fixes
2. Verify DATABASE_URL is set (this tells the system to use environment variables)
3. Check that all required API keys are set in Railway Variables

### Error: "ModuleNotFoundError: No module named 'dash_auth'"

**Cause:** Missing Python package
**Solution:** This is fixed in the latest requirements.txt. Redeploy the service.

### Agents Not Starting

**Symptoms:** Dashboard loads but shows "0 agents active"
**Solutions:**
1. Check deployment logs for agent errors
2. Verify all required environment variables are set
3. Ensure database tables were created successfully
4. Look for specific error messages about missing API keys

### Database Connection Timeouts

**Cause:** Database may be cold-starting
**Solution:** 
1. Wait 30-60 seconds and refresh
2. Check Railway dashboard for database status
3. Restart the service if needed

---

## 📊 Monitoring Your System

### Check Logs

In Railway:
1. Click on your service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. View **"Build Logs"** and **"Deploy Logs"**

### Watch Agent Activity

In your dashboard at `https://your-app-name.up.railway.app`:
1. **Agent Intelligence** section shows active agents
2. **Orchestrator Pipeline** shows decision flow
3. **Portfolio Value** displays your trading performance

### Telegram Notifications (if configured)

If you set TELEGRAM_BOT_TOKEN, you'll receive:
- Trade notifications
- Agent decisions
- Risk warnings
- System status updates

---

## 🔐 Security Best Practices

### API Key Management

1. **Never commit API keys to GitHub**
   - config.json is in .gitignore
   - Always use Railway environment variables for deployment

2. **Use API keys with minimal permissions**
   - Kraken: Enable only "Query Funds" and "Create & Modify Orders"
   - Binance: Enable only "Enable Reading" and "Enable Spot & Margin Trading"
   - Never enable withdrawal permissions

3. **Rotate keys regularly**
   - Change API keys every 3-6 months
   - Update immediately if compromised

### Railway Project Security

1. Make your Railway project private
2. Use Railway's built-in authentication
3. Don't share your deployment URLs publicly

---

## 💰 Cost Estimates

### Railway Costs (Monthly)

- **Starter Plan:** $5/month
  - 512 MB RAM
  - Shared CPU
  - Good for testing

- **Developer Plan:** $20/month
  - 8 GB RAM
  - Dedicated CPU
  - Recommended for live trading

### API Costs (Monthly)

- **OpenAI GPT-4:** ~$10-50 depending on usage
- **Kraken/Binance:** Free (pay only trading fees)
- **Database & Redis:** Included in Railway plan

**Total estimated cost:** $35-70/month

---

## 🔄 Updates and Maintenance

### Update Your Deployment

1. Push changes to GitHub main branch
2. Railway automatically detects and redeploys
3. Or manually trigger redeploy in Railway dashboard

### Backup Your Database

Railway provides automatic backups for paid plans. To export manually:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Export database
railway run pg_dump $DATABASE_URL > backup.sql
```

### Monitor Performance

Check these metrics regularly:
- **Agent uptime** - Should be >99%
- **Trade execution success** - Target >95%
- **Win rate** - Varies by strategy
- **Sharpe ratio** - Higher is better

---

## 🆘 Support and Resources

### Documentation

- **Main README:** See README.md for system architecture
- **Local Development:** Use config.json.template to create config.json
- **API Docs:** Check exchange documentation for API details

### Common Issues

- **Geo-restrictions:** Use Kraken if Binance is blocked in your region
- **Rate limits:** The system uses `enableRateLimit: true` to avoid issues
- **Cold starts:** First request after inactivity may be slow (Railway limitation)

### Getting Help

1. Check deployment logs in Railway
2. Review this guide's troubleshooting section
3. Check agent log messages for specific errors
4. Verify all environment variables are set correctly

---

## 📋 Deployment Checklist

Before going live, verify:

- [ ] PostgreSQL database added to Railway project
- [ ] DATABASE_URL environment variable is set (automatic)
- [ ] At least one exchange API key configured (KRAKEN or BINANCE)
- [ ] OPENAI_API_KEY is set
- [ ] All API keys are valid and have correct permissions
- [ ] Service deployed successfully (green checkmark in Railway)
- [ ] Dashboard is accessible at your Railway URL
- [ ] At least 7 agents show as "active" in dashboard
- [ ] Database tables created successfully (check logs)
- [ ] No critical errors in deployment logs

---

## 🎉 Success!

If you see:
- ✅ Dashboard loads without errors
- ✅ All 7 agents are active
- ✅ Portfolio value is displayed
- ✅ No critical errors in logs

**Congratulations!** Your crypto trading system is live and operational on Railway! 🚀

---

## 📝 Environment Variables Reference

### Complete List of Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ Auto | PostgreSQL connection URL | `postgresql://user:pass@host:5432/db` |
| `KRAKEN_API_KEY` | ✅* | Kraken exchange API key | `your_key_here` |
| `KRAKEN_API_SECRET` | ✅* | Kraken exchange API secret | `your_secret_here` |
| `BINANCE_API_KEY` | ✅* | Binance exchange API key | `your_key_here` |
| `BINANCE_API_SECRET` | ✅* | Binance exchange API secret | `your_secret_here` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for GPT-4 | `sk-...` |
| `ANTHROPIC_API_KEY` | ⭕ | Claude API key | `sk-ant-...` |
| `GROK_API_KEY` | ⭕ | Grok API key | `gsk-...` |
| `PERPLEXITY_API_KEY` | ⭕ | Perplexity API key | `pplx-...` |
| `TELEGRAM_BOT_TOKEN` | ⭕ | Telegram bot token | `123456:ABC-DEF...` |
| `TELEGRAM_USER_ID` | ⭕ | Your Telegram user ID | `7171577450` |
| `TELEGRAM_GROUP_CHAT_ID` | ⭕ | Telegram group chat ID | `-4800163944` |
| `REDIS_URL` | ⭕ Auto | Redis connection URL | `redis://host:6379` |
| `INITIAL_CAPITAL` | ⭕ | Starting capital | `100` |
| `MAX_POSITION_SIZE` | ⭕ | Max position size (decimal) | `0.1` |
| `MAX_DAILY_LOSS` | ⭕ | Max daily loss (decimal) | `0.05` |
| `STOP_LOSS_PERCENTAGE` | ⭕ | Stop loss percentage | `0.02` |
| `TAKE_PROFIT_PERCENTAGE` | ⭕ | Take profit percentage | `0.05` |

**Legend:**
- ✅ = Required
- ✅ Auto = Automatically set by Railway
- ✅* = At least one exchange required (Kraken OR Binance)
- ⭕ = Optional

---

## 🔗 Useful Links

- **Railway Dashboard:** https://railway.app/dashboard
- **GitHub Repository:** https://github.com/hshahrokni2/TwiLight
- **Railway Documentation:** https://docs.railway.app/
- **Kraken API Docs:** https://docs.kraken.com/rest/
- **Binance API Docs:** https://binance-docs.github.io/apidocs/spot/en/
- **OpenAI API Docs:** https://platform.openai.com/docs/

---

**Last Updated:** October 26, 2025
**Version:** 2.0 (Complete Railway deployment fixes applied)
