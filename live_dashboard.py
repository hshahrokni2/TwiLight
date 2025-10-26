import dash
from dash import dcc, html, Input, Output
import ccxt
import json
import time
from datetime import datetime
import threading

print("Loading configuration...")
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

binance_key = config.get('binance_api_key', '')
binance_secret = config.get('binance_api_secret', '')
kraken_key = config.get('kraken_api_key', '')
kraken_secret = config.get('kraken_api_secret', '')

print("Initializing exchanges...")
exchanges = {}

if binance_key and binance_secret:
    exchanges['binance'] = ccxt.binance({
        'apiKey': binance_key,
        'secret': binance_secret,
        'timeout': 10000,
        'enableRateLimit': True
    })
    print("✓ Binance configured")
else:
    exchanges['binance'] = None
    print("✗ Binance not configured")

if kraken_key and kraken_secret:
    exchanges['kraken'] = ccxt.kraken({
        'apiKey': kraken_key,
        'secret': kraken_secret,
        'timeout': 10000,
        'enableRateLimit': True
    })
    print("✓ Kraken configured")
else:
    exchanges['kraken'] = None
    print("✗ Kraken not configured")

# Simple cache
cache = {}
cache_lock = threading.Lock()

def get_cached(key, fetch_func, ttl=30):
    with cache_lock:
        now = time.time()
        if key in cache:
            data, timestamp, error = cache[key]
            if now - timestamp < ttl:
                return data, error
        
        try:
            data = fetch_func()
            cache[key] = (data, now, None)
            return data, None
        except Exception as e:
            error_msg = str(e)
            if key in cache:
                old_data, _, _ = cache[key]
                cache[key] = (old_data, now, error_msg)
                return old_data, error_msg
            cache[key] = ({}, now, error_msg)
            return {}, error_msg

def fetch_binance_balance():
    if not exchanges['binance']:
        raise Exception("Not configured")
    return exchanges['binance'].fetch_balance().get('total', {})

def fetch_kraken_balance():
    if not exchanges['kraken']:
        raise Exception("Not configured")
    return exchanges['kraken'].fetch_balance().get('total', {})

print("Creating Dash app...")
app = dash.Dash(__name__)
app.title = "Live Crypto Trading Dashboard"

app.layout = html.Div([
    html.H1("🚀 Live Crypto Trading Dashboard", 
            style={'textAlign': 'center', 'color': '#00ff00', 'marginBottom': '20px'}),
    
    html.Div(id='status-bar', style={'textAlign': 'center', 'fontSize': '18px', 'marginBottom': '30px'}),
    
    html.Div([
        html.Div([
            html.H2("💰 Portfolio Value", style={'color': '#00ff00'}),
            html.Div(id='portfolio-value', style={'fontSize': '42px', 'fontWeight': 'bold', 'color': '#00ff00'})
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '30px', 
                  'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'}),
        
        html.Div([
            html.H2("📊 Exchange Status", style={'color': '#00ff00'}),
            html.Div(id='exchange-status', style={'fontSize': '16px'})
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '30px', 
                  'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'})
    ]),
    
    html.Div([
        html.H2("💼 Account Balances", style={'color': '#00ff00'}),
        html.Div(id='balances', style={'fontSize': '16px'})
    ], style={'padding': '30px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'}),
    
    html.Div([
        html.H2("🤖 System Status", style={'color': '#00ff00'}),
        html.Div(id='system-status', style={'fontSize': '14px'})
    ], style={'padding': '30px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'}),
    
    dcc.Interval(id='update-interval', interval=5000, n_intervals=0)
    
], style={'backgroundColor': '#0a0a0a', 'color': '#ffffff', 'fontFamily': 'Arial', 
          'padding': '20px', 'minHeight': '100vh'})

