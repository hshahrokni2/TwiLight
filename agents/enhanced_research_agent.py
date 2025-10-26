#!/usr/bin/env python3
"""
Enhanced Research Agent with Detailed Reasoning
Analyzes market sentiment and logs detailed decision-making process
"""

import json
import time
import psycopg2
import requests
from datetime import datetime
import redis
import ccxt

class EnhancedResearchAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        self.redis_client = redis.Redis(**self.config['redis'])
        
        # Initialize exchange for market data
        self.exchange = ccxt.kraken({
            'apiKey': self.config.get('kraken_api_key'),
            'secret': self.config.get('kraken_api_secret'),
            'timeout': 10000,
            'enableRateLimit': True
        })
    
    def fetch_market_data(self, symbol, timeframe='1h', limit=100):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"Error fetching market data for {symbol}: {e}")
            return []
    
    def calculate_technical_indicators(self, ohlcv_data):
        """Calculate technical indicators"""
        if not ohlcv_data or len(ohlcv_data) < 20:
            return {}
        
        closes = [candle[4] for candle in ohlcv_data]
        volumes = [candle[5] for candle in ohlcv_data]
        
        # Simple Moving Averages
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
        
        # Price changes
        current_price = closes[-1]
        price_change_1h = ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) > 1 else 0
        price_change_24h = ((closes[-1] - closes[-24]) / closes[-24] * 100) if len(closes) >= 24 else 0
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Trend detection
        if current_price > sma_20 > sma_50:
            trend = "STRONG UPTREND"
        elif current_price > sma_20:
            trend = "UPTREND"
        elif current_price < sma_20 < sma_50:
            trend = "STRONG DOWNTREND"
        elif current_price < sma_20:
            trend = "DOWNTREND"
        else:
            trend = "SIDEWAYS"
        
        return {
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'volume_ratio': volume_ratio,
            'trend': trend
        }
    
    def analyze_with_llm(self, symbol, technical_data):
        """Use LLM for deep market analysis"""
        try:
            prompt = f"""As a professional cryptocurrency analyst, provide a detailed market analysis for {symbol}.

Technical Data:
- Current Price: ${technical_data['current_price']:,.2f}
- 20-period SMA: ${technical_data['sma_20']:,.2f}
- 50-period SMA: ${technical_data['sma_50']:,.2f}
- 1-hour Change: {technical_data['price_change_1h']:+.2f}%
- 24-hour Change: {technical_data['price_change_24h']:+.2f}%
- Volume Ratio: {technical_data['volume_ratio']:.2f}x
- Detected Trend: {technical_data['trend']}

Provide a comprehensive analysis covering:
1. **Market Sentiment**: Current bullish/bearish momentum
2. **Key Levels**: Support and resistance zones
3. **Trading Opportunity**: Specific entry/exit recommendations with reasoning
4. **Risk Factors**: What could invalidate this analysis
5. **Confidence Level**: Your confidence in this analysis (0-100%)

Be specific, actionable, and professional."""

            headers = {
                'Authorization': f"Bearer {self.config.get('openai_api_key')}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert cryptocurrency market analyst with deep knowledge of technical analysis and market psychology.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 800,
                'temperature': 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                analysis = response.json()['choices'][0]['message']['content']
                
                # Extract confidence level from analysis
                confidence = 70.0  # Default
                if 'confidence' in analysis.lower():
                    # Try to extract confidence number
                    import re
                    conf_match = re.search(r'confidence[:\s]+(\d+)', analysis.lower())
                    if conf_match:
                        confidence = float(conf_match.group(1))
                
                return analysis, confidence
            else:
                print(f"LLM API Error: {response.status_code} - {response.text}")
                return None, 0
                
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return None, 0
    
    def log_decision(self, symbol, decision_type, reasoning, confidence):
        """Log detailed decision to database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO agent_decisions (agent, decision, reasoning, confidence, executed)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'research_agent',
                f"{decision_type} Analysis: {symbol}",
                reasoning,
                confidence,
                False
            ))
            self.db_conn.commit()
            cursor.close()
            print(f"✓ Logged {decision_type} decision for {symbol}")
        except Exception as e:
            print(f"Error logging decision: {e}")
            self.db_conn.rollback()
    
    def analyze_symbol(self, symbol):
        """Complete analysis pipeline for a symbol"""
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing {symbol}...")
        print(f"{'='*60}")
        
        # Step 1: Fetch market data
        print("📊 Fetching market data...")
        ohlcv_data = self.fetch_market_data(symbol, timeframe='1h', limit=100)
        
        if not ohlcv_data:
            print(f"⚠️  No market data available for {symbol}")
            return
        
        # Step 2: Calculate technical indicators
        print("📈 Calculating technical indicators...")
        technical_data = self.calculate_technical_indicators(ohlcv_data)
        
        print(f"   Current Price: ${technical_data['current_price']:,.2f}")
        print(f"   Trend: {technical_data['trend']}")
        print(f"   24h Change: {technical_data['price_change_24h']:+.2f}%")
        
        # Step 3: LLM Analysis
        print("🤖 Performing deep LLM analysis...")
        llm_analysis, confidence = self.analyze_with_llm(symbol, technical_data)
        
        if llm_analysis:
            print(f"✓ Analysis complete (Confidence: {confidence}%)")
            
            # Step 4: Generate trading decision
            decision_type = "MARKET ANALYSIS"
            
            # Determine action based on trend and analysis
            if technical_data['trend'] in ['STRONG UPTREND', 'UPTREND'] and confidence > 65:
                decision_type = "BULLISH SIGNAL"
            elif technical_data['trend'] in ['STRONG DOWNTREND', 'DOWNTREND'] and confidence > 65:
                decision_type = "BEARISH SIGNAL"
            
            # Create comprehensive reasoning
            comprehensive_reasoning = f"""
## Technical Analysis Summary

**Current Market State:**
- Price: ${technical_data['current_price']:,.2f}
- 20-SMA: ${technical_data['sma_20']:,.2f}
- 50-SMA: ${technical_data['sma_50']:,.2f}
- Trend: {technical_data['trend']}
- 24h Change: {technical_data['price_change_24h']:+.2f}%
- Volume: {technical_data['volume_ratio']:.2f}x average

**Detailed Analysis:**
{llm_analysis}

**Analysis Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Step 5: Log to database
            self.log_decision(symbol, decision_type, comprehensive_reasoning, confidence)
            
            # Cache in Redis
            self.redis_client.setex(
                f"research:{symbol}:analysis",
                1800,  # 30 minutes
                comprehensive_reasoning
            )
            
            print(f"✓ Decision logged and cached")
        else:
            print("⚠️  LLM analysis failed")
        
        print(f"{'='*60}\n")
    
    def run(self):
        """Main loop"""
        print("="*80)
        print("🚀 Enhanced Research Agent Started")
        print("="*80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📊 Will analyze:", ', '.join(self.config['trading_pairs']))
        print("="*80)
        
        cycle = 0
        while True:
            try:
                cycle += 1
                print(f"\n🔄 Analysis Cycle #{cycle}")
                
                for symbol in self.config['trading_pairs']:
                    self.analyze_symbol(symbol)
                    time.sleep(30)  # Wait between symbols
                
                print(f"\n✓ Cycle #{cycle} complete. Waiting 10 minutes...")
                time.sleep(600)  # Run every 10 minutes
                
            except KeyboardInterrupt:
                print("\n⚠️  Shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    agent = EnhancedResearchAgent()
    agent.run()
