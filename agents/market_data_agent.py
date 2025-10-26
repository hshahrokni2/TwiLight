#!/usr/bin/env python3
import ccxt
import json
import time
import psycopg2
from datetime import datetime
import redis

class MarketDataAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Use Kraken since Binance is geo-blocked
        self.exchange = ccxt.kraken({
            'apiKey': self.config['kraken_api_key'],
            'secret': self.config['kraken_api_secret'],
            'enableRateLimit': True
        })
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        try:
            self.redis_client = redis.Redis(**self.config['redis'])
        except:
            self.redis_client = None
        
    def fetch_and_store_data(self):
        """Fetch market data from Kraken and store in database"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        
        for symbol in symbols:
            try:
                # Fetch OHLCV data
                ohlcv = self.exchange.fetch_ohlcv(symbol, '5m', limit=10)
                
                # Store in database
                cursor = self.db_conn.cursor()
                for candle in ohlcv:
                    timestamp = datetime.fromtimestamp(candle[0]/1000)
                    cursor.execute("""
                        INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume, exchange)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (symbol, timestamp, candle[1], candle[2], candle[3], candle[4], candle[5], 'kraken'))
                
                self.db_conn.commit()
                cursor.close()
                
                # Store latest in Redis for quick access
                if self.redis_client:
                    latest = ohlcv[-1]
                    data = {
                        'timestamp': latest[0],
                        'open': latest[1],
                        'high': latest[2],
                        'low': latest[3],
                        'close': latest[4],
                        'volume': latest[5]
                    }
                    self.redis_client.setex(
                        f"kraken:{symbol}:latest",
                        300,
                        json.dumps(data)
                    )
                
                print(f"[{datetime.now()}] Fetched {symbol}: ${ohlcv[-1][4]:.2f}")
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
            
            time.sleep(1)
    
    def run(self):
        """Main loop"""
        print(f"Market Data Agent started at {datetime.now()}")
        print("Using Kraken exchange (Binance geo-blocked)")
        
        while True:
            try:
                self.fetch_and_store_data()
                time.sleep(60)  # Fetch every minute
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    agent = MarketDataAgent()
    agent.run()
