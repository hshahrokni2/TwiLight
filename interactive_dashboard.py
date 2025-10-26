#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import psycopg2
import json
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, session, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
import openai

# Load config
with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

# Initialize Flask server
server = Flask(__name__)
server.secret_key = 'crypto-trading-secret-key-2024'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# User credentials (hashed password for "CryptoTrader2024!")
USERS = {
    'admin': generate_password_hash('CryptoTrader2024!')
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Initialize Dash app
app = dash.Dash(
    __name__, 
    server=server,
    external_stylesheets=[
        dbc.themes.CYBORG,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
    ],
    suppress_callback_exceptions=True
)

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Crypto Trading Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                transition: transform 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
            }
            .metric-card {
                text-align: center;
                padding: 20px;
            }
            .metric-value {
                font-size: 2.5rem;
                font-weight: bold;
                background: linear-gradient(45deg, #00ff88, #00ccff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #aaa;
                text-transform: uppercase;
            }
            .chat-container {
                height: 500px;
                display: flex;
                flex-direction: column;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 15px;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                margin-bottom: 15px;
                padding: 10px;
            }
            .chat-message {
                margin-bottom: 15px;
                padding: 12px 15px;
                border-radius: 10px;
                max-width: 80%;
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin-left: auto;
                text-align: right;
            }
            .assistant-message {
                background: rgba(255, 255, 255, 0.1);
                margin-right: auto;
            }
            .login-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                width: 100%;
                max-width: 400px;
                padding: 40px;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 20px;
            }
            .dashboard-title {
                background: linear-gradient(45deg, #00ff88, #00ccff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: bold;
            }
            .status-live {
                background: linear-gradient(45deg, #00ff88, #00cc66);
                color: #000;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: bold;
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

def login_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2("🚀 Crypto Trading System", className="dashboard-title text-center"),
                    html.P("Secure Login", className="text-center text-muted mb-4"),
                    dbc.Input(id="username-input", placeholder="Username", type="text", className="mb-3"),
                    dbc.Input(id="password-input", placeholder="Password", type="password", className="mb-3"),
                    dbc.Button("Login", id="login-button", color="primary", className="w-100 mb-3", size="lg"),
                    html.Div(id="login-alert")
                ], className="login-card")
            ], width=12)
        ], className="login-container")
    ], fluid=True)

def dashboard_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2([html.I(className="fas fa-chart-line mr-2"), "Crypto Trading Dashboard"], 
                           className="dashboard-title d-inline-block"),
                    html.Span("LIVE", className="status-live ml-3"),
                    dbc.Button([html.I(className="fas fa-sign-out-alt mr-2"), "Logout"],
                              id="logout-button", color="danger", size="sm", className="float-right")
                ])
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-wallet fa-2x mb-3", style={'color': '#00ff88'}),
                        html.Div("Total Capital", className="metric-label"),
                        html.Div(id="total-capital", className="metric-value")
                    ], className="metric-card")
                ])])
            ], width=3),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-calendar-day fa-2x mb-3", style={'color': '#00ccff'}),
                        html.Div("Daily PnL", className="metric-label"),
                        html.Div(id="daily-pnl", className="metric-value")
                    ], className="metric-card")
                ])])
            ], width=3),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-line fa-2x mb-3", style={'color': '#ff6b6b'}),
                        html.Div("Total PnL", className="metric-label"),
                        html.Div(id="total-pnl", className="metric-value")
                    ], className="metric-card")
                ])])
            ], width=3),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-coins fa-2x mb-3", style={'color': '#ffd93d'}),
                        html.Div("Open Positions", className="metric-label"),
                        html.Div(id="open-positions", className="metric-value")
                    ], className="metric-card")
                ])])
            ], width=3),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H4([html.I(className="fas fa-chart-area mr-2"), "Portfolio Value"]),
                    dcc.Graph(id="portfolio-chart", config={'displayModeBar': False})
                ])])
            ], width=8),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H4([html.I(className="fas fa-robot mr-2"), "AI Assistant"]),
                    html.Div([
                        html.Div(id="chat-messages", className="chat-messages"),
                        html.Div([
                            dbc.Input(id="chat-input", placeholder="Ask about portfolio...", type="text", style={'flex': '1'}),
                            dbc.Button(html.I(className="fas fa-paper-plane"), id="send-button", color="primary", className="ml-2")
                        ], style={'display': 'flex', 'gap': '10px'})
                    ], className="chat-container")
                ])])
            ], width=4)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H4([html.I(className="fas fa-exchange-alt mr-2"), "Recent Trades"]),
                    html.Div(id="recent-trades")
                ])])
            ], width=6),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H4([html.I(className="fas fa-briefcase mr-2"), "Open Positions"]),
                    html.Div(id="positions-table")
                ])])
            ], width=6)
        ]),
        
        dcc.Store(id='chat-history', data=[]),
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
    ], fluid=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

def get_db_connection():
    return psycopg2.connect(**config['database'])

openai.api_key = config.get('openai_api_key', '')