@app.callback(
    [Output('status-bar', 'children'),
     Output('portfolio-value', 'children'),
     Output('exchange-status', 'children'),
     Output('balances', 'children'),
     Output('system-status', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_all(n):
    # Fetch data
    binance_bal, binance_err = get_cached('binance', fetch_binance_balance, 30)
    kraken_bal, kraken_err = get_cached('kraken', fetch_kraken_balance, 30)
    
    # Status bar
    if binance_err and "451" in str(binance_err):
        status = html.Div("⚠️ BINANCE GEO-BLOCKED - Complete NordVPN Setup", 
                         style={'color': '#ff0000', 'fontWeight': 'bold', 'fontSize': '20px'})
    elif binance_err or kraken_err:
        status = html.Div("⚠️ Some API Errors Detected", 
                         style={'color': '#ffaa00', 'fontWeight': 'bold'})
    else:
        status = html.Div("✓ All Systems Operational", 
                         style={'color': '#00ff00', 'fontWeight': 'bold'})
    
    # Calculate portfolio value
    btc_price = 67000
    eth_price = 2600
    
    binance_usd = (binance_bal.get('USDT', 0) + binance_bal.get('BUSD', 0) + 
                   binance_bal.get('BTC', 0) * btc_price + 
                   binance_bal.get('ETH', 0) * eth_price)
    
    kraken_usd = (kraken_bal.get('USD', 0) + kraken_bal.get('USDT', 0) + 
                  kraken_bal.get('BTC', 0) * btc_price + 
                  kraken_bal.get('ETH', 0) * eth_price)
    
    total = binance_usd + kraken_usd
    portfolio = f"${total:,.2f}"
    
    # Exchange status
    binance_status = "🔴 Geo-Blocked (451)" if (binance_err and "451" in str(binance_err)) else ("🔴 Error" if binance_err else "🟢 Connected")
    kraken_status = "🔴 Error" if kraken_err else "🟢 Connected"
    
    exchange_status = html.Div([
        html.Div([html.Strong("Binance: "), binance_status], style={'marginBottom': '10px'}),
        html.Div([html.Strong("Kraken: "), kraken_status])
    ])
    
    # Balances
    balances = html.Div([
        html.Div([
            html.H3("Binance", style={'color': '#ffaa00'}),
            html.Div(f"Value: ${binance_usd:,.2f}" if not binance_err else f"Error: {binance_err[:50]}"),
            html.Div(f"USDT: {binance_bal.get('USDT', 0):.2f}"),
            html.Div(f"BTC: {binance_bal.get('BTC', 0):.8f}"),
            html.Div(f"ETH: {binance_bal.get('ETH', 0):.6f}"),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '20px'}),
        
        html.Div([
            html.H3("Kraken", style={'color': '#ffaa00'}),
            html.Div(f"Value: ${kraken_usd:,.2f}" if not kraken_err else f"Error: {kraken_err[:50]}"),
            html.Div(f"USD: {kraken_bal.get('USD', 0):.2f}"),
            html.Div(f"BTC: {kraken_bal.get('BTC', 0):.8f}"),
            html.Div(f"ETH: {kraken_bal.get('ETH', 0):.6f}"),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '20px'})
    ])
    
    # System status
    current_time = datetime.now().strftime('%H:%M:%S')
    system = html.Div([
        html.Div(f"[{current_time}] Dashboard running on port 8050", style={'color': '#00ff00'}),
        html.Div(f"[{current_time}] Last update: {n} intervals", style={'color': '#00aaff'}),
        html.Div(f"[{current_time}] Kraken: {len([k for k,v in kraken_bal.items() if v > 0])} assets", style={'color': '#00ff00'}),
        html.Div(f"[{current_time}] Binance: {'Geo-blocked - VPN needed' if binance_err and '451' in str(binance_err) else 'OK'}", 
                style={'color': '#ff0000' if (binance_err and '451' in str(binance_err)) else '#00ff00'}),
    ])
    
    return status, portfolio, exchange_status, balances, system

if __name__ == '__main__':
    print("Starting dashboard on port 8050...")
    app.run(host='0.0.0.0', port=8050, debug=False)
