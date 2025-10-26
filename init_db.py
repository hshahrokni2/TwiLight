
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create database
    cursor.execute("DROP DATABASE IF EXISTS crypto_trading")
    cursor.execute("CREATE DATABASE crypto_trading")
    print("Database created successfully")
    
    # Create user
    cursor.execute("DROP USER IF EXISTS trader")
    cursor.execute("CREATE USER trader WITH PASSWORD 'trader_password_2024'")
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE crypto_trading TO trader")
    print("User created successfully")
    
    cursor.close()
    conn.close()
    
    # Connect to the new database
    conn = psycopg2.connect(
        host="localhost",
        database="crypto_trading",
        user="trader",
        password="trader_password_2024"
    )
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exchange VARCHAR(50),
            symbol VARCHAR(20),
            side VARCHAR(10),
            price DECIMAL(20, 8),
            amount DECIMAL(20, 8),
            cost DECIMAL(20, 8),
            fee DECIMAL(20, 8),
            agent VARCHAR(50),
            status VARCHAR(20),
            order_id VARCHAR(100)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exchange VARCHAR(50),
            symbol VARCHAR(20),
            side VARCHAR(10),
            entry_price DECIMAL(20, 8),
            current_price DECIMAL(20, 8),
            amount DECIMAL(20, 8),
            unrealized_pnl DECIMAL(20, 8),
            realized_pnl DECIMAL(20, 8),
            agent VARCHAR(50),
            status VARCHAR(20)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exchange VARCHAR(50),
            symbol VARCHAR(20),
            timeframe VARCHAR(10),
            open DECIMAL(20, 8),
            high DECIMAL(20, 8),
            low DECIMAL(20, 8),
            close DECIMAL(20, 8),
            volume DECIMAL(20, 8)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_decisions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent VARCHAR(50),
            decision TEXT,
            reasoning TEXT,
            confidence DECIMAL(5, 2),
            executed BOOLEAN DEFAULT FALSE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_capital DECIMAL(20, 8),
            available_capital DECIMAL(20, 8),
            total_exposure DECIMAL(20, 8),
            daily_pnl DECIMAL(20, 8),
            total_pnl DECIMAL(20, 8),
            win_rate DECIMAL(5, 2),
            sharpe_ratio DECIMAL(10, 4),
            max_drawdown DECIMAL(5, 2)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX idx_trades_timestamp ON trades(timestamp)
    """)
    cursor.execute("""
        CREATE INDEX idx_trades_symbol ON trades(symbol)
    """)
    cursor.execute("""
        CREATE INDEX idx_positions_symbol ON positions(symbol)
    """)
    cursor.execute("""
        CREATE INDEX idx_market_data_symbol ON market_data(symbol, timestamp)
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("All tables created successfully")

if __name__ == "__main__":
    init_database()
