
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

def init_database():
    # Check if we're on Railway or local
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # On Railway, database is already created - just initialize tables
        print("🌐 Running on Railway - using provided database")
        try:
            # Parse DATABASE_URL
            import urllib.parse as urlparse
            url = urlparse.urlparse(database_url)
            
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port or 5432,
                database=url.path[1:],
                user=url.username,
                password=url.password
            )
        except Exception as e:
            print(f"❌ Error connecting to Railway database: {e}")
            print("⚠️  Continuing without database initialization...")
            return
    else:
        # Local development - create database if needed
        print("🏠 Running locally - setting up local database")
        try:
            conn = psycopg2.connect(
                host="localhost",
                user="postgres",
                password="postgres"
            )
        except Exception as e:
            print(f"❌ Error connecting to local PostgreSQL: {e}")
            print("⚠️  Make sure PostgreSQL is running locally")
            sys.exit(1)
    
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    if not database_url:
        # Only create database and user for local development
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
    else:
        # On Railway, already connected to the database
        print("✅ Connected to Railway database")
    
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
