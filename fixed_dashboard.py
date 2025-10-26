#!/usr/bin/env python3
"""
Fixed Crypto Trading Dashboard - Shows REAL Exchange Data
"""
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import ccxt
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

# Initialize exchanges
STARTING_CAPITAL = 100.0  # Fixed: $100 starting capital

def get_kraken_client():
    """Get Kraken exchange client"""
    try:
        return ccxt.kraken({
            'apiKey': config.get('kraken_api_key', ''),
            'secret': config.get('kraken_api_secret', ''),
            'enableRateLimit': True
        })
    except Exception as e:
        logger.error(f"Error initializing Kraken: {e}")
        return None

def get_binance_client():
    """Get Binance exchange client"""
    try:
        return ccxt.binance({
            'apiKey': config.get('binance_api_key', ''),
            'secret': config.get('binance_api_secret', ''),
            'enableRateLimit': True
        })
    except Exception as e:
        logger.error(f"Error initializing Binance: {e}")
        return None

def get_exchange_balance(exchange, exchange_name):
    """Get balance from exchange with error handling"""
    try:
        if exchange is None:
            return 0.0, "Not Connected", []
        
        balance = exchange.fetch_balance()
        total_usd = 0.0
        holdings = []
        
        # Calculate total USD value
        for currency, amount in balance['total'].items():
            if amount > 0:
                if currency in ['USD', 'USDT', 'USDC']:
                    usd_value = amount
                else:
                    try:
                        # Try to get USD price
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
        
        return total_usd, "Connected", holdings
        
    except Exception as e:
        error_msg = str(e)
        if "restricted location" in error_msg.lower():
            return 0.0, "GEO-BLOCKED", []
        else:
            return 0.0, f"API Error: {error_msg[:50]}", []

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Crypto Trading Dashboard - REAL DATA"

