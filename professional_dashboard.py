#!/usr/bin/env python3
"""
Professional Cryptocurrency Trading Dashboard
Bloomberg Terminal-inspired design with deep agent insights and GPT-4o integration
"""

import dash
from dash import dcc, html, Input, Output, State, ctx, ALL
import dash_auth
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import ccxt
import json
import time
from datetime import datetime, timedelta
import threading
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from llm_tools import TradingDataTools, FUNCTION_DEFINITIONS, execute_function

# AUTHENTICATION
VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'CryptoTrader2024!'
}

# Load configuration
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

# Initialize trading data tools
trading_tools = TradingDataTools(config['database'])

# Database connection
def get_db_connection():
    return psycopg2.connect(**config['database'], cursor_factory=RealDictCursor)

# Initialize exchanges
exchanges = {}
if config.get('binance_api_key') and config.get('binance_api_secret'):
    try:
        exchanges['binance'] = ccxt.binanceus({
            'apiKey': config['binance_api_key'],
            'secret': config['binance_api_secret'],
            'timeout': 10000,
            'enableRateLimit': True,
        })
    except:
        exchanges['binance'] = ccxt.binance({
            'apiKey': config['binance_api_key'],
            'secret': config['binance_api_secret'],
            'timeout': 10000,
            'enableRateLimit': True,
        })

if config.get('kraken_api_key') and config.get('kraken_api_secret'):
    exchanges['kraken'] = ccxt.kraken({
        'apiKey': config['kraken_api_key'],
        'secret': config['kraken_api_secret'],
        'timeout': 10000,
        'enableRateLimit': True
    })

# Cache and state
cache = {}
cache_lock = threading.Lock()
chat_history = []
chat_lock = threading.Lock()

def get_cached_or_fetch(key, fetch_func, ttl=30):
    """Get cached data or fetch new"""
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

def fetch_balance(exchange_name):
    """Fetch balance from exchange"""
    if exchange_name not in exchanges or not exchanges[exchange_name]:
        raise Exception(f"{exchange_name} not configured")
    return exchanges[exchange_name].fetch_balance().get('total', {})

def get_crypto_prices():
    """Fetch current crypto prices"""
    try:
        response = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD', timeout=5)
        data = response.json()
        if data.get('error'):
            return {'BTC': 111220, 'ETH': 3971, 'SOL': 190}
        
        result = data.get('result', {})
        btc_price = float(result.get('XXBTZUSD', {}).get('c', [111220])[0])
        eth_price = float(result.get('XETHZUSD', {}).get('c', [3971])[0])
        sol_price = float(result.get('SOLUSD', {}).get('c', [190])[0])
        return {'BTC': btc_price, 'ETH': eth_price, 'SOL': sol_price}
    except:
        return {'BTC': 111220, 'ETH': 3971, 'SOL': 190}

def chat_with_gpt4o(user_message, conversation_history):
    """Chat with GPT-4o using function calling"""
    try:
        headers = {
            'Authorization': f"Bearer {config.get('openai_api_key')}",
            'Content-Type': 'application/json'
        }
        
        # Prepare messages with system prompt
        system_prompt = """You are an expert cryptocurrency trading assistant with full access to the trading system's database. 

You can use the following tools to query data:
- query_trades: Get trade history with filters
- get_agent_decisions: See agent reasoning and decisions
- get_portfolio_metrics: Get portfolio statistics
- get_market_data: Get OHLCV data for analysis
- get_risk_analysis: Get risk metrics
- get_agent_performance: See which agents are performing best
- get_orchestrator_state: See the decision-making pipeline

Provide insightful analysis based on the actual data. Be professional, concise, and data-driven."""

        messages = [{'role': 'system', 'content': system_prompt}] + conversation_history + [{'role': 'user', 'content': user_message}]
        
        payload = {
            'model': 'gpt-4o',
            'messages': messages,
            'tools': [{"type": "function", "function": func_def} for func_def in FUNCTION_DEFINITIONS],
            'tool_choice': 'auto',
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        
        response_data = response.json()
        assistant_message = response_data['choices'][0]['message']
        
        # Handle function calls
        if assistant_message.get('tool_calls'):
            # Execute all function calls
            function_results = []
            for tool_call in assistant_message['tool_calls']:
                function_name = tool_call['function']['name']
                function_args = json.loads(tool_call['function']['arguments'])
                
                # Execute the function
                result = execute_function(function_name, function_args, trading_tools)
                function_results.append({
                    'tool_call_id': tool_call['id'],
                    'role': 'tool',
                    'name': function_name,
                    'content': result
                })
            
            # Make second API call with function results
            messages.append(assistant_message)
            messages.extend(function_results)
            
            payload['messages'] = messages
            payload.pop('tool_choice', None)  # Remove tool_choice for second call
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                return f"Error in function call response: {response.status_code}"
            
            response_data = response.json()
            final_message = response_data['choices'][0]['message']['content']
            return final_message
        else:
            # No function calls, return direct response
            return assistant_message.get('content', 'No response generated')
            
    except Exception as e:
        return f"Error communicating with GPT-4o: {str(e)}"

# Initialize Dash app
external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap'
]
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)
app.title = "🚀 Professional Crypto Trading Terminal"

