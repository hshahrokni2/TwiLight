
#!/usr/bin/env python3
import ccxt
import json
import time
import psycopg2
import redis
from datetime import datetime

class ExecutionAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.exchanges = {}
        if self.config['exchanges']['binance']['enabled']:
            self.exchanges['binance'] = ccxt.binance({
                'apiKey': self.config['exchanges']['binance']['api_key'],
                'secret': self.config['exchanges']['binance']['api_secret'],
                'enableRateLimit': True
            })
        
        if self.config['exchanges']['kraken']['enabled']:
            self.exchanges['kraken'] = ccxt.kraken({
                'apiKey': self.config['exchanges']['kraken']['api_key'],
                'secret': self.config['exchanges']['kraken']['api_secret'],
                'enableRateLimit': True
            })
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
    def execute_trade(self, signal):
        """Execute a trading signal"""
        try:
            symbol = signal['symbol']
            side = signal['signal'].lower()
            
            if side not in ['buy', 'sell', 'close']:
                return
            
            # Get available capital
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT available_capital FROM risk_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            available_capital = float(result[0]) if result else self.config['initial_capital']
            
            # Calculate position size
            max_position = available_capital * self.config['risk_management']['max_position_size']
            
            # Use first available exchange
            exchange_name = list(self.exchanges.keys())[0]
            exchange = self.exchanges[exchange_name]
            
            # Get current price
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Calculate amount
            amount = max_position / current_price
            
            # Round to exchange precision
            markets = exchange.load_markets()
            market = markets[symbol]
            amount = exchange.amount_to_precision(symbol, amount)
            
            if side == 'buy':
                print(f"[{datetime.now()}] Executing BUY {amount} {symbol} @ ${current_price}")
                # In production, uncomment this:
                # order = exchange.create_market_buy_order(symbol, amount)
                order = {'id': f'sim_{int(time.time())}', 'status': 'closed', 'filled': amount}
                
                # Record trade
                cursor.execute("""
                    INSERT INTO trades (exchange, symbol, side, price, amount, cost, agent, status, order_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (exchange_name, symbol, 'buy', current_price, amount, 
                      float(amount) * current_price, signal.get('strategy', 'unknown'),
                      order['status'], order['id']))
                
                # Create position
                cursor.execute("""
                    INSERT INTO positions (exchange, symbol, side, entry_price, current_price, amount, agent, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (exchange_name, symbol, 'long', current_price, current_price, amount,
                      signal.get('strategy', 'unknown'), 'open'))
                
            elif side == 'sell':
                print(f"[{datetime.now()}] Executing SELL {amount} {symbol} @ ${current_price}")
                # In production, uncomment this:
                # order = exchange.create_market_sell_order(symbol, amount)
                order = {'id': f'sim_{int(time.time())}', 'status': 'closed', 'filled': amount}
                
                # Record trade
                cursor.execute("""
                    INSERT INTO trades (exchange, symbol, side, price, amount, cost, agent, status, order_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (exchange_name, symbol, 'sell', current_price, amount,
                      float(amount) * current_price, signal.get('strategy', 'unknown'),
                      order['status'], order['id']))
            
            self.db_conn.commit()
            cursor.close()
            
            print(f"[{datetime.now()}] Trade executed successfully: {side.upper()} {symbol}")
            
        except Exception as e:
            print(f"Error executing trade: {e}")
    
    def run(self):
        """Main loop - listen for approved signals"""
        print(f"Execution Agent started at {datetime.now()}")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('approved_signals')
        
        while True:
            try:
                message = pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    signal = json.loads(message['data'])
                    self.execute_trade(signal)
                
                time.sleep(1)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    agent = ExecutionAgent()
    agent.run()