def chat_with_llm(user_message, chat_history):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT total_capital, daily_pnl, total_pnl FROM risk_metrics ORDER BY timestamp DESC LIMIT 1")
        metrics = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
        open_positions = cursor.fetchone()[0]
        
        cursor.execute("SELECT symbol, side, price, amount, timestamp FROM trades ORDER BY timestamp DESC LIMIT 5")
        recent_trades = cursor.fetchall()
        
        cursor.execute("SELECT symbol, entry_price, current_price, amount, pnl FROM positions WHERE status = 'open'")
        positions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = f"""You are an AI trading assistant. Current status:
Portfolio: ${metrics[0]:,.2f} capital, ${metrics[1]:,.2f} daily PnL, ${metrics[2]:,.2f} total PnL
Open Positions: {open_positions}
Recent Trades: {len(recent_trades)} trades
Answer concisely and professionally."""
        
        messages = [{"role": "system", "content": context}]
        for msg in chat_history[-5:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    return dashboard_layout() if pathname == '/dashboard' else login_layout()

@app.callback(
    [Output('url', 'pathname'), Output('login-alert', 'children')],
    Input('login-button', 'n_clicks'),
    [State('username-input', 'value'), State('password-input', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if username in USERS and check_password_hash(USERS[username], password):
        user = User(username)
        login_user(user)
        return '/dashboard', None
    return '/', dbc.Alert("Invalid credentials", color="danger")

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks):
    logout_user()
    return '/'

@app.callback(
    [Output('total-capital', 'children'), Output('daily-pnl', 'children'),
     Output('total-pnl', 'children'), Output('open-positions', 'children'),
     Output('portfolio-chart', 'figure'), Output('recent-trades', 'children'),
     Output('positions-table', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT total_capital, daily_pnl, total_pnl FROM risk_metrics ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        total_capital = f"${result[0]:,.2f}"
        daily_pnl = f"${result[1]:,.2f}"
        total_pnl = f"${result[2]:,.2f}"
    else:
        total_capital = f"${config['initial_capital']:,.2f}"
        daily_pnl = "$0.00"
        total_pnl = "$0.00"
    
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
    open_pos = cursor.fetchone()[0]
    
    cursor.execute("SELECT timestamp, total_capital FROM risk_metrics WHERE timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp")
    history = cursor.fetchall()
    
    if history:
        df = pd.DataFrame(history, columns=['timestamp', 'capital'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['capital'], mode='lines', name='Portfolio',
                                line=dict(color='#00ff88', width=3), fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.1)'))
        fig.update_layout(template='plotly_dark', height=350, margin=dict(l=20, r=20, t=20, b=20),
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    else:
        fig = go.Figure()
        fig.update_layout(template='plotly_dark', height=350, paper_bgcolor='rgba(0,0,0,0)')
    
    cursor.execute("SELECT timestamp, symbol, side, price, amount FROM trades ORDER BY timestamp DESC LIMIT 10")
    trades = cursor.fetchall()
    
    if trades:
        trades_table = dbc.Table([
            html.Thead(html.Tr([html.Th("Time"), html.Th("Symbol"), html.Th("Side"), html.Th("Price"), html.Th("Amount")])),
            html.Tbody([
                html.Tr([
                    html.Td(t[0].strftime("%H:%M:%S")),
                    html.Td(t[1]),
                    html.Td(html.Span(t[2].upper(), style={'background': '#00ff88' if t[2]=='buy' else '#ff6b6b', 
                                                           'color': '#000', 'padding': '5px 10px', 'borderRadius': '10px'})),
                    html.Td(f"${t[3]:,.2f}"),
                    html.Td(f"{t[4]:.6f}")
                ]) for t in trades
            ])
        ], bordered=True, dark=True, hover=True, size='sm')
    else:
        trades_table = html.P("No trades yet", className="text-muted text-center")
    
    cursor.execute("SELECT symbol, entry_price, current_price, pnl FROM positions WHERE status = 'open'")
    positions = cursor.fetchall()
    
    if positions:
        positions_table = dbc.Table([
            html.Thead(html.Tr([html.Th("Symbol"), html.Th("Entry"), html.Th("Current"), html.Th("PnL")])),
            html.Tbody([
                html.Tr([
                    html.Td(p[0]),
                    html.Td(f"${p[1]:,.2f}"),
                    html.Td(f"${p[2]:,.2f}"),
                    html.Td(html.Span(f"${p[3]:,.2f}", style={'color': '#00ff88' if p[3]>=0 else '#ff6b6b', 'fontWeight': 'bold'}))
                ]) for p in positions
            ])
        ], bordered=True, dark=True, hover=True, size='sm')
    else:
        positions_table = html.P("No open positions", className="text-muted text-center")
    
    cursor.close()
    conn.close()
    
    return total_capital, daily_pnl, total_pnl, str(open_pos), fig, trades_table, positions_table

@app.callback(
    [Output('chat-messages', 'children'), Output('chat-history', 'data'), Output('chat-input', 'value')],
    [Input('send-button', 'n_clicks'), Input('chat-input', 'n_submit')],
    [State('chat-input', 'value'), State('chat-history', 'data')],
    prevent_initial_call=True
)
def handle_chat(n_clicks, n_submit, message, chat_history):
    if not message or message.strip() == '':
        return dash.no_update, dash.no_update, dash.no_update
    
    chat_history.append({"role": "user", "content": message})
    ai_response = chat_with_llm(message, chat_history)
    chat_history.append({"role": "assistant", "content": ai_response})
    
    messages_ui = []
    for msg in chat_history[-10:]:
        if msg["role"] == "user":
            messages_ui.append(html.Div(msg["content"], className="chat-message user-message"))
        else:
            messages_ui.append(html.Div(msg["content"], className="chat-message assistant-message"))
    
    return messages_ui, chat_history, ''

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
