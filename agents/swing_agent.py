
#!/usr/bin/env python3
import json
import time
import psycopg2
import redis
from datetime import datetime
import numpy as np

class SwingAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
    def calculate_swing_signals(self, symbol):
        """Calculate swing trading signals based on medium-term trends"""
        try:
            # Get historical data
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT close, high, low FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 100
            """, (symbol,))
            data = cursor.fetchall()
            cursor.close()
            
            if len(data) < 50:
                return None
            
            closes = np.array([float(row[0]) for row in data])
            highs = np.array([float(row[1]) for row in data])
            lows = np.array([float(row[2]) for row in data])
            
            # Calculate moving averages
            ma_20 = np.mean(closes[:20])
            ma_50 = np.mean(closes[:50])
            
            # Calculate RSI
            deltas = np.diff(closes)
            gains = deltas.copy()
            losses = deltas.copy()
            gains[gains < 0] = 0
            losses[losses > 0] = 0
            losses = abs(losses)
            
            avg_gain = np.mean(gains[:14])
            avg_loss = np.mean(losses[:14])
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            signal = None
            confidence = 0
            
            # Swing trading logic
            if closes[0] > ma_20 > ma_50 and rsi < 70:
                signal = 'BUY'
                confidence = 70
            elif closes[0] < ma_20 < ma_50 and rsi > 30:
                signal = 'SELL'
                confidence = 70
            
            if signal:
                decision = {
                    'symbol': symbol,
                    'signal': signal,
                    'price': float(closes[0]),
                    'confidence': confidence,
                    'strategy': 'swing',
                    'ma_20': float(ma_20),
                    'ma_50': float(ma_50),
                    'rsi': float(rsi)
                }
                
                # Store decision
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_decisions (agent, decision, reasoning, confidence)
                    VALUES (%s, %s, %s, %s)
                """, ('swing_agent', json.dumps(decision),
                      f"MA20: {ma_20:.2f}, MA50: {ma_50:.2f}, RSI: {rsi:.2f}",
                      confidence))
                self.db_conn.commit()
                cursor.close()
                
                # Publish to Redis
                self.redis_client.publish('trading_signals', json.dumps(decision))
                
                print(f"[{datetime.now()}] Swing signal: {signal} {symbol} @ ${closes[0]:.2f} (RSI: {rsi:.1f})")
                
                return decision
            
        except Exception as e:
            print(f"Error calculating swing signals for {symbol}: {e}")
        
        return None
    
    def run(self):
        """Main loop"""
        print(f"Swing Agent started at {datetime.now()}")
        while True:
            try:
                for symbol in self.config['trading_pairs']:
                    self.calculate_swing_signals(symbol)
                    time.sleep(5)
                
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    agent = SwingAgent()
    agent.run()
