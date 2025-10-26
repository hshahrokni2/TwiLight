
#!/usr/bin/env python3
import json
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Load config
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

def get_db_connection():
    return psycopg2.connect(**config['database'])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Welcome to Crypto Trading Bot!\n\n'
        'Available commands:\n'
        '/status - Get current portfolio status\n'
        '/positions - View open positions\n'
        '/trades - View recent trades\n'
        '/pnl - View profit/loss summary'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get portfolio status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_capital, available_capital, total_exposure, daily_pnl, total_pnl
        FROM risk_metrics
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    if result:
        msg = f"📊 *Portfolio Status*\n\n"
        msg += f"💰 Total Capital: ${result[0]:,.2f}\n"
        msg += f"💵 Available: ${result[1]:,.2f}\n"
        msg += f"📈 Exposure: ${result[2]:,.2f}\n"
        msg += f"📅 Daily PnL: ${result[3]:,.2f}\n"
        msg += f"💎 Total PnL: ${result[4]:,.2f}"
    else:
        msg = "No data available yet."
    
    cursor.close()
    conn.close()
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get open positions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, entry_price, current_price, amount
        FROM positions
        WHERE status = 'open'
    """)
    positions = cursor.fetchall()
    
    if positions:
        msg = "📍 *Open Positions*\n\n"
        for p in positions:
            pnl_pct = ((p[2] - p[1]) / p[1]) * 100
            emoji = "🟢" if pnl_pct > 0 else "🔴"
            msg += f"{emoji} {p[0]}\n"
            msg += f"   Entry: ${p[1]:,.2f} | Current: ${p[2]:,.2f}\n"
            msg += f"   Amount: {p[3]:.6f} | PnL: {pnl_pct:+.2f}%\n\n"
    else:
        msg = "No open positions."
    
    cursor.close()
    conn.close()
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get recent trades"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, symbol, side, price, amount
        FROM trades
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    trades = cursor.fetchall()
    
    if trades:
        msg = "📝 *Recent Trades*\n\n"
        for t in trades:
            emoji = "🟢" if t[2] == 'buy' else "🔴"
            msg += f"{emoji} {t[2].upper()} {t[1]}\n"
            msg += f"   Price: ${t[3]:,.2f} | Amount: {t[4]:.6f}\n"
            msg += f"   Time: {t[0].strftime('%H:%M:%S')}\n\n"
    else:
        msg = "No trades yet."
    
    cursor.close()
    conn.close()
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get PnL summary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT daily_pnl, total_pnl, total_capital
        FROM risk_metrics
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    if result:
        daily_pnl, total_pnl, total_capital = result
        daily_pct = (daily_pnl / total_capital) * 100
        total_pct = (total_pnl / config['initial_capital']) * 100
        
        msg = f"💰 *Profit/Loss Summary*\n\n"
        msg += f"📅 Daily PnL: ${daily_pnl:,.2f} ({daily_pct:+.2f}%)\n"
        msg += f"💎 Total PnL: ${total_pnl:,.2f} ({total_pct:+.2f}%)\n"
        msg += f"📊 Total Capital: ${total_capital:,.2f}"
    else:
        msg = "No data available yet."
    
    cursor.close()
    conn.close()
    
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(config['telegram']['bot_token']).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("positions", positions))
    application.add_handler(CommandHandler("trades", trades))
    application.add_handler(CommandHandler("pnl", pnl))
    
    # Start the bot
    print("Telegram bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
