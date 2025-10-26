
#!/usr/bin/env python3
import json
import time
import psycopg2
import redis
from datetime import datetime

class RiskManagerAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
    def check_risk_limits(self, signal):
        """Check if a trading signal passes risk management rules"""
        try:
            cursor = self.db_conn.cursor()
            
            # Get current portfolio metrics
            cursor.execute("""
                SELECT total_capital, available_capital, total_exposure, daily_pnl
                FROM risk_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if not result:
                total_capital = self.config['initial_capital']
                available_capital = total_capital
                total_exposure = 0
                daily_pnl = 0
            else:
                total_capital, available_capital, total_exposure, daily_pnl = result
                total_capital = float(total_capital)
                available_capital = float(available_capital)
                total_exposure = float(total_exposure)
                daily_pnl = float(daily_pnl)
            
            # Check daily loss limit
            if daily_pnl < -total_capital * self.config['risk_management']['max_daily_loss']:
                print(f"[{datetime.now()}] RISK ALERT: Daily loss limit exceeded")
                cursor.close()
                return False
            
            # Check position size limit
            max_position_value = total_capital * self.config['risk_management']['max_position_size']
            
            # Check if we have enough capital
            if available_capital < max_position_value * 0.1:  # Need at least 10% of max position
                print(f"[{datetime.now()}] RISK ALERT: Insufficient capital")
                cursor.close()
                return False
            
            # Check total exposure
            if total_exposure > total_capital * 0.8:  # Max 80% exposure
                print(f"[{datetime.now()}] RISK ALERT: Total exposure too high")
                cursor.close()
                return False
            
            cursor.close()
            print(f"[{datetime.now()}] Risk check passed for {signal.get('symbol', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"Error checking risk limits: {e}")
            return False
    
    def monitor_positions(self):
        """Monitor open positions for risk violations"""
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT id, symbol, entry_price, current_price, amount
                FROM positions
                WHERE status = 'open'
            """)
            positions = cursor.fetchall()
            
            for position in positions:
                pos_id, symbol, entry_price, current_price, amount = position
                entry_price = float(entry_price)
                current_price = float(current_price)
                
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check stop loss
                if pnl_pct <= -self.config['risk_management']['stop_loss_percentage']:
                    print(f"[{datetime.now()}] RISK ALERT: Stop loss triggered for {symbol}")
                    # Publish emergency close signal
                    close_signal = {
                        'symbol': symbol,
                        'signal': 'CLOSE',
                        'reason': 'stop_loss',
                        'position_id': pos_id,
                        'priority': 'HIGH'
                    }
                    self.redis_client.publish('trading_signals', json.dumps(close_signal))
            
            cursor.close()
            
        except Exception as e:
            print(f"Error monitoring positions: {e}")
    
    def run(self):
        """Main loop"""
        print(f"Risk Manager Agent started at {datetime.now()}")
        
        # Subscribe to trading signals
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('trading_signals')
        
        while True:
            try:
                # Check for new signals
                message = pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    signal = json.loads(message['data'])
                    if self.check_risk_limits(signal):
                        # Approve signal
                        self.redis_client.publish('approved_signals', json.dumps(signal))
                
                # Monitor existing positions
                self.monitor_positions()
                
                time.sleep(10)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    agent = RiskManagerAgent()
    agent.run()
