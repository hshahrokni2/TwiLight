#!/bin/bash
# Railway Unified Startup Script
# This script runs all components of the crypto trading system

set -e  # Exit on error

echo "🚀 Starting Crypto Trading System on Railway..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $(pwd)"

# Initialize database if needed
echo "🗄️  Initializing database..."
python init_db.py || echo "⚠️  Database initialization skipped (may already exist)"

# Wait a moment for database to be ready
sleep 2

# Start all agents in background
echo "🤖 Starting trading agents..."
python agents/market_data_agent.py &
AGENT_PIDS[0]=$!
echo "   ✅ Market Data Agent started (PID: ${AGENT_PIDS[0]})"

python agents/research_agent.py &
AGENT_PIDS[1]=$!
echo "   ✅ Research Agent started (PID: ${AGENT_PIDS[1]})"

python agents/scalping_agent.py &
AGENT_PIDS[2]=$!
echo "   ✅ Scalping Agent started (PID: ${AGENT_PIDS[2]})"

python agents/swing_agent.py &
AGENT_PIDS[3]=$!
echo "   ✅ Swing Agent started (PID: ${AGENT_PIDS[3]})"

python agents/portfolio_agent.py &
AGENT_PIDS[4]=$!
echo "   ✅ Portfolio Agent started (PID: ${AGENT_PIDS[4]})"

python agents/risk_manager_agent.py &
AGENT_PIDS[5]=$!
echo "   ✅ Risk Manager Agent started (PID: ${AGENT_PIDS[5]})"

python agents/execution_agent.py &
AGENT_PIDS[6]=$!
echo "   ✅ Execution Agent started (PID: ${AGENT_PIDS[6]})"

# Start Telegram bot in background
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "📱 Starting Telegram bot..."
    python telegram_bot.py &
    TELEGRAM_PID=$!
    echo "   ✅ Telegram Bot started (PID: $TELEGRAM_PID)"
else
    echo "   ⚠️  Telegram bot skipped (TELEGRAM_BOT_TOKEN not set)"
fi

# Wait a moment for agents to initialize
sleep 3

# Start dashboard in foreground (Railway needs a foreground process)
echo "🎨 Starting dashboard..."
echo "   Dashboard will be available on port ${PORT:-8050}"
exec python stunning_dashboard.py

# Cleanup function (called on exit)
cleanup() {
    echo "🛑 Shutting down..."
    for pid in "${AGENT_PIDS[@]}" $TELEGRAM_PID; do
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
        fi
    done
    echo "✅ Shutdown complete"
}

trap cleanup EXIT INT TERM