# Define layout
app.layout = html.Div([
    html.H1("🚀 Live Crypto Trading Dashboard", 
            style={'textAlign': 'center', 'color': '#00ff00', 'backgroundColor': '#000'}),
    
    html.Div([
        html.H2("⚠️ Partial API Access - One Exchange Down", 
                style={'textAlign': 'center', 'color': '#ffaa00', 'backgroundColor': '#000'})
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # Update every 10 seconds
        n_intervals=0
    ),
    
    html.Div([
        html.Div([
            html.H3("💰 Total Portfolio Value", style={'color': '#fff'}),
            html.H1(id='total-value', style={'color': '#00ff00', 'fontSize': '48px'}),
            html.P(id='total-change', style={'fontSize': '24px'})
        ], style={'backgroundColor': '#1a1a1a', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px'}),
        
        html.Div([
            html.H3("📊 Exchange Balances", style={'color': '#fff'}),
            html.Div(id='exchange-balances')
        ], style={'backgroundColor': '#1a1a1a', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px'}),
        
        html.Div([
            html.H3("📈 Holdings Breakdown", style={'color': '#fff'}),
            html.Div(id='holdings-table')
        ], style={'backgroundColor': '#1a1a1a', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px'}),
        
        html.Div([
            html.H3("💹 Daily P&L", style={'color': '#fff'}),
            html.H2(id='daily-pnl', style={'fontSize': '36px'}),
            html.P(id='daily-pnl-pct', style={'fontSize': '20px'})
        ], style={'backgroundColor': '#1a1a1a', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px'}),
    ], style={'backgroundColor': '#0a0a0a', 'padding': '20px'}),
    
    html.Div([
        html.P(f"Starting Capital: ${STARTING_CAPITAL:.2f}", 
               style={'color': '#888', 'textAlign': 'center'}),
        html.P(id='last-update', 
               style={'color': '#888', 'textAlign': 'center'})
    ])
], style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})

@app.callback(
    [Output('total-value', 'children'),
     Output('total-change', 'children'),
     Output('total-change', 'style'),
     Output('exchange-balances', 'children'),
     Output('holdings-table', 'children'),
     Output('daily-pnl', 'children'),
     Output('daily-pnl', 'style'),
     Output('daily-pnl-pct', 'children'),
     Output('last-update', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Update dashboard with real exchange data"""
    
    # Get Kraken balance
    kraken = get_kraken_client()
    kraken_balance, kraken_status, kraken_holdings = get_exchange_balance(kraken, "Kraken")
    
    # Get Binance balance
    binance = get_binance_client()
    binance_balance, binance_status, binance_holdings = get_exchange_balance(binance, "Binance")
    
    # Calculate totals
    total_value = kraken_balance + binance_balance
    pnl = total_value - STARTING_CAPITAL
    pnl_pct = (pnl / STARTING_CAPITAL) * 100 if STARTING_CAPITAL > 0 else 0
    
    # Format values
    total_value_str = f"${total_value:.2f}"
    pnl_str = f"${pnl:+.2f}"
    pnl_color = '#00ff00' if pnl >= 0 else '#ff0000'
    
    # Exchange balances
    exchange_info = html.Div([
        html.Div([
            html.H4("🔹 Kraken", style={'color': '#00aaff'}),
            html.P(f"Balance: ${kraken_balance:.2f}", style={'color': '#fff', 'fontSize': '20px'}),
            html.P(f"Status: {kraken_status}", style={'color': '#00ff00' if kraken_status == 'Connected' else '#ff0000'})
        ], style={'display': 'inline-block', 'width': '45%', 'verticalAlign': 'top'}),
        
        html.Div([
            html.H4("🔸 Binance", style={'color': '#f0b90b'}),
            html.P(f"Balance: ${binance_balance:.2f}", style={'color': '#fff', 'fontSize': '20px'}),
            html.P(f"Status: {binance_status}", style={'color': '#00ff00' if binance_status == 'Connected' else '#ff0000'})
        ], style={'display': 'inline-block', 'width': '45%', 'verticalAlign': 'top', 'marginLeft': '5%'})
    ])
    
    # Holdings table
    all_holdings = [
        {'exchange': 'Kraken', **h} for h in kraken_holdings
    ] + [
        {'exchange': 'Binance', **h} for h in binance_holdings
    ]
    
    if all_holdings:
        holdings_rows = [
            html.Tr([
                html.Th("Exchange", style={'color': '#fff', 'borderBottom': '2px solid #444'}),
                html.Th("Asset", style={'color': '#fff', 'borderBottom': '2px solid #444'}),
                html.Th("Amount", style={'color': '#fff', 'borderBottom': '2px solid #444'}),
                html.Th("USD Value", style={'color': '#fff', 'borderBottom': '2px solid #444'})
            ])
        ]
        
        for h in all_holdings:
            holdings_rows.append(
                html.Tr([
                    html.Td(h['exchange'], style={'color': '#aaa'}),
                    html.Td(h['currency'], style={'color': '#fff'}),
                    html.Td(f"{h['amount']:.8f}", style={'color': '#aaa'}),
                    html.Td(f"${h['usd_value']:.2f}", style={'color': '#00ff00'})
                ])
            )
        
        holdings_table = html.Table(holdings_rows, style={'width': '100%'})
    else:
        holdings_table = html.P("No holdings found", style={'color': '#888'})
    
    # Last update time
    last_update = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    return (
        total_value_str,
        pnl_str,
        {'color': pnl_color, 'fontSize': '24px'},
        exchange_info,
        holdings_table,
        pnl_str,
        {'color': pnl_color},
        f"({pnl_pct:+.2f}%)",
        last_update
    )

if __name__ == '__main__':
    logger.info("Starting Fixed Dashboard with REAL exchange data")
    logger.info(f"Starting Capital: ${STARTING_CAPITAL:.2f}")
    app.run_server(host='0.0.0.0', port=3000, debug=False)
