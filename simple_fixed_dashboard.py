#!/usr/bin/env python3
"""
Simple Fixed Dashboard - Shows REAL Exchange Balances
"""
from flask import Flask, render_template_string
import ccxt
import json
from datetime import datetime
import time
import threading

# Load configuration
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

STARTING_CAPITAL = 100.0

# Global cache for exchange data
data_cache = {
    'kraken_balance': 0.0,
    'kraken_status': 'Loading...',
    'kraken_holdings': [],
    'binance_balance': 0.0,
    'binance_status': 'Loading...',
    'binance_holdings': [],
    'last_update': 'Never',
    'total_value': 0.0,
    'pnl': 0.0,
    'pnl_pct': 0.0
}

def get_exchange_balance(exchange_name, api_key, api_secret):
    """Get balance from exchange"""
    try:
        if exchange_name.lower() == 'kraken':
            exchange = ccxt.kraken({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })
        else:
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })
        
        balance = exchange.fetch_balance()
        total_usd = 0.0
        holdings = []
        
        for currency, amount in balance['total'].items():
            if amount > 0:
                if currency in ['USD', 'USDT', 'USDC']:
                    usd_value = amount
                else:
                    try:
                        symbol = f"{currency}/USDT" if exchange_name == "Binance" else f"{currency}/USD"
                        ticker = exchange.fetch_ticker(symbol)
                        usd_value = amount * ticker['last']
                    except:
                        usd_value = 0
                
                total_usd += usd_value
                holdings.append({
                    'currency': currency,
                    'amount': amount,
                    'usd_value': usd_value
                })
        
        return total_usd, "Connected ✅", holdings
        
    except Exception as e:
        error_msg = str(e)
        if "restricted location" in error_msg.lower():
            return 0.0, "GEO-BLOCKED 🚫", []
        else:
            return 0.0, f"Error ❌", []

def update_data():
    """Background thread to update exchange data"""
    while True:
        try:
            # Get Kraken data
            kraken_balance, kraken_status, kraken_holdings = get_exchange_balance(
                'Kraken',
                config.get('kraken_api_key', ''),
                config.get('kraken_api_secret', '')
            )
            
            # Get Binance data
            binance_balance, binance_status, binance_holdings = get_exchange_balance(
                'Binance',
                config.get('binance_api_key', ''),
                config.get('binance_api_secret', '')
            )
            
            # Update cache
            total_value = kraken_balance + binance_balance
            pnl = total_value - STARTING_CAPITAL
            pnl_pct = (pnl / STARTING_CAPITAL) * 100 if STARTING_CAPITAL > 0 else 0
            
            data_cache.update({
                'kraken_balance': kraken_balance,
                'kraken_status': kraken_status,
                'kraken_holdings': kraken_holdings,
                'binance_balance': binance_balance,
                'binance_status': binance_status,
                'binance_holdings': binance_holdings,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'total_value': total_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
        except Exception as e:
            print(f"Error updating data: {e}")
        
        time.sleep(15)  # Update every 15 seconds

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Dashboard - REAL DATA</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body {
            background-color: #0a0a0a;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #00ff00;
            font-size: 36px;
            margin-bottom: 10px;
        }
        .warning {
            background-color: #ff8800;
            color: #000;
            padding: 15px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .card {
            background-color: #1a1a1a;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border: 2px solid #333;
        }
        .big-value {
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }
        .positive { color: #00ff00; }
        .negative { color: #ff0000; }
        .neutral { color: #ffaa00; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th {
            color: #00ff00;
            border-bottom: 2px solid #00ff00;
        }
        .exchange-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            margin-top: 10px;
        }
        .status-connected {
            background-color: #00ff00;
            color: #000;
        }
        .status-error {
            background-color: #ff0000;
            color: #fff;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 LIVE CRYPTO TRADING DASHBOARD</h1>
        <div class="warning">
            ⚠️ SHOWING REAL EXCHANGE DATA - ONE EXCHANGE IS GEO-BLOCKED
        </div>
        
        <div class="card">
            <h2>💰 Total Portfolio Value</h2>
            <div class="big-value {{ 'positive' if pnl >= 0 else 'negative' }}">
                ${{ "%.2f"|format(total_value) }}
            </div>
            <div style="font-size: 24px;" class="{{ 'positive' if pnl >= 0 else 'negative' }}">
                {{ "%.2f"|format(pnl) if pnl >= 0 else "%.2f"|format(pnl) }} 
                ({{ "%.2f"|format(pnl_pct) }}%)
            </div>
            <p style="color: #888; margin-top: 15px;">
                Starting Capital: ${{ "%.2f"|format(starting_capital) }}
            </p>
        </div>
        
        <div class="exchange-grid">
            <div class="card">
                <h3>🔹 Kraken Exchange</h3>
                <div class="big-value neutral">${{ "%.2f"|format(kraken_balance) }}</div>
                <span class="status-badge {{ 'status-connected' if 'Connected' in kraken_status else 'status-error' }}">
                    {{ kraken_status }}
                </span>
                {% if kraken_holdings %}
                <table>
                    <tr><th>Asset</th><th>Amount</th><th>Value (USD)</th></tr>
                    {% for h in kraken_holdings %}
                    <tr>
                        <td>{{ h['currency'] }}</td>
                        <td>{{ "%.8f"|format(h['amount']) }}</td>
                        <td class="positive">${{ "%.2f"|format(h['usd_value']) }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% endif %}
            </div>
            
            <div class="card">
                <h3>🔸 Binance Exchange</h3>
                <div class="big-value neutral">${{ "%.2f"|format(binance_balance) }}</div>
                <span class="status-badge {{ 'status-connected' if 'Connected' in binance_status else 'status-error' }}">
                    {{ binance_status }}
                </span>
                {% if binance_holdings %}
                <table>
                    <tr><th>Asset</th><th>Amount</th><th>Value (USD)</th></tr>
                    {% for h in binance_holdings %}
                    <tr>
                        <td>{{ h['currency'] }}</td>
                        <td>{{ "%.8f"|format(h['amount']) }}</td>
                        <td class="positive">${{ "%.2f"|format(h['usd_value']) }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% endif %}
            </div>
        </div>
        
        <div class="footer">
            Last Updated: {{ last_update }} | Auto-refresh every 15 seconds<br>
            System Status: REAL TRADING MODE | Starting Capital: $100.00
        </div>
    </div>
</body>
</html>
'''

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Render dashboard"""
    return render_template_string(
        HTML_TEMPLATE,
        starting_capital=STARTING_CAPITAL,
        total_value=data_cache['total_value'],
        pnl=data_cache['pnl'],
        pnl_pct=data_cache['pnl_pct'],
        kraken_balance=data_cache['kraken_balance'],
        kraken_status=data_cache['kraken_status'],
        kraken_holdings=data_cache['kraken_holdings'],
        binance_balance=data_cache['binance_balance'],
        binance_status=data_cache['binance_status'],
        binance_holdings=data_cache['binance_holdings'],
        last_update=data_cache['last_update']
    )

if __name__ == '__main__':
    print("Starting Simple Fixed Dashboard")
    print(f"Starting Capital: ${STARTING_CAPITAL:.2f}")
    
    # Start background update thread
    update_thread = threading.Thread(target=update_data, daemon=True)
    update_thread.start()
    
    # Give it a moment to fetch initial data
    time.sleep(2)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=3000, debug=False)
