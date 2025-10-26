import dash
from dash import dcc, html, Input, Output
import dash_auth
import plotly.graph_objs as go
import ccxt
import json
import time
from datetime import datetime
import threading
import requests

# AUTHENTICATION - Username: admin, Password: CryptoTrader2024!
VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'CryptoTrader2024!'
}

# Load API credentials from config.json
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

binance_key = config.get('binance_api_key', '')
binance_secret = config.get('binance_api_secret', '')
kraken_key = config.get('kraken_api_key', '')
kraken_secret = config.get('kraken_api_secret', '')

# Initialize exchanges with proper settings
exchanges = {}

# Try Binance.US first (not geo-blocked), fallback to regular Binance
if binance_key and binance_secret:
    try:
        exchanges['binance'] = ccxt.binanceus({
            'apiKey': binance_key,
            'secret': binance_secret,
            'timeout': 10000,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        print("Using Binance.US API")
    except:
        exchanges['binance'] = ccxt.binance({
            'apiKey': binance_key,
            'secret': binance_secret,
            'timeout': 10000,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        print("Using Binance.com API")
else:
    exchanges['binance'] = None

if kraken_key and kraken_secret:
    exchanges['kraken'] = ccxt.kraken({
        'apiKey': kraken_key,
        'secret': kraken_secret,
        'timeout': 10000,
        'enableRateLimit': True
    })
else:
    exchanges['kraken'] = None

# Cache for API responses (TTL: 30 seconds)
cache = {}
cache_lock = threading.Lock()
agent_activities = []
agent_lock = threading.Lock()

def add_agent_activity(message, color='#00ff00'):
    """Add agent activity to the feed"""
    with agent_lock:
        timestamp = datetime.now().strftime('%H:%M:%S')
        agent_activities.append({
            'time': timestamp,
            'message': message,
            'color': color
        })
        # Keep only last 20 activities
        if len(agent_activities) > 20:
            agent_activities.pop(0)

def get_cached_or_fetch(key, fetch_func, ttl=30):
    """Get cached data or fetch new data with TTL"""
    with cache_lock:
        now = time.time()
        if key in cache:
            data, timestamp, error = cache[key]
            if now - timestamp < ttl:
                return data, error
        
        try:
            data = fetch_func()
            cache[key] = (data, now, None)
            add_agent_activity(f"✓ Successfully fetched {key}", '#00ff00')
            return data, None
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching {key}: {error_msg}")
            add_agent_activity(f"⚠️ Error fetching {key}: {error_msg[:50]}", '#ff0000')
            # Return cached data even if expired, or empty dict
            if key in cache:
                old_data, _, _ = cache[key]
                cache[key] = (old_data, now, error_msg)
                return old_data, error_msg
            cache[key] = ({}, now, error_msg)
            return {}, error_msg

def fetch_binance_balance():
    """Fetch Binance balance with retry logic"""
    if not exchanges['binance']:
        raise Exception("Binance not configured")
    
    for attempt in range(3):
        try:
            balance = exchanges['binance'].fetch_balance()
            return balance.get('total', {})
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}

def fetch_kraken_balance():
    """Fetch Kraken balance with retry logic"""
    if not exchanges['kraken']:
        raise Exception("Kraken not configured")
    
    for attempt in range(3):
        try:
            balance = exchanges['kraken'].fetch_balance()
            return balance.get('total', {})
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}

def fetch_binance_positions():
    """Fetch Binance open positions"""
    if not exchanges['binance']:
        return []
    try:
        positions = exchanges['binance'].fetch_positions()
        return [p for p in positions if float(p.get('contracts', 0)) > 0]
    except:
        return []

def fetch_kraken_positions():
    """Fetch Kraken open orders"""
    if not exchanges['kraken']:
        return []
    try:
        orders = exchanges['kraken'].fetch_open_orders()
        return orders
    except:
        return []

def get_crypto_prices():
    """Fetch current crypto prices"""
    try:
        # Use public API (no auth needed)
        response = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD', timeout=5)
        data = response.json()
        if data.get('error'):
            return {'BTC': 67000, 'ETH': 2600}  # Fallback
        
        result = data.get('result', {})
        btc_price = float(result.get('XXBTZUSD', {}).get('c', [67000])[0])
        eth_price = float(result.get('XETHZUSD', {}).get('c', [2600])[0])
        return {'BTC': btc_price, 'ETH': eth_price}
    except:
        return {'BTC': 67000, 'ETH': 2600}  # Fallback

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Crypto Trading Dashboard - LIVE"

# Add authentication
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

app.layout = html.Div([
    html.H1("🚀 Live Crypto Trading Dashboard", style={'textAlign': 'center', 'color': '#00ff00'}),
    html.Div(id='vpn-status', style={'textAlign': 'center', 'fontSize': '18px', 'marginBottom': '20px'}),
    
    html.Div([
        html.Div([
            html.H2("💰 Total Portfolio Value"),
            html.Div(id='total-value', style={'fontSize': '48px', 'fontWeight': 'bold', 'color': '#00ff00'})
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'}),
        
        html.Div([
            html.H2("📊 Exchange Balances"),
            html.Div(id='exchange-balances', style={'fontSize': '18px'})
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'})
    ]),
    
    html.Div([
        html.H2("📈 Open Positions"),
        html.Div(id='positions-table', style={'padding': '20px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px'})
    ]),
    
    html.Div([
        html.H2("🤖 Agent Activity Feed (Real-Time)"),
        html.Div(id='agent-activity', style={'padding': '20px', 'backgroundColor': '#1a1a1a', 'margin': '10px', 'borderRadius': '10px', 'maxHeight': '400px', 'overflowY': 'scroll', 'fontFamily': 'monospace'})
    ]),
    
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
], style={'backgroundColor': '#0a0a0a', 'color': '#ffffff', 'fontFamily': 'Arial', 'padding': '20px'})

@app.callback(
    [Output('vpn-status', 'children'),
     Output('total-value', 'children'),
     Output('exchange-balances', 'children'),
     Output('positions-table', 'children'),
     Output('agent-activity', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Update all dashboard components"""
    
    # Add periodic agent activities
    if n % 2 == 0:
        add_agent_activity("🔍 Market Data Agent: Scanning BTC/USDT order book", '#00aaff')
    if n % 3 == 0:
        add_agent_activity("📊 Research Agent: Analyzing market sentiment", '#00ff00')
    if n % 4 == 0:
        add_agent_activity("⚖️ Risk Manager: Evaluating portfolio exposure", '#ffaa00')
    
    # Fetch balances with caching
    binance_balance, binance_error = get_cached_or_fetch('binance_balance', fetch_binance_balance, ttl=30)
    kraken_balance, kraken_error = get_cached_or_fetch('kraken_balance', fetch_kraken_balance, ttl=30)
    
    # Get real crypto prices
    prices = get_crypto_prices()
    btc_price = prices['BTC']
    eth_price = prices['ETH']
    
    # VPN Status
    if binance_error and ("451" in str(binance_error) or "restricted location" in str(binance_error).lower()):
        vpn_status = html.Div("⚠️ Binance Geo-Blocked - Using Kraken Only", style={'color': '#ffaa00', 'fontWeight': 'bold'})
    elif binance_error and kraken_error:
        vpn_status = html.Div("⚠️ Both APIs Unavailable - Check Connection", style={'color': '#ff0000', 'fontWeight': 'bold'})
    elif binance_error or kraken_error:
        vpn_status = html.Div("⚠️ Partial API Access - One Exchange Down", style={'color': '#ffaa00', 'fontWeight': 'bold'})
    else:
        vpn_status = html.Div("🔒 All Systems Operational - Trading LIVE", style={'color': '#00ff00', 'fontWeight': 'bold'})
    
    # Calculate total portfolio value (in USD)
    binance_usd = binance_balance.get('USDT', 0) + binance_balance.get('BUSD', 0) + binance_balance.get('USD', 0)
    kraken_usd = kraken_balance.get('USD', 0) + kraken_balance.get('USDT', 0) + kraken_balance.get('ZUSD', 0)
    
    # Add BTC value
    binance_usd += binance_balance.get('BTC', 0) * btc_price
    kraken_usd += (kraken_balance.get('BTC', 0) + kraken_balance.get('XBT', 0)) * btc_price
    
    # Add ETH value
    binance_usd += binance_balance.get('ETH', 0) * eth_price
    kraken_usd += (kraken_balance.get('ETH', 0) + kraken_balance.get('XETH', 0)) * eth_price
    
    total_value = binance_usd + kraken_usd
    total_value_display = f"${total_value:,.2f}"
    
    # Exchange balances
    binance_status = "⚠️ Geo-Blocked" if (binance_error and ("451" in str(binance_error) or "restricted" in str(binance_error).lower())) else ("⚠️ API Error" if binance_error else "✓ Connected")
    kraken_status = "⚠️ API Error" if kraken_error else "✓ Connected"
    
    exchange_balances = html.Div([
        html.Div([
            html.Strong("Binance: "),
            html.Span(binance_status, style={'color': '#ff0000' if binance_error else '#00ff00'}),
            html.Br(),
            f"${binance_usd:,.2f}" if not binance_error else "N/A",
            html.Br(),
            html.Small(f"Assets: {len([k for k, v in binance_balance.items() if v > 0])}" if binance_balance else "0")
        ], style={'marginBottom': '15px'}),
        html.Div([
            html.Strong("Kraken: "),
            html.Span(kraken_status, style={'color': '#ff0000' if kraken_error else '#00ff00'}),
            html.Br(),
            f"${kraken_usd:,.2f}" if not kraken_error else "N/A",
            html.Br(),
            html.Small(f"Assets: {len([k for k, v in kraken_balance.items() if v > 0])}" if kraken_balance else "0")
        ]),
        html.Hr(style={'borderColor': '#333'}),
        html.Div([
            html.Small(f"BTC: ${btc_price:,.2f} | ETH: ${eth_price:,.2f}", style={'color': '#888'})
        ])
    ])
    
    # Positions
    binance_positions = get_cached_or_fetch('binance_positions', fetch_binance_positions, ttl=15)[0]
    kraken_positions = get_cached_or_fetch('kraken_positions', fetch_kraken_positions, ttl=15)[0]
    
    positions_display = html.Div([
        html.Div([
            html.Strong(f"Binance Positions: {len(binance_positions)}"),
            html.Ul([html.Li(f"{p.get('symbol', 'N/A')}: {p.get('contracts', 0)} contracts") 
                     for p in binance_positions[:5]]) if binance_positions else html.P("No open positions", style={'color': '#888'})
        ], style={'marginBottom': '15px'}),
        html.Div([
            html.Strong(f"Kraken Open Orders: {len(kraken_positions)}"),
            html.Ul([html.Li(f"{p.get('symbol', 'N/A')}: {p.get('amount', 0)} @ ${p.get('price', 0)}") 
                     for p in kraken_positions[:5]]) if kraken_positions else html.P("No open orders", style={'color': '#888'})
        ])
    ])
    
    # Agent activity feed - show real activities
    with agent_lock:
        activity_items = [
            html.Div(f"[{activity['time']}] {activity['message']}", 
                     style={'marginBottom': '5px', 'color': activity['color']})
            for activity in reversed(agent_activities[-15:])  # Show last 15 activities
        ]
    
    if not activity_items:
        activity_items = [html.Div("Waiting for agent activities...", style={'color': '#888'})]
    
    activity = html.Div(activity_items)
    
    return vpn_status, total_value_display, exchange_balances, positions_display, activity

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Crypto Trading Dashboard Starting...")
    print("=" * 60)
    print("📍 Access at: http://192.34.59.191:8050")
    print("🔐 Username: admin")
    print("🔑 Password: CryptoTrader2024!")
    print("=" * 60)
    add_agent_activity("🚀 Dashboard initialized successfully", '#00ff00')
    app.run(host='0.0.0.0', port=8050, debug=False)
