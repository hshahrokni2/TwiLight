
#!/usr/bin/env python3
import json
import time
import psycopg2
import redis
from datetime import datetime
import numpy as np

class ScalpingAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
    def calculate_signals(self, symbol):
        """Calculate scalping signals based on short-term price movements"""
        try:
            # Get recent price data
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT close, volume FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 20
            """, (symbol,))
            data = cursor.fetchall()
            cursor.close()
            
            if len(data) < 20:
                return None
            
            prices = np.array([float(row[0]) for row in data])
            volumes = np.array([float(row[1]) for row in data])
            
            # Simple scalping strategy: momentum + volume
            price_change = (prices[0] - prices[5]) / prices[5]
            volume_ratio = volumes[0] / np.mean(volumes[1:10])
            
            signal = None
            confidence = 0
            
            if price_change > 0.002 and volume_ratio > 1.5:
                signal = 'BUY'
                confidence = min(80, 60 + abs(price_change) * 1000)
            elif price_change < -0.002 and volume_ratio > 1.5:
                signal = 'SELL'
                confidence = min(80, 60 + abs(price_change) * 1000)
            
            if signal:
                decision = {
                    'symbol': symbol,
                    'signal': signal,
                    'price': float(prices[0]),
                    'confidence': confidence,
                    'strategy': 'scalping'
                }
                
                # Store decision
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_decisions (agent, decision, reasoning, confidence)
                    VALUES (%s, %s, %s, %s)
                """, ('scalping_agent', json.dumps(decision), 
                      f"Price change: {price_change:.4f}, Volume ratio: {volume_ratio:.2f}", 
                      confidence))
                self.db_conn.commit()
                cursor.close()
                
                # Publish to Redis for execution agent
                self.redis_client.publish('trading_signals', json.dumps(decision))
                
                print(f"[{datetime.now()}] Scalping signal: {signal} {symbol} @ ${prices[0]:.2f} (confidence: {confidence}%)")
                
                return decision
            
        except Exception as e:
            print(f"Error calculating signals for {symbol}: {e}")
        
        return None
    
    def run(self):
        """Main loop"""
        print(f"Scalping Agent started at {datetime.now()}")
        while True:
            try:
                for symbol in self.config['trading_pairs']:
                    self.calculate_signals(symbol)
                    time.sleep(2)
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    agent = ScalpingAgent()
    agent.run()
