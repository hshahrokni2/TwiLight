import psycopg2
from psycopg2 import pool
import json
import time
import redis
from datetime import datetime
import numpy as np

class ScalpingAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Use connection pool instead of single connection
        self.db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            **self.config['database']
        )
        self.redis_client = redis.Redis(**self.config['redis'])
    
    def get_db_connection(self):
        """Get a connection from the pool with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = self.db_pool.getconn()
                # Test the connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return conn
            except Exception as e:
                print(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
    
    def return_db_connection(self, conn):
        """Return connection to pool"""
        try:
            self.db_pool.putconn(conn)
        except Exception as e:
            print(f"Error returning connection: {e}")
        
    def calculate_signals(self, symbol):
        """Calculate scalping signals based on short-term price movements"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get recent price data
            cursor.execute("""
                SELECT close, volume FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 20
            """, (symbol,))
            
            data = cursor.fetchall()
            cursor.close()
            
            if len(data) < 10:
                return None
            
            prices = [float(row[0]) for row in data]
            volumes = [float(row[1]) for row in data]
            
            # Calculate momentum
            price_change = ((prices[0] - prices[5]) / prices[5]) * 100
            volume_avg = np.mean(volumes[:5])
            volume_spike = volumes[0] > volume_avg * 1.5
            
            signal = None
            confidence = 0
            
            if price_change > 0.5 and volume_spike:
                signal = 'buy'
                confidence = min(abs(price_change) * 10, 95)
            elif price_change < -0.5 and volume_spike:
                signal = 'sell'
                confidence = min(abs(price_change) * 10, 95)
            
            if signal:
                decision = {
                    'agent': 'scalping',
                    'symbol': symbol,
                    'signal': signal,
                    'price': prices[0],
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log decision to database
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_decisions 
                    (agent_name, symbol, decision, confidence, reasoning, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    'scalping',
                    symbol,
                    signal,
                    confidence,
                    f'Price change: {price_change:.2f}%, Volume spike: {volume_spike}'
                ))
                conn.commit()
                cursor.close()
                
                # Publish to Redis for execution agent
                self.redis_client.publish('trading_signals', json.dumps(decision))
                
                print(f"[{datetime.now()}] Scalping signal: {signal} {symbol} @ ${prices[0]:.2f} (confidence: {confidence}%)")
                
                return decision
            
        except Exception as e:
            print(f"Error calculating signals for {symbol}: {e}")
        finally:
            if conn:
                self.return_db_connection(conn)
        
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
