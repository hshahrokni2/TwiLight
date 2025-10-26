
#!/usr/bin/env python3
import json
import time
import psycopg2
import requests
from datetime import datetime
import redis

import sys
import os

# Add parent directory to path to import agent_config_loader
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agent_config_loader import load_agent_config

class ResearchAgent:
    def __init__(self, config_path='config.json'):
        self.config = load_agent_config(config_path)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
    def analyze_market_sentiment(self, symbol):
        """Use LLM to analyze market sentiment"""
        try:
            # Get recent market data
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT close, volume FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 100
            """, (symbol,))
            data = cursor.fetchall()
            cursor.close()
            
            if not data:
                return None
            
            # Prepare prompt for LLM
            prices = [float(row[0]) for row in data]
            volumes = [float(row[1]) for row in data]
            
            prompt = f"""Analyze the following market data for {symbol}:
Recent prices: {prices[:20]}
Recent volumes: {volumes[:20]}
Current price: ${prices[0]}
Price change: {((prices[0] - prices[-1]) / prices[-1] * 100):.2f}%

Provide a brief analysis (2-3 sentences) on:
1. Market sentiment (bullish/bearish/neutral)
2. Key support/resistance levels
3. Trading recommendation
"""
            
            # Use Perplexity for real-time market analysis
            headers = {
                'Authorization': f"Bearer {self.config['llm_providers']['perplexity']['api_key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.config['llm_providers']['perplexity']['model'],
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 500
            }
            
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                analysis = response.json()['choices'][0]['message']['content']
                
                # Store decision
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_decisions (agent, decision, reasoning, confidence)
                    VALUES (%s, %s, %s, %s)
                """, ('research_agent', f"Analysis for {symbol}", analysis, 75.0))
                self.db_conn.commit()
                cursor.close()
                
                # Cache in Redis
                self.redis_client.setex(
                    f"research:{symbol}:analysis",
                    1800,  # 30 minutes
                    analysis
                )
                
                print(f"[{datetime.now()}] Research analysis for {symbol} completed")
                return analysis
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
        
        return None
    
    def run(self):
        """Main loop"""
        print(f"Research Agent started at {datetime.now()}")
        while True:
            try:
                for symbol in self.config['trading_pairs']:
                    self.analyze_market_sentiment(symbol)
                    time.sleep(10)
                
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    agent = ResearchAgent()
    agent.run()