# Add authentication
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

# Professional CSS inspired by Bloomberg Terminal
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0a0e27;
                color: #e0e0e0;
                overflow-x: hidden;
            }
            
            .mono {
                font-family: 'JetBrains Mono', monospace;
            }
            
            /* Terminal Header */
            .terminal-header {
                background: linear-gradient(135deg, #1a1f3a 0%, #0d1224 100%);
                border-bottom: 2px solid #2d3748;
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            }
            
            .terminal-title {
                font-size: 20px;
                font-weight: 700;
                color: #00ff88;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            
            .status-bar {
                display: flex;
                gap: 20px;
                align-items: center;
                font-size: 12px;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #00ff88;
                animation: pulse-dot 2s ease-in-out infinite;
            }
            
            @keyframes pulse-dot {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.6; transform: scale(1.2); }
            }
            
            /* Grid System */
            .terminal-grid {
                display: grid;
                grid-template-columns: repeat(12, 1fr);
                gap: 15px;
                padding: 15px;
                max-width: 1920px;
                margin: 0 auto;
            }
            
            /* Terminal Panel */
            .terminal-panel {
                background: linear-gradient(135deg, #1a1f3a 0%, #151929 100%);
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .terminal-panel::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, #00ff88, transparent);
                opacity: 0.3;
            }
            
            .terminal-panel:hover {
                border-color: #3d4758;
                box-shadow: 0 6px 20px rgba(0, 255, 136, 0.1);
            }
            
            .panel-header {
                font-size: 14px;
                font-weight: 600;
                color: #00ff88;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .panel-badge {
                background: rgba(0, 255, 136, 0.1);
                color: #00ff88;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            
            /* Metric Cards */
            .metric-card {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #2d3748;
                border-radius: 6px;
                padding: 15px;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                background: rgba(0, 0, 0, 0.4);
                border-color: #00ff88;
                transform: translateY(-2px);
            }
            
            .metric-label {
                font-size: 11px;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
                font-weight: 500;
            }
            
            .metric-value {
                font-size: 28px;
                font-weight: 700;
                color: #fff;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .metric-value.positive {
                color: #00ff88;
            }
            
            .metric-value.negative {
                color: #ff5252;
            }
            
            .metric-change {
                font-size: 13px;
                margin-top: 6px;
                font-family: 'JetBrains Mono', monospace;
            }
            
            /* Agent Cards */
            .agent-card {
                background: rgba(0, 0, 0, 0.3);
                border-left: 3px solid #00ff88;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 12px;
                transition: all 0.3s ease;
            }
            
            .agent-card:hover {
                background: rgba(0, 255, 136, 0.05);
                transform: translateX(4px);
            }
            
            .agent-card.research { border-left-color: #00d4ff; }
            .agent-card.execution { border-left-color: #ff9800; }
            .agent-card.risk { border-left-color: #f44336; }
            .agent-card.scalping { border-left-color: #9c27b0; }
            .agent-card.swing { border-left-color: #4caf50; }
            
            .agent-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .agent-name {
                font-weight: 600;
                color: #00ff88;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .agent-timestamp {
                font-size: 11px;
                color: #666;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .agent-decision {
                color: #fff;
                font-size: 13px;
                margin-bottom: 8px;
                line-height: 1.5;
            }
            
            .agent-reasoning {
                color: #888;
                font-size: 12px;
                line-height: 1.6;
                margin-bottom: 10px;
            }
            
            .agent-footer {
                display: flex;
                gap: 15px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .agent-confidence {
                color: #00d4ff;
            }
            
            .agent-status {
                color: #ff9800;
            }
            
            .agent-status.executed {
                color: #4caf50;
            }
            
            /* Orchestrator Visualization */
            .orchestrator-flow {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                padding: 20px;
                margin-top: 15px;
            }
            
            .flow-node {
                background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 255, 136, 0.1) 100%);
                border: 1px solid #2d3748;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 10px;
                position: relative;
            }
            
            .flow-node::after {
                content: '↓';
                position: absolute;
                bottom: -20px;
                left: 50%;
                transform: translateX(-50%);
                color: #00ff88;
                font-size: 16px;
            }
            
            .flow-node:last-child::after {
                display: none;
            }
            
            /* Chat Interface */
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 500px;
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                margin-bottom: 15px;
            }
            
            .chat-message {
                background: rgba(0, 0, 0, 0.4);
                border-left: 3px solid #00d4ff;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 12px;
            }
            
            .chat-message.assistant {
                border-left-color: #00ff88;
            }
            
            .chat-message-header {
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 6px;
                color: #00d4ff;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .chat-message.assistant .chat-message-header {
                color: #00ff88;
            }
            
            .chat-message-content {
                color: #e0e0e0;
                font-size: 13px;
                line-height: 1.6;
            }
            
            .chat-input-container {
                display: flex;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                background: rgba(0, 0, 0, 0.4) !important;
                border: 1px solid #2d3748 !important;
                border-radius: 6px !important;
                padding: 12px !important;
                color: #fff !important;
                font-size: 13px !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            .chat-input:focus {
                outline: none !important;
                border-color: #00ff88 !important;
                box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.1) !important;
            }
            
            .chat-send-btn {
                background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
                color: #0a0e27;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
                font-weight: 600;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .chat-send-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
            }
            
            /* Trade List */
            .trade-item {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 8px;
                border-left: 3px solid transparent;
                transition: all 0.3s ease;
            }
            
            .trade-item.buy {
                border-left-color: #00ff88;
            }
            
            .trade-item.sell {
                border-left-color: #ff5252;
            }
            
            .trade-item:hover {
                background: rgba(0, 0, 0, 0.5);
                transform: translateX(4px);
            }
            
            .trade-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 6px;
            }
            
            .trade-symbol {
                font-weight: 600;
                color: #fff;
                font-size: 13px;
            }
            
            .trade-side {
                font-weight: 600;
                font-size: 12px;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .trade-side.buy {
                color: #00ff88;
            }
            
            .trade-side.sell {
                color: #ff5252;
            }
            
            .trade-details {
                display: flex;
                gap: 15px;
                font-size: 11px;
                color: #888;
                font-family: 'JetBrains Mono', monospace;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #00d4ff 0%, #00ff88 100%);
            }
            
            /* Responsive Grid Columns */
            .col-12 { grid-column: span 12; }
            .col-6 { grid-column: span 6; }
            .col-4 { grid-column: span 4; }
            .col-3 { grid-column: span 3; }
            .col-8 { grid-column: span 8; }
            
            /* Performance badges */
            .perf-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .perf-badge.excellent {
                background: rgba(76, 175, 80, 0.2);
                color: #4caf50;
            }
            
            .perf-badge.good {
                background: rgba(0, 255, 136, 0.2);
                color: #00ff88;
            }
            
            .perf-badge.average {
                background: rgba(255, 152, 0, 0.2);
                color: #ff9800;
            }
            
            .perf-badge.poor {
                background: rgba(244, 67, 54, 0.2);
                color: #f44336;
            }
            
            /* Tabs */
            .tab-container {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #2d3748;
            }
            
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                color: #888;
                font-weight: 500;
                font-size: 13px;
                border-bottom: 2px solid transparent;
                transition: all 0.3s ease;
            }
            
            .tab:hover {
                color: #00ff88;
            }
            
            .tab.active {
                color: #00ff88;
                border-bottom-color: #00ff88;
            }
            
            /* Loading Animation */
            .loading {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid rgba(0, 255, 136, 0.3);
                border-radius: 50%;
                border-top-color: #00ff88;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    
    # Terminal Header
    html.Div([
        html.Div("🚀 CRYPTO TRADING TERMINAL", className='terminal-title'),
        html.Div([
            html.Div([
                html.Div(className='status-dot'),
                html.Span("SYSTEM ONLINE", className='mono')
            ], className='status-indicator'),
            html.Div([
                html.Span(id='current-time', className='mono')
            ], className='status-indicator'),
        ], className='status-bar')
    ], className='terminal-header'),
    
    # Main Terminal Grid
    html.Div([
        
        # Top Metrics Row
        html.Div([
            html.Div([
                html.Div("PORTFOLIO VALUE", className='metric-label'),
                html.Div(id='portfolio-value', className='metric-value'),
                html.Div(id='portfolio-change', className='metric-change')
            ], className='metric-card')
        ], className='col-3'),
        
        html.Div([
            html.Div([
                html.Div("DAILY P&L", className='metric-label'),
                html.Div(id='daily-pnl', className='metric-value'),
                html.Div(id='daily-pnl-change', className='metric-change')
            ], className='metric-card')
        ], className='col-3'),
        
        html.Div([
            html.Div([
                html.Div("OPEN POSITIONS", className='metric-label'),
                html.Div(id='open-positions', className='metric-value'),
                html.Div(id='position-exposure', className='metric-change')
            ], className='metric-card')
        ], className='col-3'),
        
        html.Div([
            html.Div([
                html.Div("WIN RATE", className='metric-label'),
                html.Div(id='win-rate', className='metric-value'),
                html.Div(id='sharpe-ratio', className='metric-change')
            ], className='metric-card')
        ], className='col-3'),
        
        # Portfolio Chart
        html.Div([
            html.Div([
                html.Div("PORTFOLIO PERFORMANCE", className='panel-header'),
                dcc.Graph(id='portfolio-chart', config={'displayModeBar': False}, style={'height': '350px'})
            ], className='terminal-panel')
        ], className='col-8'),
        
        # Exchange Balances
        html.Div([
            html.Div([
                html.Div("EXCHANGE BALANCES", className='panel-header'),
                html.Div(id='exchange-balances')
            ], className='terminal-panel')
        ], className='col-4'),
        
        # Agent Insights & Orchestrator
        html.Div([
            html.Div([
                html.Div([
                    html.Span("AGENT INTELLIGENCE", style={'flex': 1}),
                    html.Span(id='agent-count', className='panel-badge')
                ], className='panel-header'),
                html.Div(id='agent-insights', style={'maxHeight': '600px', 'overflowY': 'auto'})
            ], className='terminal-panel')
        ], className='col-6'),
        
        # Orchestrator Visualization
        html.Div([
            html.Div([
                html.Div([
                    html.Span("ORCHESTRATOR PIPELINE", style={'flex': 1}),
                    html.Span(id='orchestrator-status', className='panel-badge')
                ], className='panel-header'),
                html.Div(id='orchestrator-viz', style={'maxHeight': '600px', 'overflowY': 'auto'})
            ], className='terminal-panel')
        ], className='col-6'),
        
        # AI Assistant Chat
        html.Div([
            html.Div([
                html.Div([
                    html.Span("AI ASSISTANT (GPT-4o)", style={'flex': 1}),
                    html.Span("FUNCTION CALLING ENABLED", className='panel-badge')
                ], className='panel-header'),
                html.Div([
                    html.Div(id='chat-history', className='chat-messages'),
                    html.Div([
                        dcc.Input(
                            id='chat-input',
                            type='text',
                            placeholder='Ask about agents, trades, risk, or market analysis...',
                            className='chat-input'
                        ),
                        html.Button('SEND', id='chat-send', n_clicks=0, className='chat-send-btn')
                    ], className='chat-input-container')
                ], className='chat-container')
            ], className='terminal-panel')
        ], className='col-8'),
        
        # Recent Trades
        html.Div([
            html.Div([
                html.Div("RECENT TRADES", className='panel-header'),
                html.Div(id='recent-trades', style={'maxHeight': '500px', 'overflowY': 'auto'})
            ], className='terminal-panel')
        ], className='col-4'),
        
        # Agent Performance Metrics
        html.Div([
            html.Div([
                html.Div("AGENT PERFORMANCE", className='panel-header'),
                html.Div(id='agent-performance', style={'maxHeight': '400px', 'overflowY': 'auto'})
            ], className='terminal-panel')
        ], className='col-6'),
        
        # Risk Dashboard
        html.Div([
            html.Div([
                html.Div("RISK METRICS", className='panel-header'),
                html.Div(id='risk-dashboard')
            ], className='terminal-panel')
        ], className='col-6'),
        
    ], className='terminal-grid'),
    
    # Update interval
    dcc.Interval(id='interval-update', interval=5000, n_intervals=0),
    
    # Store for chat history
    dcc.Store(id='chat-store', data=[]),
    
])

# Callbacks
@app.callback(
    Output('current-time', 'children'),
    Input('interval-update', 'n_intervals')
)
def update_time(n):
    """Update current time"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

@app.callback(
    [Output('portfolio-value', 'children'),
     Output('portfolio-change', 'children'),
     Output('daily-pnl', 'children'),
     Output('daily-pnl-change', 'children'),
     Output('open-positions', 'children'),
     Output('position-exposure', 'children'),
     Output('win-rate', 'children'),
     Output('sharpe-ratio', 'children'),
     Output('exchange-balances', 'children'),
     Output('portfolio-chart', 'figure')],
    Input('interval-update', 'n_intervals')
)
def update_metrics(n):
    """Update top-level metrics"""
    
    # Get portfolio data from database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest portfolio snapshot
        cursor.execute("""
            SELECT total_value, cash_balance, positions, pnl, pnl_percentage
            FROM portfolio
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        portfolio_data = cursor.fetchone()
        
        if portfolio_data:
            total_value = float(portfolio_data['total_value'])
            cash_balance = float(portfolio_data['cash_balance'])
            positions = portfolio_data['positions']
            total_pnl = float(portfolio_data['pnl'])
            pnl_pct = float(portfolio_data['pnl_percentage'])
        else:
            # Fallback if no data
            total_value = 0
            cash_balance = 0
            positions = {}
            total_pnl = 0
            pnl_pct = 0
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching portfolio from database: {e}")
        total_value = 0
        total_pnl = 0
        pnl_pct = 0
    
    # Fetch balances for display (optional, for exchange status)
    binance_balance, binance_error = get_cached_or_fetch('binance', lambda: fetch_balance('binance'), ttl=30)
    kraken_balance, kraken_error = get_cached_or_fetch('kraken', lambda: fetch_balance('kraken'), ttl=30)
    
    # Get prices for exchange balance calculation
    prices = get_crypto_prices()
    
    # Calculate exchange USD values for display
    binance_usd = binance_balance.get('USDT', 0) + binance_balance.get('USD', 0)
    kraken_usd = kraken_balance.get('USD', 0) + kraken_balance.get('ZUSD', 0)
    
    # Add crypto values for display
    binance_usd += binance_balance.get('BTC', 0) * prices['BTC']
    kraken_usd += (kraken_balance.get('BTC', 0) + kraken_balance.get('XBT', 0)) * prices['BTC']
    binance_usd += binance_balance.get('ETH', 0) * prices['ETH']
    kraken_usd += (kraken_balance.get('ETH', 0) + kraken_balance.get('XETH', 0)) * prices['ETH']
    
    # Get portfolio metrics from database
    portfolio_metrics = trading_tools.get_portfolio_metrics()
    latest_metrics = portfolio_metrics.get('latest_metrics', {})
    
    # Portfolio value
    portfolio_value_display = f"${total_value:,.2f}"
    
    initial_capital = config.get('initial_capital', 100)
    portfolio_change_display = html.Span([
        f"${total_pnl:+,.2f} ",
        html.Span(f"({pnl_pct:+.2f}%)", style={'color': '#00ff88' if total_pnl >= 0 else '#ff5252'})
    ], className='mono')
    
    # Daily P&L
    daily_pnl_val = float(latest_metrics.get('daily_pnl', 0))
    daily_pnl_display = f"${daily_pnl_val:+,.2f}"
    daily_pnl_pct = (daily_pnl_val / total_value) * 100 if total_value > 0 else 0
    daily_pnl_change_display = html.Span(f"{daily_pnl_pct:+.2f}% TODAY", style={
        'color': '#00ff88' if daily_pnl_val >= 0 else '#ff5252'
    }, className='mono')
    
    # Open positions
    open_pos_count = portfolio_metrics.get('open_positions_count', 0)
    open_positions_display = str(open_pos_count)
    total_exposure = float(latest_metrics.get('total_exposure', 0))
    position_exposure_display = html.Span(f"EXPOSURE: ${total_exposure:,.2f}", className='mono')
    
    # Win rate & Sharpe
    win_rate_val = float(latest_metrics.get('win_rate', 0))
    win_rate_display = f"{win_rate_val:.1f}%"
    sharpe_val = float(latest_metrics.get('sharpe_ratio', 0))
    sharpe_display = html.Span(f"SHARPE: {sharpe_val:.2f}", className='mono')
    
    # Exchange balances
    binance_status = "⚠ BLOCKED" if binance_error and "451" in str(binance_error) else ("⚠ ERROR" if binance_error else "✓ ONLINE")
    kraken_status = "⚠ ERROR" if kraken_error else "✓ ONLINE"
    
    exchange_display = html.Div([
        # Binance
        html.Div([
            html.Div([
                html.Span("BINANCE", style={'fontWeight': '600', 'fontSize': '13px'}),
                html.Span(binance_status, style={
                    'float': 'right',
                    'color': '#ff5252' if binance_error else '#00ff88',
                    'fontSize': '11px',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ]),
            html.Div(f"${binance_usd:,.2f}", style={
                'fontSize': '24px',
                'fontWeight': '700',
                'color': '#00d4ff',
                'marginTop': '8px',
                'fontFamily': 'JetBrains Mono, monospace'
            }),
            html.Div(f"ASSETS: {len([k for k, v in binance_balance.items() if v > 0])}", style={
                'color': '#666',
                'fontSize': '11px',
                'marginTop': '5px',
                'fontFamily': 'JetBrains Mono, monospace'
            })
        ], style={
            'background': 'rgba(0, 212, 255, 0.05)',
            'padding': '15px',
            'borderRadius': '6px',
            'marginBottom': '15px',
            'border': '1px solid rgba(0, 212, 255, 0.2)'
        }),
        
        # Kraken
        html.Div([
            html.Div([
                html.Span("KRAKEN", style={'fontWeight': '600', 'fontSize': '13px'}),
                html.Span(kraken_status, style={
                    'float': 'right',
                    'color': '#ff5252' if kraken_error else '#00ff88',
                    'fontSize': '11px',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ]),
            html.Div(f"${kraken_usd:,.2f}", style={
                'fontSize': '24px',
                'fontWeight': '700',
                'color': '#9c27b0',
                'marginTop': '8px',
                'fontFamily': 'JetBrains Mono, monospace'
            }),
            html.Div(f"ASSETS: {len([k for k, v in kraken_balance.items() if v > 0])}", style={
                'color': '#666',
                'fontSize': '11px',
                'marginTop': '5px',
                'fontFamily': 'JetBrains Mono, monospace'
            })
        ], style={
            'background': 'rgba(156, 39, 176, 0.05)',
            'padding': '15px',
            'borderRadius': '6px',
            'border': '1px solid rgba(156, 39, 176, 0.2)'
        }),
        
        html.Hr(style={'borderColor': '#2d3748', 'margin': '20px 0'}),
        
        # Market prices
        html.Div([
            html.Div([
                html.Span("BTC", style={'color': '#888', 'fontSize': '11px'}),
                html.Span(f"${prices['BTC']:,.2f}", style={'float': 'right', 'color': '#fff', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("ETH", style={'color': '#888', 'fontSize': '11px'}),
                html.Span(f"${prices['ETH']:,.2f}", style={'float': 'right', 'color': '#fff', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span("SOL", style={'color': '#888', 'fontSize': '11px'}),
                html.Span(f"${prices['SOL']:,.2f}", style={'float': 'right', 'color': '#fff', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
            ])
        ])
    ])
    
    # Portfolio chart
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, total_capital, total_pnl
            FROM risk_metrics
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if history:
            history = list(reversed(history))
            timestamps = [h['timestamp'] for h in history]
            values = [float(h['total_capital']) for h in history]
        else:
            # Generate mock data
            timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]
            values = [initial_capital * (1 + np.random.uniform(-0.05, 0.15) * (i/100)) for i in range(100)]
    except:
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]
        values = [initial_capital * (1 + np.random.uniform(-0.05, 0.15) * (i/100)) for i in range(100)]
    
    portfolio_fig = go.Figure()
    portfolio_fig.add_trace(go.Scatter(
        x=timestamps,
        y=values,
        mode='lines',
        fill='tozeroy',
        line=dict(color='#00ff88', width=2),
        fillcolor='rgba(0, 255, 136, 0.1)',
        name='Portfolio Value'
    ))
    
    portfolio_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0', family='JetBrains Mono, monospace'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(45, 55, 72, 0.5)',
            color='#888',
            showline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(45, 55, 72, 0.5)',
            color='#888',
            showline=False
        ),
        margin=dict(l=40, r=20, t=20, b=40),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#1a1f3a',
            font_size=12,
            font_family='JetBrains Mono, monospace'
        )
    )
    
    return (portfolio_value_display, portfolio_change_display, daily_pnl_display, daily_pnl_change_display,
            open_positions_display, position_exposure_display, win_rate_display, sharpe_display,
            exchange_display, portfolio_fig)

@app.callback(
    [Output('agent-insights', 'children'),
     Output('agent-count', 'children')],
    Input('interval-update', 'n_intervals')
)
def update_agent_insights(n):
    """Update agent insights with detailed reasoning"""
    
    agent_decisions = trading_tools.get_agent_decisions(limit=15, hours_back=24)
    
    if not agent_decisions or 'error' in agent_decisions[0]:
        return html.Div([
            html.Div("🔍 NO AGENT ACTIVITY", style={'textAlign': 'center', 'color': '#666', 'padding': '40px'}),
            html.Div("Agents are analyzing markets and will log decisions here.", style={'textAlign': 'center', 'color': '#444', 'fontSize': '12px'})
        ], style={'marginTop': '20px'}), "0 ACTIVE"
    
    agent_cards = []
    for decision in agent_decisions:
        agent_name = decision.get('agent', 'unknown').replace('_', ' ').upper()
        agent_class = decision.get('agent', 'unknown').split('_')[0]
        
        timestamp = decision.get('timestamp', '')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
            except:
                timestamp = str(timestamp)[-8:] if len(str(timestamp)) >= 8 else str(timestamp)
        else:
            timestamp = str(timestamp)
        
        agent_card = html.Div([
            html.Div([
                html.Span(f"🤖 {agent_name}", className='agent-name'),
                html.Span(timestamp, className='agent-timestamp')
            ], className='agent-header'),
            html.Div(decision.get('decision', 'No decision'), className='agent-decision'),
            html.Div(decision.get('reasoning', 'No reasoning provided')[:250] + ('...' if len(decision.get('reasoning', '')) > 250 else ''), 
                    className='agent-reasoning'),
            html.Div([
                html.Span(f"CONFIDENCE: {decision.get('confidence', 0):.1f}%", className='agent-confidence'),
                html.Span(" | ", style={'color': '#444'}),
                html.Span(
                    "EXECUTED" if decision.get('executed') else "PENDING",
                    className=f"agent-status {'executed' if decision.get('executed') else ''}"
                )
            ], className='agent-footer')
        ], className=f'agent-card {agent_class}')
        
        agent_cards.append(agent_card)
    
    return html.Div(agent_cards), f"{len(agent_decisions)} DECISIONS"

@app.callback(
    [Output('orchestrator-viz', 'children'),
     Output('orchestrator-status', 'children')],
    Input('interval-update', 'n_intervals')
)
def update_orchestrator(n):
    """Update orchestrator visualization"""
    
    orchestrator_state = trading_tools.get_orchestrator_state()
    
    if 'error' in orchestrator_state:
        return html.Div("ERROR LOADING ORCHESTRATOR STATE", style={'color': '#ff5252', 'textAlign': 'center', 'padding': '40px'}), "ERROR"
    
    pending_decisions = orchestrator_state.get('pending_decisions', [])
    agent_activity = orchestrator_state.get('agent_activity', [])
    
    # Agent Activity Summary
    activity_cards = []
    for activity in agent_activity[:5]:
        agent_name = activity.get('agent', 'unknown').replace('_', ' ').upper()
        decisions_count = activity.get('decisions_last_hour', 0)
        avg_confidence = activity.get('avg_confidence', 0)
        
        activity_card = html.Div([
            html.Div([
                html.Span(agent_name, style={'fontWeight': '600', 'color': '#00ff88'}),
                html.Span(f"{decisions_count} DECISIONS", style={'float': 'right', 'fontSize': '11px', 'color': '#888'})
            ]),
            html.Div([
                html.Span(f"AVG CONFIDENCE: {avg_confidence:.1f}%", style={'fontSize': '11px', 'color': '#00d4ff'})
            ], style={'marginTop': '5px'})
        ], style={
            'background': 'rgba(0, 0, 0, 0.3)',
            'padding': '12px',
            'borderRadius': '6px',
            'marginBottom': '10px',
            'border': '1px solid #2d3748'
        })
        activity_cards.append(activity_card)
    
    # Decision Pipeline
    pipeline_viz = html.Div([
        html.Div("🔄 DECISION PIPELINE", style={'fontSize': '13px', 'fontWeight': '600', 'color': '#00d4ff', 'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Div("1. AGENT ANALYSIS", style={'fontWeight': '600', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.Div(f"{len(agent_activity)} agents active", style={'fontSize': '11px', 'color': '#888'})
            ], className='flow-node'),
            html.Div([
                html.Div("2. DECISION RANKING", style={'fontWeight': '600', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.Div("By confidence & priority", style={'fontSize': '11px', 'color': '#888'})
            ], className='flow-node'),
            html.Div([
                html.Div("3. RISK VALIDATION", style={'fontWeight': '600', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.Div("Risk manager approval", style={'fontSize': '11px', 'color': '#888'})
            ], className='flow-node'),
            html.Div([
                html.Div("4. EXECUTION", style={'fontWeight': '600', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.Div(f"{len([d for d in pending_decisions if not d.get('executed')])} pending", style={'fontSize': '11px', 'color': '#888'})
            ], className='flow-node')
        ], className='orchestrator-flow')
    ])
    
    # Pending Decisions Queue
    pending_viz = html.Div([
        html.Div("⏳ PENDING QUEUE", style={'fontSize': '13px', 'fontWeight': '600', 'color': '#ff9800', 'marginTop': '20px', 'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.Span(d.get('agent', 'unknown').replace('_', ' ').upper(), style={'fontWeight': '600', 'fontSize': '11px', 'color': '#fff'}),
                    html.Span(f"CONF: {d.get('confidence', 0):.0f}%", style={'float': 'right', 'fontSize': '11px', 'color': '#00ff88'})
                ]),
                html.Div(d.get('decision', 'No decision')[:100], style={'fontSize': '11px', 'color': '#888', 'marginTop': '5px'})
            ], style={
                'background': 'rgba(255, 152, 0, 0.05)',
                'padding': '10px',
                'borderRadius': '4px',
                'marginBottom': '8px',
                'borderLeft': '2px solid #ff9800'
            })
            for d in pending_decisions[:5]
        ]) if pending_decisions else html.Div("No pending decisions", style={'color': '#666', 'fontSize': '12px', 'textAlign': 'center', 'padding': '20px'})
    ])
    
    return html.Div([
        html.Div(activity_cards),
        pipeline_viz,
        pending_viz
    ]), f"{len(pending_decisions)} PENDING"

@app.callback(
    Output('recent-trades', 'children'),
    Input('interval-update', 'n_intervals')
)
def update_recent_trades(n):
    """Update recent trades list"""
    
    trades = trading_tools.query_trades(limit=20)
    
    if not trades or 'error' in trades[0]:
        return html.Div("No recent trades", style={'color': '#666', 'textAlign': 'center', 'padding': '40px'})
    
    trade_items = []
    for trade in trades:
        side = trade.get('side', 'unknown')
        symbol = trade.get('symbol', 'N/A')
        price = float(trade.get('price', 0))
        quantity = float(trade.get('quantity', 0))
        exchange = trade.get('exchange', 'N/A')
        timestamp = trade.get('timestamp', '')
        
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp).strftime('%m-%d %H:%M')
            except:
                timestamp = str(timestamp)[:16] if len(str(timestamp)) >= 16 else str(timestamp)
        else:
            timestamp = str(timestamp)
        
        trade_item = html.Div([
            html.Div([
                html.Span(symbol, className='trade-symbol'),
                html.Span(side.upper(), className=f'trade-side {side}')
            ], className='trade-header'),
            html.Div([
                html.Span(f"${price:,.2f}"),
                html.Span(" · "),
                html.Span(f"QTY: {quantity:.4f}"),
                html.Span(" · "),
                html.Span(exchange.upper()),
                html.Span(" · "),
                html.Span(timestamp)
            ], className='trade-details')
        ], className=f'trade-item {side}')
        
        trade_items.append(trade_item)
    
    return html.Div(trade_items)

@app.callback(
    Output('agent-performance', 'children'),
    Input('interval-update', 'n_intervals')
)
def update_agent_performance(n):
    """Update agent performance metrics"""
    
    performance = trading_tools.get_agent_performance(days=7)
    
    if not performance or 'error' in performance[0]:
        return html.Div("No performance data available", style={'color': '#666', 'textAlign': 'center', 'padding': '40px'})
    
    perf_cards = []
    for perf in performance:
        agent_name = perf.get('agent', 'unknown').replace('_', ' ').upper()
        total_decisions = perf.get('total_decisions', 0)
        executed = perf.get('executed_decisions', 0)
        avg_conf = perf.get('avg_confidence', 0)
        win_rate = perf.get('win_rate', 0)
        total_pnl = perf.get('total_pnl', 0)
        
        # Performance badge
        if win_rate >= 70:
            badge_class = "excellent"
        elif win_rate >= 55:
            badge_class = "good"
        elif win_rate >= 40:
            badge_class = "average"
        else:
            badge_class = "poor"
        
        perf_card = html.Div([
            html.Div([
                html.Span(agent_name, style={'fontWeight': '600', 'fontSize': '13px'}),
                html.Span(f"{win_rate:.0f}%", className=f'perf-badge {badge_class}', style={'float': 'right'})
            ]),
            html.Div([
                html.Div([
                    html.Span("DECISIONS: ", style={'color': '#888', 'fontSize': '11px'}),
                    html.Span(f"{executed}/{total_decisions}", style={'color': '#fff', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
                ], style={'marginTop': '8px'}),
                html.Div([
                    html.Span("AVG CONF: ", style={'color': '#888', 'fontSize': '11px'}),
                    html.Span(f"{avg_conf:.1f}%", style={'color': '#00d4ff', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
                ], style={'marginTop': '5px'}),
                html.Div([
                    html.Span("P&L: ", style={'color': '#888', 'fontSize': '11px'}),
                    html.Span(f"${total_pnl:+,.2f}", style={'color': '#00ff88' if total_pnl >= 0 else '#ff5252', 'fontSize': '11px', 'fontFamily': 'JetBrains Mono, monospace'})
                ], style={'marginTop': '5px'}) if total_pnl != 0 else html.Div()
            ])
        ], style={
            'background': 'rgba(0, 0, 0, 0.3)',
            'padding': '15px',
            'borderRadius': '6px',
            'marginBottom': '12px',
            'border': '1px solid #2d3748'
        })
        
        perf_cards.append(perf_card)
    
    return html.Div(perf_cards)

@app.callback(
    Output('risk-dashboard', 'children'),
    Input('interval-update', 'n_intervals')
)
def update_risk_dashboard(n):
    """Update risk metrics dashboard"""
    
    risk_analysis = trading_tools.get_risk_analysis(days=7)
    
    if 'error' in risk_analysis:
        return html.Div("No risk data available", style={'color': '#666', 'textAlign': 'center', 'padding': '40px'})
    
    avg_daily_pnl = risk_analysis.get('avg_daily_pnl', 0)
    max_gain = risk_analysis.get('max_daily_gain', 0)
    max_loss = risk_analysis.get('max_daily_loss', 0)
    worst_drawdown = risk_analysis.get('worst_drawdown', 0)
    sharpe = risk_analysis.get('current_sharpe_ratio', 0)
    win_rate = risk_analysis.get('current_win_rate', 0)
    
    risk_display = html.Div([
        # Risk metrics grid
        html.Div([
            html.Div([
                html.Div("AVG DAILY P&L", className='metric-label'),
                html.Div(f"${avg_daily_pnl:+,.2f}", style={
                    'fontSize': '20px',
                    'fontWeight': '700',
                    'color': '#00ff88' if avg_daily_pnl >= 0 else '#ff5252',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("MAX DAILY GAIN", className='metric-label'),
                html.Div(f"${max_gain:+,.2f}", style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#00ff88',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("MAX DAILY LOSS", className='metric-label'),
                html.Div(f"${max_loss:+,.2f}", style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#ff5252',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("WORST DRAWDOWN", className='metric-label'),
                html.Div(f"{worst_drawdown:+,.2f}%", style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#ff5252',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("SHARPE RATIO", className='metric-label'),
                html.Div(f"{sharpe:.2f}", style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#00d4ff',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("WIN RATE", className='metric-label'),
                html.Div(f"{win_rate:.1f}%", style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#00ff88' if win_rate >= 50 else '#ff9800',
                    'fontFamily': 'JetBrains Mono, monospace'
                })
            ])
        ])
    ])
    
    return risk_display

@app.callback(
    [Output('chat-history', 'children'),
     Output('chat-input', 'value'),
     Output('chat-store', 'data')],
    [Input('chat-send', 'n_clicks')],
    [State('chat-input', 'value'),
     State('chat-store', 'data')]
)
def handle_chat(n_clicks, user_message, conversation_history):
    """Handle chat with GPT-4o function calling"""
    
    if not user_message or n_clicks == 0:
        welcome_msg = html.Div([
            html.Div([
                html.Div("AI ASSISTANT", className='chat-message-header'),
                html.Div("👋 Hello! I'm your AI trading assistant powered by GPT-4o with full database access. I can analyze trades, explain agent decisions, provide market insights, and answer questions about your portfolio. What would you like to know?", 
                        className='chat-message-content')
            ], className='chat-message assistant')
        ])
        return welcome_msg, "", []
    
    # Get LLM response with function calling
    llm_response = chat_with_gpt4o(user_message, conversation_history)
    
    # Update conversation history
    conversation_history.append({'role': 'user', 'content': user_message})
    conversation_history.append({'role': 'assistant', 'content': llm_response})
    
    # Keep only last 10 messages
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]
    
    # Display chat messages
    chat_display = []
    for msg in conversation_history:
        is_user = msg['role'] == 'user'
        chat_msg = html.Div([
            html.Div("YOU" if is_user else "AI ASSISTANT", className='chat-message-header'),
            html.Div(msg['content'], className='chat-message-content')
        ], className=f'chat-message {"" if is_user else "assistant"}')
        chat_display.append(chat_msg)
    
    return html.Div(chat_display), "", conversation_history

if __name__ == '__main__':
    print("=" * 100)
    print("🚀 PROFESSIONAL CRYPTO TRADING TERMINAL")
    print("=" * 100)
    print(f"📍 Access URL: http://192.34.59.191:3000")
    print(f"🔐 Username: admin")
    print(f"🔑 Password: CryptoTrader2024!")
    print("=" * 100)
    print("✨ Features:")
    print("   • Bloomberg Terminal-inspired professional UI")
    print("   • GPT-4o with function calling for intelligent chat")
    print("   • Deep agent insights with full reasoning")
    print("   • Orchestrator visualization")
    print("   • Agent performance metrics")
    print("   • Advanced risk dashboard")
    print("   • Real-time portfolio tracking")
    print("=" * 100)
    
    app.run(host='0.0.0.0', port=3000, debug=False)
