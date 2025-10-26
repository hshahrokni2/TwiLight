
#!/usr/bin/env python3
import json
import time
import psycopg2
from datetime import datetime

class PortfolioAgent:
    def __init__(self, config_path='/opt/crypto-trading/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_conn = psycopg2.connect(**self.config['database'])
        
    def calculate_portfolio_metrics(self):
        """Calculate and update portfolio metrics"""
        try:
            cursor = self.db_conn.cursor()
            
            # Get all open positions
            cursor.execute("""
                SELECT symbol, amount, entry_price, current_price
                FROM positions
                WHERE status = 'open'
            """)
            positions = cursor.fetchall()
            
            # Calculate total exposure
            total_exposure = sum(float(row[1]) * float(row[3]) for row in positions)
            
            # Get total capital
            cursor.execute("""
                SELECT total_capital FROM risk_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            total_capital = float(result[0]) if result else self.config['initial_capital']
            
            # Calculate available capital
            available_capital = total_capital - total_exposure
            
            # Calculate daily PnL
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM positions
                WHERE DATE(timestamp) = CURRENT_DATE
            """)
            result = cursor.fetchone()
            daily_pnl = float(result[0]) if result and result[0] else 0
            
            # Calculate total PnL
            total_pnl = total_capital - self.config['initial_capital']
            
            # Store metrics
            cursor.execute("""
                INSERT INTO risk_metrics (total_capital, available_capital, total_exposure, daily_pnl, total_pnl)
                VALUES (%s, %s, %s, %s, %s)
            """, (total_capital, available_capital, total_exposure, daily_pnl, total_pnl))
            
            self.db_conn.commit()
            cursor.close()
            
            print(f"[{datetime.now()}] Portfolio: Capital=${total_capital:.2f}, Exposure=${total_exposure:.2f}, PnL=${total_pnl:.2f}")
            
        except Exception as e:
            print(f"Error calculating portfolio metrics: {e}")
    
    def rebalance_portfolio(self):
        """Rebalance portfolio based on risk parameters"""
        try:
            cursor = self.db_conn.cursor()
            
            # Get current positions
            cursor.execute("""
                SELECT symbol, amount, entry_price, current_price
                FROM positions
                WHERE status = 'open'
            """)
            positions = cursor.fetchall()
            
            # Check if rebalancing is needed
            for position in positions:
                symbol, amount, entry_price, current_price = position
                pnl_pct = (float(current_price) - float(entry_price)) / float(entry_price)
                
                # Close position if stop loss or take profit hit
                if pnl_pct <= -self.config['risk_management']['stop_loss_percentage']:
                    print(f"[{datetime.now()}] Stop loss triggered for {symbol}")
                    # Signal to close position
                elif pnl_pct >= self.config['risk_management']['take_profit_percentage']:
                    print(f"[{datetime.now()}] Take profit triggered for {symbol}")
                    # Signal to close position
            
            cursor.close()
            
        except Exception as e:
            print(f"Error rebalancing portfolio: {e}")
    
    def run(self):
        """Main loop"""
        print(f"Portfolio Agent started at {datetime.now()}")
        while True:
            try:
                self.calculate_portfolio_metrics()
                self.rebalance_portfolio()
                time.sleep(60)  # Update every minute
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    agent = PortfolioAgent()
    agent.run()
